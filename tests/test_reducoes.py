import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geodesia import reducoes as R


class TestReducoes(unittest.TestCase):
    def test_zenital(self):  # Exemplo 2 (o material imprime 13,082; a fórmula dá 13,084)
        dh, dv = R.inclinada_zenital(250, 87)
        self.assertAlmostEqual(dh, 249.657, 3)
        self.assertAlmostEqual(dv, 13.084, 3)

    def test_vertical(self):  # Exemplo 5 (o material imprime 9,866; a fórmula dá 10,159)
        _, dv, dH = R.inclinada_vertical(120, 5, 1.5, 1.8)
        self.assertAlmostEqual(dv, 10.459, 3)
        self.assertAlmostEqual(dH, 10.159, 3)

    def test_elipsoide(self):  # Exemplo 6
        self.assertAlmostEqual(R.reduzir_ao_elipsoide(2000000, 800, 6371000), 1999749.0, delta=1.0)

    def test_escala(self):  # Exemplo 7
        self.assertAlmostEqual(R.distancia_grelha(1000000, 0.9998), 999800.0, 6)

    def test_nivelamento(self):  # Exemplo 3
        dh, hf, e = R.circuito_nivelamento([1.425], [0.985], 32.650, 0.44)
        self.assertAlmostEqual(dh, 0.44, 9); self.assertAlmostEqual(hf, 33.09, 9); self.assertAlmostEqual(e, 0.0, 9)

    def test_alturas(self):  # Exemplo 8
        self.assertAlmostEqual(R.altura_ortometrica(82.4, -27.6), 110.0, 9)
        self.assertAlmostEqual(R.altura_elipsoidal(110.0, -27.6), 82.4, 9)

    def test_coordenadas(self):  # Exemplo 4
        dE, dN, EB, NB = R.coordenadas_por_azimute(500000, 7100000, 100, 30)
        self.assertAlmostEqual(dE, 50.0, 6); self.assertAlmostEqual(NB, 7100086.603, 3)
        d, a = R.azimute_distancia(500000, 7100000, EB, NB)
        self.assertAlmostEqual(d, 100.0, 6); self.assertAlmostEqual(a, 30.0, 6)


if __name__ == "__main__":
    unittest.main()
