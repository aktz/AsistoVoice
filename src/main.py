import unicodedata

import flet as ft
from datetime import datetime
from typing import List

from audio import Grabadora
from procesamiento import EjecutorInstrucciones, ParserInstrucciones
from whispercpp import transcribir


class ChatMessage:
    """Clase para representar un mensaje del chat"""

    def __init__(self, content: str, is_user: bool = True):
        self.content = content
        self.is_user = is_user
        self.timestamp = datetime.now()


class ChatView:
    """Vista principal del chat tipo ChatGPT"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.messages: List[ChatMessage] = []
        self.chat_container = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
        )
        self.text_input = ft.TextField(
            label="Texto (voz o escrito)",
            multiline=True,
            min_lines=2,
            max_lines=2,
            expand=True,
            on_submit=self._send_message,
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Enviar",
            on_click=self._send_message,
        )
        self._parser = ParserInstrucciones()
        self._ejecutor = EjecutorInstrucciones()
        self._grabadora = Grabadora()
        # Un solo botón: micrófono para iniciar, stop para parar (luego guarda y transcribe)
        self.mic_btn = ft.IconButton(
            icon=ft.Icons.MIC,
            tooltip="Grabar",
            on_click=self._on_mic_click,
        )

    async def _rellenar_texto(self, texto: str):
        """Pone el texto en el control de entrada (para reutilizar desde el historial)."""
        self.text_input.value = texto or ""
        await self.text_input.focus()
        self.page.update()

    def _click_historial(self, content: str):
        """Devuelve el handler async para el clic en un mensaje del usuario."""
        async def _handler(e):
            await self._rellenar_texto(content)
        return _handler

    def _build_message_row(self, message: ChatMessage) -> ft.Row:
        """Construye una fila de mensaje. Los mensajes del usuario son clicables para rellenar el texto."""
        alignment = (
            ft.MainAxisAlignment.END if message.is_user else ft.MainAxisAlignment.START
        )
        bg_color = ft.Colors.BLUE_700 if message.is_user else ft.Colors.GREY_800
        text_color = ft.Colors.WHITE

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        message.content,
                        color=text_color,
                        size=14,
                        selectable=True,
                    ),
                    ft.Text(
                        message.timestamp.strftime("%H:%M"),
                        color=ft.Colors.GREY_400,
                        size=10,
                    ),
                ],
                tight=True,
                spacing=4,
            ),
            padding=12,
            border_radius=12,
            bgcolor=bg_color,
            width=300,
        )
        if message.is_user:
            content.on_click = self._click_historial(message.content)
            content.tooltip = "Tocar para usar este texto"
            content.ink = True

        return ft.Row(
            [content],
            alignment=alignment,
        )

    def _add_message(self, content: str, is_user: bool = True):
        """Añade un mensaje al chat (los más recientes abajo, estilo ChatGPT)."""
        message = ChatMessage(content, is_user)
        self.messages.append(message)
        self.chat_container.controls.append(self._build_message_row(message))
        self.page.update()

    def _on_mic_click(self, e):
        """Un clic: si no graba → inicia y cambia a Stop. Si graba → para, guarda y transcribe."""
        if not self._grabadora.grabando:
            # Iniciar grabación y mostrar ícono Stop
            try:
                self._grabadora.iniciar_grabacion()
            except Exception as err:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error al iniciar: {err}"),
                    open=True,
                    bgcolor=ft.Colors.ERROR,
                )
                self.page.update()
                return
            self.mic_btn.icon = ft.Icons.STOP
            self.mic_btn.tooltip = "Detener grabación"
            self.page.update()
        else:
            # Detener: guardar y transcribir en hilo
            self.mic_btn.icon = ft.Icons.MIC
            self.mic_btn.tooltip = "Grabar"
            self.mic_btn.disabled = True
            self.page.update()

            def _guardar_y_transcribir():
                ok = False
                texto = ""
                error = None
                try:
                    ruta = self._grabadora.detener_grabacion()
                    if ruta and ruta.exists():
                        texto = transcribir()
                        ok = True
                    else:
                        error = "No se grabó audio."
                except Exception as err:
                    error = str(err)
                # Programar actualización en el hilo principal (obligatorio en Flet)
                def _aplicar_en_ui():
                    self.mic_btn.disabled = False
                    if ok:
                        t = (texto or "").strip()
                        self.text_input.value = unicodedata.normalize("NFC", t)
                        self.text_input.update()
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("Transcripción completada"),
                            open=True,
                        )
                    else:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Error: {error}"),
                            open=True,
                            bgcolor=ft.Colors.ERROR,
                        )
                    self.page.update()
                self.page.loop.call_soon_threadsafe(_aplicar_en_ui)

            self.page.run_thread(_guardar_y_transcribir)

    async def _send_message(self, e):
        """Procesar: toma el texto del control, lo envía al historial y ejecuta con la BD."""
        texto = (self.text_input.value or "").strip()
        if not texto:
            return
        self._add_message(texto, is_user=True)
        self.text_input.value = ""
        await self.text_input.focus()
        self.page.update()
        self._procesar_instruccion(texto)

    def _procesar_instruccion(self, texto: str):
        """Parsea el texto, ejecuta la instrucción vía categorias_service y responde en el chat."""
        inst = self._parser.parsear(texto)
        if inst is None:
            self._add_message(
                "No entendí. Ejemplos:\n"
                "• Nueva categoria descripcion Espectaculos activa si\n"
                "• Listado categorias\n"
                "• Editar categoria 1 Descripcion Conciertos\n"
                "• Eliminar categoria 3",
                is_user=False,
            )
        else:
            msg = self._ejecutor.ejecutar(inst)
            self._add_message(msg, is_user=False)
        self.page.update()

    def build(self) -> ft.Container:
        """Construye la vista completa del chat"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=self.chat_container,
                        expand=True,
                        padding=10,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                self.mic_btn,
                                self.text_input,
                                self.send_button,
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=10,
                        bgcolor=ft.Colors.GREY_900,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )


def main(page: ft.Page):
    """Función principal de la aplicación"""
    page.title = "AsistoVoice"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    chat_view = ChatView(page)
    page.add(ft.SafeArea(expand=True, content=chat_view.build()))


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
