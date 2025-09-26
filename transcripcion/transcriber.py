# transcripcion/transcriber.py

import queue
import json
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from transcripcion.vosk_utils import crear_recognizer, SAMPLE_RATE
import wave
import sys
import time
from vocabularios.vocabulariocl import VOCABULARIO_CL

class TranscriberThread(QThread):
    new_text = pyqtSignal(str, bool)  # Emite texto y si es parcial o final
    finished = pyqtSignal()

    def __init__(self, model, device_index, filepath, audio_filepath):
        super().__init__()
        self.model = model
        self.device_index = device_index
        self.filepath = filepath
        self.audio_filepath = audio_filepath
        self.q = queue.Queue(maxsize=20)
        self.running = True
        self.texto_total = ""
        self.last_emitted_final = ""
        self.partial_buffer = ""
        self.last_partial_time = 0
        self.partial_timeout = 0.5
        self.muted = False
        self.audio_buffer = []

        # Usamos la lista importada para potenciar el reconocedor
        # Es buena práctica añadir '[unk]' para que marque palabras desconocidas
        self.recognizer = crear_recognizer(self.model, grammar=VOCABULARIO_CL + ['[unk]'])

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
                                    if texto.startswith(self.texto_total):
                                        nuevo = texto[len(self.texto_total):].strip()
                                    else:
                                        nuevo = texto
                                    if nuevo:
                                        self.texto_total += nuevo + " "
                                        f.write(nuevo + " ")
                                        f.flush()
                                        self.last_emitted_final = texto
                                        self.new_text.emit(nuevo, False)
                                        self.partial_buffer = ""
                                        self.last_partial_time = current_time
                            else:
                                parcial = json.loads(self.recognizer.PartialResult())
                                partial_text = parcial.get("partial", "").strip()
                                if partial_text:
                                    if partial_text.startswith(self.partial_buffer):
                                        nuevo_parcial = partial_text[len(self.partial_buffer):].strip()
                                    else:
                                        nuevo_parcial = partial_text
                                    if nuevo_parcial:
                                        self.partial_buffer = partial_text
                                        if (current_time - self.last_partial_time >= self.partial_timeout or
                                            len(partial_text.split()) >= 3):
                                            self.new_text.emit(self.partial_buffer, True)
                                            self.last_partial_time = current_time
                        except queue.Empty:
                            self.msleep(5)
                        except Exception as e:
                            print(f"Error en transcripción: {e}")

                    # Guardar el audio y emitir restos al finalizar el bucle
                    for audio_chunk in self.audio_buffer:
                        wav_file.writeframes(audio_chunk.tobytes())
                    if self.partial_buffer:
                        self.new_text.emit(self.partial_buffer, True)

        self.finished.emit()

    def stop(self):
        self.running = False