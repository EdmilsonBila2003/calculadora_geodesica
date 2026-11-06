"""Testes do núcleo geodésico. Executar:  python -m unittest discover -s tests -v

Os resultados de Puissant e Sodano são comparados com a solução de Vincenty (referência).
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geodesia import CATALOGO, puissant, sodano, coordenadas, utm
from geodesia.utils import ler_angulo, dd_para_dms, formatar_dms, dms_para_dd
from tests import referencia_vincenty as V

ELL = CATALOGO["WGS84"]
P1 = (-25.9692, 32.5732)   # Maputo (valor aproximado, só para teste)


def dif_az(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


class TestAngulos(unittest.TestCase):
    def test_leitura(self):
        self.assertAlmostEqual(ler_angulo("-25.9692"), -25.9692, 9)
        self.assertAlmostEqual(ler_angulo("25 58 09.12 S"), -(25 + 58 / 60 + 9.12 / 3600), 9)
        self.assertAlmostEqual(ler_angulo("25°58'9,12\" W"), -(25 + 58 / 60 + 9.12 / 3600), 9)
        self.assertAlmostEqual(ler_angulo("32 34 E"), 32 + 34 / 60, 9)
        with self.assertRaises(ValueError):
            ler_angulo("abc")
        with self.assertRaises(ValueError):
            ler_angulo("10 75 0")

    def test_dms(self):
        self.assertEqual(dd_para_dms(10.9999999999, 3)[1:3], (11, 0))   # arredondamento 60"
        self.assertAlmostEqual(dms_para_dd(25, 30, 0), 25.5)
        self.assertTrue(formatar_dms(-25.5, "lat").endswith("S"))


class TestCoordenadas(unittest.TestCase):
    def test_ida_e_volta(self):
        for lat, lon, h in [(-25.9692, 32.5732, 55.0), (89.9, 10.0, 100.0), (0.0, -179.0, 0.0), (-60.0, 120.0, 5000.0)]:
            X, Y, Z = coordenadas.geodesicas_para_cartesianas(ELL, lat, lon, h)
            la, lo, hh = coordenadas.cartesianas_para_geodesicas(ELL, X, Y, Z)
            self.assertAlmostEqual(la, lat, 9)
            self.assertAlmostEqual(lo, lon, 9)
            self.assertAlmostEqual(hh, h, 4)

    def test_equador(self):
        X, Y, Z = coordenadas.geodesicas_para_cartesianas(ELL, 0, 0, 0)
        self.assertAlmostEqual(X, ELL.a, 6)
        self.assertAlmostEqual(Z, 0, 6)


class TestUTM(unittest.TestCase):
    def test_meridiano_central(self):
        z, h, E, N = utm.geodesicas_para_utm(ELL, 0.0, 33.0)
        self.assertEqual((z, h), (36, "N"))
        self.assertAlmostEqual(E, 500000.0, 4)
        self.assertAlmostEqual(N, 0.0, 4)

    def test_um_grau_no_equador(self):
        _, _, E, _ = utm.geodesicas_para_utm(ELL, 0.0, 34.0)
        esperado = 500000.0 + 0.9996 * ELL.a * math.radians(1.0)
        # esperado ignora o termo cúbico da série (~5,7 m), por isso a tolerância é de 10 m
        self.assertAlmostEqual(E, esperado, delta=10.0)

    def test_ida_e_volta(self):
        for lat, lon in [(-25.9692, 32.5732), (-19.8, 34.9), (45.0, 10.0), (-10.0, 40.5)]:
            z, h, E, N = utm.geodesicas_para_utm(ELL, lat, lon)
            la, lo = utm.utm_para_geodesicas(ELL, z, h, E, N)
            self.assertAlmostEqual(la, lat, 8)
            self.assertAlmostEqual(lo, lon, 8)

    def test_hemisferio_sul(self):
        z, h, E, N = utm.geodesicas_para_utm(ELL, -25.9692, 32.5732)
        self.assertEqual((z, h), (36, "S"))
        self.assertTrue(7e6 < N < 8e6)


class TestInverso(unittest.TestCase):
    CURTOS = [(*P1, -25.5, 33.0), (*P1, -26.5, 33.2), (*P1, -25.3, 32.0), (*P1, -25.9, 32.9)]
    LONGOS = [(*P1, -19.8, 34.9), (*P1, 38.72, -9.14), (10.0, 20.0, 80.0, 100.0), (0, 0, 0, 60), (30, 30, 60, 30)]

    def test_puissant_curto(self):
        for c in self.CURTOS:
            s, a1, a2 = V.inverso(ELL, *c)
            r = puissant.inverso(ELL, *c)
            self.assertLess(abs(r.s - s), 0.5, c)
            self.assertLess(abs(dif_az(r.az12, a1)) * 3600, 0.5, c)
            self.assertLess(abs(dif_az(r.az21, a2)) * 3600, 0.5, c)

    def test_sodano_curto_e_longo(self):
        for c in self.CURTOS + self.LONGOS:
            s, a1, a2 = V.inverso(ELL, *c)
            r = sodano.inverso(ELL, *c)
            self.assertLess(abs(r.s - s), 0.5, c)
            self.assertLess(abs(dif_az(r.az12, a1)) * 3600, 1.0, c)
            self.assertLess(abs(dif_az(r.az21, a2)) * 3600, 1.0, c)

    def test_pontos_iguais(self):
        self.assertEqual(puissant.inverso(ELL, *P1, *P1).s, 0.0)
        self.assertEqual(sodano.inverso(ELL, *P1, *P1).s, 0.0)


class TestDirecto(unittest.TestCase):
    def test_puissant_curto(self):
        for az, s in [(45, 50e3), (200, 100e3), (300, 100e3), (0, 80e3), (90, 80e3)]:
            la, lo, a2 = V.directo(ELL, *P1, az, s)
            r = puissant.directo(ELL, *P1, az, s)
            self.assertLess(abs(r.lat2 - la) * 111320, 0.3)
            self.assertLess(abs(r.lon2 - lo) * 111320 * math.cos(math.radians(P1[0])), 0.3)
            self.assertLess(abs(dif_az(r.az21, a2)) * 3600, 0.5)

    def test_sodano(self):
        for az, s in [(45, 50e3), (300, 100e3), (10, 700e3), (330, 5e6), (80, 5e6)]:
            la, lo, a2 = V.directo(ELL, *P1, az, s)
            r = sodano.directo(ELL, *P1, az, s)
            self.assertLess(abs(r.lat2 - la) * 111320, 5.0)
            self.assertLess(abs(r.lon2 - lo) * 111320, 5.0)
            self.assertLess(abs(dif_az(r.az21, a2)) * 3600, 1.0)

    def test_ida_e_volta_sodano(self):
        d = sodano.directo(ELL, *P1, 60.0, 2.0e6)
        i = sodano.inverso(ELL, *P1, d.lat2, d.lon2)
        self.assertAlmostEqual(i.s, 2.0e6, delta=0.5)
        self.assertAlmostEqual(i.az12, 60.0, delta=1e-3)


if __name__ == "__main__":
    unittest.main()
