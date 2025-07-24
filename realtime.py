import os
import sys
import queue
import sounddevice as sd
import json
from datetime import datetime
from vocabulariocl import VOCABULARIO_CL
from vosk import Model, KaldiRecognizer

# Parámetros
MODEL_PATH = "vosk-model-es-0.42"
SAMPLE_RATE = 16000

# Carpeta donde se guardarán las transcripciones
SAVE_FOLDER = "stt_guardados"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Crear nombre de archivo con fecha y hora
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
FILENAME = f"transcripcion_{now}.txt"
FILEPATH = os.path.join(SAVE_FOLDER, FILENAME)

# Verificar existencia del modelo
if not os.path.exists(MODEL_PATH):
    print(f"Modelo no encontrado en {MODEL_PATH}")
    sys.exit(1)

# Listar dispositivos de entrada disponibles
print("Dispositivos de entrada disponibles:")
input_devices = []
for i, dev in enumerate(sd.query_devices()):
    if dev['max_input_channels'] > 0:
        input_devices.append(i)
        print(f"{i}: {dev['name']} (canales entrada: {dev['max_input_channels']})")

# Elegir dispositivo
while True:
    try:
        device_index = int(input("Escribe el número del dispositivo de entrada que quieres usar: "))
        if device_index in input_devices:
            break
        else:
            print("Número inválido. Intenta de nuevo.")
    except ValueError:
        print("Por favor, ingresa un número válido.")

# Cargar modelo y crear recognizer con gramática personalizada
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE, json.dumps(VOCABULARIO_CL))
recognizer.SetWords(True)

# Cola para audio
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(f"[!] Estado: {status}", file=sys.stderr)
    q.put(bytes(indata))

print(f"🎤 Comenzando a escuchar desde dispositivo {device_index}. Presiona Ctrl+C para salir.\n")

# Variable para guardar el texto total transcrito hasta ahora
texto_total = ""

# Abrir archivo en modo escritura
with open(FILEPATH, "w", encoding="utf-8") as f:
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, dtype='int16', channels=1, callback=callback, device=device_index):
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    texto = res.get("text", "").strip()
                    if texto:
                        if texto.startswith(texto_total):
                            nuevo_fragmento = texto[len(texto_total):]
                        else:
                            nuevo_fragmento = texto

                        if nuevo_fragmento:
                            print("📝", texto)
                            f.write(nuevo_fragmento + " ")
                            f.flush()
                            texto_total = texto
                else:
                    partial = json.loads(recognizer.PartialResult())
                    if partial.get("partial"):
                        print("...", partial["partial"], end="\r")
    except KeyboardInterrupt:
        print("\n👋 Finalizado por el usuario.")
    except Exception as e:
        print(f"[ERROR] {e}")

# Preguntar si guardar o borrar el archivo
while True:
    respuesta = input(f"\n¿Quieres guardar la transcripción en '{FILENAME}'? (s/n): ").strip().lower()
    if respuesta == 's':
        print(f"Archivo guardado como '{FILENAME}'.")
        break
    elif respuesta == 'n':
        os.remove(FILEPATH)
        print("Archivo eliminado.")
        break
    else:
        print("Por favor, responde 's' para sí o 'n' para no.")
