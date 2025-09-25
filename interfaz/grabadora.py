# grabadora.py

from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QApplication, QProgressDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation
import sounddevice as sd
from transcripcion.transcriber import TranscriberThread
import os
import argostranslate.translate
from datetime import datetime
from interfaz.menu import NuevaVentana
import pyttsx3
import sys
import queue
import json
import time
from flask import Flask, Response, render_template, request, jsonify
import threading
import requests
from docx import Document
from io import StringIO, BytesIO

# ---- Configuración de Flask y STTTVAR ----
app = Flask(__name__, template_folder="templates")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Variables globales para compartir datos con Flask
transcripcion = ""
current_partial = ""
client_ai_responses = {}
clientes_idioma = {}
clientes_idioma_acumulado = {}
translation_cache = {}
chat_messages = []
qtextedit_buffer = ""
last_qtextedit_update = 0
qtextedit_update_interval = 0.5

model = None
q = queue.Queue(maxsize=20)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:7b-instruct-q4_K_M"

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
            if package:
                argostranslate.package.install_from_path(package.download())
    except Exception as e:
        print(f"Error al instalar paquetes de traducción: {e}")

setup_argos()
installed_languages = argostranslate.translate.get_installed_languages()
source_lang = next((l for l in installed_languages if l.code == "es"), None)

# ---- Rutas Flask (de STTTVAR) ----
@app.route("/")
def index():
    return render_template("index.html")

# ==================== RUTA DE CHAT MEJORADA PARA ACEPTAR APUNTES ====================
@app.route('/chat/send', methods=['POST'])
def send_chat_message():
    data = request.json
    if not data or 'user' not in data:
        return jsonify({"status": "error", "message": "Falta el usuario"}), 400

    # Determinar si es un mensaje de texto normal o unos apuntes
    is_note = data.get('isNote', False)
    
    if is_note:
        if 'content' not in data or not data['content'].strip():
            return jsonify({"status": "error", "message": "Los apuntes están vacíos"}), 400
        message_data = {
            "user": data['user'],
            "isNote": True,
            "content": data['content'],
            "timestamp": time.time()
        }
    else:
        if 'message' not in data or not data['message'].strip():
            return jsonify({"status": "error", "message": "El mensaje está vacío"}), 400
        message_data = {
            "user": data['user'],
            "isNote": False,
            "message": data['message'],
            "timestamp": time.time()
        }

    chat_messages.append(message_data)
    if len(chat_messages) > 100:
        chat_messages.pop(0)
        
    return jsonify({"status": "ok"})


@app.route("/stream")
def stream():
    def event_stream(client_id):
        last_chat_message_count = len(chat_messages)
        last_sent_data = {}

        while True:
            # --- 1. Preparar datos de transcripción traducidos para este cliente ---
            idioma_sub = clientes_idioma.get(client_id, "es")
            idioma_acum = clientes_idioma_acumulado.get(client_id, "es")
            subtitulo_text = current_partial
            acumulado_text = transcripcion
            ai_response_text = client_ai_responses.get(client_id, "")

            if idioma_sub != "es" and current_partial.strip() and source_lang:
                cache_key_sub = f"{current_partial}:{idioma_sub}"
                if cache_key_sub in translation_cache:
                    subtitulo_text = translation_cache[cache_key_sub]
                else:
                    try:
                        target_language = next((l for l in installed_languages if l.code == idioma_sub), None)
                        if target_language:
                            subtitulo_text = source_lang.get_translation(target_language).translate(current_partial)
                            translation_cache[cache_key_sub] = subtitulo_text
                    except Exception as e:
                        print(f"Error en traducción de subtítulo a {idioma_sub}: {e}")

            if idioma_acum != "es" and transcripcion.strip() and source_lang:
                cache_key_acum = f"{transcripcion}:{idioma_acum}"
                if cache_key_acum in translation_cache:
                    acumulado_text = translation_cache[cache_key_acum]
                else:
                    try:
                        target_language = next((l for l in installed_languages if l.code == idioma_acum), None)
                        if target_language:
                            acumulado_text = source_lang.get_translation(target_language).translate(transcripcion)
                            translation_cache[cache_key_acum] = acumulado_text
                    except Exception as e:
                        print(f"Error en traducción de acumulado a {idioma_acum}: {e}")
            
            # --- 2. Comprobar si hay cambios en los datos de transcripción ---
            current_data = {
                "subtitulo": subtitulo_text,
                "acumulado": acumulado_text,
                "ai_response": ai_response_text
            }
            if current_data != last_sent_data.get("transcript"):
                last_sent_data["transcript"] = current_data
                transcript_payload = {"type": "transcript", "data": current_data}
                yield f"data: {json.dumps(transcript_payload)}\n\n"

            # --- 3. Comprobar si hay nuevos mensajes de chat (incluyendo apuntes) ---
            if len(chat_messages) > last_chat_message_count:
                new_messages = chat_messages[last_chat_message_count:]
                for msg in new_messages:
                    chat_payload = {"type": "chat", "data": msg}
                    yield f"data: {json.dumps(chat_payload)}\n\n"
                last_chat_message_count = len(chat_messages)

            time.sleep(0.1)

    client_id = request.args.get("client_id", "default")
    return Response(event_stream(client_id), mimetype="text/event-stream")

# (El resto del código de grabadora.py no cambia y se mantiene igual)

@app.route("/set_language/<client_id>/<lang>", methods=['POST'])
def set_language(client_id, lang):
    clientes_idioma[client_id] = lang
    return "OK"

@app.route("/set_language_acumulado/<client_id>/<lang>", methods=['POST'])
def set_language_acumulado(client_id, lang):
    clientes_idioma_acumulado[client_id] = lang
    return "OK"

@app.route("/clear_text/<client_id>", methods=['POST'])
def clear_text(client_id):
    global transcripcion, current_partial, qtextedit_buffer
    transcripcion = ""; current_partial = ""; qtextedit_buffer = ""
    client_ai_responses.pop(client_id, None)
    return "OK"

@app.route("/ask_ai/<client_id>", methods=['POST'])
def ask_ai(client_id):
    data = request.get_json()
    if not data:
        return "Bad Request: No JSON data received", 400
    question = data.get("question", "")
    ai_thread = threading.Thread(target=process_ai_question, args=(question, client_id))
    ai_thread.start()
    return "OK"

@app.route("/download_txt/<client_id>/<filename>", methods=['POST'])
def download_txt(client_id, filename):
    idioma_acum = clientes_idioma_acumulado.get(client_id, "es")
    acumulado_text = transcripcion
    if idioma_acum != "es" and transcripcion.strip() and source_lang:
        try:
            target_language = next((l for l in installed_languages if l.code == idioma_acum), None)
            if target_language:
                acumulado_text = source_lang.get_translation(target_language).translate(transcripcion)
        except Exception as e:
            print(f"Error en traducción para TXT a {idioma_acum}: {e}")
    buffer = StringIO()
    buffer.write(f"Transcripción de STTTVAR\n")
    buffer.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n\n")
    buffer.write(acumulado_text)
    txt_content = buffer.getvalue()
    buffer.close()
    return Response(txt_content, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename={filename}.txt'})

@app.route("/download_docx/<client_id>/<filename>", methods=['POST'])
def download_docx(client_id, filename):
    idioma_acum = clientes_idioma_acumulado.get(client_id, "es")
    acumulado_text = transcripcion
    if idioma_acum != "es" and transcripcion.strip() and source_lang:
        try:
            target_language = next((l for l in installed_languages if l.code == idioma_acum), None)
            if target_language:
                acumulado_text = source_lang.get_translation(target_language).translate(transcripcion)
        except Exception as e:
            print(f"Error en traducción para DOCX a {idioma_acum}: {e}")
    doc = Document()
    doc.add_heading("Transcripción de STTTVAR", 0)
    doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %I:%M %p')}")
    doc.add_heading("Transcripción:", level=1)
    doc.add_paragraph(acumulado_text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    headers={'Content-Disposition': f'attachment; filename={filename}.docx'})

def process_ai_question(question, client_id):
    if not ollama_available:
        client_ai_responses[client_id] = "Error: Ollama no está disponible."
        return
    if not question.strip():
        client_ai_responses[client_id] = "Error: La pregunta está vacía."
        return
    try:
        context = transcripcion.strip() or "No hay contexto disponible."
        prompt = (f"Eres un asistente que responde en español de forma clara y concreta, "
                  f"usando el siguiente texto como referencia:\n\n{context}\n\n"
                  f"Pregunta: {question}\nRespuesta:")
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "options": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 512}}
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            client_ai_responses[client_id] = response.json().get("response", "No se recibió respuesta válida.").strip()
        else:
            client_ai_responses[client_id] = f"Error en la API de Ollama: Código {response.status_code}."
    except Exception as e:
        client_ai_responses[client_id] = f"Error al procesar la pregunta: {str(e)}"

class TranscriptionWindow(QWidget):
    # (El código aquí es idéntico a la versión anterior, no es necesario cambiar nada)
    transcription_status_changed = pyqtSignal(bool)
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setWindowTitle("🎙 Transcriptor en Tiempo Real")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMinimumSize(650, 110)
        self.resize(650, 110)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.transcriber_thread = None
        self.transcription_active = False
        self.current_transcription_filepath = None
        self.current_audio_filepath = None
        self.selected_language = "es"
        self._already_stopped = False
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
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = None
    def enterEvent(self, event):
        if self.transcription_active: self._hide_button_timer.stop(); self._fade_in_buttons()
        super().enterEvent(event)
    def leaveEvent(self, event):
        if self.transcription_active and not self.language_combo.view().isVisible(): self._hide_button_timer.start(300)
        super().leaveEvent(event)
    def _setup_ui(self):
        self.base_widget = QWidget(self); self.base_widget.setObjectName("baseWidget"); self.base_widget.setMouseTracking(True); self.setMouseTracking(True)
        self.base_widget.setStyleSheet("#baseWidget { background-color: rgba(30, 30, 30, 200); border: 1px solid rgba(70, 70, 70, 150); border-radius: 10px; }")
        self.title_bar_layout = QHBoxLayout(); self.title_bar_layout.setContentsMargins(10, 5, 5, 0)
        self.window_title_label = QLabel("🎙 STTVAR"); self.window_title_label.setStyleSheet("color: #bbbbbb; font-size: 13px; font-weight: bold;")
        self.close_button = QPushButton("✕"); self.close_button.setFixedSize(24, 24); self.close_button.setToolTip("Cerrar"); self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #bbbbbb; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; color: white; }")
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.window_title_label); self.title_bar_layout.addStretch(); self.title_bar_layout.addWidget(self.close_button)
        self.device_label = QLabel("🎧 Dispositivo de entrada:"); self.device_label.setStyleSheet("color: #bbbbbb; font-size: 13px;")
        self.device_combo = QComboBox(); self.device_combo.setToolTip("Selecciona tu micrófono.")
        self.device_combo.setStyleSheet("QComboBox { border: 1px solid #505050; border-radius: 5px; padding: 3px; background-color: #3a3a3a; color: #e0e0e0; } QComboBox QAbstractItemView { background-color: #3a3a3a; selection-background-color: #557799; }")
        self.language_combo = QComboBox(); self.language_combo.addItem("Español", "es"); self.language_combo.addItem("Inglés", "en"); self.language_combo.addItem("Francés", "fr"); self.language_combo.addItem("Alemán", "de")
        self.language_combo.setToolTip("Selecciona el idioma de transcripción."); self.language_combo.setFixedSize(100, 36); self.language_combo.setCursor(Qt.PointingHandCursor)
        self.language_combo.setStyleSheet("QComboBox { background-color: #444444; border: 2px solid #666666; border-radius: 18px; color: #dddddd; font-size: 14px; padding: 8px; font-weight: bold; } QComboBox:hover { border-color: #e74c3c; } QComboBox QAbstractItemView { background-color: #3a3a3a; selection-background-color: #557799; color: #e0e0e0; border: none; } QComboBox::drop-down { border: none; width: 20px; } QComboBox::down-arrow { image: none; width: 12px; height: 12px; }")
        self.toggle_recording_button = QPushButton("🔴 Iniciar Grabación"); self.toggle_recording_button.setCursor(Qt.PointingHandCursor)
        self.toggle_recording_button.setStyleSheet("QPushButton { background-color: #c0392b; color: white; border-radius: 12px; padding: 8px 18px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #e74c3c; } QPushButton:pressed { background-color: #a8322a; }")
        self.mute_button = QPushButton("🎙️"); self.mute_button.setCheckable(True); self.mute_button.setToolTip("Micrófono activo."); self.mute_button.setCursor(Qt.PointingHandCursor); self.mute_button.setFixedSize(36, 36)
        self.mute_button.setStyleSheet("QPushButton { background-color: #444444; border: 2px solid #666666; border-radius: 18px; color: #dddddd; font-size: 18px; padding: 0; } QPushButton:checked { background-color: #c0392b; border-color: #e74c3c; color: white; } QPushButton:hover { border-color: #e74c3c; } QPushButton:pressed { background-color: #a8322a; border-color: #911f1a; }")
        self.qr_button = QPushButton("🌐"); self.qr_button.setToolTip("Abrir QR o página web"); self.qr_button.setCursor(Qt.PointingHandCursor); self.qr_button.setFixedSize(36, 36)
        self.qr_button.setStyleSheet("QPushButton { background-color: #444444; border: 2px solid #666666; border-radius: 18px; color: #dddddd; font-size: 18px; padding: 0; } QPushButton:hover { border-color: #e74c3c; } QPushButton:pressed { background-color: #a8322a; border-color: #911f1a; }")
        self.buttons_layout = QHBoxLayout(); self.buttons_layout.setSpacing(10); self.buttons_layout.addWidget(self.toggle_recording_button); self.buttons_layout.addWidget(self.mute_button); self.buttons_layout.addWidget(self.qr_button); self.buttons_layout.addWidget(self.language_combo)
        self.settings_button = QPushButton("⚙️"); self.settings_button.setFixedSize(32, 32); self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet("QPushButton { background-color: #4a4a4a; border: 1px solid #5a5a5a; color: #dddddd; border-radius: 8px; } QPushButton:hover { background-color: #5a5a5a; }")
        self.text_area = QTextEdit(); self.text_area.setReadOnly(True); self.text_area.setPlaceholderText("Transcribiendo... Habla ahora.")
        self.text_area.setStyleSheet("QTextEdit { background-color: rgba(0, 0, 0, 0); font-family: 'Segoe UI'; font-size: 18px; padding: 5px 10px; border: none; color: #f0f0f0; }")
        self.control_layout = QHBoxLayout(); self.control_layout.setContentsMargins(10, 5, 10, 5); self.control_layout.setSpacing(8)
        self.control_layout.addWidget(self.device_label); self.control_layout.addWidget(self.device_combo, 1); self.control_layout.addLayout(self.buttons_layout); self.control_layout.addWidget(self.settings_button)
        self.main_layout = QVBoxLayout(self.base_widget); self.main_layout.setContentsMargins(5, 5, 5, 5); self.main_layout.setSpacing(5); self.main_layout.addLayout(self.title_bar_layout)
        self.main_layout.addLayout(self.control_layout); self.main_layout.addWidget(self.text_area); self.main_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(QVBoxLayout()); self.layout().setContentsMargins(0, 0, 0, 0); self.layout().addWidget(self.base_widget)
    def _connect_signals(self):
        self.toggle_recording_button.clicked.connect(self._toggle_recording); self.transcription_status_changed.connect(self._update_ui_for_transcription_status)
        self.settings_button.clicked.connect(self._open_settings_window); self.mute_button.clicked.connect(self._toggle_mute); self.qr_button.clicked.connect(self._on_qr_button_clicked)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
    def _initialize_ui_state(self):
        self.device_label.setVisible(True); self.device_combo.setVisible(True); self.text_area.setVisible(False); self.toggle_recording_button.setVisible(True)
        self.toggle_recording_button.setWindowOpacity(1); self.mute_button.setVisible(False); self.mute_button.setWindowOpacity(0); self.language_combo.setVisible(False)
        self.language_combo.setWindowOpacity(0); self.qr_button.setVisible(False); self.qr_button.setWindowOpacity(0)
    def _populate_devices(self):
        try:
            devices = sd.query_devices(); input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            if not input_devices: self.device_combo.addItem("No se encontraron dispositivos."); self.toggle_recording_button.setEnabled(False); return
            for idx, name in input_devices: self.device_combo.addItem(name, idx)
        except Exception as e: QMessageBox.critical(self, "Error al detectar dispositivos", str(e))
    def _toggle_recording(self):
        if self.transcription_active: self._stop_transcription()
        else: self._start_transcription()
    def _start_transcription(self):
        global qtextedit_buffer
        device_index = self.device_combo.currentData();
        if device_index is None: QMessageBox.warning(self, "Falta dispositivo", "Selecciona un micrófono."); return
        engine = pyttsx3.init(); engine.setProperty('voice', 'spanish'); engine.setProperty('rate', 150); engine.setProperty('volume', 0.9)
        engine.say("Se iniciará la grabación"); engine.runAndWait()
        progress = QProgressDialog("Iniciando transcripción...", None, 0, 0, self); progress.setWindowModality(Qt.WindowModal); progress.setWindowFlags(Qt.FramelessWindowHint); progress.setMinimumDuration(0)
        progress.setAutoClose(True); progress.setStyleSheet("QProgressDialog { background-color: #2a2a2a; border: 2px solid #c0392b; border-radius: 10px; color: #dddddd; font-size: 16px; font-weight: bold; padding: 10px; } QLabel { color: #dddddd; font-size: 16px; }")
        progress.setMinimumSize(300, 150); progress.show(); QApplication.processEvents()
        output_dir = "stt_guardados"; audio_output_dir = "sttaudio_guardados"; os.makedirs(output_dir, exist_ok=True); os.makedirs(audio_output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S"); self.current_transcription_filepath = f"{output_dir}/{timestamp}.txt"; self.current_audio_filepath = f"{audio_output_dir}/{timestamp}.wav"
        try:
            self.transcriber_thread = TranscriberThread(self.model, device_index, self.current_transcription_filepath, self.current_audio_filepath)
            self.transcriber_thread.new_text.connect(self._update_text_area); self.transcriber_thread.finished.connect(self._on_transcription_finished); self.transcriber_thread.start()
            self.transcriber_thread.set_mute(self.mute_button.isChecked()); self.transcription_active = True; self.transcription_status_changed.emit(True); self.text_area.clear()
            qtextedit_buffer = ""; self._already_stopped = False
        except Exception as e: progress.close(); QMessageBox.critical(self, "Error", str(e)); return
        progress.close()
    def _stop_transcription(self):
        global qtextedit_buffer;
        if self._already_stopped: return; self._already_stopped = True
        if self.transcriber_thread: self.transcriber_thread.stop(); self.transcriber_thread.wait(); self.transcriber_thread = None
        self.transcription_active = False; self.transcription_status_changed.emit(False); self._prompt_save_or_discard(); qtextedit_buffer = ""
    def _toggle_mute(self):
        muted = self.mute_button.isChecked(); self.mute_button.setText("🔇" if muted else "🎙️")
        if self.transcriber_thread: self.transcriber_thread.set_mute(muted)
    def _on_qr_button_clicked(self):
        try:
            import subprocess; qr_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_app.py")
            if not os.path.exists(qr_app_path): raise FileNotFoundError(f"No se encontró el archivo {qr_app_path}")
            subprocess.Popen([sys.executable, qr_app_path])
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir el código QR: {str(e)}")
    def _fade_in_buttons(self):
        for widget in [self.toggle_recording_button, self.mute_button, self.language_combo, self.qr_button]:
            widget.setVisible(True); anim = QPropertyAnimation(widget, b"windowOpacity"); anim.setDuration(200)
            anim.setStartValue(widget.windowOpacity() if widget.isVisible() else 0); anim.setEndValue(1); anim.start(); setattr(widget, "_anim", anim)
    def _fade_out_buttons(self):
        for widget in [self.toggle_recording_button, self.mute_button, self.language_combo, self.qr_button]:
            anim = QPropertyAnimation(widget, b"windowOpacity"); anim.setDuration(200); anim.setStartValue(widget.windowOpacity())
            anim.setEndValue(0); anim.finished.connect(lambda w=widget: w.setVisible(False)); anim.start(); setattr(widget, "_anim", anim)
    def _update_ui_for_transcription_status(self, active: bool):
        self.device_label.setVisible(not active); self.device_combo.setVisible(not active); self.text_area.setVisible(active); self.settings_button.setVisible(not active)
        self.close_button.setVisible(not active); self.window_title_label.setVisible(not active)
        if active:
            self.toggle_recording_button.setText("■ Detener Grabación"); self.mute_button.setText("🎙️" if not self.mute_button.isChecked() else "🔇"); self.toggle_recording_button.setVisible(False)
            self.toggle_recording_button.setWindowOpacity(0); self.mute_button.setVisible(False); self.mute_button.setWindowOpacity(0); self.language_combo.setVisible(False)
            self.language_combo.setWindowOpacity(0); self.qr_button.setVisible(False); self.qr_button.setWindowOpacity(0)
        else:
            self.toggle_recording_button.setText("🔴 Iniciar Grabación"); self.toggle_recording_button.setVisible(True); self.toggle_recording_button.setWindowOpacity(1)
            self.mute_button.setVisible(False); self.mute_button.setWindowOpacity(0); self.language_combo.setVisible(False); self.language_combo.setWindowOpacity(0)
            self.qr_button.setVisible(False); self.qr_button.setWindowOpacity(0)
    def _update_text_area(self, text_es: str, is_partial: bool):
        global transcripcion, current_partial, qtextedit_buffer, last_qtextedit_update
        if text_es.strip():
            current_time = time.time()
            if is_partial: qtextedit_buffer = text_es; current_partial = text_es
            else: transcripcion += text_es + " "; current_partial = text_es; qtextedit_buffer = text_es
            if is_partial and current_time - last_qtextedit_update < qtextedit_update_interval: return
            text_to_display = qtextedit_buffer
            if self.selected_language == "es": self.text_area.setPlainText(text_to_display)
            else:
                try:
                    installed = argostranslate.translate.get_installed_languages(); from_lang = next((l for l in installed if l.code == "es"), None); to_lang = next((l for l in installed if l.code == self.selected_language), None)
                    if from_lang and to_lang:
                        translation = from_lang.get_translation(to_lang); cache_key = f"{text_to_display}:{self.selected_language}"
                        if cache_key in translation_cache: text_translated = translation_cache[cache_key]
                        else: text_translated = translation.translate(text_to_display); translation_cache[cache_key] = text_translated
                    else: text_translated = "[Modelos de traducción no disponibles] " + text_to_display
                except Exception as e: text_translated = f"[Error al traducir] {str(e)}\nTexto original: {text_to_display}"
                self.text_area.setPlainText(text_translated)
            self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum()); last_qtextedit_update = current_time
    def _on_language_changed(self, index):
        global qtextedit_buffer
        self.selected_language = self.language_combo.itemData(index)
        if self.transcription_active and qtextedit_buffer.strip(): self._update_text_area(qtextedit_buffer, is_partial=True)
    def _on_transcription_finished(self):
        self._stop_transcription()
    def _prompt_save_or_discard(self):
        global transcripcion, qtextedit_buffer
        if self.current_transcription_filepath and os.path.exists(self.current_transcription_filepath):
            reply_transcription = QMessageBox.question(self, "Guardar Transcripción", "¿Deseas guardar la transcripción?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            transcription_saved = (reply_transcription == QMessageBox.Yes)
            if not transcription_saved:
                try: 
                    if os.path.exists(self.current_transcription_filepath): os.remove(self.current_transcription_filepath)
                except Exception as e: QMessageBox.warning(self, "Error al eliminar", str(e))
            if self.current_audio_filepath and os.path.exists(self.current_audio_filepath):
                reply_audio = QMessageBox.question(self, "Guardar Audio", "Guardar la grabación es bajo tu propia responsabilidad.\n\n¿Deseas guardar el audio?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply_audio == QMessageBox.No:
                    try: 
                        if os.path.exists(self.current_audio_filepath): os.remove(self.current_audio_filepath)
                    except Exception as e: QMessageBox.warning(self, "Error al eliminar", str(e))
                if transcription_saved: QMessageBox.information(self, "Guardado", "La transcripción" + (" y el audio han sido guardados." if reply_audio == QMessageBox.Yes else " ha sido guardada."))
                elif reply_audio == QMessageBox.Yes: QMessageBox.information(self, "Guardado", "El audio ha sido guardado.")
        self.current_transcription_filepath = None; self.current_audio_filepath = None; transcripcion = ""; qtextedit_buffer = ""
    def closeEvent(self, event):
        if self.transcriber_thread and self.transcriber_thread.isRunning():
            reply = QMessageBox.question(self, "Transcripción Activa", "¿Detener y cerrar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes: self._stop_transcription(); event.accept()
            else: event.ignore()
        else: event.accept()
    def _open_settings_window(self):
        self.settings_window = NuevaVentana(self); self.settings_window.show(); self.hide()