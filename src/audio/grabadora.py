"""
Grabación de audio desde el micrófono y guardado en carpeta audios.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf


class Grabadora:
    """
    Graba audio del micrófono hasta que se llame a detener.
    Guarda el archivo en la carpeta indicada (por defecto audios).
    """

    SAMPLERATE = 44100
    CHANNELS = 1
    SUBTYPE = "PCM_16"

    def __init__(self, carpeta: str | Path | None = None):
        """
        carpeta: ruta donde guardar los archivos. Si es None, se usa 'audios'
                 relativo al directorio de trabajo o al directorio del script.
        """
        if carpeta is None:
            carpeta = Path(__file__).resolve().parent.parent / "audios"
        self._carpeta = Path(carpeta)
        self._chunks: list[np.ndarray] = []
        self._stop_requested = False
        self._thread: threading.Thread | None = None
        self._last_path: str | None = None
        self._error: str | None = None

    def _ensure_carpeta(self) -> None:
        self._carpeta.mkdir(parents=True, exist_ok=True)

    def _generar_ruta(self) -> Path:
        self._ensure_carpeta()
        nombre = datetime.now().strftime("grabacion_%Y%m%d_%H%M%S.wav")
        return self._carpeta / nombre

    def _worker(self) -> None:
        self._chunks.clear()
        self._error = None
        path = self._generar_ruta()

        def callback(indata: np.ndarray, frames: int, time: object, status: sd.CallbackFlags) -> None:
            if status:
                self._error = str(status)
            self._chunks.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.SAMPLERATE,
                channels=self.CHANNELS,
                callback=callback,
                dtype=np.int16,
            ):
                while not self._stop_requested:
                    sd.sleep(100)
            if self._chunks:
                data = np.concatenate(self._chunks, axis=0)
                sf.write(path, data, self.SAMPLERATE, subtype=self.SUBTYPE)
                self._last_path = str(path)
            else:
                self._last_path = None
                self._error = "No se grabó audio."
        except Exception as e:
            self._error = str(e)
            self._last_path = None

    def iniciar(self) -> None:
        """Inicia la grabación en un hilo. No bloquea."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_requested = False
        self._last_path = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def detener(self) -> tuple[str | None, str | None]:
        """
        Pide detener la grabación, espera al hilo y guarda el archivo.
        Retorna (ruta_del_archivo, mensaje_error).
        Si todo fue bien: (ruta, None). Si hubo error: (None, mensaje).
        """
        self._stop_requested = True
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        if self._error:
            return None, self._error
        return self._last_path, None

    def esta_grabando(self) -> bool:
        """True si la grabación está en curso."""
        return self._thread is not None and self._thread.is_alive()
