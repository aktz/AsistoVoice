"""
Parser de texto entrante: extrae acción, entidad y parámetros.
"""
from __future__ import annotations

from typing import Any

from .modelo import Accion, Entidad, Instruccion


# Palabras que indican cada acción (minúsculas)
_ACCIONES_CREAR = {
    "nueva", "nuevo", "crear", "insertar", "agregar", "añadir", "alta", "registrar",
}
_ACCIONES_LISTAR = {
    "listar", "ver", "mostrar", "todas", "todos",
}
_ACCIONES_ACTUALIZAR = {
    "editar", "actualizar", "modificar", "cambiar", "actualiza", "modifica",
}
_ACCIONES_ELIMINAR = {
    "eliminar", "borrar", "quitar", "elimina", "borra",
}

# Entidades (singular y plural) -> Entidad
_ENTIDADES: dict[str, Entidad] = {
    "categoria": Entidad.CATEGORIAS,
    "categorias": Entidad.CATEGORIAS,
    "categoría": Entidad.CATEGORIAS,
    "categorías": Entidad.CATEGORIAS,
}

# Nombres de campo reconocidos al actualizar (permite valores multi-palabra hasta el siguiente campo)
_CAMPOS_ACTUALIZABLES = {"descripcion"}

# Palabras a ignorar entre acción/entidad y datos
_STOPWORDS = {"la", "las", "los", "el", "de", "a", "en", "con", "todas", "todos"}


def _normalizar(s: str) -> str:
    return " ".join(s.split()).strip()


def _primera_palabra_accion(palabras: list[str], low: list[str]) -> tuple[Accion | None, int]:
    """
    Detecta la acción en el inicio del texto.
    Retorna (Accion, índice tras la última palabra de la acción) o (None, 0).
    """
    if not palabras:
        return None, 0
    w = low[0]
    if w in _ACCIONES_CREAR:
        return Accion.CREAR, 1
    if w in _ACCIONES_LISTAR:
        return Accion.LISTAR, 1
    if w in _ACCIONES_ACTUALIZAR:
        return Accion.ACTUALIZAR, 1
    if w in _ACCIONES_ELIMINAR:
        return Accion.ELIMINAR, 1
    # "Ver todas las categorias" -> listar
    if len(low) >= 2 and w == "ver" and low[1] in ("todas", "todos"):
        return Accion.LISTAR, 2
    return None, 0


def _buscar_entidad(palabras: list[str], low: list[str], desde: int) -> tuple[Entidad | None, int]:
    """
    Busca la entidad en el texto a partir de 'desde'.
    Retorna (Entidad, índice del primer token tras la entidad).
    """
    i = desde
    while i < len(low):
        if low[i] in _STOPWORDS:
            i += 1
            continue
        if low[i] in _ENTIDADES:
            return _ENTIDADES[low[i]], i + 1
        return None, desde
    return None, desde


def _extraer_params(
    accion: Accion,
    entidad: Entidad,
    palabras: list[str],
    low: list[str],
    desde: int,
) -> dict[str, Any]:
    """Extrae parámetros según acción y entidad."""
    rest = palabras[desde:]
    rest_low = low[desde:]
    params: dict[str, Any] = {}

    if accion == Accion.CREAR:
        desc = " ".join(w for w in rest if w).strip()
        if desc:
            params["descripcion"] = desc

    elif accion == Accion.LISTAR:
        pass

    elif accion == Accion.ACTUALIZAR:
        # "actualizar evento 2 descripcion evento2 visible falso" -> id=2, descripcion="evento2", visible=False
        # id obligatorio, luego pares campo valor (valor hasta el siguiente campo conocido o fin)
        idx = 0
        while idx < len(rest_low) and rest_low[idx] in _STOPWORDS:
            idx += 1
        if idx < len(rest) and rest[idx].isdigit():
            params["id"] = int(rest[idx])
            idx += 1
        while idx < len(rest_low):
            while idx < len(rest_low) and rest_low[idx] in _STOPWORDS:
                idx += 1
            if idx >= len(rest_low):
                break
            if rest_low[idx] not in _CAMPOS_ACTUALIZABLES:
                idx += 1
                continue
            campo = rest_low[idx]
            idx += 1
            # Valor: tokens hasta el siguiente campo conocido o fin
            valor_tokens: list[str] = []
            while idx < len(rest_low):
                if rest_low[idx] in _CAMPOS_ACTUALIZABLES:
                    break
                if rest_low[idx] not in _STOPWORDS:
                    valor_tokens.append(rest[idx])
                idx += 1
            valor_str = " ".join(valor_tokens).strip()
            if not valor_str:
                continue
            # Normalizar booleanos
            v_low = valor_str.lower()
            if v_low in ("verdadero", "true", "1", "si", "sí", "yes"):
                params[campo] = True
            elif v_low in ("falso", "false", "0", "no"):
                params[campo] = False
            else:
                params[campo] = valor_str

    elif accion == Accion.ELIMINAR:
        idx = 0
        while idx < len(rest_low) and rest_low[idx] in _STOPWORDS:
            idx += 1
        if idx < len(rest) and rest[idx].isdigit():
            params["id"] = int(rest[idx])

    return params


class ParserInstrucciones:
    """
    Parsea texto con instrucciones en lenguaje natural y produce Instruccion.
    Ej.: "Nueva categoria Espectaculos" -> CREAR categorias, descripcion="Espectaculos".
    """

    def parsear(self, texto: str) -> Instruccion | None:
        """
        Parsea el texto y retorna una Instruccion o None si no se reconoce.
        """
        t = _normalizar(texto)
        if not t:
            return None
        palabras = t.split()
        low = [p.lower() for p in palabras]

        accion, fin_accion = _primera_palabra_accion(palabras, low)
        if accion is None:
            return None

        entidad, fin_entidad = _buscar_entidad(palabras, low, fin_accion)
        if entidad is None:
            return None

        params = _extraer_params(accion, entidad, palabras, low, fin_entidad)

        # Validaciones mínimas
        if accion == Accion.CREAR and "descripcion" not in params:
            return None
        if accion == Accion.ACTUALIZAR and ("id" not in params or len(params) <= 1):
            return None  # id + al menos un campo a actualizar
        if accion == Accion.ELIMINAR and "id" not in params:
            return None

        return Instruccion(accion=accion, entidad=entidad, params=params)
