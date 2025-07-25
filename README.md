🧠 Proyecto Transcripción en Tiempo Real con IA (Vosk + Python + Ollama) 🧠
Este proyecto integra tres poderosas tecnologías para ofrecer una experiencia completa de transcripción y análisis de voz en español:

🎤 Transcripción de voz en tiempo real usando Vosk + Python + PyQt5
🖥️ Interfaz gráfica intuitiva para explorar, editar y exportar transcripciones
🤖 Consultas inteligentes a un modelo local de IA (Ollama mistral:7b-instruct-q4_K_M) para analizar el texto transcrito

📥 Descarga del Modelo Vosk en Español
Para que la transcripción funcione correctamente, descarga el modelo de reconocimiento de voz en español desde:
Modelo recomendado: vosk-model-small-es-0.42
Una vez descargado, descomprime la carpeta dentro del directorio raíz del proyecto y renómbrala como:
vosk-model-es-0.42


📁 Estructura del Proyecto
yaml
Copiar
Editar
STTVAR/
├── interfaz/
│   ├── grabadora.py         # UI de grabación, control de mute y STT en vivo
│   └── menu.py              # Ventana de menú para abrir explorador y consultas IA
├── stt_guardados/           # Carpeta con transcripciones guardadas automáticamente
│   ├── 2025-07-24_19-52-37.txt
│   └── 2025-07-24_19-58-06.txt
├── transcripcion/
│   ├── transcriber.py       # Thread que ejecuta Vosk para STT en tiempo real
│   └── vosk_utils.py        # Funciones auxiliares para cargar y configurar Vosk
├── vosk-model-es-0.42/      # Modelo Vosk descargado y renombrado
├── main.py                  # Punto de entrada: inicia ventana principal de transcripción
├── README.md                # Documentación del proyecto (este archivo)
├── STTVAR.bat               # Script para ejecutar main.py sin mostrar consola
├── vocabulariocl.py         # (Opcional) Glosario/modismos chilenos para mejorar precisión
└── .gitignore               # Archivos y carpetas ignorados por Git


🛠️ Instalación y Preparación
1. Instala dependencias Python
    pip install -r requirements.txt
    Contenido mínimo de requirements.txt:

2. Configura Ollama y descarga modelo IA
Sigue las instrucciones oficiales en https://ollama.com/
Descarga el modelo ejecutando: ollama pull mistral:7b-instruct-q4_K_M
Asegúrate de que la ruta al ejecutable ollama.exe esté correcta en interfaz/menu.py

▶️ Cómo Ejecutar
Con micrófono conectado y configurado, ejecuta: python main.py

Se abrirá la ventana 🎙 Transcriptor en Tiempo Real
Selecciona tu dispositivo de entrada (micrófono) desde el combo box
Presiona 🔴 Iniciar Grabación para comenzar la transcripción
Durante la grabación puedes usar el botón 🔇/🎙️ para silenciar o reactivar el micrófono
Cuando termines, presiona ■ Detener Grabación para guardar la transcripción automáticamente en: stt_guardados/YYYY-MM-DD_HH-MM-SS.txt
Al detener, el sistema te permitirá guardar o descartar la transcripción

Desde la ventana de menú (⚙️), abre el Explorador de Transcripciones para:

Listar y seleccionar archivos .txt guardados
Editar el texto en un editor con bordes redondeados y estilos agradables
Guardar cambios y exportar en formatos PDF, Word o Markdown
Realizar consultas con IA enviando el texto visible como contexto a Ollama, con respuesta en la interfaz
Nota: Al cambiar de archivo, el campo de pregunta y respuesta IA se limpia automáticamente para evitar confusiones.

⚠️ Consideraciones y Personalizaciones
Puedes mejorar el reconocimiento del español chileno añadiendo modismos y glosario en vocabulariocl.py

Para escuchar todo el audio del sistema (no solo el micrófono), es necesario usar software externo como VB-Audio Cable (Windows) o Loopback Audio (macOS). Esto requiere configuración fuera de Python.

El estilo visual (colores, bordes, tamaños) de la UI puede personalizarse editando los estilos CSS en grabadora.py y menu.py

Cambia la ruta y nombre del modelo IA en menu.py si usas otra instalación de Ollama o diferente modelo

📄 Exportación de Transcripciones
    PDF: Usando ReportLab, con saltos de página automáticos

    Word (.docx): Documento con encabezado y párrafos formateados

    Markdown (.md): Texto plano con título y contenido limpio

