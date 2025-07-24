🧠 Proyecto de Transcripción en Tiempo Real (Vosk + Python) 🧠

Este proyecto permite la transcripción de voz en tiempo real desde un micrófono utilizando Vosk con Python. Ideal para pruebas locales, prototipos o herramientas personalizadas de reconocimiento de voz.

📦 Descarga del modelo Vosk (español)

Este proyecto utiliza el modelo de reconocimiento de voz en español de Vosk.  
Para usarlo, descarga el modelo desde:

👉 https://alphacephei.com/vosk/models

Modelo recomendado: `vosk-model-small-es-0.42`

Descomprime la carpeta dentro del directorio del proyecto y asegúrate de que se llame `vosk-model-es-0.42`.

📦 Estructura del Proyecto
test-vosk/
├── realtime.py              # Script principal
├── vocabulariocl.py         # Lista de modismos personalizados
├── vosk-model-es-0.42/      # Modelo de reconocimiento en español
├── stt_guardados/
│   └── transcripcion_temp.txt  # Transcripción temporal

Primero Instala las dependencias: pip install -r requirements.txt
vosk==0.3.45
sounddevice==0.4.6


▶️ Ejecución
Asegúrate de tener un micrófono configurado y ejecuta:

python realtime.py
Selecciona el dispositivo de entrada que deseas utilizar cuando se te indique.

El sistema comenzará a transcribir en tiempo real y mostrará partes del texto progresivamente.

La transcripción también se guarda en: stt_guardados/transcripcion_temp.txt

⚠️ Notas

Puedes personalizar el vocabulario chileno en vocabulariocl.py para mejorar el reconocimiento.

Si deseas escuchar todo el audio del sistema (no solo el micrófono), deberías implementar un loopback de audio, lo cual requiere configuración adicional fuera de Python (como usar VB-Audio Cable en Windows o Loopback Audio en macOS).

