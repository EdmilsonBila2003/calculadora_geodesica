"""Projecção UTM (Transversa de Mercator) — séries clássicas (Snyder/Redfearn)."""
import math

K0 = 0.9996
FALSO_E = 500000.0
FALSO_N_SUL = 10000000.0


def zona_utm(lon: float) -> int:
    return int((lon + 180.0) // 6.0) % 60 + 1


def meridiano_central(zona: int) -> float:
    return -183.0 + 6.0 * zona


def _arco_meridiano(ell, phi):
    e2 = ell.e2
    e4, e6 = e2 ** 2, e2 ** 3
    return ell.a * (
        (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
        - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
        + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi)
        - (35 * e6 / 3072) * math.sin(6 * phi)
    )


def geodesicas_para_utm(ell, lat: float, lon: float, zona: int | None = None):
    """Devolve (zona, hemisfério 'N'/'S', E, N)."""
    if not -80.0 <= lat <= 84.0:
        raise ValueError("UTM só é definida para latitudes entre 80°S e 84°N.")
    zona = zona or zona_utm(lon)
    if not 1 <= zona <= 60:
        raise ValueError("A zona UTM deve estar entre 1 e 60.")
    phi = math.radians(lat)
    dlon = lon - meridiano_central(zona)
    dlon = (dlon + 180.0) % 360.0 - 180.0
    lam = math.radians(dlon)
    ep2, e2 = ell.ep2, ell.e2
    N = ell.a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    T = math.tan(phi) ** 2
    C = ep2 * math.cos(phi) ** 2
    A = lam * math.cos(phi)
    M = _arco_meridiano(ell, phi)
    x = K0 * N * (A + (1 - T + C) * A ** 3 / 6
                  + (5 - 18 * T + T ** 2 + 72 * C - 58 * ep2) * A ** 5 / 120)
    y = K0 * (M + N * math.tan(phi) * (A ** 2 / 2
              + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
              + (61 - 58 * T + T ** 2 + 600 * C - 330 * ep2) * A ** 6 / 720))
    hemi = "N" if lat >= 0 else "S"
    E = FALSO_E + x
    Nn = y + (FALSO_N_SUL if hemi == "S" else 0.0)
    return zona, hemi, E, Nn


def utm_para_geodesicas(ell, zona: int, hemi: str, E: float, N: float):
    """Devolve (lat°, lon°)."""
    hemi = hemi.strip().upper()
    if hemi not in ("N", "S"):
        raise ValueError("Hemisfério deve ser 'N' ou 'S'.")
    if not 1 <= zona <= 60:
        raise ValueError("A zona UTM deve estar entre 1 e 60.")
    ep2, e2 = ell.ep2, ell.e2
    x = E - FALSO_E
    y = N - (FALSO_N_SUL if hemi == "S" else 0.0)
    M = y / K0
    mu = M / (ell.a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
            + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    C1 = ep2 * math.cos(phi1) ** 2
    T1 = math.tan(phi1) ** 2
    w = 1 - e2 * math.sin(phi1) ** 2
    N1 = ell.a / math.sqrt(w)
    R1 = ell.a * (1 - e2) / w ** 1.5
    D = x / (N1 * K0)
    phi = phi1 - (N1 * math.tan(phi1) / R1) * (
        D ** 2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * D ** 4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * ep2 - 3 * C1 ** 2) * D ** 6 / 720)
    lam = (D - (1 + 2 * T1 + C1) * D ** 3 / 6
           + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * D ** 5 / 120) / math.cos(phi1)
    return math.degrees(phi), meridiano_central(zona) + math.degrees(lam)
