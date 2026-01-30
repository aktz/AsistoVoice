"""
Servicio CRUD para la tabla categorías en asisto.db.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from .db import get_connection


def _row_a_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convierte un sqlite3.Row en diccionario."""
    return dict(row)


class CategoriasService:
    """
    Servicio CRUD para la tabla categorias.
    Campos: id (PK), descripcion.
    """

    _TABLA = "categorias"

    def create(self, descripcion: str) -> int:
        """
        Inserta una categoría.
        Retorna el id del registro insertado.
        """
        with get_connection() as conn:
            cur = conn.execute(
                f"INSERT INTO {self._TABLA} (descripcion) VALUES (?)",
                (descripcion.strip(),),
            )
            return cur.lastrowid

    def get_by_id(self, id_val: int) -> dict[str, Any] | None:
        """Obtiene una categoría por id. Retorna None si no existe."""
        with get_connection() as conn:
            cur = conn.execute(
                f"SELECT * FROM {self._TABLA} WHERE id = ?",
                (id_val,),
            )
            row = cur.fetchone()
            return _row_a_dict(row) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        """Lista todas las categorías."""
        with get_connection() as conn:
            cur = conn.execute(f"SELECT * FROM {self._TABLA}")
            return [_row_a_dict(r) for r in cur.fetchall()]

    def update(self, id_val: int, data: dict[str, Any]) -> int:
        """
        Actualiza una categoría por id con los campos indicados en data.
        data: dict con nombres de columna (ej. descripcion). Solo se actualizan las claves presentes.
        Retorna el número de filas afectadas.
        """
        if not data:
            return 0
        # Solo se permiten columnas existentes en la tabla
        columnas = [c for c in data if c in ("descripcion",)]
        if not columnas:
            return 0
        with get_connection() as conn:
            set_clause = ", ".join(f"{c} = ?" for c in columnas)
            valores = []
            for c in columnas:
                v = data[c]
                if isinstance(v, bool):
                    valores.append(1 if v else 0)
                elif isinstance(v, str):
                    valores.append(v.strip())
                else:
                    valores.append(v)
            cur = conn.execute(
                f"UPDATE {self._TABLA} SET {set_clause} WHERE id = ?",
                (*valores, id_val),
            )
            return cur.rowcount

    def delete(self, id_val: int) -> int:
        """Elimina una categoría por id. Retorna el número de filas afectadas."""
        with get_connection() as conn:
            cur = conn.execute(
                f"DELETE FROM {self._TABLA} WHERE id = ?",
                (id_val,),
            )
            return cur.rowcount
