# 🧠 STTVAR: Transcripción y Análisis de Voz en Tiempo Real con IA

[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Vosk](https://img.shields.io/badge/Vosk-0.42%2B-orange.svg)](https://alphacephei.com/vosk/)
[![Ollama](https://img.shields.io/badge/Ollama-Mistral%207B-purple.svg)](https://ollama.com/)

---

¡Bienvenido a **STTVAR** (Speech-to-Text-Voice-Analysis-Realtime)! Este proyecto revoluciona la forma en que interactúas con el audio, ofreciendo una solución integral para la **transcripción de voz en tiempo real** y el **análisis de texto inteligente** en español. Desarrollado con tecnologías de vanguardia como **Vosk**, **PyQt5** y **Ollama**, STTVAR proporciona una experiencia fluida e intuitiva, ideal para periodistas, investigadores, estudiantes o cualquier persona que necesite convertir voz en conocimiento.

---

## ✨ Características Destacadas

* **🎤 Transcripción Instantánea:** Convierte tu voz en texto al momento gracias a la potencia de **Vosk**.
* **🖥️ Interfaz Intuitiva con PyQt5:** Explora, edita y gestiona tus transcripciones fácilmente con una UI moderna y responsiva.
* **🤖 Análisis Inteligente con IA Local:** Integra **Ollama** con `mistral:7b-instruct-q4_K_M` para obtener insights, resúmenes o respuestas a tus preguntas directamente desde el texto transcrito, ¡todo offline!
* **📝 Gestión Completa de Transcripciones:** Guarda, edita y exporta tus documentos en formatos populares como PDF, Word y Markdown.
* **⚙️ Personalizable y Extensible:** Adapta el vocabulario, la configuración de audio y los estilos visuales a tus necesidades.

---

## 🚀 Demo del Proyecto

<p align="center">
  <img src="assets/sttvar_demo.gif" alt="Demostración de STTVAR" width="700"/>
  <br>
  <em>Transcripción en tiempo real y análisis inteligente al alcance de tu mano.</em>
</p>

---

## 📥 Configuración Inicial

Para poner STTVAR en marcha, sigue estos sencillos pasos:

### 1. Descarga el Modelo de Voz Vosk

STTVAR utiliza un modelo de reconocimiento de voz local para la transcripción.
1.  Visita 🔗 [Vosk Model Small ES](https://alphacephei.com/vosk/models) (se recomienda `vosk-model-small-es-0.42`).
2.  **Descomprime** el archivo ZIP descargado.
3.  **Renombra** la carpeta resultante a `vosk-model-es-0.42` y colócala en el directorio raíz del proyecto (junto a `main.py`).

### 2. Instala las Dependencias de Python

Asegúrate de tener Python 3.9+ instalado y ejecuta:

```bash
pip install -r requirements.txt
````

**`requirements.txt`** (Contenido mínimo):

```
PyQt5
vosk
sounddevice
numpy
reportlab
python-docx
ollama
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
│   ├── grabadora.py         # 🎤 UI principal de grabación y transcripción en vivo
│   └── menu.py              # 📝 Menú para explorar, editar y consultar transcripciones con IA
├── stt_guardados/           # 📂 Carpeta donde se guardan las transcripciones (YYYY-MM-DD_HH-MM-SS.txt)
├── transcripcion/
│   ├── transcriber.py       # ⚡ Hilo dedicado para la ejecución de Vosk en tiempo real
│   └── vosk_utils.py        # 🛠️ Funciones auxiliares para la interacción con Vosk
├── vosk-model-es-0.42/      # 🗣️ Modelo de reconocimiento de voz de Vosk (¡recuerda renombrarlo!)
├── main.py                  # ▶️ Punto de entrada principal de la aplicación
├── README.md                # 📖 Documentación del proyecto
├── STTVAR.bat               # 🚀 Script de un clic para iniciar main.py (Windows)
├── vocabulariocl.py         # 💬 (Opcional) Glosario de términos chilenos para mejorar el reconocimiento
└── .gitignore               # 🚫 Archivos y carpetas ignorados por Git
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
      * Usa 🔇/🎙️ para **silenciar/reactivar** tu micrófono sin detener la transcripción.
      * Presiona ■ **Detener Grabación** para finalizar y guardar la transcripción en `stt_guardados/`. Se te preguntará si deseas guardar o descartar.

4.  **Explorador de Transcripciones (Botón ⚙️):**

      * Accede a una lista de tus transcripciones guardadas (`.txt`).
      * **Edita** el texto directamente en un editor integrado.
      * **Exporta** tus transcripciones a **PDF**, **Word** o **Markdown**.
      * **Consulta la IA:** Utiliza el texto de tu transcripción como contexto para hacer preguntas a Ollama y recibir respuestas directamente en la interfaz. *Nota: Cambiar de archivo limpiará automáticamente el campo de consulta IA.*

-----

## ⚠️ Consideraciones y Consejos

  * **Mejora del Reconocimiento:** Si trabajas con español chileno, te animamos a personalizar el archivo `vocabulariocl.py` con modismos y términos locales para optimizar la precisión de Vosk.
  * **Captura de Audio del Sistema:** Para transcribir audio que no provenga directamente de un micrófono (ej. YouTube, videollamadas), considera usar herramientas de audio virtual como **VB-Audio Cable** (Windows) o **Loopback Audio** (macOS).
  * **Personalización Visual:** Los estilos CSS para la interfaz están en `grabadora.py` y `menu.py`. ¡Siéntete libre de jugar con los colores y la tipografía\!
  * **Modelo de IA:** La ruta y el modelo de Ollama pueden cambiarse en `menu.py` si deseas experimentar con otros LLMs compatibles.

-----

## 📄 Formatos de Exportación

STTVAR te permite exportar tus transcripciones con facilidad:

| Formato    | Descripción                                           | Biblioteca Usada |
| :--------- | :---------------------------------------------------- | :--------------- |
| **PDF** | Documento portable con saltos de página automáticos.  | `ReportLab`      |
| **Word** | (`.docx`) Documento editable con formato de párrafo.  | `python-docx`    |
| **Markdown** | (`.md`) Texto plano con formato estructurado simple. | N/A              |

-----

## ✅ Soporte de Idiomas (Traducción Experimental)

STTVAR tiene la capacidad de expandirse para la traducción. Para añadir soporte a más idiomas:

1.  **Instala `argostranslate`:**
    ```bash
    pip install argostranslate
    ```
2.  **Instala los paquetes de idioma deseados** desde tu consola. Por ejemplo:
    ```bash
    argos-translate-cli --install eng spa  # Inglés a Español
    argos-translate-cli --install zho spa  # Chino a Español
    argos-translate-cli --install deu spa  # Alemán a Español
    argos-translate-cli --install por spa  # Portugués a Español
    ```
    Puedes ver todos los idiomas disponibles con: `argos-translate-cli --list-languages`

-----

## 💬 Contribuciones

¡Tu feedback y contribuciones son bienvenidos\! Si encuentras un bug, tienes una sugerencia o quieres añadir una nueva característica, por favor, abre un "issue" o envía un "pull request".

-----

## 🛡️ Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para más detalles.

-----

**Desarrollado con 💖 por Lucas Jimenez Sepulveda**  
📧 Contacto: lucasjimenezsepulveda@gmail.com  

```
```