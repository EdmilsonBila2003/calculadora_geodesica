"""Reduções de observações, nivelamento, alturas e coordenadas locais (material da disciplina)."""
import math


def inclinada_zenital(S: float, z: float):
    """Dh = S sin z ; Δh = S cos z   (z em graus, contado do zénite)."""
    zr = math.radians(z)
    return S * math.sin(zr), S * math.cos(zr)


def inclinada_vertical(S: float, v: float, i: float = 0.0, p: float = 0.0):
    """Dh = S cos v ; Δh = S sin v ; ΔH = S sin v + i − p   (v em graus, do horizonte)."""
    vr = math.radians(v)
    dh = S * math.sin(vr)
    return S * math.cos(vr), dh, dh + i - p


def reduzir_ao_elipsoide(Dh: float, H: float, R: float) -> float:
    """D0 ≈ Dh · R / (R + H)."""
    if R + H == 0:
        raise ValueError("R + H não pode ser zero.")
    return Dh * R / (R + H)


def distancia_grelha(D0: float, k: float) -> float:
    """D_grelha ≈ k · D0."""
    return k * D0


def distancia_elipsoide_de_grelha(Dgrelha: float, k: float) -> float:
    if k == 0:
        raise ValueError("k não pode ser zero.")
    return Dgrelha / k


def desnivel(a: float, f: float) -> float:
    """ΔH = a − f."""
    return a - f


def circuito_nivelamento(atras, frente, HA: float | None = None, desnivel_conhecido: float | None = None):
    """ΔH_total = Σa − Σf; devolve (ΔH_total, H_final, erro_de_fecho)."""
    dh = sum(atras) - sum(frente)
    h_final = None if HA is None else HA + dh
    erro = None if desnivel_conhecido is None else dh - desnivel_conhecido
    return dh, h_final, erro


def altura_ortometrica(h: float, N: float) -> float:
    """H ≈ h − N."""
    return h - N


def altura_elipsoidal(H: float, N: float) -> float:
    """h ≈ H + N."""
    return H + N


def coordenadas_por_azimute(EA: float, NA: float, D: float, A: float):
    """ΔE = D sin A ; ΔN = D cos A ; devolve (ΔE, ΔN, EB, NB)."""
    ar = math.radians(A)
    dE, dN = D * math.sin(ar), D * math.cos(ar)
    return dE, dN, EA + dE, NA + dN


def azimute_distancia(EA: float, NA: float, EB: float, NB: float):
    """D = √(ΔE²+ΔN²) ; A = atan2(ΔE, ΔN) em [0, 360)."""
    dE, dN = EB - EA, NB - NA
    return math.hypot(dE, dN), math.degrees(math.atan2(dE, dN)) % 360.0
