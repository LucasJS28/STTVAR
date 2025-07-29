import queue
import json
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from transcripcion.vosk_utils import crear_recognizer, SAMPLE_RATE
import wave

class TranscriberThread(QThread):
    new_text = pyqtSignal(str)

    def __init__(self, model, device_index, filepath, audio_filepath):
        super().__init__()
        self.model = model  # Recibir el modelo como parámetro
        self.device_index = device_index
        self.filepath = filepath
        self.audio_filepath = audio_filepath
        self.q = queue.Queue()
        self.running = True
        self.texto_total = ""
        self.recognizer = crear_recognizer(self.model)
        self.muted = False
        self.audio_buffer = []

    def set_mute(self, mute: bool):
        self.muted = mute

    def callback(self, indata, frames, time, status):
        if not self.muted:
            self.q.put(bytes(indata))
            self.audio_buffer.append(np.copy(indata))
        else:
            pass

    def run(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            with wave.open(self.audio_filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)

                with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, dtype='int16',
                                       channels=1, callback=self.callback, device=self.device_index):
                    while self.running:
                        data = self.q.get()
                        if self.recognizer.AcceptWaveform(data):
                            res = json.loads(self.recognizer.Result())
                            texto = res.get("text", "").strip()
                            if texto:
                                if texto.startswith(self.texto_total):
                                    nuevo = texto[len(self.texto_total):]
                                else:
                                    nuevo = texto
                                if nuevo:
                                    f.write(nuevo + " ")
                                    f.flush()
                                    self.texto_total = texto
                                    self.new_text.emit(self.texto_total)
                        else:
                            parcial = json.loads(self.recognizer.PartialResult())
                            if parcial.get("partial"):
                                self.new_text.emit(parcial["partial"])

                for audio_chunk in self.audio_buffer:
                    wav_file.writeframes(audio_chunk.tobytes())

    def stop(self):
        self.running = False
        self.quit()
        self.wait()