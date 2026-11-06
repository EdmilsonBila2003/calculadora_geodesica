"""Pacote com os cálculos geodésicos (sem dependências externas)."""
from .elipsoides import Elipsoide, CATALOGO
from . import puissant, sodano, coordenadas, utm, utils

__all__ = ["Elipsoide", "CATALOGO", "puissant", "sodano", "coordenadas", "utm", "utils"]
