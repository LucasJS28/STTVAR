# 🚀 STTVAR: Plataforma Colaborativa de Transcripción y Análisis en Tiempo Real (Desktop Server + Web Client)

[](https://opensource.org/licenses/MIT)
[](https://www.python.org/)
[](https://alphacephei.com/vosk/)
[](https://ollama.com/)
[](https://flask.palletsprojects.com/)

-----

¡Bienvenido a **STTVAR**\! Este proyecto ha evolucionado de una simple herramienta de transcripción a una **potente plataforma colaborativa y multiusuario**. STTVAR opera bajo un modelo **Servidor-Cliente**, donde la aplicación de escritorio (`grabadora.py`) actúa como el *Servidor* que realiza la transcripción, la grabación, y aloja un **servidor web Flask** en segundo plano para el *Streaming* de datos.

La **interfaz web (Frontend)** permite a colaboradores, estudiantes o asistentes de reunión conectarse vía **código QR** para **ver la transcripción en vivo**, **chatear**, **tomar apuntes** y **analizar el texto con IA**, todo en tiempo real y con traducción individual. Es la herramienta definitiva para convertir voz en conocimiento accesible, colaborativo y globalmente compartible.

-----

## ✨ Características Estelares

### 💡 Core & Desktop

  * **🎤 Transcripción Instantánea con Selección de Idioma:** Convierte voz en texto al momento, eligiendo entre español o inglés, adaptando el modelo **Vosk** dinámicamente.
  * **🎧 Grabación de Audio Concurrente:** Captura y guarda el audio original (`.wav`) mientras la transcripción se ejecuta.
  * **🖥️ Gestión de Transcripciones (PyQt5):** Interfaz de escritorio para explorar, editar, consultar la IA, traducir y exportar documentos (PDF, Word, Markdown).
  * **🔒 Aceptación de Términos:** El *launcher* inicializa la app solo tras la aceptación de los términos para garantizar la privacidad y el uso legal.

### 🌐 Interfaz Web (Colaboración en Tiempo Real)

  * **⚡ Streaming de Subtítulos con SSE:** La transcripción se "empuja" a todos los clientes web en tiempo real sin recargas (Server-Sent Events).
  * **💬 Chat Global Integrado:** Los usuarios pueden comunicarse en vivo en un chat que se actualiza a todos los clientes.
  * **📝 Apuntes Colaborativos:** Los usuarios toman apuntes y pueden **compartirlos** con el grupo a través del chat, donde se muestran como un bloque destacado con opción de descarga.
  * **🗣️ Comunicación Multi-Idioma Individual:** Cada usuario web selecciona su idioma de preferencia. La aplicación traduce el texto de la transcripción **específicamente para ese cliente** usando **Argos Translate** antes de enviárselo.
  * **🤖 Asistente de IA (Ollama/Mistral 7B):** La interfaz web permite a los colaboradores hacer preguntas sobre el texto transcrito y recibir respuestas generadas **localmente**.
  * **📲 Acceso con Código QR:** Un botón en la UI de escritorio genera un QR que permite unirse a la sesión fácilmente desde cualquier dispositivo en la red local.

### 🌎 Alcance Global

  * **🔗 Ngrok Automatizado:** El botón de compartir inicia automáticamente un túnel **Ngrok** en segundo plano, generando una URL pública para que usuarios **fuera de la red local** puedan conectarse con un solo clic.

-----

## 🏗️ Justificación y Evolución Arquitectónica

El proyecto pasó de ser una aplicación local a una plataforma híbrida para resolver dos problemas clave: **la colaboración** y **el acceso remoto**.

| Componente | Objetivo | Tecnología |
| :--- | :--- | :--- |
| **Backend (PyQt5)** | Controla el flujo de datos: Vosk → Flask → Clientes. | `grabadora.py` (Manejo de audio y servidor Flask) |
| **Server-Sent Events (SSE)** | Permite enviar datos desde el servidor a múltiples clientes al mismo tiempo, esencial para el streaming en vivo y el chat global. | Flask `/stream` route |
| **Ngrok** | Supera las limitaciones de la red local, permitiendo compartir la sesión globalmente de forma segura y automatizada. | `pyngrok` y `qr_app.py` |
| **Lógica Individualizada** | Garantiza que las preferencias de un usuario (traducción, IA) no afecten a los demás, manteniendo una experiencia personal. | Diccionarios globales en `grabadora.py` (`clientes_idioma`, `client_ai_responses`) |

-----

## 📥 Configuración Inicial

Para poner STTVAR en marcha, sigue estos sencillos pasos:

### 1\. Descarga los Modelos de Voz Vosk

STTVAR utiliza modelos de reconocimiento de voz locales para la transcripción. Necesitarás descargar al menos el modelo en español y el inglés.

1.  Visita 🔗 [Vosk Models](https://alphacephei.com/vosk/models)
2.  **Descarga los modelos** (ej. `vosk-model-small-es-0.42`).
3.  **Descomprime** y **renombra** las carpetas, colocándolas en el **directorio raíz** del proyecto (junto a `main.py`).

### 2\. Instala las Dependencias de Python

Asegúrate de tener Python 3.9+ instalado y ejecuta:

```bash
pip install -r requirements.txt
```

**`requirements.txt`** (Contenido mínimo ampliado):

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
Flask         # Para el servidor web
qrcode        # Para generar el QR de conexión
pyngrok       # Para compartir la sesión globalmente
```

### 3\. Configura Ollama y Descarga el Modelo de IA

Ollama te permite ejecutar modelos de lenguaje grandes (LLMs) localmente.

1.  **Instala Ollama:** Sigue las instrucciones para tu sistema operativo en 🔗 [ollama.com](https://ollama.com/).

2.  **Descarga el Modelo:** Abre tu terminal y ejecuta:

    ```bash
    ollama pull mistral:7b-instruct-q4_K_M
    ```

### 4\. Configuración de Ngrok (Opcional, para Compartir Globalmente)

Para usar la función de compartir fuera de tu red local, necesitas un token de Ngrok:

1.  Regístrate en Ngrok y obtén tu `authtoken`.
2.  La primera vez que hagas clic en el botón de compartir (**🌐**) en la aplicación de escritorio, se te pedirá ingresar este token.

-----

## 📁 Estructura del Proyecto

La nueva arquitectura se organiza para separar las responsabilidades de la UI de escritorio, el servidor web y la lógica del núcleo.

```
STTVAR/
├── interfaz/
│   ├── grabadora.py         # 💻 UI Principal (Contiene el Servidor Flask)
│   ├── launcher.py          # ▶️ Validador de términos e iniciador de la UI
│   ├── menu.py              # 📝 Explorador y editor de transcripciones
│   ├── terminos.py          # 📄 Pantalla de Términos y Condiciones
│   ├── qr_app.py            # 📲 Genera la ventana con el QR y URLs de conexión
│   └── templates/             # 🌐 Contiene index.html (Frontend Cliente)
├── stt_guardados/           # 📂 Transcripciones guardadas
├── sttaudio_guardados/      # 🎧 Audios WAV originales
├── traduccion/              # 🌐 Módulo de Argos Translate
├── transcripcion/           # ⚡ Lógica de Vosk y Transcripción
├── vocabularios/            # 💬 Archivos de vocabulario personalizados
├── vosk-model-es-0.42/      # 🗣️ Modelo de Vosk (Español)
├── main.py                  # ▶️ Punto de entrada principal
└── requirements.txt         # 📦 Dependencias
```

-----

## 🗺️ Guía de Uso Rápido (Servidor y Clientes)

### 1\. Inicio y Conexión

1.  Ejecuta `python main.py`.
2.  Acepta los términos y condiciones.
3.  En la UI de escritorio (`grabadora.py`), selecciona el idioma de transcripción y el micrófono.
4.  Haz clic en el botón **Compartir** (**🌐**). La aplicación inicia el servidor Flask, configura Ngrok (si es necesario) y muestra la ventana `qr_app.py`.
5.  **Conexión de Clientes:** Pide a los colaboradores que **escaneen el QR** o usen la **URL local/pública** para acceder a la interfaz web en su navegador.

### 2\. Funcionalidad Web (Cliente)

Una vez conectados, los clientes pueden:

  * **Ver Subtítulos:** La transcripción parcial y acumulada se actualizan en vivo.
  * **Traducir (Individual):** Usar el selector de idioma para ver el texto **traducido solo para ellos**.
  * **Chatear:** Enviar mensajes al chat global que se muestra a todos los demás clientes.
  * **Tomar y Compartir Apuntes:** Usar el panel de apuntes para tomar notas privadas y, si lo desean, **compartirlas** con el grupo a través del chat con un formato descargable.
  * **Preguntar a la IA:** Usar el asistente para obtener un resumen o preguntar sobre el texto acumulado.

### 3\. Finalización

1.  Haz clic en **Detener Grabación** (■) en la UI de escritorio.
2.  Al cerrar la aplicación principal, el servidor Flask y el túnel Ngrok **se cierran automáticamente** para liberar recursos y garantizar la privacidad.

-----

## ⚠️ Consideraciones y Consejos

  * **Integridad del Audio:** Para transcribir audio del sistema (ej. una reunión de Teams), considera usar una utilidad de audio virtual (ej., VB-Audio Cable o Loopback) en lugar del micrófono físico.
  * **Latencia Web:** La latencia puede variar ligeramente al usar Ngrok debido a la distancia y la infraestructura de internet, pero el sistema SSE minimiza el retraso en la recepción de datos.
  * **Vocabulario Local:** Se recomienda modificar el archivo en la carpeta `vocabularios/` para aumentar la precisión de Vosk con términos y modismos locales.

-----

## 📄 Formatos de Exportación

STTVAR te permite exportar tus transcripciones con facilidad:

| Formato    | Descripción                                           | Biblioteca Usada   |
| :--------- | :---------------------------------------------------- | :----------------- |
| **PDF** | Documento portable con saltos de página automáticos.  | `ReportLab`        |
| **Word** | (`.docx`) Documento editable con formato de párrafo.  | `python-docx`      |
| **Markdown** | (`.md`) Texto plano con formato estructurado simple. | N/A                |

-----

## 💬 Contribuciones y Licencia

¡Tu feedback y contribuciones son bienvenidos\! Este proyecto es un esfuerzo constante por mejorar la accesibilidad y la colaboración.

Este proyecto está distribuido bajo la **Licencia MIT**.

-----

**Desarrollado con 💖 por Lucas Jimenez Sepulveda**
📧 Contacto: lucasjimenezsepulveda@gmail.com
🌐 Repositorio: [https://github.com/LucasJS28/STTVAR](https://github.com/LucasJS28/STTVAR)