"""Elipsoides de referência e parâmetros derivados."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Elipsoide:
    nome: str
    a: float        # semi-eixo maior (m)
    inv_f: float    # inverso do achatamento (1/f)

    @classmethod
    def personalizado(cls, a: float, inv_f: float | None = None, b: float | None = None):
        if a <= 0:
            raise ValueError("O semi-eixo maior 'a' deve ser positivo.")
        if inv_f is None and b is None:
            raise ValueError("Indique 1/f ou o semi-eixo menor 'b'.")
        if inv_f is None:
            if not 0 < b < a:
                raise ValueError("É necessário 0 < b < a.")
            inv_f = a / (a - b)
        if inv_f <= 1:
            raise ValueError("O valor de 1/f deve ser maior que 1.")
        return cls("Personalizado", a, inv_f)

    @property
    def f(self) -> float:        # achatamento
        return 1.0 / self.inv_f

    @property
    def b(self) -> float:        # semi-eixo menor
        return self.a * (1.0 - self.f)

    @property
    def e2(self) -> float:       # 1ª excentricidade ao quadrado
        return self.f * (2.0 - self.f)

    @property
    def ep2(self) -> float:      # 2ª excentricidade ao quadrado
        return self.e2 / (1.0 - self.e2)

    @property
    def n(self) -> float:        # 3.º achatamento de Helmert
        return self.f / (2.0 - self.f)


# Parâmetros conforme valores usuais da literatura — confirme com o material da disciplina.
CATALOGO = {
    "WGS84": Elipsoide("WGS84", 6378137.0, 298.257223563),
    "GRS80": Elipsoide("GRS80", 6378137.0, 298.257222101),
    "Clarke 1880 (RGS)": Elipsoide("Clarke 1880 (RGS)", 6378249.145, 293.465),
    "Clarke 1866": Elipsoide("Clarke 1866", 6378206.4, 294.9786982),
    "Bessel 1841": Elipsoide("Bessel 1841", 6377397.155, 299.1528128),
    "Internacional 1924 (Hayford)": Elipsoide("Internacional 1924 (Hayford)", 6378388.0, 297.0),
    "Krassovsky 1940": Elipsoide("Krassovsky 1940", 6378245.0, 298.3),
}
