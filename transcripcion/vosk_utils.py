# transcripcion/vosk_utils.py

import os
import sys
import json  # <-- Importado para manejar el vocabulario
from vosk import Model, KaldiRecognizer

# Parámetros de configuración
# CONSEJO: Usa "vosk-model-small-es-0.42" para una carga inicial MUCHO más rápida.
MODEL_PATH = "vosk-model-es-0.42" 
SAMPLE_RATE = 16000
SAVE_FOLDER = "stt_guardados"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def generar_nombre_archivo():
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"transcripcion_{now}.txt"

def cargar_modelo():
    """Carga el modelo de Vosk y lo retorna."""
    if not os.path.exists(MODEL_PATH):
        print(f"Modelo no encontrado en {MODEL_PATH}")
        sys.exit(1)
    return Model(MODEL_PATH)

def crear_recognizer(modelo, grammar=None):
    """
    Crea un reconocedor. Si se proporciona 'grammar' (un vocabulario),
    se inicializa con esas palabras específicas.
    """
    if grammar:
        # Si le pasamos un vocabulario, lo usamos para crear el reconocedor
        recognizer = KaldiRecognizer(modelo, SAMPLE_RATE, json.dumps(grammar))
    else:
        # Si no, creamos un reconocedor normal como antes
        recognizer = KaldiRecognizer(modelo, SAMPLE_RATE)

    # Mantenemos esta línea que ya tenías, es útil para obtener más detalles.
    recognizer.SetWords(True)
    return recognizer