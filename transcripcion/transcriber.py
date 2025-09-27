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
    new_text = pyqtSignal(dict)
    finished = pyqtSignal()

    # --- CAMBIO CLAVE: Aceptar el buffer de memoria compartida ---
    def __init__(self, model, device_index, filepath, audio_filepath, shared_in_memory_buffer):
        super().__init__()
        self.model = model
        self.device_index = device_index
        self.filepath = filepath
        self.audio_filepath = audio_filepath
        self.q = queue.Queue(maxsize=20)
        self.running = True
        self.muted = False
        self.audio_buffer_for_file = [] # Buffer para guardar el archivo final
        self.shared_in_memory_buffer = shared_in_memory_buffer # Referencia al buffer global
        
        self.recognizer = crear_recognizer(self.model, grammar=VOCABULARIO_CL + ['[unk]'])
        self.recognizer.SetWords(True)

    def set_mute(self, mute: bool):
        self.muted = mute

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if not self.muted:
            try:
                # Convertir a bytes para la cola de Vosk
                data_bytes = bytes(indata)
                self.q.put_nowait(data_bytes)
                
                # --- CAMBIO CLAVE: Añadir los bytes también al buffer de memoria compartida ---
                self.shared_in_memory_buffer.append(data_bytes)
                
                # Guardar el array numpy para el archivo .wav final
                self.audio_buffer_for_file.append(np.copy(indata))
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
                            data = self.q.get(timeout=0.1)

                            if self.recognizer.AcceptWaveform(data):
                                res = json.loads(self.recognizer.Result())
                                texto = res.get("text", "").strip()
                                
                                if texto and 'result' in res and res['result']:
                                    start_time = res['result'][0]['start']
                                    end_time = res['result'][-1]['end']
                                    
                                    final_data = {
                                        "text": texto, "is_partial": False,
                                        "start_sec": start_time, "end_sec": end_time
                                    }
                                    self.new_text.emit(final_data)
                                    f.write(texto + " ")
                                    f.flush()
                            else:
                                parcial = json.loads(self.recognizer.PartialResult())
                                partial_text = parcial.get("partial", "").strip()
                                if partial_text:
                                    self.new_text.emit({"text": partial_text, "is_partial": True})

                        except queue.Empty:
                            self.msleep(5)
                        except Exception as e:
                            print(f"Error en transcripción: {e}")

                    # Procesar audio final
                    final_res = json.loads(self.recognizer.FinalResult())
                    final_text = final_res.get("text", "").strip()
                    if final_text and 'result' in final_res and final_res['result']:
                        start_time = final_res['result'][0]['start']
                        end_time = final_res['result'][-1]['end']
                        self.new_text.emit({
                            "text": final_text, "is_partial": False, 
                            "start_sec": start_time, "end_sec": end_time
                        })
                        f.write(final_text + " ")
                        f.flush()

                    # Guardar el archivo .wav final
                    for audio_chunk in self.audio_buffer_for_file:
                        wav_file.writeframes(audio_chunk.tobytes())

        self.finished.emit()

    def stop(self):
        self.running = False