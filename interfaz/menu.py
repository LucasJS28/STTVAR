# interfaz/menu.py

import subprocess
import os
import sys
import json
import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QApplication, QLabel, QComboBox, QFileDialog,
    QLineEdit, QInputDialog, QMenu, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import Qt, QPoint, QUrl, QSize, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from argostranslate import translate
import pyttsx3
from collections import Counter
import re

CONFIG_FILE = 'config.json'

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
            if start_idx == -1:
                continue
            highlighted_counts[word] += 1
            if (word not in self.original_word_counts or 
                highlighted_counts[word] > self.original_word_counts.get(word, 0)):
                self.setFormat(start_idx, len(word), self.new_word_format)
            current_pos = start_idx + len(word)

# =====================================================================
# >>>>> OLLAMA WORKER TOTALMENTE MODIFICADO PARA STREAMING <<<<<
# =====================================================================
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
            payload = {
                "model": self.model_name,
                "prompt": self.prompt,
                "stream": True,
                "options": {
                    "temperature": 0.6,
                    "num_predict": 256
                }
            }
            
            with requests.post('http://localhost:11434/api/generate', json=payload, stream=True, timeout=60) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("response", "")
                                if content:
                                    self.chunk_received.emit(content)
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                print(f"Error decodificando chunk de Ollama: {line}")
                else:
                    self.error_signal.emit(f"Error: Código de estado HTTP {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.error_signal.emit("Error: La consulta a Ollama excedió el tiempo límite.")
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"Error al conectar con Ollama: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"Error inesperado: {str(e)}")
        finally:
            self.finished.emit()


class TranslationWorker(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, text, source_lang, target_lang, installed_languages):
        super().__init__()
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.installed_languages = installed_languages

    def run(self):
        try:
            source_lang_obj = next((lang for lang in self.installed_languages if lang.code == self.source_lang), None)
            target_lang_obj = next((lang for lang in self.installed_languages if lang.code == self.target_lang), None)

            if source_lang_obj is None or target_lang_obj is None:
                self.error_signal.emit(f"No está instalado el paquete de traducción para: {self.source_lang} -> {self.target_lang}")
                return

            translator = source_lang_obj.get_translation(target_lang_obj)
            if translator is None:
                self.error_signal.emit(f"No existe traducción directa para: {self.source_lang} -> {self.target_lang}")
                return

            translated_text = translator.translate(self.text)
            self.result_signal.emit(translated_text)
        except Exception as e:
            self.error_signal.emit(f"Error al traducir: {str(e)}")

class NuevaVentana(QWidget):
    def __init__(self, parent_transcription_window):
        super().__init__()
        self.parent_transcription_window = parent_transcription_window
        self.setObjectName("MainWindow")
        self.setWindowTitle("Explorador de Transcripciones")
        self.setMinimumSize(900, 600)
        
        self.ollama_available = False
        self.ollama_model_name = "No disponible"
        self._load_ollama_config()

        self.folder_path = "stt_guardados"
        self.audio_folder_path = "sttaudio_guardados"
        self.current_file = None
        self.texto_original = ""
        self.is_dark_theme = False
        self.original_text = ""
        self.highlighter = None

        self.tts_engine = None
        self.initialize_tts_engine()
        self.is_reading = False

        self.audio_player = QMediaPlayer()
        self.audio_player.stateChanged.connect(self.handle_audio_state_changed)
        self.current_audio_file = None

        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        if not os.path.exists(self.audio_folder_path):
            os.makedirs(self.audio_folder_path)

        self.light_theme = """
            QWidget#MainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f4f8, stop:1 #d9e2ec); border-radius: 15px; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #2d3436; }
            QTextEdit { background-color: #ffffff; border: 2px solid #dfe6e9; border-radius: 12px; padding: 12px; font-size: 14px; border-top: none; }
            QTableWidget { background-color: #ffffff; border: 2px solid #dfe6e9; border-radius: 12px; padding: 8px; font-size: 13px; show-decoration-selected: 1; alternate-background-color: #f8fafc; border-top: none; }
            QTableWidget::item { padding: 0px; border: none; height: 40px; alignment: center; }
            QTableWidget::item:selected { background-color: #0984e3; color: #ffffff; }
            QTableWidget { gridline-color: transparent; }
            QPushButton { background-color: #0984e3; color: white; border: none; border-radius: 12px; padding: 8px 12px; font-size: 13px; margin-top: 10px; }
            QPushButton:hover { background-color: #0652dd; }
            QPushButton:pressed { background-color: #0549b5; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
            QPushButton#themeButton, QPushButton#ttsButton, QPushButton#speakerButton { background-color: #ffffff; color: #0984e3; border: 2px solid #dfe6e9; padding: 0px; font-size: 14px; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; border-radius: 8px; margin: 4px; border-top: none; }
            QPushButton#themeButton:hover, QPushButton#ttsButton:hover, QPushButton#speakerButton:hover:enabled { background-color: #e6f0fa; color: #0652dd; border: 2px solid #b3d4fc; }
            QPushButton#themeButton:pressed, QPushButton#ttsButton:pressed, QPushButton#speakerButton:pressed:enabled { background-color: #cce0ff; color: #0549b5; border: 2px solid #b3d4fc; }
            QPushButton#speakerButton:disabled { color: #b0b0b0; border: 2px solid #dfe6e9; }
            QPushButton#backButton { background-color: #ffffff; color: #e17055; border: 2px solid #dfe6e9; padding: 4px 8px; font-size: 12px; margin: 0 5px; border-top: none; }
            QPushButton#backButton:hover { background-color: #ffebee; color: #d35400; border: 2px solid #ffc1cc; }
            QPushButton#backButton:pressed { background-color: #ffcdd2; color: #b74700; border: 2px solid #ffc1cc; }
            QPushButton#undoButton, QPushButton#redoButton { background-color: #ffffff; color: #0984e3; border: 2px solid #dfe6e9; padding: 4px 8px; font-size: 12px; margin: 4px; border-radius: 8px; border-top: none; }
            QPushButton#undoButton:hover, QPushButton#redoButton:hover:enabled { background-color: #e6f0fa; color: #0652dd; border: 2px solid #b3d4fc; }
            QPushButton#undoButton:pressed, QPushButton#redoButton:pressed:enabled { background-color: #cce0ff; color: #0549b5; border: 2px solid #b3d4fc; }
            QPushButton#undoButton:disabled, QPushButton#redoButton:disabled { color: #b0b0b0; border: 2px solid #dfe6e9; }
            QComboBox { background-color: #ffffff; border: 2px solid #dfe6e9; border-radius: 12px; padding: 6px; font-size: 13px; border-top: none; }
            QComboBox#translateCombo { max-width: 130px; padding: 4px; font-size: 12px; }
            QComboBox:hover { background-color: #f8fafc; border: 2px solid #b3d4fc; }
            QLabel { font-weight: 600; font-size: 13px; color: #2d3436; margin-right: 8px; padding: 2px; }
            #titleLabel { font-size: 14px; font-weight: bold; color: #0984e3; padding: 8px; }
            #headerContainer { background: transparent; padding: 10px 15px; margin: 0; border: none; }
            #exportContainer, #iaQueryContainer, #iaResponseContainer { background-color: #f0f4f8; border: 2px solid #dfe6e9; border-radius: 12px; margin-top: 10px; padding: 12px; border-top: none; }
            QLineEdit { background-color: #ffffff; border: 2px solid #dfe6e9; border-radius: 12px; padding: 8px; font-size: 13px; border-top: none; }
            QLineEdit:hover { background-color: #f8fafc; border: 2px solid #b3d4fc; }
            QLabel#iaModelLabel { font-size: 10px; color: #6c757d; padding: 0 12px; margin-top: -5px; }
        """

        self.dark_theme = """
            QWidget#MainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d3436, stop:1 #1e272e); border-radius: 15px; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #dfe6e9; }
            QTextEdit { background-color: #353b48; border: 2px solid #4b5468; border-radius: 12px; padding: 12px; font-size: 14px; color: #dfe6e9; border-top: none; }
            QTableWidget { background-color: #353b48; border: 2px solid #4b5468; border-radius: 12px; padding: 8px; font-size: 13px; color: #dfe6e9; show-decoration-selected: 1; alternate-background-color: #3b434f; border-top: none; }
            QTableWidget::item { padding: 0px; border: none; height: 40px; alignment: center; }
            QTableWidget::item:selected { background-color: #0984e3; color: #ffffff; }
            QTableWidget { gridline-color: transparent; }
            QPushButton { background-color: #0984e3; color: white; border: none; border-radius: 12px; padding: 8px 12px; font-size: 13px; margin-top: 10px; }
            QPushButton:hover { background-color: #0652dd; }
            QPushButton:pressed { background-color: #0549b5; }
            QPushButton:disabled { background-color: #57606f; color: #a4b0be; }
            QPushButton#themeButton, QPushButton#ttsButton, QPushButton#speakerButton { background-color: #353b48; color: #74b9ff; border: 2px solid #4b5468; padding: 0px; font-size: 14px; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; border-radius: 8px; margin: 4px; border-top: none; }
            QPushButton#themeButton:hover, QPushButton#ttsButton:hover, QPushButton#speakerButton:hover:enabled { background-color: #34495e; color: #54a0ff; border: 2px solid #74b9ff; }
            QPushButton#themeButton:pressed, QPushButton#ttsButton:pressed, QPushButton#speakerButton:pressed:enabled { background-color: #2c3e50; color: #339af0; border: 2px solid #74b9ff; }
            QPushButton#speakerButton:disabled { color: #6b7280; border: 2px solid #4b5468; }
            QPushButton#backButton { background-color: #353b48; color: #e17055; border: 2px solid #4b5468; padding: 4px 8px; font-size: 12px; margin: 0 5px; border-top: none; }
            QPushButton#backButton:hover { background-color: #34495e; color: #d35400; border: 2px solid #ff8a80; }
            QPushButton#backButton:pressed { background-color: #2c3e50; color: #b74700; border: 2px solid #ff8a80; }
            QPushButton#undoButton, QPushButton#redoButton { background-color: #353b48; color: #74b9ff; border: 2px solid #4b5468; padding: 4px 8px; font-size: 12px; margin: 4px; border-radius: 8px; border-top: none; }
            QPushButton#undoButton:hover, QPushButton#redoButton:hover:enabled { background-color: #34495e; color: #54a0ff; border: 2px solid #74b9ff; }
            QPushButton#undoButton:pressed, QPushButton#redoButton:pressed:enabled { background-color: #2c3e50; color: #339af0; border: 2px solid #74b9ff; }
            QPushButton#undoButton:disabled, QPushButton#redoButton:disabled { color: #6b7280; border: 2px solid #4b5468; }
            QComboBox { background-color: #353b48; border: 2px solid #4b5468; border-radius: 12px; padding: 6px; font-size: 13px; color: #dfe6e9; border-top: none; }
            QComboBox#translateCombo { max-width: 130px; padding: 4px; font-size: 12px; }
            QComboBox:hover { background-color: #3b434f; border: 2px solid #74b9ff; }
            QLabel { font-weight: 600; font-size: 13px; color: #dfe6e9; margin-right: 8px; padding: 2px; }
            #titleLabel { font-size: 14px; font-weight: bold; color: #54a0ff; padding: 8px; }
            #headerContainer { background: transparent; padding: 10px 15px; margin: 0; border: none; }
            #exportContainer, #iaQueryContainer, #iaResponseContainer { background-color: #2d3436; border: 2px solid #4b5468; border-radius: 12px; margin-top: 10px; padding: 12px; border-top: none; }
            QLineEdit { background-color: #353b48; border: 2px solid #4b5468; border-radius: 12px; padding: 8px; font-size: 13px; color: #dfe6e9; border-top: none; }
            QLineEdit:hover { background-color: #3b434f; border: 2px solid #74b9ff; }
            QLabel#iaModelLabel { font-size: 10px; color: #868e96; padding: 0 12px; margin-top: -5px; }
        """

        self.setStyleSheet(self.light_theme)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        header_container = QWidget()
        header_container.setObjectName("headerContainer")
        header_layout = QHBoxLayout()
        header_container.setLayout(header_layout)
        header_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel("🎙️ STTVAR")
        title_label.setObjectName("titleLabel")
        title_label.setFixedHeight(30)
        title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.back_button = QPushButton("🔙")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back_to_transcription)
        header_layout.addWidget(self.back_button)

        self.theme_button = QPushButton("☀")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_button)

        main_layout.addWidget(header_container)

        layout = QHBoxLayout()
        main_layout.addLayout(layout)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(left_layout, 3)

        self.textbox = QTextEdit()
        self.textbox.setPlaceholderText("Selecciona un archivo para editarlo...")
        self.textbox.textChanged.connect(self.check_text_changes)
        left_layout.addWidget(self.textbox)

        edit_buttons_layout = QHBoxLayout()
        edit_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.undo_button = QPushButton("↶ Deshacer")
        self.undo_button.setObjectName("undoButton")
        self.undo_button.clicked.connect(self.textbox.undo)
        self.undo_button.setEnabled(False)
        self.redo_button = QPushButton("↷ Rehacer")
        self.redo_button.setObjectName("redoButton")
        self.redo_button.clicked.connect(self.textbox.redo)
        self.redo_button.setEnabled(False)
        edit_buttons_layout.addWidget(self.undo_button)
        edit_buttons_layout.addWidget(self.redo_button)
        edit_buttons_layout.addStretch()
        left_layout.addLayout(edit_buttons_layout)

        self.textbox.undoAvailable.connect(self.undo_button.setEnabled)
        self.textbox.redoAvailable.connect(self.redo_button.setEnabled)

        ia_response_container = QWidget()
        ia_response_container.setObjectName("iaResponseContainer")
        ia_response_layout = QVBoxLayout()
        ia_response_container.setLayout(ia_response_layout)
        ia_response_layout.setContentsMargins(0, 0, 0, 0)

        self.ia_response_box = QTextEdit()
        self.ia_response_box.setReadOnly(True)
        self.ia_response_box.setPlaceholderText("Respuesta de IA aparecerá aquí...")
        self.ia_response_box.hide()
        ia_response_layout.addWidget(self.ia_response_box)

        translate_container = QWidget()
        translate_layout = QHBoxLayout()
        translate_container.setLayout(translate_layout)

        translate_layout.addWidget(QLabel("🈯 Traducir a:"))
        self.translate_combo = QComboBox()
        self.translate_combo.setObjectName("translateCombo")
        self.translate_combo.addItems(["Español (es)", "Inglés (en)", "Portugués (pt)"])
        self.translate_combo.currentIndexChanged.connect(self.handle_translation)
        translate_layout.addWidget(self.translate_combo)

        self.tts_button = QPushButton("🔊")
        self.tts_button.setObjectName("ttsButton")
        self.tts_button.clicked.connect(self.toggle_text_to_speech)
        self.tts_button.hide()
        translate_layout.addWidget(self.tts_button)
        translate_layout.addStretch()

        translate_container.hide()
        ia_response_layout.addWidget(translate_container)

        self.translate_container = translate_container
        left_layout.addWidget(ia_response_container)

        self.save_button = QPushButton("💾 Guardar cambios")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.hide()
        left_layout.addWidget(self.save_button)

        export_container = QWidget()
        export_container.setObjectName("exportContainer")
        export_layout = QHBoxLayout()
        export_container.setLayout(export_layout)

        export_layout.addWidget(QLabel("Exportar a:"))

        self.export_combo = QComboBox()
        self.export_combo.addItems(["PDF", "Word (.docx)", "Markdown (.md)"])
        export_layout.addWidget(self.export_combo)

        self.download_button = QPushButton("📥 Descargar")
        self.download_button.clicked.connect(self.export_selected_format)
        export_layout.addWidget(self.download_button)

        export_layout.setSpacing(12)
        export_layout.setContentsMargins(10, 5, 10, 5)
        left_layout.addWidget(export_container)

        self.ia_query_container = QWidget()
        self.ia_query_container.setObjectName("iaQueryContainer")
        ia_query_layout = QHBoxLayout()
        self.ia_query_container.setLayout(ia_query_layout)

        ia_query_layout.addWidget(QLabel("💬 Preguntar a IA:"))
        self.ia_query_input = QLineEdit()
        self.ia_query_input.setPlaceholderText("Escribe tu consulta aquí...")
        ia_query_layout.addWidget(self.ia_query_input)
        self.ia_query_button = QPushButton("🤖 Enviar")
        self.ia_query_button.clicked.connect(self.handle_ia_query)
        ia_query_layout.addWidget(self.ia_query_button)
        ia_query_layout.setSpacing(12)
        ia_query_layout.setContentsMargins(10, 5, 10, 5)
        left_layout.addWidget(self.ia_query_container)

        self.ia_model_label = QLabel(f"Usando el modelo: {self.ollama_model_name}")
        self.ia_model_label.setObjectName("iaModelLabel")
        self.ia_model_label.setAlignment(Qt.AlignRight)
        left_layout.addWidget(self.ia_model_label)
        
        self.ia_query_container.setVisible(self.ollama_available)
        self.ia_model_label.setVisible(self.ollama_available)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar por nombre de archivo...")
        self.search_bar.textChanged.connect(self.load_file_list)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Ordenar: Nombre (A-Z)", "Nombre (Z-A)", "Fecha reciente", "Fecha antigua"])
        self.sort_combo.currentIndexChanged.connect(self.load_file_list)

        self.file_list = QTableWidget()
        self.file_list.setColumnCount(2)
        self.file_list.setHorizontalHeaderLabels(["Archivo", "Audio"])
        self.file_list.horizontalHeader().hide()
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_list.verticalHeader().setVisible(False)
        self.file_list.setSelectionMode(QTableWidget.SingleSelection)
        self.file_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list.cellClicked.connect(self.load_file_content)
        self.file_list.cellDoubleClicked.connect(self.rename_file)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.file_list.setMinimumHeight(300)
        self.file_list.setShowGrid(False)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        right_container = QVBoxLayout()
        right_container.addWidget(self.search_bar)
        right_container.addWidget(self.sort_combo)
        right_container.addWidget(self.file_list)
        layout.addLayout(right_container, 1)

        self.load_file_list()
        self.installed_languages = translate.get_installed_languages()

    def _load_ollama_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.ollama_model_name = config.get('ollama_model', 'No configurado')
            else:
                self.ollama_model_name = 'phi3.5:latest'
        except (IOError, json.JSONDecodeError):
            self.ollama_model_name = 'Error al leer config'

        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200 and response.json().get("models"):
                self.ollama_available = True
            else:
                self.ollama_available = False
                self.ollama_model_name = "IA no disponible"
        except requests.exceptions.RequestException:
            self.ollama_available = False
            self.ollama_model_name = "IA no disponible"

    def initialize_tts_engine(self):
        try:
            if self.tts_engine:
                self.tts_engine.stop()
                self.tts_engine = None
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 170)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo inicializar el motor TTS: {e}")

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.setStyleSheet(self.dark_theme if self.is_dark_theme else self.light_theme)
        self.theme_button.setText("🌙" if self.is_dark_theme else "☀")
        self.file_list.setUpdatesEnabled(False)
        self.load_file_list()
        self.file_list.setUpdatesEnabled(True)

    def back_to_transcription(self):
        self.parent_transcription_window.show()
        self.close()

    def get_code_from_selection(self):
        text = self.translate_combo.currentText()
        if "(" in text and ")" in text:
            return text.split("(")[-1].replace(")", "").strip()
        return "es"

    def handle_translation(self):
        if not self.texto_original:
            self.ia_response_box.hide()
            self.tts_button.hide()
            self.translate_container.hide()
            return

        idioma_destino = self.get_code_from_selection()
        idioma_origen = "es"

        if idioma_destino == idioma_origen:
            self.ia_response_box.setPlainText(self.texto_original)
            self.ia_response_box.show()
            self.tts_button.show()
            self.translate_container.show()
            return

        self.ia_response_box.setPlainText("Traduciendo, por favor espera...")
        self.ia_response_box.show()
        self.tts_button.hide()
        self.translate_container.show()
        QApplication.processEvents()

        self.translation_worker = TranslationWorker(self.texto_original, idioma_origen, idioma_destino, self.installed_languages)
        self.translation_worker.result_signal.connect(self.handle_translation_result)
        self.translation_worker.error_signal.connect(self.handle_translation_error)
        self.translation_worker.start()

    def handle_translation_result(self, translated_text):
        self.ia_response_box.setPlainText(translated_text)
        self.ia_response_box.show()
        self.tts_button.show()
        self.translate_container.show()
        self.stop_text_to_speech()
        self.is_reading = False
        self.tts_button.setText("🔊")
        self.translation_worker = None

    def handle_translation_error(self, error):
        self.ia_response_box.setPlainText(error)
        self.ia_response_box.show()
        self.tts_button.hide()
        self.translate_container.hide()
        self.stop_text_to_speech()
        self.is_reading = False
        self.tts_button.setText("🔊")
        self.translation_worker = None

    def load_file_list(self):
        self.file_list.clearContents()
        self.file_list.setRowCount(0)
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        files = [f for f in os.listdir(self.folder_path) if f.endswith(".txt")]

        search_term = self.search_bar.text().lower()
        if search_term:
            files = [f for f in files if search_term in f.lower()]

        sort_option = self.sort_combo.currentText()
        if "Nombre (A-Z)" in sort_option:
            files.sort()
        elif "Nombre (Z-A)" in sort_option:
            files.sort(reverse=True)
        elif "Fecha reciente" in sort_option or "Fecha antigua" in sort_option:
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(self.folder_path, f)),
                reverse="Fecha reciente" in sort_option
            )

        self.file_list.setRowCount(len(files))
        for row, filename in enumerate(files):
            self.file_list.setRowHeight(row, 40)
            text_item = QTableWidgetItem(filename)
            text_item.setData(Qt.UserRole, filename)
            text_item.setFlags(text_item.flags() & ~Qt.ItemIsEditable)
            text_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.file_list.setItem(row, 0, text_item)

            base_name = os.path.splitext(filename)[0]
            audio_path = os.path.join(self.audio_folder_path, f"{base_name}.wav")
            has_audio = os.path.exists(audio_path)

            speaker_button = QPushButton("🔊" if has_audio else "🔇")
            speaker_button.setObjectName("speakerButton")
            speaker_button.setEnabled(has_audio)
            speaker_button.setFixedSize(32, 32)
            speaker_button.setStyleSheet("margin: 4px;")
            if has_audio:
                speaker_button.clicked.connect(lambda checked, f=audio_path: self.toggle_audio_playback(f))
            self.file_list.setCellWidget(row, 1, speaker_button)

        if not files:
            self.file_list.setRowCount(1)
            self.file_list.setRowHeight(0, 40)
            text_item = QTableWidgetItem("⚠️ No se encontraron archivos.")
            text_item.setFlags(text_item.flags() & ~Qt.ItemIsEditable)
            text_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.file_list.setItem(0, 0, text_item)

        self.file_list.setColumnWidth(1, 40)
        self.file_list.resizeColumnsToContents()

    def toggle_audio_playback(self, audio_file):
        if self.audio_player.state() == QMediaPlayer.PlayingState and self.current_audio_file == audio_file:
            self.audio_player.pause()
        else:
            self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file)))
            self.current_audio_file = audio_file
            self.audio_player.play()

    def handle_audio_state_changed(self, state):
        for row in range(self.file_list.rowCount()):
            item = self.file_list.item(row, 0)
            if item:
                filename = item.data(Qt.UserRole)
                if filename and filename != "⚠️ No se encontraron archivos.":
                    base_name = os.path.splitext(filename)[0]
                    audio_path = os.path.join(self.audio_folder_path, f"{base_name}.wav")
                    if audio_path == self.current_audio_file:
                        speaker_button = self.file_list.cellWidget(row, 1)
                        if speaker_button:
                            speaker_button.setText("⏸" if state == QMediaPlayer.PlayingState else "🔊")

    def load_file_content(self, row, column):
        item = self.file_list.item(row, 0)
        if not item or item.text() == "⚠️ No se encontraron archivos.":
            return
        filename = item.data(Qt.UserRole)
        filepath = os.path.join(self.folder_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                self.textbox.setPlainText(content)
                self.original_text = content
                self.current_file = filepath
                self.highlighter = TextHighlighter(self.textbox.document(), self.original_text)
            self.ia_response_box.clear()
            self.ia_response_box.hide()
            self.tts_button.hide()
            self.translate_container.hide()
            self.ia_query_input.clear()
            self.translate_combo.setCurrentIndex(0)
            self.texto_original = ""
            self.stop_text_to_speech()
            self.audio_player.stop()
            self.current_audio_file = None
            self.save_button.hide()
            self.load_file_list()
        except Exception as e:
            self.textbox.setPlainText(f"⚠️ Error al leer el archivo: {e}")
            self.current_file = None
            self.original_text = ""
            self.ia_response_box.clear()
            self.ia_response_box.hide()
            self.tts_button.hide()
            self.translate_container.hide()
            self.ia_query_input.clear()
            self.texto_original = ""
            self.stop_text_to_speech()
            self.save_button.hide()
            self.highlighter = None

    def check_text_changes(self):
        if not self.current_file:
            self.save_button.hide()
            return
        current_text = self.textbox.toPlainText()
        if current_text != self.original_text:
            self.save_button.show()
        else:
            self.save_button.hide()

    def save_file(self):
        if not self.current_file:
            QMessageBox.warning(self, "Advertencia", "No hay archivo seleccionado para guardar.")
            return
        try:
            with open(self.current_file, "w", encoding="utf-8") as file:
                content = self.textbox.toPlainText()
                file.write(content)
                self.original_text = content
                self.highlighter = TextHighlighter(self.textbox.document(), self.original_text)
            self.save_button.hide()
            QMessageBox.information(self, "Éxito", f"Archivo guardado correctamente en: {os.path.basename(self.current_file)}")
        except PermissionError:
            QMessageBox.critical(self, "Error", f"No tienes permisos para guardar en: {self.current_file}.")
        except IOError as e:
            QMessageBox.critical(self, "Error", f"Error de E/S al guardar el archivo: {e}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")

    def export_selected_format(self):
        if not self.current_file:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar un archivo para exportar.")
            return
        format_selected = self.export_combo.currentText()
        if "PDF" in format_selected: self.export_to_pdf()
        elif "Word" in format_selected: self.export_to_word()
        elif "Markdown" in format_selected: self.export_to_markdown()

    def export_to_pdf(self):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            export_path, _ = QFileDialog.getSaveFileName(self, "Guardar como PDF", self.current_file.replace(".txt", ".pdf"), "Archivos PDF (*.pdf)")
            if not export_path: return
            text = self.textbox.toPlainText()
            c = canvas.Canvas(export_path, pagesize=letter)
            width, height = letter
            y = height - 40
            for line in text.splitlines():
                c.drawString(40, y, line[:100])
                y -= 15
                if y < 40: c.showPage(); y = height - 40
            c.save()
            QMessageBox.information(self, "Éxito", f"Archivo exportado a PDF:\n{export_path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF:\n{e}")

    def export_to_word(self):
        try:
            from docx import Document
            export_path, _ = QFileDialog.getSaveFileName(self, "Guardar como Word", self.current_file.replace(".txt", ".docx"), "Documentos Word (*.docx)")
            if not export_path: return
            text = self.textbox.toPlainText()
            doc = Document()
            for line in text.splitlines(): doc.add_paragraph(line)
            doc.save(export_path)
            QMessageBox.information(self, "Éxito", f"Archivo exportado a Word:\n{export_path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a Word:\n{e}")

    def export_to_markdown(self):
        export_path, _ = QFileDialog.getSaveFileName(self, "Guardar como Markdown", self.current_file.replace(".txt", ".md"), "Archivos Markdown (*.md)")
        if not export_path: return
        try:
            text = self.textbox.toPlainText()
            with open(export_path, "w", encoding="utf-8") as f: f.write(text)
            QMessageBox.information(self, "Éxito", f"Archivo exportado a Markdown:\n{export_path}")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo exportar a Markdown:\n{e}")

    def rename_file(self, row, column):
        item = self.file_list.item(row, 0)
        if not item or item.text() == "⚠️ No se encontraron archivos.": return
        old_name = item.data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, "Renombrar archivo", "Nuevo nombre:", text=old_name)
        if ok and new_name:
            if not new_name.endswith(".txt"): new_name += ".txt"
            old_path = os.path.join(self.folder_path, old_name)
            new_path = os.path.join(self.folder_path, new_name)
            if os.path.exists(new_path): QMessageBox.warning(self, "Error", "Ya existe un archivo con ese nombre."); return
            try:
                os.rename(old_path, new_path)
                old_audio_path = os.path.join(self.audio_folder_path, os.path.splitext(old_name)[0] + ".wav")
                new_audio_path = os.path.join(self.audio_folder_path, os.path.splitext(new_name)[0] + ".wav")
                if os.path.exists(old_audio_path): os.rename(old_audio_path, new_audio_path)
                self.load_file_list()
                if self.current_file == old_path: self.current_file = new_path
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo renombrar el archivo:\n{e}")

    def show_context_menu(self, position: QPoint):
        item = self.file_list.itemAt(position)
        if not item or item.text() == "⚠️ No se encontraron archivos.": return
        menu = QMenu()
        rename_action = menu.addAction("Renombrar archivo")
        delete_action = menu.addAction("Eliminar archivo")
        view_location_action = menu.addAction("Ver ubicación del archivo")
        action = menu.exec_(self.file_list.viewport().mapToGlobal(position))
        if action == rename_action: self.rename_file(self.file_list.row(item), 0)
        elif action == delete_action: self.delete_file(item)
        elif action == view_location_action: self.open_file_location(item)

    def open_file_location(self, item: QTableWidgetItem):
        filename = item.data(Qt.UserRole)
        if filename and filename != "⚠️ No se encontraron archivos.":
            filepath = os.path.join(self.folder_path, filename)
            if os.path.exists(filepath):
                try: subprocess.Popen(['explorer.exe', '/select,', filepath])
                except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir la ubicación: {e}")
            else: QMessageBox.warning(self, "Advertencia", "El archivo no existe.")

    def delete_file(self, item: QTableWidgetItem):
        filename = item.data(Qt.UserRole)
        if filename == "⚠️ No se encontraron archivos.": return
        filepath = os.path.join(self.folder_path, filename)
        audio_path = os.path.join(self.audio_folder_path, os.path.splitext(filename)[0] + ".wav")
        reply = QMessageBox.question(self, "Confirmar eliminación", f"¿Estás seguro de que quieres eliminar:\n{filename}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if self.current_audio_file == audio_path: self.audio_player.stop(); self.current_audio_file = None
                os.remove(filepath)
                if os.path.exists(audio_path): os.remove(audio_path)
                if self.current_file == filepath:
                    self.current_file = None; self.textbox.clear(); self.original_text = ""
                    self.ia_response_box.clear(); self.ia_response_box.hide()
                    self.tts_button.hide(); self.translate_container.hide()
                    self.ia_query_input.clear(); self.texto_original = ""; self.stop_text_to_speech()
                    self.save_button.hide(); self.highlighter = None
                self.load_file_list()
                QMessageBox.information(self, "Éxito", f"'{filename}' y su audio asociado han sido eliminados.")
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo:\n{e}")

    def handle_ia_query(self):
        pregunta = self.ia_query_input.text().strip()
        if not pregunta: QMessageBox.warning(self, "Advertencia", "Debes escribir una pregunta."); return
        contenido = self.textbox.toPlainText().strip()
        if not contenido: QMessageBox.warning(self, "Advertencia", "No hay contexto para la IA."); return
        prompt = f"Eres un asistente que responde en español claro y concreto, usando el siguiente texto como referencia:\n\n{contenido}\n\nPregunta: {pregunta}\nRespuesta:"
        
        self.ia_query_button.setEnabled(False)
        self.ia_response_box.clear()
        self.ia_response_box.setPlaceholderText("Consultando a la IA, por favor espera...")
        self.ia_response_box.show()
        self.tts_button.hide()
        self.translate_container.show()
        QApplication.processEvents()

        self.worker = OllamaWorker(prompt, self.ollama_model_name)
        self.worker.chunk_received.connect(self.handle_ia_chunk)
        self.worker.finished.connect(self.handle_ia_finished)
        self.worker.error_signal.connect(self.handle_ia_error)
        self.worker.start()

    def handle_ia_chunk(self, chunk):
        self.ia_response_box.insertPlainText(chunk)
        self.ia_response_box.verticalScrollBar().setValue(self.ia_response_box.verticalScrollBar().maximum())

    def handle_ia_finished(self):
        self.ia_query_button.setEnabled(True)
        self.ia_query_input.clear()
        self.texto_original = self.ia_response_box.toPlainText()
        self.translate_combo.setCurrentIndex(0)
        self.tts_button.show()
        self.stop_text_to_speech()
        self.is_reading = False
        self.tts_button.setText("🔊")
        self.worker = None

    def handle_ia_error(self, error):
        self.ia_response_box.setPlainText(error)
        self.ia_query_button.setEnabled(True)
        self.tts_button.hide()
        self.worker = None

    def toggle_text_to_speech(self):
        text = self.ia_response_box.toPlainText().strip()
        if not text: QMessageBox.warning(self, "Advertencia", "No hay texto para leer."); return
        try:
            if self.is_reading:
                self.stop_text_to_speech()
                self.is_reading = False
                self.tts_button.setText("🔊")
            else:
                self.stop_text_to_speech()
                self.initialize_tts_engine()
                self.is_reading = True
                self.tts_button.setText("⏸")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.is_reading = False
                self.tts_button.setText("🔊")
        except Exception as e:
            self.stop_text_to_speech()
            self.is_reading = False
            self.tts_button.setText("🔊")
            QMessageBox.critical(self, "Error", f"Error al reproducir el texto: {e}")
            self.initialize_tts_engine()

    def stop_text_to_speech(self):
        try:
            if self.tts_engine: self.tts_engine.stop()
        except Exception: pass

    def closeEvent(self, event):
        self.stop_text_to_speech()
        self.audio_player.stop()
        if self.parent_transcription_window: self.parent_transcription_window.show()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    class MockParent:
        def show(self): print("Volviendo a la ventana de transcripción (simulado)")
    window = NuevaVentana(MockParent())
    window.show()
    sys.exit(app.exec_())