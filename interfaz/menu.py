# interfaz/menu.py

import subprocess
import os
import sys
import json
import requests
import tempfile
import re
from collections import Counter
from functools import partial
import uuid

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QApplication, QLabel, QComboBox, QFileDialog,
    QLineEdit, QInputDialog, QMenu, QSizePolicy, QHeaderView, QFrame, QStyle,
    QSlider
)
# MODIFICADO: Se añade QTimer para la carga optimizada
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

# --- Importaciones opcionales para exportación ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
# ---------------------------------------------------

from argostranslate import translate
import pyttsx3


CONFIG_FILE = 'config.json'

# =====================================================================
# >>>>> WIDGET REPRODUCTOR DE AUDIO - VERSIÓN FINAL <<<<<
# Con control de volumen ocultable y slider de búsqueda 100% funcional.
# =====================================================================
class AudioPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.player.setNotifyInterval(100)
        self.is_user_dragging_slider = False # Flag para controlar el arrastre del usuario

        # --- Controles de la Interfaz ---
        self.play_pause_button = QPushButton()
        self.play_pause_button.setObjectName("playerButton")
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_button.setIconSize(QSize(16, 16))
        self.play_pause_button.clicked.connect(self.toggle_playback)

        self.stop_button = QPushButton()
        self.stop_button.setObjectName("playerButton")
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.setIconSize(QSize(16, 16))
        self.stop_button.clicked.connect(self.stop_playback)

        self.position_slider = QSlider(Qt.Horizontal)
        # CONEXIONES CORREGIDAS PARA EL SLIDER
        self.position_slider.sliderPressed.connect(self.slider_pressed)
        self.position_slider.sliderMoved.connect(self.update_label_while_dragging)
        self.position_slider.sliderReleased.connect(self.set_position_on_release)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setFixedWidth(100)

        self.volume_button = QPushButton()
        self.volume_button.setObjectName("volumeButton")
        self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume_button.setIconSize(QSize(18, 18))
        self.volume_button.clicked.connect(self.toggle_volume_slider)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.player.setVolume)
        self.volume_slider.hide()
        self.player.setVolume(80)

        # --- Layout ---
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.time_label)
        layout.addSpacing(10)
        layout.addWidget(self.volume_button)
        layout.addWidget(self.volume_slider)
        self.setLayout(layout)

        # --- Conexión de Señales ---
        self.player.stateChanged.connect(self.update_state)
        self.player.positionChanged.connect(self.update_slider_position)
        self.player.durationChanged.connect(self.update_duration)

    def toggle_volume_slider(self):
        self.volume_slider.setVisible(not self.volume_slider.isVisible())

    def format_time(self, ms):
        if ms <= 0: return "00:00"
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def set_media(self, file_path):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))

    def toggle_playback(self):
        if self.player.mediaStatus() == QMediaPlayer.NoMedia: return
        if self.player.state() == QMediaPlayer.PlayingState: self.player.pause()
        else: self.player.play()

    def stop_playback(self):
        self.player.stop()

    def update_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def update_slider_position(self, position):
        if not self.is_user_dragging_slider:
            self.position_slider.setValue(position)
            duration = self.player.duration()
            self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def slider_pressed(self):
        self.is_user_dragging_slider = True

    def update_label_while_dragging(self, position):
        duration = self.player.duration()
        self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def set_position_on_release(self):
        self.player.setPosition(self.position_slider.value())
        self.is_user_dragging_slider = False

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        position = self.player.position()
        self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")


# =====================================================================
# >>>>> WORKER PARA TEXT-TO-SPEECH (TTS) CON SELECCIÓN DE VOZ <<<<<
# =====================================================================
class TTSWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text_to_speak, voice_id, output_path, parent=None):
        super().__init__(parent)
        self.text = text_to_speak
        self.voice_id = voice_id
        self.output_path = output_path

    def run(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 170)
            if self.voice_id:
                engine.setProperty('voice', self.voice_id)
            engine.save_to_file(self.text, self.output_path)
            engine.runAndWait()
            engine.stop()
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class TextHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, original_text):
        super().__init__(parent)
        self.original_word_counts = Counter(
            word.lower() for word in re.findall(r'\b\w+\b', original_text, re.UNICODE)
        )
        self.new_word_format = QTextCharFormat()
        self.new_word_format.setForeground(QColor("#2ecc71"))
        self.new_word_format.setFontUnderline(False)

    def highlightBlock(self, text):
        self.setFormat(0, len(text), QTextCharFormat())
        current_words = list(re.findall(r'\b\w+\b', text.lower(), re.UNICODE))
        current_word_counts = Counter(current_words)
        highlighted_counts = Counter()
        current_pos = 0
        for word in current_words:
            start_idx = text.lower().find(word, current_pos)
            if start_idx == -1: continue
            highlighted_counts[word] += 1
            if (word not in self.original_word_counts or
                highlighted_counts[word] > self.original_word_counts.get(word, 0)):
                self.setFormat(start_idx, len(word), self.new_word_format)
            current_pos = start_idx + len(word)


class OllamaWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, prompt, model_name):
        super().__init__()
        self.prompt = prompt
        self.model_name = model_name

    def run(self):
        try:
            payload = {"model": self.model_name, "prompt": self.prompt, "stream": True, "options": {"temperature": 0.6, "num_predict": 1024}}
            with requests.post('http://localhost:11434/api/generate', json=payload, stream=True, timeout=60) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("response", "")
                                if content: self.chunk_received.emit(content)
                                if chunk.get("done"): break
                            except json.JSONDecodeError: print(f"Error decodificando chunk de Ollama: {line}")
                else: self.error_signal.emit(f"Error: Código de estado HTTP {response.status_code}")
        except requests.exceptions.Timeout: self.error_signal.emit("Error: La consulta a Ollama excedió el tiempo límite.")
        except requests.exceptions.RequestException as e: self.error_signal.emit(f"Error al conectar con Ollama: {str(e)}")
        except Exception as e: self.error_signal.emit(f"Error inesperado: {str(e)}")
        finally: self.finished.emit()


class TranslationWorker(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, text, source_lang, target_lang, installed_languages):
        super().__init__()
        self.text = text; self.source_lang = source_lang; self.target_lang = target_lang; self.installed_languages = installed_languages

    def run(self):
        try:
            source_lang_obj = next((lang for lang in self.installed_languages if lang.code == self.source_lang), None)
            target_lang_obj = next((lang for lang in self.installed_languages if lang.code == self.target_lang), None)
            if source_lang_obj is None or target_lang_obj is None:
                self.error_signal.emit(f"No está instalado el paquete de traducción para: {self.source_lang} -> {self.target_lang}"); return
            translator = source_lang_obj.get_translation(target_lang_obj)
            if translator is None:
                self.error_signal.emit(f"No existe traducción directa para: {self.source_lang} -> {self.target_lang}"); return
            translated_text = translator.translate(self.text)
            self.result_signal.emit(translated_text)
        except Exception as e: self.error_signal.emit(f"Error al traducir: {str(e)}")


class NuevaVentana(QWidget):
    def __init__(self, parent_transcription_window):
        super().__init__(parent_transcription_window)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)

        self.parent_transcription_window = parent_transcription_window
        self.setObjectName("MainWindow")
        self.setWindowTitle("Explorador de Transcripciones")
        self.setMinimumSize(1300, 700)
        
        # --- INICIALIZACIÓN RÁPIDA DE VARIABLES ---
        self.ollama_available = False
        self.ollama_model_name = "Cargando..." # Texto inicial mientras se verifica
        self.folder_path = "stt_guardados"
        self.audio_folder_path = "sttaudio_guardados"
        self.current_file = None
        self.texto_original = ""
        self.is_dark_theme = False
        self.original_text = ""
        self.highlighter = None
        self.tts_worker = None
        self.tts_temp_file = None
        self.current_recorded_file = None
        self.tts_voices = None
        self.installed_languages = []

        if not os.path.exists(self.folder_path): os.makedirs(self.folder_path)
        if not os.path.exists(self.audio_folder_path): os.makedirs(self.audio_folder_path)

        # --- STYLESHEETS ---
        self.light_theme = """
            QWidget#MainWindow { background-color: #f0f4f7; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #333; }
            QTextEdit, QLineEdit { background-color: #fff; border: 1px solid #dcdcdc; border-radius: 8px; padding: 10px; font-size: 14px; }
            QTextEdit:focus, QLineEdit:focus { border: 1px solid #0078d7; }
            QTableWidget { background-color: #fff; border: 1px solid #dcdcdc; border-radius: 8px; font-size: 13px; alternate-background-color: #f8f8f8; gridline-color: #e0e0e0; }
            QTableWidget::item { padding: 5px; border: none; }
            QTableWidget::item:selected { background-color: #0078d7; color: #fff; }
            QHeaderView::section { background-color: #f0f4f7; border: none; padding: 5px; font-weight: bold; }
            QPushButton { background-color: #0078d7; color: white; border: none; border-radius: 8px; padding: 10px 15px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004578; }
            QPushButton:disabled { background-color: #e0e0e0; color: #a0a0a0; }
            QPushButton#iconButton { background-color: transparent; border: none; padding: 5px; }
            QPushButton#iconButton:hover { background-color: #e6f1f9; border-radius: 8px; }
            QPushButton#predefinedQueryButton { background-color: #e6f1f9; color: #005a9e; font-weight: normal; padding: 8px 12px; }
            QPushButton#predefinedQueryButton:hover { background-color: #d1e3f4; }
            QComboBox { background-color: #fff; border: 1px solid #dcdcdc; border-radius: 8px; padding: 8px; font-size: 13px; }
            QComboBox::drop-down { border: none; }
            QLabel { font-weight: 600; font-size: 13px; color: #555; }
            QLabel#titleLabel { font-size: 16px; font-weight: bold; color: #0078d7; }
            QFrame#container { background-color: #fdfdfd; border: 1px solid #dcdcdc; border-radius: 8px; }
            QLineEdit#searchBar { padding-left: 30px; }
            AudioPlayerWidget QPushButton#playerButton, AudioPlayerWidget QPushButton#volumeButton {
                background-color: #e6f1f9; border: none; border-radius: 14px; min-width: 28px;
                max-width: 28px; min-height: 28px; max-height: 28px;
            }
            AudioPlayerWidget QPushButton#playerButton:hover, AudioPlayerWidget QPushButton#volumeButton:hover { background-color: #d1e3f4; }
            AudioPlayerWidget QSlider::groove:horizontal {
                border: 1px solid #bbb; background: #e0e0e0; height: 8px; border-radius: 4px;
            }
            AudioPlayerWidget QSlider::handle:horizontal {
                background: #0078d7; border: 1px solid #0078d7; width: 14px; height: 14px;
                margin: -4px 0; border-radius: 7px;
            }
            AudioPlayerWidget QLabel#timeLabel { font-weight: bold; }
        """

        self.dark_theme = """
            QWidget#MainWindow { background-color: #1e1e1e; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #e0e0e0; }
            QTextEdit, QLineEdit, QTableWidget { background-color: #2d2d2d; border: 1px solid #444; border-radius: 8px; color: #e0e0e0; }
            QTextEdit, QLineEdit { padding: 10px; font-size: 14px; }
            QTextEdit:focus, QLineEdit:focus { border: 1px solid #0090ff; }
            QTableWidget { font-size: 13px; alternate-background-color: #353535; gridline-color: #404040; }
            QTableWidget::item { padding: 5px; border: none; }
            QTableWidget::item:selected { background-color: #0078d7; color: #fff; }
            QHeaderView::section { background-color: #2d2d2d; border: none; padding: 5px; font-weight: bold; color: #e0e0e0;}
            QPushButton { background-color: #0078d7; color: white; border: none; border-radius: 8px; padding: 10px 15px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #0090ff; }
            QPushButton:pressed { background-color: #005a9e; }
            QPushButton:disabled { background-color: #555; color: #999; }
            QPushButton#iconButton { background-color: transparent; border: none; padding: 5px; }
            QPushButton#iconButton:hover { background-color: #3a3a3a; border-radius: 8px; }
            QPushButton#predefinedQueryButton { background-color: #3a3a3a; color: #90caff; font-weight: normal; padding: 8px 12px; }
            QPushButton#predefinedQueryButton:hover { background-color: #4f4f4f; }
            QComboBox { background-color: #2d2d2d; border: 1px solid #444; border-radius: 8px; padding: 8px; font-size: 13px; }
            QComboBox::drop-down { border: none; }
            QLabel { font-weight: 600; font-size: 13px; color: #bbb; }
            QLabel#titleLabel { font-size: 16px; font-weight: bold; color: #0090ff; }
            QFrame#container { background-color: #252525; border: 1px solid #444; border-radius: 8px; }
            QLineEdit#searchBar { padding-left: 30px; }
            AudioPlayerWidget QPushButton#playerButton, AudioPlayerWidget QPushButton#volumeButton {
                background-color: #3a3a3a; color: #e0e0e0; border: none; border-radius: 14px;
                min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px;
            }
            AudioPlayerWidget QPushButton#playerButton:hover, AudioPlayerWidget QPushButton#volumeButton:hover { background-color: #4f4f4f; }
            AudioPlayerWidget QSlider::groove:horizontal {
                background: #555; border: 1px solid #444; height: 8px; border-radius: 4px;
            }
            AudioPlayerWidget QSlider::handle:horizontal {
                background: #0090ff; border: 1px solid #0090ff; width: 14px; height: 14px;
                margin: -4px 0; border-radius: 7px;
            }
            AudioPlayerWidget QLabel#timeLabel { font-weight: bold; }
        """

        self.setStyleSheet(self.light_theme)

        # --- LAYOUT PRINCIPAL (RÁPIDO) ---
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(15, 15, 15, 15); main_layout.setSpacing(10)
        header_layout = QHBoxLayout()
        title_label = QLabel("🎙️ STTVAR - Explorador"); title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label); header_layout.addStretch()
        self.back_button = QPushButton("🔙 Volver"); self.back_button.clicked.connect(self.close)
        header_layout.addWidget(self.back_button)
        self.theme_button = QPushButton("🌙"); self.theme_button.setObjectName("iconButton"); self.theme_button.setFixedSize(36, 36)
        self.theme_button.clicked.connect(self.toggle_theme); header_layout.addWidget(self.theme_button)
        main_layout.addLayout(header_layout)

        # --- LAYOUT CENTRAL (COLUMNAS) (RÁPIDO) ---
        central_layout = QHBoxLayout(); main_layout.addLayout(central_layout, 1)
        left_column = QVBoxLayout(); central_layout.addLayout(left_column, 2)
        self.textbox = QTextEdit(); self.textbox.setPlaceholderText("Cargando archivos...")
        self.textbox.textChanged.connect(self.check_text_changes); left_column.addWidget(self.textbox, 1)
        edit_buttons_layout = QHBoxLayout()
        self.undo_button = QPushButton("↶ Deshacer"); self.undo_button.clicked.connect(self.textbox.undo)
        self.redo_button = QPushButton("↷ Rehacer"); self.redo_button.clicked.connect(self.textbox.redo)
        self.undo_button.setEnabled(False); self.redo_button.setEnabled(False)
        self.textbox.undoAvailable.connect(self.undo_button.setEnabled); self.textbox.redoAvailable.connect(self.redo_button.setEnabled)
        edit_buttons_layout.addWidget(self.undo_button); edit_buttons_layout.addWidget(self.redo_button); edit_buttons_layout.addStretch()
        left_column.addLayout(edit_buttons_layout)
        tools_container = QFrame(); tools_container.setObjectName("container"); tools_layout = QVBoxLayout(tools_container)
        left_column.addWidget(tools_container)
        self.ia_response_box = QTextEdit(); self.ia_response_box.setReadOnly(True)
        self.ia_response_box.setPlaceholderText("La respuesta de la IA aparecerá aquí..."); self.ia_response_box.hide()
        tools_layout.addWidget(self.ia_response_box)
        self.translate_container = QWidget(); translate_layout = QHBoxLayout(self.translate_container)
        translate_layout.setContentsMargins(0, 5, 0, 0); translate_layout.addWidget(QLabel("🈯 Traducir a:"))
        self.translate_combo = QComboBox(); self.translate_combo.addItems(["Español (es)", "Inglés (en)", "Portugués (pt)"])
        self.translate_combo.currentIndexChanged.connect(self.handle_translation); translate_layout.addWidget(self.translate_combo)
        self.tts_button = QPushButton("🔊 Generar Audio"); self.tts_button.setMinimumHeight(36)
        self.tts_button.clicked.connect(self.generate_text_to_speech); self.tts_button.hide()
        translate_layout.addWidget(self.tts_button); translate_layout.addStretch(); self.translate_container.hide()
        tools_layout.addWidget(self.translate_container)
        self.tts_audio_player = AudioPlayerWidget(); self.tts_audio_player.hide(); tools_layout.addWidget(self.tts_audio_player)
        predefined_queries_layout = QHBoxLayout(); predefined_queries_layout.addWidget(QLabel("Consultas IA:"))
        self.summarize_button = QPushButton("📄 Resumir"); self.summarize_button.setObjectName("predefinedQueryButton")
        self.keywords_button = QPushButton("🔑 Puntos Clave"); self.keywords_button.setObjectName("predefinedQueryButton")
        self.correct_button = QPushButton("✍️ Corregir"); self.correct_button.setObjectName("predefinedQueryButton")
        self.predefined_buttons = [self.summarize_button, self.keywords_button, self.correct_button]
        for btn in self.predefined_buttons: predefined_queries_layout.addWidget(btn)
        predefined_queries_layout.addStretch(); tools_layout.addLayout(predefined_queries_layout)
        self.summarize_button.clicked.connect(lambda: self.handle_predefined_ia_query("summarize"))
        self.keywords_button.clicked.connect(lambda: self.handle_predefined_ia_query("keywords"))
        self.correct_button.clicked.connect(lambda: self.handle_predefined_ia_query("correct"))
        ia_query_layout = QHBoxLayout()
        self.ia_query_input = QLineEdit(); self.ia_query_input.setPlaceholderText("O haz una pregunta personalizada...")
        ia_query_layout.addWidget(self.ia_query_input, 1); self.ia_query_button = QPushButton("🤖 Enviar")
        self.ia_query_button.clicked.connect(self.handle_custom_ia_query); ia_query_layout.addWidget(self.ia_query_button)
        tools_layout.addLayout(ia_query_layout)
        self.ia_model_label = QLabel(f"Modelo: {self.ollama_model_name}"); self.ia_model_label.setAlignment(Qt.AlignRight)
        tools_layout.addWidget(self.ia_model_label)
        
        # Ocultar widgets de IA por defecto, se mostrarán después de la carga si están disponibles
        self.ia_widgets = [self.summarize_button, self.keywords_button, self.correct_button, self.ia_query_input, self.ia_query_button, self.ia_model_label]
        for widget in self.ia_widgets: widget.setVisible(False)
        
        bottom_actions_layout = QHBoxLayout()
        self.save_button = QPushButton("💾 Guardar Cambios"); self.save_button.clicked.connect(self.save_file); self.save_button.hide()
        bottom_actions_layout.addWidget(self.save_button); bottom_actions_layout.addStretch()
        bottom_actions_layout.addWidget(QLabel("Exportar como:"))
        self.export_combo = QComboBox(); self.export_combo.addItems(["PDF", "Word (.docx)", "Markdown (.md)"])
        bottom_actions_layout.addWidget(self.export_combo); self.download_button = QPushButton("📥 Descargar")
        self.download_button.clicked.connect(self.export_selected_format); bottom_actions_layout.addWidget(self.download_button)
        left_column.addLayout(bottom_actions_layout)

        # --- COLUMNA DERECHA (RÁPIDO) ---
        right_column = QVBoxLayout(); central_layout.addLayout(right_column, 1)
        file_list_controls_layout = QHBoxLayout()
        self.search_bar = QLineEdit(); self.search_bar.setObjectName("searchBar"); self.search_bar.setPlaceholderText("🔍 Buscar...")
        self.sort_combo = QComboBox(); self.sort_combo.addItems(["Fecha reciente", "Fecha antigua", "Nombre (A-Z)", "Nombre (Z-A)"])
        file_list_controls_layout.addWidget(self.search_bar, 1)
        file_list_controls_layout.addWidget(self.sort_combo)
        right_column.addLayout(file_list_controls_layout)
        self.file_list = QTableWidget(); self.file_list.setColumnCount(2); self.file_list.setHorizontalHeaderLabels(["Archivo", "Audio"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch); self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_list.verticalHeader().setVisible(False); self.file_list.setSelectionMode(QTableWidget.SingleSelection)
        self.file_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.setShowGrid(False); right_column.addWidget(self.file_list, 1)
        self.recorded_audio_player = AudioPlayerWidget(); self.recorded_audio_player.hide()
        right_column.addWidget(self.recorded_audio_player)
        
        # Conectar señales ahora que los widgets existen
        self.search_bar.textChanged.connect(self.load_file_list)
        self.sort_combo.currentIndexChanged.connect(self.load_file_list)
        self.file_list.cellClicked.connect(self.load_file_content)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.recorded_audio_player.player.stateChanged.connect(self.update_recorded_audio_icons)

        # --- CAMBIO CLAVE: DIFERIR LA CARGA LENTA ---
        # Programar las operaciones de carga para que se ejecuten después de que la ventana se haya mostrado
        QTimer.singleShot(50, self._post_init_load)

    def _post_init_load(self):
        """
        Ejecuta todas las operaciones de carga lentas después de que la interfaz de usuario
        sea visible para evitar que la aplicación se congele al abrirse.
        """
        # 1. Realizar todas las operaciones lentas
        self._load_ollama_config()
        self._cache_tts_voices()
        self.installed_languages = translate.get_installed_languages()
        self.load_file_list()

        # 2. Actualizar la interfaz de usuario con la información obtenida
        for widget in self.ia_widgets:
            widget.setVisible(self.ollama_available)
        self.ia_model_label.setText(f"Modelo: {self.ollama_model_name}")
        self.textbox.setPlaceholderText("Selecciona un archivo para ver y editar su contenido...")

    def _cache_tts_voices(self):
        if self.tts_voices is not None: return
        try:
            engine = pyttsx3.init()
            self.tts_voices = engine.getProperty('voices')
            engine.stop()
        except Exception as e:
            print(f"No se pudieron precargar las voces de TTS: {e}")
            self.tts_voices = []
            
    def _load_ollama_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f: config = json.load(f); self.ollama_model_name = config.get('ollama_model', 'phi3:latest')
            else: self.ollama_model_name = 'phi3:latest'
        except (IOError, json.JSONDecodeError): self.ollama_model_name = 'phi3:latest'
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200 and response.json().get("models"): self.ollama_available = True
            else: self.ollama_available = False; self.ollama_model_name = "IA no disponible"
        except requests.exceptions.RequestException: self.ollama_available = False; self.ollama_model_name = "IA no disponible"

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme; self.setStyleSheet(self.dark_theme if self.is_dark_theme else self.light_theme)
        self.theme_button.setText("☀️" if self.is_dark_theme else "🌙")

    def get_code_from_selection(self):
        text = self.translate_combo.currentText(); match = re.search(r'\((\w+)\)', text); return match.group(1) if match else "es"

    def handle_translation(self):
        self.tts_audio_player.stop_playback(); self.tts_audio_player.hide()
        if not self.texto_original: return
        target_lang = self.get_code_from_selection(); source_lang = "es"
        if target_lang == source_lang: self.ia_response_box.setPlainText(self.texto_original); self.tts_button.show(); return
        self.ia_response_box.setPlainText("Traduciendo, por favor espera..."); self.tts_button.hide()
        self.translation_worker = TranslationWorker(self.texto_original, source_lang, target_lang, self.installed_languages)
        self.translation_worker.result_signal.connect(self.handle_translation_result); self.translation_worker.error_signal.connect(self.handle_translation_error)
        self.translation_worker.start()

    def handle_translation_result(self, translated_text):
        self.ia_response_box.setPlainText(translated_text); self.tts_button.show(); self.translation_worker = None

    def handle_translation_error(self, error):
        self.ia_response_box.setPlainText(error); self.tts_button.hide(); self.translation_worker = None
        
    def load_file_list(self):
        self.file_list.clearContents(); self.file_list.setRowCount(0)
        if not os.path.exists(self.folder_path): return
        try:
            files = [f for f in os.listdir(self.folder_path) if f.endswith(".txt")]
        except OSError:
            QMessageBox.critical(self, "Error", f"No se pudo acceder a la carpeta: {self.folder_path}")
            return
            
        search_term = self.search_bar.text().lower()
        if search_term: files = [f for f in files if search_term in f.lower()]
        sort_option = self.sort_combo.currentText()
        try:
            sort_key = lambda f: os.path.getmtime(os.path.join(self.folder_path, f)); reverse = "reciente" in sort_option
            if "Nombre" in sort_option: sort_key = str.lower; reverse = "Z-A" in sort_option
            files.sort(key=sort_key, reverse=reverse)
        except Exception as e:
            print(f"Error al ordenar archivos: {e}")

        self.file_list.setRowCount(len(files))
        for row, filename in enumerate(files):
            text_item = QTableWidgetItem(os.path.splitext(filename)[0]); text_item.setData(Qt.UserRole, filename)
            text_item.setFlags(text_item.flags() & ~Qt.ItemIsEditable); self.file_list.setItem(row, 0, text_item)
            audio_path = os.path.join(self.audio_folder_path, f"{os.path.splitext(filename)[0]}.wav")
            has_audio = os.path.exists(audio_path)
            
            speaker_button = QPushButton(); speaker_button.setObjectName("iconButton")
            speaker_button.setFixedSize(28, 28); speaker_button.setStyleSheet("border: none; background-color: transparent;")
            if has_audio:
                speaker_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay)); speaker_button.setEnabled(True)
                speaker_button.setToolTip("Reproducir audio"); speaker_button.clicked.connect(partial(self.play_recorded_audio, audio_path))
            else:
                speaker_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted)); speaker_button.setEnabled(False)
                speaker_button.setToolTip("No hay audio disponible")
            
            cell_widget = QWidget(); cell_layout = QHBoxLayout(cell_widget); cell_layout.addWidget(speaker_button)
            cell_layout.setAlignment(Qt.AlignCenter); cell_layout.setContentsMargins(0, 0, 0, 0)
            self.file_list.setCellWidget(row, 1, cell_widget)
        self.file_list.setColumnWidth(1, 40)

    def play_recorded_audio(self, audio_path):
        self.tts_audio_player.stop_playback() 
        if self.current_recorded_file == audio_path and self.recorded_audio_player.player.state() != QMediaPlayer.StoppedState:
            self.recorded_audio_player.toggle_playback()
        else:
            self.recorded_audio_player.stop_playback(); self.current_recorded_file = audio_path
            self.recorded_audio_player.set_media(audio_path); self.recorded_audio_player.show()
            self.recorded_audio_player.player.play()

    def update_recorded_audio_icons(self):
        state = self.recorded_audio_player.player.state()
        for row in range(self.file_list.rowCount()):
            item = self.file_list.item(row, 0)
            if not item: continue
            filename = item.data(Qt.UserRole)
            audio_path = os.path.join(self.audio_folder_path, f"{os.path.splitext(filename)[0]}.wav")
            cell_widget = self.file_list.cellWidget(row, 1)
            if cell_widget:
                button = cell_widget.findChild(QPushButton)
                if button and button.isEnabled():
                    is_current = (audio_path == self.current_recorded_file)
                    is_playing = (state == QMediaPlayer.PlayingState)
                    icon = QStyle.SP_MediaPause if is_current and is_playing else QStyle.SP_MediaPlay
                    button.setIcon(self.style().standardIcon(icon))
        if state == QMediaPlayer.StoppedState and self.current_recorded_file:
            self.current_recorded_file = None; self.recorded_audio_player.hide()

    def load_file_content(self, row, column):
        if column == 1: return
        item = self.file_list.item(row, 0)
        if not item: return
        filename = item.data(Qt.UserRole); filepath = os.path.join(self.folder_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file: content = file.read()
            self.textbox.setPlainText(content); self.original_text = content; self.current_file = filepath
            self.highlighter = TextHighlighter(self.textbox.document(), self.original_text); self.reset_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo: {e}")
            self.current_file = None; self.original_text = ""; self.highlighter = None

    def reset_ui_state(self):
        self.ia_response_box.clear(); self.ia_response_box.hide(); self.tts_button.hide(); self.translate_container.hide()
        self.ia_query_input.clear(); self.translate_combo.setCurrentIndex(0); self.texto_original = ""
        self.recorded_audio_player.stop_playback(); self.tts_audio_player.stop_playback(); self.tts_audio_player.hide(); self.save_button.hide()
    
    def check_text_changes(self):
        if self.current_file: self.save_button.setVisible(self.textbox.toPlainText() != self.original_text)

    def save_file(self):
        if not self.current_file: return
        try:
            with open(self.current_file, "w", encoding="utf-8") as file: content = self.textbox.toPlainText(); file.write(content)
            self.original_text = content; self.highlighter.rehighlight(); self.save_button.hide()
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")

    def export_selected_format(self):
        if not self.current_file: QMessageBox.warning(self, "Advertencia", "Debes seleccionar un archivo para exportar."); return
        format_selected = self.export_combo.currentText()
        if "PDF" in format_selected: self.export_to_pdf()
        elif "Word" in format_selected: self.export_to_word()
        elif "Markdown" in format_selected: self.export_to_markdown()

    def export_to_pdf(self):
        if not REPORTLAB_AVAILABLE: QMessageBox.critical(self, "Error", "La librería 'reportlab' es necesaria.\nInstálala con: pip install reportlab"); return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", self.current_file.replace(".txt", ".pdf"), "*.pdf")
        if not path: return
        try:
            c = canvas.Canvas(path, pagesize=letter); text_object = c.beginText(40, letter[1] - 40)
            for line in self.textbox.toPlainText().splitlines(): text_object.textLine(line)
            c.drawText(text_object); c.save(); QMessageBox.information(self, "Éxito", f"Archivo exportado a PDF:\n{path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF:\n{e}")

    def export_to_word(self):
        if not DOCX_AVAILABLE: QMessageBox.critical(self, "Error", "La librería 'python-docx' es necesaria.\nInstálala con: pip install python-docx"); return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar DOCX", self.current_file.replace(".txt", ".docx"), "*.docx")
        if not path: return
        try:
            doc = Document(); doc.add_paragraph(self.textbox.toPlainText()); doc.save(path); QMessageBox.information(self, "Éxito", f"Archivo exportado a Word:\n{path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a Word:\n{e}")

    def export_to_markdown(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Markdown", self.current_file.replace(".txt", ".md"), "*.md")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f: f.write(self.textbox.toPlainText()); QMessageBox.information(self, "Éxito", f"Archivo exportado a Markdown:\n{path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a Markdown:\n{e}")

    def show_context_menu(self, position):
        item = self.file_list.itemAt(position)
        if not item: return
        menu = QMenu(); rename_action = menu.addAction("✏️ Renombrar"); delete_action = menu.addAction("🗑️ Eliminar"); folder_action = menu.addAction("📁 Abrir ubicación")
        action = menu.exec_(self.file_list.viewport().mapToGlobal(position))
        if action == rename_action: self.rename_file(self.file_list.row(item))
        elif action == delete_action: self.delete_file(item)
        elif action == folder_action: self.open_file_location(item)

    def rename_file(self, row):
        old_name = self.file_list.item(row, 0).data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=os.path.splitext(old_name)[0])
        if ok and new_name:
            new_name_txt = new_name + ".txt"; old_path = os.path.join(self.folder_path, old_name); new_path = os.path.join(self.folder_path, new_name_txt)
            if os.path.exists(new_path): QMessageBox.warning(self, "Error", "Ya existe un archivo con ese nombre."); return
            try:
                os.rename(old_path, new_path)
                old_audio = os.path.join(self.audio_folder_path, os.path.splitext(old_name)[0] + ".wav")
                if os.path.exists(old_audio): new_audio = os.path.join(self.audio_folder_path, new_name + ".wav"); os.rename(old_audio, new_audio)
                if self.current_file == old_path: self.current_file = new_path
                self.load_file_list()
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo renombrar:\n{e}")

    def delete_file(self, item):
        filename = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Confirmar", f"¿Eliminar permanentemente '{filename}' y su audio?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                filepath = os.path.join(self.folder_path, filename)
                if os.path.exists(filepath): os.remove(filepath)
                audio_path = os.path.join(self.audio_folder_path, f"{os.path.splitext(filename)[0]}.wav")
                if os.path.exists(audio_path): os.remove(audio_path)
                if self.current_file == filepath: self.current_file = None; self.textbox.clear(); self.reset_ui_state()
                self.load_file_list()
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def open_file_location(self, item):
        try:
            filepath = os.path.join(self.folder_path)
            if sys.platform == 'win32': os.startfile(filepath)
            elif sys.platform == 'darwin': subprocess.Popen(['open', filepath])
            else: subprocess.Popen(['xdg-open', filepath])
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta: {e}")

    def start_ia_worker(self, prompt):
        self.set_ia_buttons_enabled(False); self.ia_response_box.clear(); self.ia_response_box.setPlaceholderText("Consultando a la IA, por favor espera...")
        self.ia_response_box.show(); self.translate_container.show(); self.tts_button.hide(); self.tts_audio_player.hide()
        self.worker = OllamaWorker(prompt, self.ollama_model_name); self.worker.chunk_received.connect(self.handle_ia_chunk)
        self.worker.finished.connect(self.handle_ia_finished); self.worker.error_signal.connect(self.handle_ia_error); self.worker.start()

    def handle_custom_ia_query(self):
        pregunta = self.ia_query_input.text().strip()
        if not pregunta: QMessageBox.warning(self, "Advertencia", "Debes escribir una pregunta."); return
        contenido = self.textbox.toPlainText().strip()
        if not contenido: QMessageBox.warning(self, "Advertencia", "No hay texto en el editor para usar como contexto."); return
        prompt = f"Usando el siguiente texto como referencia, responde a la pregunta.\n\nTexto: \"{contenido}\"\n\nPregunta: {pregunta}\n\nRespuesta concisa:"
        self.start_ia_worker(prompt)

    def handle_predefined_ia_query(self, query_type):
        contenido = self.textbox.toPlainText().strip()
        if not contenido: QMessageBox.warning(self, "Advertencia", "No hay texto en el editor para procesar."); return
        prompts = {
            "summarize": f"Resume los puntos más importantes del siguiente texto de forma concisa y clara en español:\n\n\"{contenido}\"",
            "keywords": f"Extrae las 5 a 7 ideas o palabras clave más relevantes del siguiente texto, presentadas como una lista en español:\n\n\"{contenido}\"",
            "correct": f"Revisa y corrige la ortografía y gramática del siguiente texto. Devuelve únicamente el texto corregido sin añadir comentarios adicionales.\n\nTexto original:\n\"{contenido}\"\n\nTexto corregido:"
        }
        self.start_ia_worker(prompts[query_type])

    def set_ia_buttons_enabled(self, enabled):
        self.ia_query_button.setEnabled(enabled)
        for btn in self.predefined_buttons: btn.setEnabled(enabled)

    def handle_ia_chunk(self, chunk):
        self.ia_response_box.insertPlainText(chunk); self.ia_response_box.verticalScrollBar().setValue(self.ia_response_box.verticalScrollBar().maximum())

    def handle_ia_finished(self):
        self.set_ia_buttons_enabled(True); self.ia_query_input.clear(); self.texto_original = self.ia_response_box.toPlainText()
        self.translate_combo.setCurrentIndex(0); self.tts_button.show(); self.worker = None

    def handle_ia_error(self, error):
        self.ia_response_box.setPlainText(error); self.set_ia_buttons_enabled(True); self.worker = None

    def on_tts_synthesis_finished(self, filepath=None):
        self.tts_button.setText("🔊 Generar Audio"); self.tts_button.setEnabled(True); self.tts_worker = None
        if filepath:
            self.recorded_audio_player.stop_playback()
            self.tts_audio_player.set_media(filepath)
            self.tts_audio_player.show()
            self.tts_audio_player.toggle_playback()

    def on_tts_synthesis_error(self, error_message):
        QMessageBox.critical(self, "Error de TTS", f"Ocurrió un error al generar el audio:\n{error_message}"); self.on_tts_synthesis_finished()
        
    def get_voice_for_language(self, target_lang_code):
        if self.tts_voices is None: return None
        exact_matches = []; prefix_matches = []
        target_lang_code = target_lang_code.lower()
        for voice in self.tts_voices:
            for lang in voice.languages:
                clean_lang = lang.lower().replace('_', '-')
                if clean_lang == target_lang_code: exact_matches.append(voice.id)
                elif clean_lang.startswith(target_lang_code + '-'): prefix_matches.append(voice.id)
        if exact_matches: return exact_matches[0]
        if prefix_matches: return prefix_matches[0]
        return None

    def generate_text_to_speech(self):
        if self.tts_worker and self.tts_worker.isRunning(): return
        text = self.ia_response_box.toPlainText().strip()
        if not text: QMessageBox.warning(self, "Advertencia", "No hay texto para leer."); return
        
        if self.tts_temp_file and os.path.exists(self.tts_temp_file):
            try: os.remove(self.tts_temp_file)
            except OSError as e: print(f"No se pudo eliminar el archivo TTS temporal anterior: {e}")
        
        self.tts_temp_file = os.path.join(tempfile.gettempdir(), f"sttvar_tts_{uuid.uuid4()}.wav")

        target_lang = self.get_code_from_selection()
        voice_id = self.get_voice_for_language(target_lang)

        if not voice_id:
             QMessageBox.warning(self, "Voz no encontrada", f"No se encontró una voz para el idioma '{target_lang}' en tu sistema. Se usará la voz predeterminada.")
        
        self.recorded_audio_player.stop_playback()
        self.tts_audio_player.stop_playback()
        self.tts_button.setText("Generando..."); self.tts_button.setEnabled(False)
        
        self.tts_worker = TTSWorker(text, voice_id, self.tts_temp_file)
        self.tts_worker.finished.connect(self.on_tts_synthesis_finished)
        self.tts_worker.error.connect(self.on_tts_synthesis_error)
        self.tts_worker.start()
    
    def closeEvent(self, event):
        self.recorded_audio_player.stop_playback()
        self.tts_audio_player.stop_playback()
        if self.tts_worker and self.tts_worker.isRunning(): self.tts_worker.terminate()
        if self.tts_temp_file and os.path.exists(self.tts_temp_file):
            try: os.remove(self.tts_temp_file)
            except OSError as e: print(f"No se pudo eliminar el archivo TTS temporal: {e}")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    class MockParent:
        def show(self): print("Volviendo a la ventana de transcripción (simulado)")
    window = NuevaVentana(MockParent())
    window.show()
    sys.exit(app.exec_())