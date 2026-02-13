"""
Grabadora de audio: guarda WAV en whispercpp/audios para transcripción con WhisperCpp.
Usa InputStream con callback para captura continua y fiable del micrófono.
"""
import threading
import wave
from pathlib import Path

# Ruta base del paquete src
_SRC_DIR = Path(__file__).resolve().parent.parent
WHISPERCPP_AUDIOS = _SRC_DIR / "whispercpp" / "audios"
ARCHIVO_GRABACION = "grabacion.wav"

# Tamaño de bloque para el callback (muestras). ~64 ms a 16 kHz.
BLOCKSIZE = 1024


class Grabadora:
    """Graba audio desde el micrófono. Iniciar con iniciar_grabacion(), detener con detener_grabacion()."""

    def __init__(self, sample_rate: int = 16000, canales: int = 1):
        self.sample_rate = sample_rate
        self.canales = canales
        self._stream = None
        self._chunks = []
        self._lock = threading.Lock()

    def _asegurar_carpeta(self) -> Path:
        WHISPERCPP_AUDIOS.mkdir(parents=True, exist_ok=True)
        return WHISPERCPP_AUDIOS

    def ruta_wav(self) -> Path:
        """Ruta completa del archivo WAV de grabación."""
        self._asegurar_carpeta()
        return WHISPERCPP_AUDIOS / ARCHIVO_GRABACION

    @property
    def grabando(self) -> bool:
        return self._stream is not None and self._stream.active

    def iniciar_grabacion(self) -> None:
        """Inicia la grabación con InputStream (callback). Llamar detener_grabacion() para guardar."""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            raise ImportError(
                "Se necesita 'sounddevice' y 'numpy' para grabar. "
                "Instale con: pip install sounddevice numpy"
            )

        if self.grabando:
            return

        self._asegurar_carpeta()
        with self._lock:
            self._chunks = []

        def _callback(indata, _frames, _time, status):
            if status:
                return
            with self._lock:
                self._chunks.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.canales,
                dtype="float32",
                blocksize=BLOCKSIZE,
                callback=_callback,
            )
            self._stream.start()
        except Exception:
            self._stream = None
            raise

    def detener_grabacion(self) -> Path | None:
        """
        Detiene la grabación, guarda en whispercpp/audios/grabacion.wav y retorna la ruta.
        Retorna None si no había grabación o no hay datos.
        """
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

        with self._lock:
            chunks = list(self._chunks)
            self._chunks = []

        if not chunks:
            return None

        try:
            import numpy as np
        except ImportError:
            return None

        # indata tiene shape (blocksize, canales)
        grabacion = np.concatenate(chunks, axis=0)
        datos_int16 = (np.clip(grabacion, -1.0, 1.0) * 32767).astype(np.int16)
        if self.canales > 1:
            datos_int16 = datos_int16.flatten()

        ruta = self.ruta_wav()
        with wave.open(str(ruta), "wb") as wav:
            wav.setnchannels(self.canales)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(datos_int16.tobytes())

        return ruta

    def grabar_bloque(self, duracion_segundos: float) -> Path:
        """
        Graba un bloque de duración fija (compatibilidad). Retorna la ruta del archivo.
        """
        import time
        self.iniciar_grabacion()
        try:
            time.sleep(duracion_segundos)
        finally:
            return self.detener_grabacion() or self.ruta_wav()
