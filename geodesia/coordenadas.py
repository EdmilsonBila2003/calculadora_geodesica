"""Coordenadas geodésicas (φ, λ, h) <-> cartesianas geocêntricas (X, Y, Z)."""
import math


def geodesicas_para_cartesianas(ell, lat: float, lon: float, h: float = 0.0):
    phi, lam = math.radians(lat), math.radians(lon)
    N = ell.a / math.sqrt(1.0 - ell.e2 * math.sin(phi) ** 2)
    X = (N + h) * math.cos(phi) * math.cos(lam)
    Y = (N + h) * math.cos(phi) * math.sin(lam)
    Z = (N * (1.0 - ell.e2) + h) * math.sin(phi)
    return X, Y, Z


def cartesianas_para_geodesicas(ell, X: float, Y: float, Z: float):
    """Método iterativo; devolve (lat°, lon°, h)."""
    lon = math.atan2(Y, X)
    p = math.hypot(X, Y)
    if p == 0.0:                      # sobre o eixo de rotação
        lat = math.copysign(math.pi / 2, Z)
        return math.degrees(lat), 0.0, abs(Z) - ell.b
    lat = math.atan2(Z, p * (1.0 - ell.e2))
    for _ in range(20):
        N = ell.a / math.sqrt(1.0 - ell.e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - N if abs(lat) < math.pi / 4 else Z / math.sin(lat) - N * (1.0 - ell.e2)
        nova = math.atan2(Z, p * (1.0 - ell.e2 * N / (N + h)))
        if abs(nova - lat) < 1e-14:
            lat = nova
            break
        lat = nova
    N = ell.a / math.sqrt(1.0 - ell.e2 * math.sin(lat) ** 2)
    h = p / math.cos(lat) - N if abs(lat) < math.pi / 4 else Z / math.sin(lat) - N * (1.0 - ell.e2)
    return math.degrees(lat), math.degrees(lon), h
