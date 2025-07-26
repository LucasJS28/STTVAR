Aquí tienes una versión optimizada y visualmente atractiva del `README.md` para que se vea bien en GitHub, manteniendo el contenido original pero con un formato más limpio, organizado y con emojis que aprovechan el estilo de Markdown de GitHub:

```markdown
# 🧠 Proyecto Transcripción en Tiempo Real con IA (Vosk + Python + Ollama)

¡Bienvenido a **STTVAR**! Este proyecto combina tecnologías de vanguardia para ofrecer una solución completa de **transcripción de voz en tiempo real** y análisis de texto en español, con una interfaz gráfica intuitiva y capacidades de inteligencia artificial.

## ✨ Características Principales

- 🎤 **Transcripción en tiempo real**: Usa **Vosk** para convertir voz en texto al instante.
- 🖥️ **Interfaz gráfica**: Desarrollada con **PyQt5**, permite explorar, editar y exportar transcripciones.
- 🤖 **Análisis con IA**: Integra **Ollama** (modelo `mistral:7b-instruct-q4_K_M`) para consultas inteligentes basadas en el texto transcrito.

---

## 📥 Configuración del Modelo Vosk

Para que la transcripción funcione correctamente, sigue estos pasos:

1. Descarga el modelo de reconocimiento de voz en español desde:  
   🔗 [Vosk Model Small ES](https://alphacephei.com/vosk/models) (Recomendado: `vosk-model-small-es-0.42`).
2. Descomprime el archivo en el directorio raíz del proyecto.
3. Renombra la carpeta a `vosk-model-es-0.42`.

---

## 📁 Estructura del Proyecto

```plaintext
STTVAR/
├── interfaz/
│   ├── grabadora.py         # UI para grabación, control de mute y STT en vivo
│   └── menu.py              # Menú para explorar transcripciones y consultas IA
├── stt_guardados/           # Carpeta con transcripciones guardadas (YYYY-MM-DD_HH-MM-SS.txt)
├── transcripcion/
│   ├── transcriber.py       # Hilo para ejecutar Vosk en tiempo real
│   └── vosk_utils.py        # Funciones auxiliares para Vosk
├── vosk-model-es-0.42/      # Modelo Vosk renombrado
├── main.py                  # Punto de entrada de la aplicación
├── README.md                # Documentación del proyecto
├── STTVAR.bat               # Script para ejecutar main.py sin consola
├── vocabulariocl.py         # (Opcional) Glosario para español chileno
└── .gitignore               # Archivos ignorados por Git
```

---

## 🛠️ Instalación y Configuración

### 1. Instala las dependencias de Python
```bash
pip install -r requirements.txt
```

Contenido mínimo de `requirements.txt`:
```
PyQt5
vosk
sounddevice
numpy
reportlab
python-docx
ollama
```

### 2. Configura Ollama
- Sigue las instrucciones en [ollama.com](https://ollama.com/).
- Descarga el modelo ejecutando:
  ```bash
  ollama pull mistral:7b-instruct-q4_K_M
  ```
- Asegúrate de que la ruta al ejecutable `ollama.exe` esté correcta en `interfaz/menu.py`.

---

## ▶️ Cómo Usar

1. **Conecta y configura un micrófono**.
2. Ejecuta el proyecto:
   ```bash
   python main.py
   ```
3. **Interfaz del Transcriptor**:
   - Selecciona el dispositivo de entrada (micrófono) desde el combo box.
   - Haz clic en 🔴 **Iniciar Grabación** para comenzar la transcripción.
   - Usa 🔇/🎙️ para silenciar/reactivar el micrófono.
   - Presiona ■ **Detener Grabación** para guardar la transcripción en `stt_guardados/YYYY-MM-DD_HH-MM-SS.txt`.
   - Decide si guardar o descartar la transcripción al detener.

4. **Explorador de Transcripciones** (botón ⚙️):
   - Lista y selecciona archivos `.txt` guardados.
   - Edita el texto en un editor con diseño moderno.
   - Exporta en **PDF**, **Word** o **Markdown**.
   - Realiza consultas IA con el texto como contexto (respuestas en la interfaz).
   - **Nota**: Cambiar de archivo limpia automáticamente el campo de consulta IA.

---

## ⚠️ Consideraciones y Personalizaciones

- **Mejora el reconocimiento**: Agrega modismos chilenos en `vocabulariocl.py` para optimizar el español local.
- **Audio del sistema**: Para capturar todo el audio (no solo el micrófono), usa herramientas como **VB-Audio Cable** (Windows) o **Loopback Audio** (macOS).
- **Personalización visual**: Ajusta colores, bordes y estilos en los archivos `grabadora.py` y `menu.py` (estilos CSS).
- **Modelo IA**: Cambia la ruta o modelo en `menu.py` si usas otra configuración de Ollama.

---

## 📄 Exportación de Transcripciones

- **PDF**: Generado con **ReportLab**, incluye saltos de página automáticos.
- **Word (.docx)**: Documento con encabezado y párrafos formateados.
- **Markdown (.md)**: Texto limpio con título y contenido.

---

## 🚀 ¡Empieza Ahora!

Explora la transcripción en tiempo real y el análisis inteligente con este proyecto. Si tienes dudas o sugerencias, ¡abre un issue o contribuye al repositorio!

---

**Desarrollado con 💻 por [Tu Nombre o Equipo]**  
📧 Contacto: [tu-email@example.com]  
🌐 Licencia: [Especifica la licencia, ej. MIT]
```

### Cambios realizados para mejorar el README en GitHub:
1. **Encabezados claros y jerárquicos**: Uso de `#`, `##` y `###` para estructurar el contenido.
2. **Emojis temáticos**: Añadí emojis para mejorar la legibilidad y destacar secciones (🧠, ✨, 📥, etc.).
3. **Secciones más concisas**: Reorganicé el contenido para que sea más fácil de escanear.
4. **Código resaltado**: Usé bloques de código (```) para comandos y estructura de directorios.
5. **Enlaces y formato Markdown**: Añadí enlaces directos (ej. Vosk, Ollama) y formato limpio para listas y pasos.
6. **Notas visuales**: Uso de **negritas** y *cursivas* para resaltar términos clave.
7. **Footer opcional**: Agregué un espacio para nombre, contacto y licencia, que puedes personalizar.

Este README se verá profesional y atractivo en GitHub, con una estructura clara que facilita la comprensión del proyecto. Si necesitas ajustes adicionales (como colores específicos o más detalles), ¡avísame!


✅ PASO 1: Instala Argos Translate
Asegúrate de instalar el paquete:

bash
Copiar
Editar
pip install argostranslate
Y luego instala los idiomas deseados desde consola:

bash
Copiar
Editar
argos-translate-cli --install eng spa
argos-translate-cli --install zho spa
argos-translate-cli --install deu spa
argos-translate-cli --install por spa
Puedes revisar idiomas disponibles con:

bash
Copiar
Editar
argos-translate-cli --list-languages