"""Conversões angulares, leitura/formatação de ângulos e tipos de resultado."""
import math
import re
from typing import NamedTuple

SIN1 = math.sin(math.radians(1.0 / 3600.0))   # sin 1"


class Directo(NamedTuple):
    lat2: float     # graus decimais
    lon2: float
    az21: float     # azimute inverso (de 2 para 1), graus


class Inverso(NamedTuple):
    s: float        # distância geodésica (m)
    az12: float     # graus
    az21: float


def norm_lon(x: float) -> float:
    """Normaliza para o intervalo (-180, 180]."""
    x = math.fmod(x, 360.0)
    if x > 180.0:
        x -= 360.0
    elif x <= -180.0:
        x += 360.0
    return x


def norm_az(x: float) -> float:
    """Normaliza para [0, 360)."""
    return x % 360.0


def dms_para_dd(g: float, m: float = 0.0, s: float = 0.0, negativo: bool = False) -> float:
    dd = abs(g) + m / 60.0 + s / 3600.0
    return -dd if (negativo or g < 0) else dd


def dd_para_dms(dd: float, casas: int = 5):
    """Devolve (sinal, graus, minutos, segundos) com tratamento de arredondamento."""
    sinal = -1 if dd < 0 else 1
    v = abs(dd)
    g = int(v)
    m = int((v - g) * 60.0)
    s = round((v - g - m / 60.0) * 3600.0, casas)
    if s >= 60.0:
        s -= 60.0
        m += 1
    if m >= 60:
        m -= 60
        g += 1
    return sinal, g, m, s


def formatar_dms(dd: float, tipo: str | None = None, casas: int = 5) -> str:
    """Ex.: 25°58'09.12000" S. tipo: 'lat', 'lon' ou None (usa sinal)."""
    sinal, g, m, s = dd_para_dms(dd, casas)
    txt = f"{g}°{m:02d}'{s:0{casas + 3}.{casas}f}\""
    if tipo == "lat":
        return txt + (" S" if sinal < 0 else " N")
    if tipo == "lon":
        return txt + (" W" if sinal < 0 else " E")
    return ("-" if sinal < 0 else "") + txt


_NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def ler_angulo(texto: str) -> float:
    """Lê graus decimais ou G M S (com °, ', " ou espaços) e hemisfério N/S/E/W/L/O.

    Exemplos aceites: -25.9692 | 25 58 9.12 S | 25°58'9.12" | 32d34m
    """
    t = texto.strip()
    if not t:
        raise ValueError("Campo vazio.")
    maiusc = t.upper()
    hemi = -1 if re.search(r"[SWO]\s*$", maiusc) else 1
    nums = _NUM.findall(t.replace("d", " ").replace("D", " "))
    if not 1 <= len(nums) <= 3:
        raise ValueError(f"Ângulo inválido: '{texto}'.")
    vals = [float(x.replace(",", ".")) for x in nums]
    neg = nums[0].lstrip().startswith("-") or hemi < 0
    g = abs(vals[0])
    m = vals[1] if len(vals) > 1 else 0.0
    s = vals[2] if len(vals) > 2 else 0.0
    if not (0 <= m < 60 and 0 <= s < 60):
        raise ValueError("Minutos e segundos devem estar em [0, 60).")
    return dms_para_dd(g, m, s, negativo=neg)


def ler_numero(texto: str) -> float:
    t = texto.strip().replace(",", ".")
    if not t:
        raise ValueError("Campo vazio.")
    return float(t)
