"""Fórmulas de Puissant (linhas curtas, ~80–100 km).

Equações indicadas entre parênteses referem-se ao PDF 'Formulas_Geodesia.pdf'.
Entradas/saídas em graus e metros.
"""
import math
from .utils import SIN1, Directo, Inverso, norm_az, norm_lon


def _raios(ell, phi):
    w2 = 1.0 - ell.e2 * math.sin(phi) ** 2
    M = ell.a * (1.0 - ell.e2) / w2 ** 1.5      # Eq. 3
    N = ell.a / math.sqrt(w2)                  # Eq. 4
    return M, N, w2


def directo(ell, lat1: float, lon1: float, az12: float, s: float) -> Directo:
    phi1, az = math.radians(lat1), math.radians(az12)
    e2 = ell.e2
    M1, N1, w2 = _raios(ell, phi1)

    B = 1.0 / (M1 * SIN1)                                                   # Eq. 5
    C = math.tan(phi1) / (2.0 * M1 * N1 * SIN1)                             # Eq. 6
    D = 3.0 * e2 * math.cos(phi1) * math.sin(phi1) * SIN1 / (2.0 * w2)      # Eq. 7
    E = (1.0 + 3.0 * math.tan(phi1) ** 2) / (6.0 * N1 ** 2)                 # Eq. 8
    h = B * s * math.cos(az)                                                # Eq. 9 [")

    s2sen2 = s ** 2 * math.sin(az) ** 2
    dphi = h - C * s2sen2 - h * E * s2sen2                                  # Eq. 10 ["]
    dphi_corr = dphi - D * dphi ** 2                                        # Eq. 11 ["]
    phi2 = phi1 + math.radians(dphi_corr / 3600.0)                          # Eq. 12

    _, N2, _ = _raios(ell, phi2)                                            # Eq. 13
    T = s * math.sin(az) / (N2 * math.cos(phi2))                            # Eq. 14
    dlam = (T / SIN1) * (1.0 - s ** 2 / (6.0 * N2 ** 2) + T ** 2 / 6.0)     # Eq. 15 ["]
    lon2 = lon1 + dlam / 3600.0                                             # Eq. 16

    az21 = _az_inverso(az12, lat1, lat2=math.degrees(phi2), dlam_sec=dlam)
    return Directo(math.degrees(phi2), norm_lon(lon2), az21)


def _convergencia(phi1, phi2, dlam_sec):
    """Convergência dos meridianos γ em segundos de arco (Eq. 17–21 / 29–30)."""
    phim = (phi1 + phi2) / 2.0
    F = (1.0 / 12.0) * math.sin(phim) * math.cos(phim) ** 2 * SIN1 ** 2
    dphi = phi2 - phi1
    return dlam_sec * math.sin(phim) / math.cos(dphi / 2.0) + F * dlam_sec ** 3


def _az_inverso(az12, lat1, lat2, dlam_sec):
    gam = _convergencia(math.radians(lat1), math.radians(lat2), dlam_sec)
    base = az12 + 180.0 if (az12 % 360.0) < 180.0 else az12 - 180.0         # Eq. 22
    return norm_az(base + gam / 3600.0)


def inverso(ell, lat1: float, lon1: float, lat2: float, lon2: float) -> Inverso:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam_deg = norm_lon(lon2 - lon1)
    M1, N1, _ = _raios(ell, phi1)
    M2, N2, _ = _raios(ell, phi2)
    Nm, Mm = (N1 + N2) / 2.0, (M1 + M2) / 2.0                               # Eq. 23, 24
    phim = (phi1 + phi2) / 2.0                                              # Eq. 25
    dphi = phi2 - phi1
    dlam = math.radians(dlam_deg)                                          # Δλ"·sin1" = Δλ [rad]

    x = dlam * math.cos(phim) * Nm                                          # Eq. 27
    y = dphi * math.cos(dlam / 2.0) * Mm                                    # Eq. 28
    if x == 0.0 and y == 0.0:
        return Inverso(0.0, 0.0, 0.0)

    gam_sec = _convergencia(phi1, phi2, dlam_deg * 3600.0)                  # Eq. 29, 30
    gam = math.radians(gam_sec / 3600.0)

    # Azimute da corda/médio: atan2 resolve os quadrantes da Eq. 32.
    az_medio = math.atan2(x, y)
    az12 = az_medio - gam / 2.0     # ver README: o PDF escreve '+γ/2' na Eq. 31
    s = math.hypot(x, y)            # equivale a x/sin(Az+γ/2) = y/cos(Az+γ/2) (Eq. 33)
    az12_deg = norm_az(math.degrees(az12))
    az21 = norm_az(az12_deg + (180.0 if az12_deg < 180.0 else -180.0) + gam_sec / 3600.0)  # Eq. 34
    return Inverso(s, az12_deg, az21)
