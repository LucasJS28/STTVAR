import queue
import json
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from transcripcion.vosk_utils import crear_recognizer, SAMPLE_RATE
import wave
import sys
import time

class TranscriberThread(QThread):
    new_text = pyqtSignal(str, bool)  # Emite texto y si es parcial o final
    finished = pyqtSignal()

    def __init__(self, model, device_index, filepath, audio_filepath):
        super().__init__()
        self.model = model
        self.device_index = device_index
        self.filepath = filepath
        self.audio_filepath = audio_filepath
        self.q = queue.Queue(maxsize=20)  # Tamaño de la cola
        self.running = True
        self.texto_total = ""
        self.last_emitted_final = ""
        self.partial_buffer = ""  # Búfer para acumular resultados parciales
        self.last_partial_time = 0  # Última vez que se emitió un parcial
        self.partial_timeout = 0.5  # Tiempo (segundos) para acumular parciales
        self.recognizer = crear_recognizer(self.model)
        self.muted = False
        self.audio_buffer = []

    def set_mute(self, mute: bool):
        self.muted = mute

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if not self.muted:
            try:
                self.q.put_nowait(bytes(indata))
                self.audio_buffer.append(np.copy(indata))
            except queue.Full:
                print("Advertencia: Cola de audio llena.")
        else:
            pass

    def run(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            with wave.open(self.audio_filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)

                with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                                       channels=1, callback=self.callback, device=self.device_index):
                    while self.running:
                        try:
                            data = self.q.get_nowait()
                            current_time = time.time()

                            if self.recognizer.AcceptWaveform(data):
                                res = json.loads(self.recognizer.Result())
                                texto = res.get("text", "").strip()
                                if texto and texto != self.last_emitted_final:
                                    # Solo emitir y guardar texto nuevo
                                    if texto.startswith(self.texto_total):
                                        nuevo = texto[len(self.texto_total):].strip()
                                    else:
                                        nuevo = texto
                                    if nuevo:
                                        self.texto_total += nuevo + " "
                                        f.write(nuevo + " ")
                                        f.flush()
                                        self.last_emitted_final = texto
                                        self.new_text.emit(nuevo, False)  # Resultado final
                                        # Limpiar el búfer parcial después de un resultado final
                                        self.partial_buffer = ""
                                        self.last_partial_time = current_time
                            else:
                                parcial = json.loads(self.recognizer.PartialResult())
                                partial_text = parcial.get("partial", "").strip()
                                if partial_text:
                                    # Acumular en el búfer parcial
                                    if partial_text.startswith(self.partial_buffer):
                                        nuevo_parcial = partial_text[len(self.partial_buffer):].strip()
                                    else:
                                        nuevo_parcial = partial_text
                                    if nuevo_parcial:
                                        self.partial_buffer = partial_text
                                        # Emitir si ha pasado suficiente tiempo o hay una frase completa
                                        if (current_time - self.last_partial_time >= self.partial_timeout or
                                            len(partial_text.split()) >= 3):  # Mínimo 3 palabras
                                            self.new_text.emit(self.partial_buffer, True)  # Resultado parcial
                                            self.last_partial_time = current_time
                        except queue.Empty:
                            self.msleep(5)
                        except Exception as e:
                            print(f"Error en transcripción: {e}")
                    # Guardar el audio al finalizar
                    for audio_chunk in self.audio_buffer:
                        wav_file.writeframes(audio_chunk.tobytes())
                    # Emitir el búfer parcial restante, si existe
                    if self.partial_buffer:
                        self.new_text.emit(self.partial_buffer, True)
        self.finished.emit()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()