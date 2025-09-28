# grabadora.py

from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QApplication, QProgressDialog, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation
from PyQt5.QtGui import QCursor
import sounddevice as sd
import numpy as np
from transcripcion.transcriber import TranscriberThread
import wave
from transcripcion.vosk_utils import SAMPLE_RATE
import os
import argostranslate.translate
from datetime import datetime
from interfaz.menu import NuevaVentana
import pyttsx3
import sys
import queue
import json
import time
from flask import Flask, Response, render_template, request, jsonify, send_from_directory
import threading
import requests  # <-- Dependencia ya existente
from docx import Document
from io import StringIO, BytesIO
import socket
from pyngrok import ngrok, conf
import io

# =====================================================================
# Sección de Flask y Variables Globales (Con Optimizaciones)
# =====================================================================
app = Flask(__name__, template_folder="templates")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

transcription_chunks = []
transcripcion_con_timestamps = ""
transcripcion_plana = ""
current_partial = ""
client_ai_responses = {}
clientes_idioma = {}
clientes_idioma_acumulado = {}
translation_cache = {}
chat_messages = []
qtextedit_buffer = ""
last_qtextedit_update = 0
qtextedit_update_interval = 0.5
shared_audio_data = {}
active_clients = {}
shared_in_memory_audio_buffer = []

model = None
q = queue.Queue(maxsize=20)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3.5:latest"

# =====================================================================
# >>>>> OPTIMIZACIÓN 1: Sesión HTTP Persistente <<<<<
# Se crea una única sesión para reutilizar la conexión con Ollama,
# eliminando la latencia de crear una nueva conexión en cada llamada.
# =====================================================================
http_session = requests.Session()


def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200 and any(model["name"] == MODEL_NAME for model in response.json().get("models", [])):
            return True
        return False
    except:
        return False
ollama_available = check_ollama()

def setup_argos():
    try:
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        for lang in ["en", "fr", "de"]:
            package = next((p for p in available_packages if p.from_code == "es" and p.to_code == lang), None)
            if package: argostranslate.package.install_from_path(package.download())
    except Exception as e:
        print(f"Error al instalar paquetes de traducción: {e}")
setup_argos()
installed_languages = argostranslate.translate.get_installed_languages()
source_lang = next((l for l in installed_languages if l.code == "es"), None)

@app.route("/")
def index(): return render_template("index.html")

@app.route('/chat/send', methods=['POST'])
def send_chat_message():
    data = request.json
    if not data or 'user' not in data: return jsonify({"status": "error", "message": "Falta el usuario"}), 400
    is_note = data.get('isNote', False)
    if is_note:
        if 'content' not in data or not data['content'].strip(): return jsonify({"status": "error", "message": "Los apuntes están vacíos"}), 400
        message_data = {"user": data['user'], "isNote": True, "content": data['content'], "timestamp": time.time()}
    else:
        if 'message' not in data or not data['message'].strip(): return jsonify({"status": "error", "message": "El mensaje está vacío"}), 400
        message_data = {"user": data['user'], "isNote": False, "message": data['message'], "timestamp": time.time()}
    chat_messages.append(message_data)
    if len(chat_messages) > 100: chat_messages.pop(0)
    return jsonify({"status": "ok"})

@app.route("/stream")
def stream():
    client_id = request.args.get("client_id", "default")
    
    def event_stream():
        global active_clients
        try:
            active_clients[client_id] = time.time()
            print(f"Cliente conectado: {client_id}. Total de usuarios: {len(active_clients)}")

            last_chat_message_count = len(chat_messages)
            last_sent_data = {}
            last_sent_user_count = 0

            while True:
                current_user_count = len(active_clients)
                if current_user_count != last_sent_user_count:
                    system_payload = {"type": "system_info", "data": {"user_count": current_user_count}}
                    yield f"data: {json.dumps(system_payload)}\n\n"
                    last_sent_user_count = current_user_count
                
                idioma_sub = clientes_idioma.get(client_id, "es")
                idioma_acum = clientes_idioma_acumulado.get(client_id, "es")
                
                subtitulo_text = current_partial
                acumulado_text_flat = transcripcion_plana
                acumulado_chunks_final = transcription_chunks
                ai_response_text = client_ai_responses.get(client_id, "")

                if source_lang:
                    if idioma_sub != "es" and subtitulo_text.strip():
                        try:
                            target_lang = next((l for l in installed_languages if l.code == idioma_sub), None)
                            if target_lang: subtitulo_text = source_lang.get_translation(target_lang).translate(subtitulo_text)
                        except Exception as e: print(f"Error traduciendo subtítulo: {e}")
                    
                    if idioma_acum != "es":
                        try:
                            target_lang_acum = next((l for l in installed_languages if l.code == idioma_acum), None)
                            if target_lang_acum:
                                if acumulado_text_flat.strip():
                                    acumulado_text_flat = source_lang.get_translation(target_lang_acum).translate(acumulado_text_flat)
                                
                                translated_chunks = []
                                for chunk in transcription_chunks:
                                    translated_text = source_lang.get_translation(target_lang_acum).translate(chunk["text"])
                                    new_chunk = chunk.copy()
                                    new_chunk["text"] = translated_text
                                    translated_chunks.append(new_chunk)
                                acumulado_chunks_final = translated_chunks
                        except Exception as e: print(f"Error traduciendo acumulado: {e}")

                current_data = {
                    "subtitulo": subtitulo_text,
                    "acumulado_chunks": acumulado_chunks_final,
                    "acumulado_flat": acumulado_text_flat,
                    "ai_response": ai_response_text
                }
                
                if current_data != last_sent_data.get("transcript"):
                    last_sent_data["transcript"] = current_data
                    transcript_payload = {"type": "transcript", "data": current_data}
                    yield f"data: {json.dumps(transcript_payload)}\n\n"
                
                if len(chat_messages) > last_chat_message_count:
                    new_messages = chat_messages[last_chat_message_count:]
                    for msg in new_messages: yield f"data: {json.dumps({'type': 'chat', 'data': msg})}\n\n"
                    last_chat_message_count = len(chat_messages)
                
                time.sleep(0.1)
        finally:
            active_clients.pop(client_id, None)
            print(f"Cliente desconectado: {client_id}. Total de usuarios: {len(active_clients)}")

    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/get_audio_chunk')
def get_audio_chunk():
    global shared_in_memory_audio_buffer
    start_sec_str = request.args.get('start')
    end_sec_str = request.args.get('end')

    if not all([start_sec_str, end_sec_str]): return "Faltan parámetros de tiempo.", 400
    if not shared_in_memory_audio_buffer: return "No hay datos de audio en memoria.", 404

    try:
        start_sec, end_sec = float(start_sec_str), float(end_sec_str)
        sample_width, channels, frame_rate = 2, 1, SAMPLE_RATE
        bytes_per_second = frame_rate * sample_width * channels
        start_byte, end_byte = int(start_sec * bytes_per_second), int(end_sec * bytes_per_second)
        
        full_audio_data = b''.join(shared_in_memory_audio_buffer)
        audio_chunk_data = full_audio_data[start_byte:end_byte]

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(frame_rate)
            wf.writeframes(audio_chunk_data)
        buffer.seek(0)
        
        return Response(buffer, mimetype="audio/wav", headers={"Content-Disposition": "inline"})
    except Exception as e:
        print(f"Error al procesar chunk de audio desde memoria (método manual): {e}")
        return "Error interno del servidor al procesar el audio.", 500

@app.route("/set_language/<client_id>/<lang>", methods=['POST'])
def set_language(client_id, lang): clientes_idioma[client_id] = lang; return "OK"

@app.route("/set_language_acumulado/<client_id>/<lang>", methods=['POST'])
def set_language_acumulado(client_id, lang): clientes_idioma_acumulado[client_id] = lang; return "OK"

@app.route("/clear_text/<client_id>", methods=['POST'])
def clear_text(client_id):
    global transcripcion_con_timestamps, transcripcion_plana, current_partial, qtextedit_buffer, shared_audio_data, transcription_chunks, shared_in_memory_audio_buffer
    transcripcion_con_timestamps = ""; transcripcion_plana = ""; current_partial = ""; qtextedit_buffer = ""
    transcription_chunks = []; shared_in_memory_audio_buffer = []
    client_ai_responses.pop(client_id, None); shared_audio_data.clear()
    return "OK"

@app.route("/ask_ai/<client_id>", methods=['POST'])
def ask_ai(client_id):
    data = request.get_json()
    if not data: return "Bad Request: No JSON data received", 400
    question = data.get("question", "")
    ai_thread = threading.Thread(target=process_ai_question, args=(question, client_id)); ai_thread.start()
    return "OK"

@app.route("/download_txt/<client_id>/<filename>", methods=['POST'])
def download_txt(client_id, filename):
    acumulado_text = transcripcion_con_timestamps
    buffer = StringIO(); buffer.write(f"Transcripción de STTTVAR\nFecha: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n\n{acumulado_text}")
    txt_content = buffer.getvalue(); buffer.close()
    return Response(txt_content, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename={filename}.txt'})

@app.route("/download_docx/<client_id>/<filename>", methods=['POST'])
def download_docx(client_id, filename):
    acumulado_text = transcripcion_con_timestamps
    doc = Document(); doc.add_heading("Transcripción de STTTVAR", 0); doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %I:%M %p')}"); doc.add_heading("Transcripción:", level=1); doc.add_paragraph(acumulado_text)
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={'Content-Disposition': f'attachment; filename={filename}.docx'})

@app.route('/audio_status')
def audio_status():
    return jsonify({'available': bool(shared_audio_data and shared_audio_data.get('available')), 'filename': shared_audio_data.get('filename')})

@app.route('/download_audio')
def download_audio():
    if shared_audio_data and shared_audio_data.get('available'):
        try: return send_from_directory(shared_audio_data['directory'], shared_audio_data['filename'], as_attachment=True)
        except Exception as e: print(f"Error al servir el archivo de audio: {e}"); return "Error al leer el archivo.", 500
    return "No hay archivo de audio disponible para descargar.", 404


# =====================================================================
# >>>>> FUNCIÓN DE IA TOTALMENTE OPTIMIZADA <<<<<
# Esta es la nueva función que implementa todas las mejoras.
# =====================================================================
def process_ai_question(question, client_id):
    if not ollama_available:
        client_ai_responses[client_id] = "Error: El servicio de IA (Ollama) no está disponible."
        return
    if not question.strip():
        client_ai_responses[client_id] = "Error: La pregunta no puede estar vacía."
        return

    try:
        # >>>>> OPTIMIZACIÓN 2: Limitar el contexto enviado <<<<<
        # Se envían solo las últimas 1000 palabras para una respuesta más rápida.
        context = transcripcion_plana.strip() or "No hay contexto disponible."
        if len(context.split()) > 1000:
            context = " ".join(context.split()[-1000:])

        prompt = (f"Usando el siguiente texto como referencia:\n\n{context}\n\nPregunta: {question}\nRespuesta concisa en español:")
        
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            # >>>>> OPTIMIZACIÓN 3: Habilitar streaming <<<<<
            "stream": True,
            "options": {
                "temperature": 0.6,
                # >>>>> OPTIMIZACIÓN 4: Limitar longitud de respuesta <<<<<
                # 'num_predict' es el equivalente de 'max_tokens'. 256 es un buen balance.
                "num_predict": 256
            }
        }
        
        # Se inicializa la respuesta para que el frontend la reciba vacía al principio.
        client_ai_responses[client_id] = ""

        # Se usa la sesión HTTP persistente (http_session) para la petición.
        with http_session.post(OLLAMA_API_URL, json=payload, stream=True, timeout=60) as response:
            if response.status_code == 200:
                # Se procesa la respuesta línea por línea a medida que llega.
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("response", "")
                            if content:
                                # Se añade cada fragmento a la respuesta global.
                                client_ai_responses[client_id] += content
                            
                            # Si Ollama indica que ha terminado, se sale del bucle.
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            print(f"Error decodificando la respuesta JSON de Ollama: {line}")
            else:
                client_ai_responses[client_id] = f"Error en la API de Ollama: Código {response.status_code}."

    except requests.exceptions.RequestException as e:
        client_ai_responses[client_id] = f"Error de conexión con Ollama: {e}"
    except Exception as e:
        client_ai_responses[client_id] = f"Error inesperado al procesar la pregunta: {e}"

# =====================================================================
# El resto de la clase TranscriptionWindow y la UI no necesita cambios
# =====================================================================

class TranscriptionWindow(QWidget):
    transcription_status_changed = pyqtSignal(bool)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setWindowTitle("🎙 Transcriptor en Tiempo Real")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMinimumSize(650, 110)
        self.resize(650, 110)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.start_time = 0
        self.transcriber_thread = None
        self.transcription_active = False
        self.current_transcription_filepath = None
        self.current_audio_filepath = None
        self.selected_language = "es"
        self._already_stopped = False
        self.ngrok_tunnel = None
        self.public_url = None
        self.config_file = 'config.json'
        
        self.flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False, 'use_reloader': False})
        self.flask_thread.daemon = True
        self.flask_thread.start()

        self._setup_ui()
        self._populate_devices()
        self._connect_signals()
        self._initialize_ui_state()
        self.old_pos = None
        self._hide_button_timer = QTimer(self)
        self._hide_button_timer.setSingleShot(True)
        self._hide_button_timer.timeout.connect(self._fade_out_buttons)
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.setInterval(200)
        self.mouse_check_timer.timeout.connect(self._check_mouse_hover)

    def _check_mouse_hover(self):
        if not self.transcription_active or self.language_combo.view().isVisible(): return
        under_mouse = self.base_widget.underMouse()
        if under_mouse:
            self._hide_button_timer.stop()
            self._fade_in_buttons()
        else:
            if not self._hide_button_timer.isActive():
                self._hide_button_timer.start(300)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos: delta = event.globalPos() - self.old_pos; self.move(self.pos() + delta); self.old_pos = event.globalPos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = None
    
    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception: IP = '127.0.0.1'
        finally: s.close()
        return IP
    def _setup_ngrok_authtoken(self):
        token = None
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                try: token = json.load(f).get('ngrok_authtoken')
                except json.JSONDecodeError: pass
        
        if not token:
            token, ok = QInputDialog.getText(self, 'Configuración de Ngrok', 'Por favor, introduce tu Authtoken de Ngrok.')
            if ok and token:
                with open(self.config_file, 'w') as f: json.dump({'ngrok_authtoken': token}, f)
            else: return False
        
        try: ngrok.set_auth_token(token); return True
        except Exception as e: QMessageBox.critical(self, "Error de Ngrok", f"No se pudo configurar el token: {e}"); return False
    def _on_qr_button_clicked(self):
        if self.ngrok_tunnel: self._show_qr_window(); return
        if not self._setup_ngrok_authtoken(): QMessageBox.warning(self, "Cancelado", "Se necesita el Authtoken."); return
        progress = QProgressDialog("Creando enlace...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal); progress.setCancelButton(None); progress.show(); QApplication.processEvents()
        try:
            ngrok.kill()
            self.ngrok_tunnel = ngrok.connect(5000)
            self.public_url = self.ngrok_tunnel.public_url
            progress.close(); self._show_qr_window()
        except Exception as e: progress.close(); QMessageBox.critical(self, "Error de Ngrok", f"No se pudo crear el túnel: {e}")
    def _show_qr_window(self):
        local_ip = self._get_local_ip()
        try:
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qr_app_path = os.path.join(current_dir, "qr_app.py")
            if not os.path.exists(qr_app_path): qr_app_path = os.path.join(os.path.dirname(current_dir), "interfaz", "qr_app.py")
            subprocess.Popen([sys.executable, qr_app_path, f"http://{local_ip}:5000", self.public_url])
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de QR: {e}")
    def _setup_ui(self):
        self.base_widget = QWidget(self); self.base_widget.setObjectName("baseWidget"); self.base_widget.setMouseTracking(True); self.setMouseTracking(True)
        self.base_widget.setStyleSheet("#baseWidget { background-color: rgba(30, 30, 30, 200); border: 1px solid rgba(70, 70, 70, 150); border-radius: 10px; }")
        self.title_bar_layout = QHBoxLayout(); self.title_bar_layout.setContentsMargins(10, 5, 5, 0)
        self.window_title_label = QLabel("🎙 STTVAR"); self.window_title_label.setStyleSheet("color: #bbbbbb; font-size: 13px; font-weight: bold;")
        self.close_button = QPushButton("✕"); self.close_button.setFixedSize(24, 24); self.close_button.setToolTip("Cerrar"); self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #bbbbbb; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; color: white; }")
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.window_title_label); self.title_bar_layout.addStretch(); self.title_bar_layout.addWidget(self.close_button)
        self.device_label = QLabel("🎧 Dispositivo:"); self.device_label.setStyleSheet("color: #bbbbbb; font-size: 13px;")
        self.device_combo = QComboBox(); self.device_combo.setToolTip("Selecciona tu micrófono.")
        self.device_combo.setStyleSheet("QComboBox { border: 1px solid #505050; border-radius: 5px; padding: 3px; background-color: #3a3a3a; color: #e0e0e0; } QComboBox QAbstractItemView { background-color: #3a3a3a; selection-background-color: #557799; }")
        self.language_combo = QComboBox(); self.language_combo.addItem("Español", "es"); self.language_combo.addItem("Inglés", "en"); self.language_combo.addItem("Francés", "fr"); self.language_combo.addItem("Alemán", "de")
        self.language_combo.setToolTip("Idioma de transcripción."); self.language_combo.setFixedSize(100, 36); self.language_combo.setCursor(Qt.PointingHandCursor)
        self.language_combo.setStyleSheet("QComboBox { background-color: #444; border: 2px solid #666; border-radius: 18px; color: #ddd; font-size: 14px; padding: 8px; font-weight: bold; } QComboBox:hover { border-color: #e74c3c; }")
        self.toggle_recording_button = QPushButton("🔴 Iniciar"); self.toggle_recording_button.setCursor(Qt.PointingHandCursor)
        self.toggle_recording_button.setStyleSheet("QPushButton { background-color: #c0392b; color: white; border-radius: 12px; padding: 8px 18px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #e74c3c; }")
        self.mute_button = QPushButton("🎙️"); self.mute_button.setCheckable(True); self.mute_button.setToolTip("Micrófono activo."); self.mute_button.setCursor(Qt.PointingHandCursor); self.mute_button.setFixedSize(36, 36)
        self.mute_button.setStyleSheet("QPushButton { background-color: #444; border: 2px solid #666; border-radius: 18px; color: #ddd; font-size: 18px; } QPushButton:checked { background-color: #c0392b; border-color: #e74c3c; }")
        self.qr_button = QPushButton("🌐"); self.qr_button.setToolTip("Compartir"); self.qr_button.setCursor(Qt.PointingHandCursor); self.qr_button.setFixedSize(36, 36)
        self.qr_button.setStyleSheet("QPushButton { background-color: #444; border: 2px solid #666; border-radius: 18px; color: #ddd; font-size: 18px; } QPushButton:hover { border-color: #e74c3c; }")
        self.buttons_layout = QHBoxLayout(); self.buttons_layout.setSpacing(10); self.buttons_layout.addWidget(self.toggle_recording_button); self.buttons_layout.addWidget(self.mute_button); self.buttons_layout.addWidget(self.qr_button); self.buttons_layout.addWidget(self.language_combo)
        self.settings_button = QPushButton("⚙️"); self.settings_button.setFixedSize(32, 32); self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet("QPushButton { background-color: #4a4a4a; border: 1px solid #5a5a5a; color: #dddddd; border-radius: 8px; } QPushButton:hover { background-color: #5a5a5a; }")
        self.text_area = QTextEdit(); self.text_area.setReadOnly(True); self.text_area.setPlaceholderText("Transcribiendo...")
        self.text_area.setStyleSheet("QTextEdit { background-color: rgba(0,0,0,0); font-family: 'Segoe UI'; font-size: 18px; padding: 5px 10px; border: none; color: #f0f0f0; }")
        self.control_layout = QHBoxLayout(); self.control_layout.setContentsMargins(10, 5, 10, 5); self.control_layout.setSpacing(8)
        self.control_layout.addWidget(self.device_label); self.control_layout.addWidget(self.device_combo, 1); self.control_layout.addLayout(self.buttons_layout); self.control_layout.addWidget(self.settings_button)
        self.main_layout = QVBoxLayout(self.base_widget); self.main_layout.setContentsMargins(5, 5, 5, 5); self.main_layout.setSpacing(5); self.main_layout.addLayout(self.title_bar_layout)
        self.main_layout.addLayout(self.control_layout); self.main_layout.addWidget(self.text_area); self.main_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(QVBoxLayout()); self.layout().setContentsMargins(0, 0, 0, 0); self.layout().addWidget(self.base_widget)
    def _connect_signals(self):
        self.toggle_recording_button.clicked.connect(self._toggle_recording)
        self.transcription_status_changed.connect(self._update_ui_for_transcription_status)
        self.settings_button.clicked.connect(self._open_settings_window)
        self.mute_button.clicked.connect(self._toggle_mute)
        self.qr_button.clicked.connect(self._on_qr_button_clicked)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
    def _initialize_ui_state(self):
        self.device_label.setVisible(True); self.device_combo.setVisible(True); self.text_area.setVisible(False); self.toggle_recording_button.setVisible(True)
        self.toggle_recording_button.setWindowOpacity(1); self.mute_button.setVisible(False); self.mute_button.setWindowOpacity(0); self.language_combo.setVisible(False)
        self.language_combo.setWindowOpacity(0); self.qr_button.setVisible(False); self.qr_button.setWindowOpacity(0)
    def _populate_devices(self):
        try:
            devices = sd.query_devices(); input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            if not input_devices: self.device_combo.addItem("No hay dispositivos."); self.toggle_recording_button.setEnabled(False); return
            for idx, name in input_devices: self.device_combo.addItem(name, idx)
        except Exception as e: QMessageBox.critical(self, "Error de dispositivos", str(e))
    def _format_timestamp(self, seconds: float) -> str:
        m, s = divmod(int(seconds), 60); h, m = divmod(m, 60)
        return f"[{h:02d}:{m:02d}:{s:02d}]"
    def _toggle_recording(self):
        if self.transcription_active:
            self._stop_transcription()
        else:
            self._start_transcription()
    def _start_transcription(self):
        global transcripcion_con_timestamps, transcripcion_plana, current_partial, qtextedit_buffer, shared_audio_data, transcription_chunks, shared_in_memory_audio_buffer
        transcripcion_con_timestamps = ""; transcripcion_plana = ""; current_partial = ""; qtextedit_buffer = ""
        transcription_chunks = []; shared_in_memory_audio_buffer.clear()
        device_index = self.device_combo.currentData()
        if device_index is None: QMessageBox.warning(self, "Falta dispositivo", "Selecciona un micrófono."); return
        self.start_time = time.time()
        engine = pyttsx3.init(); engine.say("Iniciando grabación"); engine.runAndWait()
        progress = QProgressDialog("Iniciando...", None, 0, 0, self); progress.setWindowModality(Qt.WindowModal); progress.setCancelButton(None); progress.show()
        output_dir, audio_output_dir = "stt_guardados", "sttaudio_guardados"
        os.makedirs(output_dir, exist_ok=True); os.makedirs(audio_output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_transcription_filepath = f"{output_dir}/{timestamp}.txt"
        self.current_audio_filepath = f"{audio_output_dir}/{timestamp}.wav"
        try:
            shared_audio_data.clear()
            self.transcriber_thread = TranscriberThread(self.model, device_index, self.current_transcription_filepath, self.current_audio_filepath, shared_in_memory_audio_buffer)
            self.transcriber_thread.new_text.connect(self._update_text_area)
            self.transcriber_thread.finished.connect(self._on_transcription_finished)
            self.transcriber_thread.start()
            self.mouse_check_timer.start()
            self.transcriber_thread.set_mute(self.mute_button.isChecked())
            self.transcription_active = True; self.transcription_status_changed.emit(True); self.text_area.clear(); self._already_stopped = False
        except Exception as e: progress.close(); QMessageBox.critical(self, "Error", str(e)); return
        progress.close()
    def _stop_transcription(self):
        if self._already_stopped: return
        self._already_stopped = True
        if self.transcriber_thread: self.transcriber_thread.stop(); self.transcriber_thread.wait(); self.transcriber_thread = None
        self.mouse_check_timer.stop()
        self.transcription_active = False; self.transcription_status_changed.emit(False)
        self._prompt_save_or_discard()
    def _on_transcription_finished(self): self._stop_transcription()
    def _toggle_mute(self):
        muted = self.mute_button.isChecked(); self.mute_button.setText("🔇" if muted else "🎙️")
        if self.transcriber_thread: self.transcriber_thread.set_mute(muted)
    def _fade_in_buttons(self):
        for w in [self.toggle_recording_button, self.mute_button, self.language_combo, self.qr_button]:
            if not w.isVisible() or w.windowOpacity() < 1.0:
                w.setVisible(True); anim = QPropertyAnimation(w, b"windowOpacity"); anim.setDuration(200); anim.setStartValue(w.windowOpacity()); anim.setEndValue(1); anim.start()
    def _fade_out_buttons(self):
        for w in [self.toggle_recording_button, self.mute_button, self.language_combo, self.qr_button]:
            if w.isVisible():
                anim = QPropertyAnimation(w, b"windowOpacity"); anim.setDuration(200); anim.setStartValue(w.windowOpacity()); anim.setEndValue(0); anim.finished.connect(lambda wid=w: wid.setVisible(False)); anim.start()
    def _update_ui_for_transcription_status(self, active: bool):
        for w in [self.device_label, self.device_combo, self.settings_button, self.close_button, self.window_title_label]: w.setVisible(not active)
        self.text_area.setVisible(active)
        if active:
            self.toggle_recording_button.setText("■ Detener"); self.mute_button.setText("🎙️" if not self.mute_button.isChecked() else "🔇")
            for w in [self.toggle_recording_button, self.mute_button, self.language_combo, self.qr_button]: w.setVisible(False); w.setWindowOpacity(0)
        else:
            self.toggle_recording_button.setText("🔴 Iniciar"); self.toggle_recording_button.setVisible(True); self.toggle_recording_button.setWindowOpacity(1)
            for w in [self.mute_button, self.language_combo, self.qr_button]: w.setVisible(False); w.setWindowOpacity(0)
    
    def _update_text_area(self, data: dict):
        global transcripcion_con_timestamps, transcripcion_plana, current_partial, qtextedit_buffer, last_qtextedit_update, transcription_chunks
        text_es = data.get("text", "")
        is_partial = data.get("is_partial", True)
        if text_es.strip() or not is_partial:
            current_time = time.time()
            if is_partial:
                qtextedit_buffer = text_es
                current_partial = text_es
            else:
                start_sec, end_sec = data.get("start_sec"), data.get("end_sec")
                if start_sec is None: start_sec = time.time() - self.start_time
                timestamp_str = self._format_timestamp(start_sec)
                texto_limpio = text_es.strip()
                if texto_limpio:
                    chunk_data = {
                        "timestamp": timestamp_str, "text": texto_limpio,
                        "start_sec": start_sec, "end_sec": end_sec if end_sec is not None else start_sec + 2
                    }
                    transcription_chunks.append(chunk_data)
                    transcripcion_con_timestamps += f"{timestamp_str} {texto_limpio}\n"
                    transcripcion_plana += f"{texto_limpio} "
                current_partial = ""
                qtextedit_buffer = texto_limpio
            
            if is_partial and current_time - last_qtextedit_update < qtextedit_update_interval:
                return

            text_to_display = qtextedit_buffer
            
            if self.selected_language != "es" and text_to_display.strip() and source_lang:
                try:
                    target_lang = next((l for l in installed_languages if l.code == self.selected_language), None)
                    if target_lang:
                        text_to_display = source_lang.get_translation(target_lang).translate(text_to_display)
                except Exception as e:
                    print(f"Error al traducir en la ventana local: {e}")
                    text_to_display = "[Error de traducción] " + text_to_display

            self.text_area.setPlainText(text_to_display)
            self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())
            last_qtextedit_update = current_time
            
    def _on_language_changed(self, index):
        self.selected_language = self.language_combo.itemData(index)
        if self.transcription_active and qtextedit_buffer.strip():
            self._update_text_area({"text": qtextedit_buffer, "is_partial": True})

    def _prompt_save_or_discard(self):
        global shared_audio_data
        has_transcription, has_audio = (self.current_transcription_filepath and os.path.exists(self.current_transcription_filepath)), (self.current_audio_filepath and os.path.exists(self.current_audio_filepath))
        if not has_transcription and not has_audio: shared_audio_data.clear(); return
        save_transcription, save_audio, share_audio = False, False, False
        if has_transcription: save_transcription = (QMessageBox.question(self, "Guardar", "¿Guardar transcripción?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes)
        if has_audio:
            save_audio = (QMessageBox.question(self, "Guardar", "Guardar la grabación es bajo tu propia responsabilidad.\n¿Guardar el audio?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)
            if save_audio and (QMessageBox.question(self, "Compartir", "¿Compartir este audio en la web?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes):
                share_audio = True
                shared_audio_data.update({'directory': os.path.abspath(os.path.dirname(self.current_audio_filepath)), 'filename': os.path.basename(self.current_audio_filepath), 'available': True})
        if not share_audio: shared_audio_data.clear()
        try:
            if not save_transcription and has_transcription: os.remove(self.current_transcription_filepath)
            if not save_audio and has_audio: os.remove(self.current_audio_filepath)
        except Exception as e: QMessageBox.warning(self, "Error al eliminar", str(e))
        messages = [msg for msg, flag in [("Transcripción guardada.", save_transcription), ("Audio guardado.", save_audio), ("Audio disponible en la web.", share_audio)] if flag]
        if messages: QMessageBox.information(self, "Completado", "\n".join(messages))
        self.current_transcription_filepath, self.current_audio_filepath = None, None
    def closeEvent(self, event):
        if self.ngrok_tunnel: ngrok.disconnect(self.public_url); ngrok.kill(); self.ngrok_tunnel = None
        if self.transcriber_thread and self.transcriber_thread.isRunning():
            if QMessageBox.question(self, "Salir", "¿Detener transcripción y salir?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                self._stop_transcription(); event.accept()
            else: event.ignore()
        else: event.accept()
    def _open_settings_window(self):
        self.settings_window = NuevaVentana(self); self.settings_window.show(); self.hide()