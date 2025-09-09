# 🧠 STTVAR: Transcripción, Análisis y Gestión de Voz/Audio en Tiempo Real con IA

[](https://opensource.org/licenses/MIT)
[](https://www.python.org/)
[](https://alphacephei.com/vosk/)
[](https://ollama.com/)

-----

¡Bienvenido a **STTVAR** (Speech-to-Text-Voice-Analysis-Realtime)\! Este proyecto revoluciona la forma en que interactúas con el audio, ofreciendo una solución integral para la **transcripción de voz en tiempo real** con **selección de idioma**, la **grabación simultánea de audio**, el **análisis de texto inteligente** y la **traducción** en múltiples idiomas. Desarrollado con tecnologías de vanguardia como **Vosk**, **PyQt5**, **Ollama**, **pyttsx3** y **Argos Translate**, STTVAR proporciona una experiencia fluida e intuitiva, ideal para periodistas, investigadores, estudiantes o cualquier persona que necesite convertir voz en conocimiento, gestionar grabaciones de audio, traducir textos y escuchar el análisis de la IA.

-----

## ✨ Características Destacadas

  * **🎤 Transcripción Instantánea con Selección de Idioma:** Convierte tu voz en texto al momento, con la opción de elegir entre español o inglés para la transcripción en tiempo real, adaptando dinámicamente el motor de reconocimiento de voz.
  * **🎧 Grabación de Audio Concurrente:** Captura y guarda el audio original mientras se realiza la transcripción, permitiendo una revisión detallada.
  * **🌐 Interfaz Web Integrada:** Accede a la transcripción en vivo desde cualquier dispositivo en tu red local escaneando un código QR. Esta interfaz web ofrece:
      * **Subtítulos en Tiempo Real:** Visualiza la transcripción parcial mientras hablas.
      * **Traducción en Vivo:** Traduce los subtítulos a múltiples idiomas usando Argos Translate.
      * **Asistente de IA (Mistral 7B):** Haz preguntas sobre el texto acumulado y obtén respuestas generadas localmente por Ollama.
  * **🖥️ Interfaz de Escritorio con PyQt5:** Explora, edita y gestiona tus transcripciones y grabaciones fácilmente con una UI moderna y responsiva.
  * **🗣️ Lectura de Texto con Voz (TTS):** Utiliza **pyttsx3** para escuchar los resultados generados por la IA en diversos idiomas, mejorando la accesibilidad y la revisión.
  * **📝 Gestión Completa de Transcripciones:** Guarda, edita y exporta tus documentos en formatos populares como PDF, Word y Markdown.
  * **🔒 Aceptación de Términos:** La aplicación requiere la aceptación de los términos y condiciones de uso para garantizar la privacidad y el uso responsable.
  * **⚙️ Personalizable y Extensible:** Adapta el vocabulario, la configuración de audio y los estilos visuales a tus necesidades.

-----

## 📥 Configuración Inicial

Para poner STTVAR en marcha, sigue estos sencillos pasos:

### 1\. Descarga los Modelos de Voz Vosk

STTVAR utiliza modelos de reconocimiento de voz locales para la transcripción. Necesitarás descargar al menos el modelo en español y el inglés.

1.  Visita 🔗 [Vosk Models](https://alphacephei.com/vosk/models)
2.  **Descarga los siguientes modelos** (o sus versiones más recientes y pequeñas):
      * Español: `vosk-model-small-es-0.42`
      * Inglés: `vosk-model-small-en-us-0.22` (o similar, busca uno para "en-us" o "en")
3.  **Descomprime** los archivos ZIP descargados.
4.  **Renombra** las carpetas resultantes y colócalas en el directorio raíz del proyecto (junto a `main.py`). Asegúrate de que los nombres sean los que usa el programa, por ejemplo:
      * `vosk-model-es-0.42`
      * `vosk-model-en-us-0.22`

### 2\. Instala las Dependencias de Python

Asegúrate de tener Python 3.9+ instalado y ejecuta:

```bash
pip install -r requirements.txt
```

**`requirements.txt`** (Contenido mínimo):

```
PyQt5
vosk
sounddevice
numpy
reportlab
python-docx
ollama
pyttsx3
argostranslate
Flask
qrcode
# Posiblemente necesites PyAudio o similar si sounddevice no es suficiente para la grabación/reproducción
# pip install pyaudio
```

### 3\. Configura Ollama y Descarga el Modelo de IA

Ollama te permite ejecutar modelos de lenguaje grandes (LLMs) localmente.

1.  **Instala Ollama:** Sigue las instrucciones para tu sistema operativo en 🔗 [ollama.com](https://ollama.com/).

2.  **Descarga el Modelo:** Abre tu terminal y ejecuta:

    ```bash
    ollama pull mistral:7b-instruct-q4_K_M
    ```

    *(Este modelo es ideal para análisis y conversaciones rápidas.)*

3.  **Verifica la Ruta:** Asegúrate de que la ruta al ejecutable `ollama.exe` esté configurada correctamente dentro del archivo `interfaz/menu.py` si es necesario.

-----

## 📁 Estructura del Proyecto

```
STTVAR/
├── interfaz/
│   ├── __pycache__
│   ├── __init__.py
│   ├── grabadora.py         # 🎤 UI de escritorio y servidor web integrado (Flask)
│   ├── launcher.py          # ▶️ Script de inicio que verifica la aceptación de los términos y condiciones
│   ├── menu.py              # 📝 Menú para explorar, editar, consultar, traducir y reproducir audio
│   ├── terminos.py          # 📄 Muestra los términos y condiciones de uso de la aplicación
│   └── templates/             # 💻 Carpeta con archivos HTML para la interfaz web (index.html)
├── stt_guardados/           # 📂 Carpeta con transcripciones guardadas (YYYY-MM-DD_HH-MM-SS.txt)
├── sttaudio_guardados/      # 🎧 Carpeta con los audios originales grabados (YYYY-MM-DD_HH-MM-SS.wav)
├── traduccion/              # 🌐 Módulo para la gestión y ejecución de traducciones
├── transcripcion/
│   ├── __pycache__
│   ├── transcriber.py       # ⚡ Hilo dedicado para la ejecución de Vosk en tiempo real
│   └── vosk_utils.py        # 🛠️ Funciones auxiliares para la interacción con Vosk
├── vocabularios/            # 💬 Carpeta que contiene archivos de vocabulario personalizados
├── vosk-model-es-0.42/      # 🗣️ Modelo de reconocimiento de voz de Vosk para español
├── .gitignore               # 🚫 Archivos y carpetas ignorados por Git
├── main.py                  # ▶️ Punto de entrada principal de la aplicación
├── README.md                # 📖 Documentación del proyecto
├── requirements.txt         # 📦 Lista de dependencias de Python
└── STTVAR.bat               # 🚀 Script de un clic para iniciar main.py (Windows)
```

-----

## 🔒 Términos y Condiciones de Uso

Antes de usar la aplicación, se le presentará una pantalla de bienvenida que requiere la aceptación de los términos y condiciones. Estos términos están diseñados para garantizar la transparencia y el uso responsable de la herramienta.

  * **Uso Personal y Privacidad:** La aplicación es para uso personal y no comercial. Todos los datos (grabaciones y transcripciones) se procesan de forma local en su dispositivo y nunca se envían a servidores externos.
  * **Responsabilidad del Usuario:** Usted es el único responsable de cumplir con las leyes de privacidad y de obtener el consentimiento de todas las partes involucradas antes de grabar o transcribir una conversación. STTVAR no se hace responsable de ningún uso indebido o ilegal.

La aplicación no se iniciará hasta que usted acepte estos términos.

-----

## ▶️ Guía de Uso Rápido

1.  **Conecta y configura tu micrófono** como dispositivo de entrada predeterminado.

2.  Inicia la aplicación desde la terminal:

    ```bash
    python main.py
    ```

      * Al iniciar por primera vez, se mostrará una ventana con los términos y condiciones. **Debe leerlos y aceptarlos** para poder acceder a la funcionalidad principal de la aplicación.

3.  **Interfaz Principal (Grabadora):**

      * **Elige el idioma de transcripción:** Antes de iniciar la grabación, selecciona el idioma deseado para la transcripción (Español o Inglés) desde el selector en la interfaz. Esto cargará el modelo Vosk correspondiente.
      * **Selecciona tu dispositivo** de micrófono desde el menú desplegable.
      * Haz clic en 🔴 **Iniciar Grabación** para que la transcripción en tiempo real comience a aparecer en el idioma seleccionado.
          * A la vez que se transcribe, el audio de tu micrófono será **grabado y guardado** automáticamente en la carpeta `sttaudio_guardados/`.
      * **¡Nuevo\! Interfaz Web:** La aplicación generará un **código QR** que, al escanearse con un teléfono o tablet conectado a la misma red, te permitirá acceder a la interfaz web con las siguientes funciones:
          * Ver subtítulos en tiempo real.
          * Traducir el texto en vivo.
          * Interactuar con la IA para obtener resúmenes o respuestas.
      * Usa 🔇/🎙️ para **silenciar/reactivar** tu micrófono sin detener la transcripción.
      * Presiona ■ **Detener Grabación** para finalizar y guardar la transcripción en `stt_guardados/`. Se te preguntará si deseas guardar o descartar. El audio se guardará con el mismo nombre y timestamp (ej. `YYYY-MM-DD_HH-MM-SS.wav`).

4.  **Explorador de Transcripciones (Botón ⚙️):**

      * Accede a una lista de tus transcripciones guardadas (`.txt`).
      * Al seleccionar una transcripción, la aplicación buscará automáticamente un archivo de audio (`.wav`) con el mismo nombre en la carpeta `sttaudio_guardados/` para vincularlo.
      * **Reproducir Audio:** Verás un botón de **"Reproducir Audio"** (o similar) que te permitirá escuchar la grabación original asociada a la transcripción seleccionada.
      * **Edita** el texto directamente en un editor integrado.
      * **Exporta** tus transcripciones a **PDF**, **Word** o **Markdown**.
      * **Consulta la IA:** Utiliza el texto de tu transcripción como contexto para hacer preguntas a Ollama y recibir respuestas directamente en la interfaz.
          * Ahora verás un botón o una opción para **"Leer Respuesta"** que usará `pyttsx3` para vocalizar el texto generado por la IA.
      * **Traduce el Texto:** Selecciona un fragmento de texto o la transcripción completa para traducirla a los idiomas para los que hayas instalado los modelos de Argos Translate.
      * *Nota: Cambiar de archivo limpiará automáticamente los campos de consulta IA y traducción, y cargará el nuevo audio asociado.*

-----

## ⚠️ Consideraciones y Consejos

  * **Precisión del Reconocimiento de Voz:** Para una **precisión óptima en la transcripción**, es crucial que el idioma que elijas en la interfaz (Español o Inglés) coincida con el idioma que se está hablando.
  * **Mejora del Reconocimiento (Español Chileno):** Si trabajas con español chileno, puedes adaptar el archivo en la carpeta `vocabularios/` con modismos y términos locales para optimizar la precisión de Vosk en este dialecto.
  * **Captura de Audio del Sistema:** Para transcribir y grabar audio que no provenga directamente de un micrófono (ej. YouTube, videollamadas), considera usar herramientas de audio virtual como **VB-Audio Cable** (Windows) o **Loopback Audio** (macOS).
  * **Personalización Visual:** Los estilos CSS para la interfaz están en `grabadora.py` y `menu.py`. ¡Siéntete libre de jugar con los colores y la tipografía\!
  * **Modelos de Traducción:** Los modelos de Argos Translate pueden ser grandes. Asegúrate de tener suficiente espacio en disco al instalarlos.
  * **Tamaño de Archivos de Audio:** Grabar audio en formato WAV puede generar archivos de gran tamaño rápidamente, especialmente en grabaciones largas. Considera la duración de tus sesiones para gestionar el espacio de almacenamiento.

-----

## 📄 Formatos de Exportación

STTVAR te permite exportar tus transcripciones con facilidad:

| Formato    | Descripción                                           | Biblioteca Usada   |
| :--------- | :---------------------------------------------------- | :----------------- |
| **PDF** | Documento portable con saltos de página automáticos.  | `ReportLab`        |
| **Word** | (`.docx`) Documento editable con formato de párrafo.  | `python-docx`      |
| **Markdown** | (`.md`) Texto plano con formato estructurado simple. | N/A                |

-----

## 💬 Contribuciones

¡Tu feedback y contribuciones son bienvenidos\! Si encuentras un bug, tienes una sugerencia o quieres añadir una nueva característica, por favor, abre un "issue" o envía un "pull request".

-----

## 🛡️ Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para más detalles.

-----

**Desarrollado con 💖 por Lucas Jimenez Sepulveda**
📧 Contacto: lucasjimenezsepulveda@gmail.com
🌐 Repositorio: [https://github.com/LucasJS28/STTVAR](https://github.com/LucasJS28/STTVAR)