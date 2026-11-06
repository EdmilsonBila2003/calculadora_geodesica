"""Implementação de Vincenty (1975) usada APENAS como referência nos testes."""
import math


def inverso(ell, lat1, lon1, lat2, lon2):
    a, b, f = ell.a, ell.b, ell.f
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    sU1, cU1, sU2, cU2 = math.sin(U1), math.cos(U1), math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(500):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.sqrt((cU2 * sl) ** 2 + (cU1 * sU2 - sU1 * cU2 * cl) ** 2)
        cs = sU1 * sU2 + cU1 * cU2 * cl
        sig = math.atan2(ss, cs)
        sa = cU1 * cU2 * sl / ss
        c2a = 1 - sa ** 2
        c2sm = cs - 2 * sU1 * sU2 / c2a if c2a else 0.0
        C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
        nova = L + (1 - C) * f * sa * (sig + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm ** 2)))
        if abs(nova - lam) < 1e-14:
            lam = nova
            break
        lam = nova
    u2 = c2a * (a * a - b * b) / (b * b)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ds = B * ss * (c2sm + B / 4 * (cs * (-1 + 2 * c2sm ** 2) - B / 6 * c2sm * (-3 + 4 * ss ** 2) * (-3 + 4 * c2sm ** 2)))
    s = b * A * (sig - ds)
    sl, cl = math.sin(lam), math.cos(lam)
    az1 = math.atan2(cU2 * sl, cU1 * sU2 - sU1 * cU2 * cl)
    az2 = math.atan2(cU1 * sl, -sU1 * cU2 + cU1 * sU2 * cl)
    return s, math.degrees(az1) % 360, (math.degrees(az2) + 180) % 360


def directo(ell, lat1, lon1, az1, s):
    a, b, f = ell.a, ell.b, ell.f
    al = math.radians(az1)
    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    sU1, cU1 = math.sin(U1), math.cos(U1)
    sig1 = math.atan2(math.tan(U1), math.cos(al))
    sa = cU1 * math.sin(al)
    c2a = 1 - sa ** 2
    u2 = c2a * (a * a - b * b) / (b * b)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    sig = s / (b * A)
    for _ in range(500):
        c2sm = math.cos(2 * sig1 + sig)
        ss, cs = math.sin(sig), math.cos(sig)
        ds = B * ss * (c2sm + B / 4 * (cs * (-1 + 2 * c2sm ** 2) - B / 6 * c2sm * (-3 + 4 * ss ** 2) * (-3 + 4 * c2sm ** 2)))
        nova = s / (b * A) + ds
        if abs(nova - sig) < 1e-14:
            sig = nova
            break
        sig = nova
    ss, cs = math.sin(sig), math.cos(sig)
    c2sm = math.cos(2 * sig1 + sig)
    lat2 = math.atan2(sU1 * cs + cU1 * ss * math.cos(al),
                      (1 - f) * math.sqrt(sa ** 2 + (sU1 * ss - cU1 * cs * math.cos(al)) ** 2))
    lam = math.atan2(ss * math.sin(al), cU1 * cs - sU1 * ss * math.cos(al))
    C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
    L = lam - (1 - C) * f * sa * (sig + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm ** 2)))
    az2 = math.atan2(sa, -sU1 * ss + cU1 * cs * math.cos(al))
    return math.degrees(lat2), lon1 + math.degrees(L), (math.degrees(az2) + 180) % 360
