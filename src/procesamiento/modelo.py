"""
Modelo de instrucciones: acciones, entidades y parámetros.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Accion(str, Enum):
    """Acción CRUD a ejecutar."""
    CREAR = "crear"
    LISTAR = "listar"
    ACTUALIZAR = "actualizar"
    ELIMINAR = "eliminar"


class Entidad(str, Enum):
    """Entidad sobre la que actuar (mapea a servicios)."""
    CATEGORIAS = "categorias"


@dataclass(frozen=True)
class Instruccion:
    """
    Instrucción parseada a partir del texto entrante.
    accion: CRUD a ejecutar.
    entidad: Entidad (categorías, etc.).
    params: Parámetros según la acción.
        - CREAR: descripcion, etc.
        - ACTUALIZAR: id (obligatorio) y uno o más pares campo/valor
          (ej. descripcion, visible). Formato texto: "actualizar entidad id campo1 valor1 campo2 valor2 ..."
        - ELIMINAR: id.
    """
    accion: Accion
    entidad: Entidad
    params: dict[str, str | int | bool]
