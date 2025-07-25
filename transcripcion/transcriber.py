import queue
import json
import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal
from transcripcion.vosk_utils import cargar_modelo, crear_recognizer, SAMPLE_RATE
import os

class TranscriberThread(QThread):
    new_text = pyqtSignal(str)

    def __init__(self, device_index, filepath):
        super().__init__()
        self.device_index = device_index
        self.filepath = filepath
        self.q = queue.Queue()
        self.running = True
        self.texto_total = ""
        self.model = cargar_modelo()
        self.recognizer = crear_recognizer(self.model)
        self.muted = False  # Flag mute

    def set_mute(self, mute: bool):
        self.muted = mute

    def callback(self, indata, frames, time, status):
        if not self.muted:
            self.q.put(bytes(indata))
        else:
            # Si está muteado, no se envía audio
            pass

    def run(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
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

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
