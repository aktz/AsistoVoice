import flet as ft
from datetime import datetime
from pathlib import Path
from typing import List

from audio import Grabadora
from procesamiento import EjecutorInstrucciones, ParserInstrucciones


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
            label="Escribe tu mensaje...",
            multiline=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            on_submit=self._send_message,
        )
        # Usar emoji de micrófono - más seguro que depender de nombres de iconos
        self.audio_icon_text = ft.Text("🎤", size=24)
        self.audio_button = ft.Container(
            content=self.audio_icon_text,
            tooltip="Grabar audio",
            on_click=self._handle_audio_click,
            padding=8,
            border_radius=20,
            ink=True,
        )
        self._parser = ParserInstrucciones()
        self._ejecutor = EjecutorInstrucciones()
        self._grabadora = Grabadora(carpeta=Path(__file__).resolve().parent / "audios")
        # Usar emoji de envío - más seguro que depender de nombres de iconos
        self.send_button = ft.Container(
            content=ft.Text("➤", size=24, color=ft.Colors.BLUE_400),
            tooltip="Enviar mensaje",
            on_click=self._send_message,
            padding=8,
            border_radius=20,
            ink=True,
        )
        self._is_recording = False
        
    def _build_message_row(self, message: ChatMessage) -> ft.Row:
        """Construye una fila de mensaje"""
        alignment = ft.MainAxisAlignment.END if message.is_user else ft.MainAxisAlignment.START
        bg_color = ft.Colors.BLUE_700 if message.is_user else ft.Colors.GREY_800
        text_color = ft.Colors.WHITE
        
        return ft.Row(
            [
                ft.Container(
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
            ],
            alignment=alignment,
        )
    
    def _add_message(self, content: str, is_user: bool = True):
        """Añade un mensaje al chat (los más recientes abajo, estilo ChatGPT)."""
        message = ChatMessage(content, is_user)
        self.messages.append(message)
        self.chat_container.controls.append(self._build_message_row(message))
        self.page.update()

    async def _send_message(self, e):
        """Envía el mensaje desde el campo de texto"""
        texto = self.text_input.value.strip()
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
                "• Nueva categoria Espectaculos\n"
                "• Listar categorias\n"
                "• Editar categoria 1 Descripcion Conciertos\n"
                "• Eliminar categoria 3",
                is_user=False,
            )
        else:
            msg = self._ejecutor.ejecutar(inst)
            self._add_message(msg, is_user=False)
        self.page.update()
    
    def _handle_audio_click(self, e):
        """Maneja el clic en el botón de audio: iniciar o detener grabación y guardar en audios."""
        if not self._is_recording:
            self._is_recording = True
            self.audio_icon_text.value = "⏹"
            self.audio_button.tooltip = "Detener grabación"
            self.audio_button.bgcolor = ft.Colors.RED_700
            self._grabadora.iniciar()
            self.page.update()
        else:
            self._is_recording = False
            self.audio_icon_text.value = "🎤"
            self.audio_button.tooltip = "Grabar audio"
            self.audio_button.bgcolor = None
            self.page.update()
            ruta, error = self._grabadora.detener()
            if error:
                self._add_message(f"Error al grabar: {error}", is_user=False)
            elif ruta:
                nombre = Path(ruta).name
                self._add_message(f"Audio guardado en audios: {nombre}", is_user=False)
            else:
                self._add_message("No se guardó ningún audio.", is_user=False)
            self.page.update()
    
    def build(self) -> ft.Container:
        """Construye la vista completa del chat"""
        return ft.Container(
            content=ft.Column(
                [
                    # Área de mensajes
                    ft.Container(
                        content=self.chat_container,
                        expand=True,
                        padding=10,
                    ),
                    # Área de entrada
                    ft.Container(
                        content=ft.Row(
                            [
                                self.audio_button,
                                self.text_input,
                                self.send_button,
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
    
    # Configurar para mobile
    page.padding = 0
    
    chat_view = ChatView(page)
    
    page.add(
        ft.SafeArea(
            expand=True,
            content=chat_view.build(),
        )
    )


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
