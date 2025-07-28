import os
import sys
import json
from vosk import Model, KaldiRecognizer
from vocabulariocl import VOCABULARIO_CL

# Parámetros de configuración
MODEL_PATH = "vosk-model-es-0.42"
SAMPLE_RATE = 16000
SAVE_FOLDER = "stt_guardados"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def generar_nombre_archivo():
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"transcripcion_{now}.txt"

def cargar_modelo():
    if not os.path.exists(MODEL_PATH):
        print(f"Modelo no encontrado en {MODEL_PATH}")
        sys.exit(1)
    return Model(MODEL_PATH)

def crear_recognizer(modelo):
    recognizer = KaldiRecognizer(modelo, SAMPLE_RATE)  # Remove VOCABULARIO_CL
    recognizer.SetWords(True)
    return recognizer