# 🧠 STTVAR: Transcripción, Análisis y Gestión de Voz/Audio en Tiempo Real con IA

[](https://opensource.org/licenses/MIT)
[](https://www.python.org/)
[](https://alphacephei.com/vosk/)
[](https://ollama.com/)

-----

¡Bienvenido a **STTVAR** (Speech-to-Text-Voice-Analysis-Realtime)\! Este proyecto revoluciona la forma en que interactúas con el audio, ofreciendo una solución integral para la **transcripción de voz en tiempo real**, la **grabación simultánea de audio**, el **análisis de texto inteligente** y la **traducción** en múltiples idiomas. Desarrollado con tecnologías de vanguardia como **Vosk**, **PyQt5**, **Ollama**, **pyttsx3** y **Argos Translate**, STTVAR proporciona una experiencia fluida e intuitiva, ideal para periodistas, investigadores, estudiantes o cualquier persona que necesite convertir voz en conocimiento, gestionar grabaciones de audio, traducir textos y escuchar el análisis de la IA.

-----

## ✨ Características Destacadas

  * **🎤 Transcripción Instantánea:** Convierte tu voz en texto al momento gracias a la potencia de **Vosk**.
  * **🎧 Grabación de Audio Concurrente:** Captura y guarda el audio original mientras se realiza la transcripción, permitiendo una revisión detallada.
  * **🖥️ Interfaz Intuitiva con PyQt5:** Explora, edita y gestiona tus transcripciones y grabaciones fácilmente con una UI moderna y responsiva.
  * **🤖 Análisis Inteligente con IA Local:** Integra **Ollama** con `mistral:7b-instruct-q4_K_M` para obtener insights, resúmenes o respuestas a tus preguntas directamente desde el texto transcrito, ¡todo offline\!
  * **🗣️ Lectura de Texto con Voz (TTS):** Utiliza **pyttsx3** para escuchar los resultados generados por la IA en diversos idiomas, mejorando la accesibilidad y la revisión.
  * **🌐 Traducción de Texto Integrada:** Soporte para traducción a múltiples idiomas gracias a **Argos Translate**, con herramientas para gestionar los modelos de idioma.
  * **📝 Gestión Completa de Transcripciones:** Guarda, edita y exporta tus documentos en formatos populares como PDF, Word y Markdown.
  * **⚙️ Personalizable y Extensible:** Adapta el vocabulario, la configuración de audio y los estilos visuales a tus necesidades.

-----

## 📥 Configuración Inicial

Para poner STTVAR en marcha, sigue estos sencillos pasos:

### 1\. Descarga el Modelo de Voz Vosk

STTVAR utiliza un modelo de reconocimiento de voz local para la transcripción.

1.  Visita 🔗 [Vosk Model Small ES](https://alphacephei.com/vosk/models) (se recomienda `vosk-model-small-es-0.42`).
2.  **Descomprime** el archivo ZIP descargado.
3.  **Renombra** la carpeta resultante a `vosk-model-es-0.42` y colócala en el directorio raíz del proyecto (junto a `main.py`).

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

### 4\. Configuración Adicional para pyttsx3 (Sistemas Operativos)

`pyttsx3` utiliza los motores de texto a voz nativos de tu sistema operativo.

  * **Windows:** Generalmente funciona sin configuración adicional.
  * **macOS:** Funciona de inmediato con `NSSpeechSynthesizer`.
  * **Linux:** Asegúrate de tener `espeak` y/o `festival` instalados. Por ejemplo, en Ubuntu/Debian:
    ```bash
    sudo apt-get update
    sudo apt-get install espeak
    # o sudo apt-get install festival
    ```

### 5\. Configuración de Modelos de Traducción (Argos Translate)

Para que la traducción funcione, necesitas instalar los modelos de idioma de Argos Translate.
Puedes usar el script `instalar_modelos.py` ubicado en la carpeta `traduccion/` o hacerlo manualmente:

1.  **Instala los idiomas deseados** desde tu consola. Por ejemplo, para Español (spa), Inglés (eng), Chino (zho), Alemán (deu) y Portugués (por) hacia/desde español:
    ```bash
    argos-translate-cli --install eng spa
    argos-translate-cli --install zho spa
    argos-translate-cli --install deu spa
    argos-translate-cli --install por spa
    # Puedes usar: argos-translate-cli --list-languages para ver todas las opciones.
    ```
2.  Puedes ejecutar el script `traduccion/revisar_modelos.py` para verificar qué modelos tienes instalados.

-----

## 📁 Estructura del Proyecto

```
STTVAR/
├── interfaz/
│   ├── grabadora.py         # 🎤 UI principal de grabación, transcripción en vivo y grabación de audio
│   └── menu.py              # 📝 Menú para explorar, editar, consultar, traducir y reproducir audio
├── stt_guardados/           # 📂 Carpeta con transcripciones y sus audios guardados (YYYY-MM-DD_HH-MM-SS.txt / .wav)
├── traduccion/              # 🌐 Módulo para la gestión y ejecución de traducciones
│   ├── __pycache__
│   ├── __init__.py
│   ├── instalar_modelos.py  # 📥 Script para automatizar la descarga de modelos de traducción
│   └── revisar_modelos.py   # 🔍 Script para verificar modelos de traducción instalados
├── transcripcion/
│   ├── transcriber.py       # ⚡ Hilo dedicado para la ejecución de Vosk en tiempo real
│   └── vosk_utils.py        # 🛠️ Funciones auxiliares para la interacción con Vosk
├── vosk-model-es-0.42/      # 🗣️ Modelo de reconocimiento de voz de Vosk (¡recuerda renombrarlo!)
├── .gitignore               # 🚫 Archivos y carpetas ignorados por Git
├── main.py                  # ▶️ Punto de entrada principal de la aplicación
├── README.md                # 📖 Documentación del proyecto
├── requirements.txt         # 📦 Lista de dependencias de Python
├── STTVAR.bat               # 🚀 Script de un clic para iniciar main.py (Windows)
└── vocabulariocl.py         # 💬 (Opcional) Glosario de términos chilenos para mejorar el reconocimiento
```

-----

## ▶️ Guía de Uso Rápido

1.  **Conecta y configura tu micrófono** como dispositivo de entrada predeterminado.

2.  Inicia la aplicación desde la terminal:

    ```bash
    python main.py
    ```

3.  **Interfaz Principal (Grabadora):**

      * **Selecciona tu dispositivo** de micrófono desde el menú desplegable.
      * Haz clic en 🔴 **Iniciar Grabación** para que la transcripción en tiempo real comience a aparecer.
          * **¡Nuevo\!** A la vez que se transcribe, el audio de tu micrófono será **grabado y guardado** automáticamente.
      * Usa 🔇/🎙️ para **silenciar/reactivar** tu micrófono sin detener la transcripción.
      * Presiona ■ **Detener Grabación** para finalizar y guardar la transcripción en `stt_guardados/`. Se te preguntará si deseas guardar o descartar. El audio se guardará con el mismo nombre y timestamp (ej. `YYYY-MM-DD_HH-MM-SS.wav`).

4.  **Explorador de Transcripciones (Botón ⚙️):**

      * Accede a una lista de tus transcripciones guardadas (`.txt`).
      * Al seleccionar una transcripción, si existe un archivo de audio (`.wav`) con el mismo nombre asociado, se cargará automáticamente.
      * **¡Nuevo\! Reproducir Audio:** Verás un botón de **"Reproducir Audio"** (o similar) que te permitirá escuchar la grabación original asociada a la transcripción seleccionada.
      * **Edita** el texto directamente en un editor integrado.
      * **Exporta** tus transcripciones a **PDF**, **Word** o **Markdown**.
      * **Consulta la IA:** Utiliza el texto de tu transcripción como contexto para hacer preguntas a Ollama y recibir respuestas directamente en la interfaz.
          * Ahora verás un botón o una opción para **"Leer Respuesta"** que usará `pyttsx3` para vocalizar el texto generado por la IA, independientemente del idioma detectado.
      * **Traduce el Texto:** Selecciona un fragmento de texto o la transcripción completa para traducirla a los idiomas para los que hayas instalado los modelos de Argos Translate.
      * *Nota: Cambiar de archivo limpiará automáticamente los campos de consulta IA y traducción, y cargará el nuevo audio asociado.*

-----

## ⚠️ Consideraciones y Consejos

  * **Mejora del Reconocimiento:** Si trabajas con español chileno, te animamos a personalizar el archivo `vocabulariocl.py` con modismos y términos locales para optimizar la precisión de Vosk.
  * **Captura de Audio del Sistema:** Para transcribir y grabar audio que no provenga directamente de un micrófono (ej. YouTube, videollamadas), considera usar herramientas de audio virtual como **VB-Audio Cable** (Windows) o **Loopback Audio** (macOS).
  * **Personalización Visual:** Los estilos CSS para la interfaz están en `grabadora.py` y `menu.py`. ¡Siéntete libre de jugar con los colores y la tipografía\!
  * **Modelo de IA:** La ruta y el modelo de Ollama pueden cambiarse en `menu.py` si deseas experimentar con otros LLMs compatibles.
  * **Voces de pyttsx3:** La calidad y variedad de las voces disponibles con `pyttsx3` dependen de los motores TTS instalados en tu sistema operativo. Puedes explorar y seleccionar diferentes voces si tu OS las ofrece.
  * **Modelos de Traducción:** Los modelos de Argos Translate pueden ser grandes. Asegúrate de tener suficiente espacio en disco al instalarlos. La precisión de la traducción dependerá de la calidad de los modelos instalados.
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