"""
Ejecutor de instrucciones: aplica Instruccion usando los servicios (CategoriasService, etc.).
"""
from __future__ import annotations

from .modelo import Accion, Entidad, Instruccion


class EjecutorInstrucciones:
    """
    Ejecuta una Instruccion llamando al servicio correspondiente.
    Devuelve un mensaje de texto con el resultado (éxito o error) para mostrar en el chat.
    """

    def __init__(self) -> None:
        from services import CategoriasService
        self._categorias = CategoriasService()

    def ejecutar(self, inst: Instruccion) -> str:
        """
        Ejecuta la instrucción y retorna un mensaje para el usuario.
        """
        if inst.entidad == Entidad.CATEGORIAS:
            return self._ejecutar_categorias(inst)
        return "Entidad no soportada."

    def _ejecutar_categorias(self, inst: Instruccion) -> str:
        svc = self._categorias
        p = inst.params

        try:
            if inst.accion == Accion.CREAR:
                desc = p.get("descripcion", "").strip()
                if not desc:
                    return "Falta la descripción de la categoría."
                id_ = svc.create(desc)
                return f"Categoría creada: «{desc}» (id {id_})."

            if inst.accion == Accion.LISTAR:
                filas = svc.list_all()
                if not filas:
                    return "No hay categorías."
                lineas = [f"• {r['id']}: {r['descripcion']}" for r in filas]
                return "Categorías:\n" + "\n".join(lineas)

            if inst.accion == Accion.ACTUALIZAR:
                id_ = p.get("id")
                if id_ is None:
                    return "Falta el id para actualizar."
                campos = {k: v for k, v in p.items() if k != "id"}
                if not campos:
                    return "Falta al menos un campo a actualizar."
                n = svc.update(int(id_), campos)
                if n == 0:
                    return f"No existe categoría con id {id_}."
                resumen = ", ".join(f"{k}={v!r}" for k, v in campos.items())
                return f"Categoría {id_} actualizada: {resumen}."

            if inst.accion == Accion.ELIMINAR:
                id_ = p.get("id")
                if id_ is None:
                    return "Falta el id de la categoría a eliminar."
                n = svc.delete(int(id_))
                if n == 0:
                    return f"No existe categoría con id {id_}."
                return f"Categoría {id_} eliminada."

        except Exception as e:
            return f"Error: {e}"

        return "Acción no implementada."
