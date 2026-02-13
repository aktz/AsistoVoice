"""
Módulo de conexión a la base de datos asisto.db.
Proporciona contexto para operaciones con SQLite.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# Ruta a asisto.db relativa al paquete services (src/services -> src/asisto.db)
_DB_PATH = Path(__file__).resolve().parent.parent / "asisto.db"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para obtener una conexión a la base de datos.
    Garantiza commit en éxito y rollback en error; cierra la conexión al salir.
    Usa UTF-8 para todo el texto (tildes, ñ, etc.).
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.text_factory = str  # Asegura que el texto se lee como str Unicode (UTF-8)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
