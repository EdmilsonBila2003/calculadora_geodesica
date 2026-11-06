"""Fórmulas de Sodano (solução não iterativa, linhas curtas e longas).

Equações indicadas entre parênteses referem-se ao PDF 'Formulas_Geodesia.pdf'.
Entradas/saídas em graus e metros. α₂₋₁ devolvido é o azimute de 2 para 1.
"""
import math
from .utils import Directo, Inverso, norm_az, norm_lon


def _lat_reduzida(ell, B: float) -> float:
    """tan β = (1-f) tan B (Eq. 38/39 e 58/59); atan2 evita o ramo |B|>45°."""
    return math.atan2((1.0 - ell.f) * math.sin(B), math.cos(B))


def directo(ell, lat1: float, lon1: float, az12: float, s: float) -> Directo:
    f, b0, ep2 = ell.f, ell.b, ell.ep2
    B1, a12 = math.radians(lat1), math.radians(az12)
    beta1 = _lat_reduzida(ell, B1)
    sb1, cb1 = math.sin(beta1), math.cos(beta1)

    cos_b0 = cb1 * math.sin(a12)                                            # Eq. 40
    g = cb1 * math.cos(a12)                                                 # Eq. 41
    k = 1.0 + (ep2 / 2.0) * sb1 ** 2
    m1 = k * (1.0 - cos_b0 ** 2)                                               # Eq. 42
    ps = s / b0                                                             # Eq. 43
    sp, cp = math.sin(ps), math.cos(ps)
    a1 = k * (sb1 ** 2 * cp + g * sb1 * sp)                                 # Eq. 44

    e4 = ep2 ** 2
    phi0 = (ps                                                              # Eq. 45
            + a1 * (-(ep2 / 2.0) * sp)
            + m1 * (-(ep2 / 4.0) * ps + (ep2 / 4.0) * sp * cp)
            + a1 ** 2 * ((5.0 * e4 / 8.0) * sp * cp)
            + m1 ** 2 * ((11.0 * e4 / 64.0) * sp - (13.0 * e4 / 64.0) * sp * cp
                         - (e4 / 8.0) * ps * cp ** 2 + (5.0 * e4 / 32.0) * sp * cp ** 3)
            + a1 * m1 * ((3.0 * e4 / 8.0) * sp + (e4 / 4.0) * ps * cp
                         - (5.0 * e4 / 8.0) * sp * cp ** 2))
    sf, cf = math.sin(phi0), math.cos(phi0)

    num = g * cf - sb1 * sf
    az2 = math.atan2(cos_b0, num)          # Eq. 46 (azimute directo em 2)
    lam = math.atan2(sf * math.sin(a12), cb1 * cf - sb1 * sf * math.cos(a12))   # Eq. 47
    serie = (-f * ps + a1 * ((3.0 * f ** 2 / 2.0) * sp)
             + m1 * ((3.0 * f ** 2 / 4.0) * ps - (3.0 * f ** 2 / 4.0) * sp * cp))
    L = lam + cos_b0 * serie                                                # Eq. 48
    lon2 = lon1 + math.degrees(L)                                           # Eq. 49

    sin_b2 = sb1 * cf + g * sf                                              # Eq. 50
    cos_b2 = math.sqrt(cos_b0 ** 2 + num ** 2)                              # Eq. 51
    # Eq. 53/54: B2 a partir de β2. Usa-se a relação exacta tan B = tan β / (1-f)
    # em vez da série da Eq. 55 (cuja transcrição no PDF parece incompleta).
    B2 = math.atan2(sin_b2, (1.0 - f) * cos_b2)
    return Directo(math.degrees(B2), norm_lon(lon2), norm_az(math.degrees(az2) + 180.0))


def inverso(ell, lat1: float, lon1: float, lat2: float, lon2: float) -> Inverso:
    f, b0 = ell.f, ell.b
    B1, B2 = math.radians(lat1), math.radians(lat2)
    L = math.radians(norm_lon(lon2 - lon1))                                 # Eq. 57
    beta1, beta2 = _lat_reduzida(ell, B1), _lat_reduzida(ell, B2)

    a_ = math.sin(beta1) * math.sin(beta2)                                  # Eq. 60
    b_ = math.cos(beta1) * math.cos(beta2)                                  # Eq. 61
    cos_phi = a_ + b_ * math.cos(L)                                         # Eq. 62
    termo = math.sin(beta2 - beta1) + 2.0 * math.cos(beta2) * math.sin(beta1) * math.sin(L / 2.0) ** 2
    sin_phi = math.sqrt((math.sin(L) * math.cos(beta2)) ** 2 + termo ** 2)  # Eq. 63
    if sin_phi < 1e-15 and cos_phi > 0:
        return Inverso(0.0, 0.0, 0.0)
    phi = math.atan2(sin_phi, cos_phi)
    c = b_ * math.sin(L) / sin_phi                                          # Eq. 64
    m = 1.0 - c ** 2                                                        # Eq. 65

    sc = sin_phi * cos_phi
    p2_csc = phi ** 2 / sin_phi
    p2_cot = phi ** 2 * cos_phi / sin_phi
    f2 = f ** 2
    sb = ((1 + f + f2) * phi                                                # Eq. 66
          + a_ * ((f + f2) * sin_phi - (f2 / 2.0) * p2_csc)
          + m * (-(f + f2) / 2.0 * phi - (f + f2) / 2.0 * sc + (f2 / 2.0) * p2_cot)
          + a_ ** 2 * (-(f2 / 2.0) * sc)
          + m ** 2 * ((f2 / 16.0) * phi + (f2 / 16.0) * sc - (f2 / 2.0) * p2_cot
                      - (f2 / 8.0) * sin_phi * cos_phi ** 3)
          + a_ * m * ((f2 / 2.0) * p2_csc + (f2 / 2.0) * sin_phi * cos_phi ** 2))
    s = b0 * sb

    dif = c * ((f + f2) * phi                                               # Eq. 67
               + a_ * (-(f2 / 2.0) * sin_phi - f2 * p2_csc)
               + m * (-(5.0 * f2 / 4.0) * phi - (f2 / 4.0) * sc + f2 * p2_cot))
    lam = L + dif                                                           # λ = L + (λ-L)

    az1 = math.atan2(math.cos(beta2) * math.sin(lam),                       # Eq. 68
                     math.sin(beta2 - beta1) + 2.0 * math.cos(beta2) * math.sin(beta1) * math.sin(lam / 2.0) ** 2)
    # Azimute directo em 2 (equivalente à Eq. 77, mas com a esfera auxiliar em λ):
    az2 = math.atan2(math.cos(beta1) * math.sin(lam),
                     -math.sin(beta1) * math.cos(beta2) + math.cos(beta1) * math.sin(beta2) * math.cos(lam))
    return Inverso(s, norm_az(math.degrees(az1)), norm_az(math.degrees(az2) + 180.0))
