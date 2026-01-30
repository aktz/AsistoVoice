"""
Paquete procesamiento: parseo y ejecución de instrucciones en lenguaje natural.
"""
from .ejecutor import EjecutorInstrucciones
from .modelo import Accion, Entidad, Instruccion
from .parser import ParserInstrucciones

__all__ = [
    "Accion",
    "Entidad",
    "Instruccion",
    "ParserInstrucciones",
    "EjecutorInstrucciones",
]
