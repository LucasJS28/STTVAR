# configuraciones.py

import sys
import os
import json
import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QMessageBox, QApplication, QSpacerItem, QSizePolicy, QFrame,
    QGraphicsDropShadowEffect, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

# URL de la API de Ollama para obtener los modelos locales
OLLAMA_API_TAGS_URL = "http://localhost:11434/api/tags"

class ConfiguracionIA(QWidget):
    # Señal para notificar a la ventana principal que la configuración se ha guardado
    config_saved = pyqtSignal()

    def __init__(self, parent=None, config_file='config.json'):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.config_file = config_file
        self.current_config = self._load_current_config()
        self.old_pos = None

        self._setup_ui()
        self._connect_signals()
        
        QTimer.singleShot(50, self.load_models_async)

        self.show()
        self.center_on_screen()

    def _setup_ui(self):
        """Configura la interfaz gráfica completa."""
        self.setMinimumWidth(580)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))

        self.background_widget = QFrame(self)
        self.background_widget.setObjectName("backgroundWidget")
        self.background_widget.setGraphicsEffect(shadow)
        
        self.setStyleSheet("""
            #backgroundWidget {
                background-color: #282c34;
                color: #abb2bf;
                border-radius: 12px;
                border: 1px solid #3e4451;
            }
            QLabel {
                background-color: transparent;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #appTitleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #abb2bf;
                padding-left: 5px;
            }
            #titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #eceff4;
            }
            #descriptionLabel {
                font-size: 13px;
                padding-bottom: 10px;
                color: #eceff4;
            }
            QComboBox, QLineEdit {
                border: 1px solid #3e4451;
                border-radius: 5px;
                padding: 8px;
                background-color: #21252b;
                color: #e0e0e0;
                font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #21252b;
                color: #eceff4;
                selection-background-color: #61afef;
                selection-color: #ffffff;
                outline: 0px;
            }
            QPushButton {
                background-color: #61afef;
                color: #21252b;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7abfff; }
            QPushButton:disabled { background-color: #4a505c; color: #7f848e; }
            #closeButton {
                font-family: 'Arial';
                font-size: 16px;
                font-weight: bold;
                color: #abb2bf;
                background-color: transparent;
                border: none;
                padding: 0px 8px 3px 8px;
                border-radius: 5px;
            }
            #closeButton:hover {
                background-color: #e06c75;
                color: #ffffff;
            }
            #statusLabel { 
                font-size: 12px; 
                color: #9098a5;
                font-style: italic;
            }
            #statusLabel.error { 
                color: #e06c75;
                font-style: normal;
            }
            #browseButton {
                padding: 8px 15px;
            }
            #restoreButton {
                background-color: #4a505c;
                color: #abb2bf;
                padding: 10px 15px;
                font-weight: normal;
            }
            #restoreButton:hover {
                background-color: #565c68;
            }
        """)

        bg_layout = QVBoxLayout(self.background_widget)
        bg_layout.setContentsMargins(0, 0, 0, 15)
        bg_layout.setSpacing(10)

        # --- Barra de Título Personalizada ---
        self.title_bar = QFrame()
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 5, 5, 5)
        app_title_label = QLabel("STTVAR")
        app_title_label.setObjectName("appTitleLabel")
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setFixedSize(30, 30)
        title_bar_layout.addWidget(app_title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_button)
        bg_layout.addWidget(self.title_bar)
        
        # --- Contenido principal ---
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(25, 10, 25, 0)
        content_layout.setSpacing(10)

        # --- SECCIÓN MODELO IA ---
        title_icon = QLabel("🧠")
        title_icon.setStyleSheet("font-size: 22px; margin-top: -4px;")
        title_label = QLabel("Configuración del Modelo de IA")
        title_label.setObjectName("titleLabel")
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_icon, 0, Qt.AlignTop)
        title_layout.addWidget(title_label, 0, Qt.AlignVCenter)
        title_layout.addStretch()
        content_layout.addLayout(title_layout)
        description_label = QLabel("Selecciona el modelo de Ollama que la aplicación utilizará para las funciones de IA.")
        description_label.setObjectName("descriptionLabel")
        description_label.setWordWrap(True)
        content_layout.addWidget(description_label)
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Modelos de IA instalados en tu Ollama local.")
        self.model_combo.addItem("Buscando modelos...")
        self.model_combo.setEnabled(False)
        content_layout.addWidget(self.model_combo)
        content_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- SECCIÓN: RUTA DE TRANSCRIPCIONES ---
        path_icon_txt = QLabel("📝")
        path_icon_txt.setStyleSheet("font-size: 22px; margin-top: -4px;")
        path_title_txt = QLabel("Carpeta de Transcripciones (.txt)")
        path_title_txt.setObjectName("titleLabel")
        path_layout_txt = QHBoxLayout()
        path_layout_txt.addWidget(path_icon_txt, 0, Qt.AlignTop)
        path_layout_txt.addWidget(path_title_txt, 0, Qt.AlignVCenter)
        path_layout_txt.addStretch()
        content_layout.addLayout(path_layout_txt)
        
        path_edit_layout_txt = QHBoxLayout()
        self.path_edit_txt = QLineEdit()
        self.path_edit_txt.setReadOnly(True)
        self.path_edit_txt.setText(self.current_config.get('transcript_path', 'stt_guardados'))
        self.browse_button_txt = QPushButton("Examinar...")
        self.browse_button_txt.setObjectName("browseButton")
        path_edit_layout_txt.addWidget(self.path_edit_txt)
        path_edit_layout_txt.addWidget(self.browse_button_txt)
        content_layout.addLayout(path_edit_layout_txt)
        content_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- SECCIÓN: RUTA DE AUDIOS ---
        path_icon_audio = QLabel("🔊")
        path_icon_audio.setStyleSheet("font-size: 22px; margin-top: -4px;")
        path_title_audio = QLabel("Carpeta de Audios (.wav)")
        path_title_audio.setObjectName("titleLabel")
        path_layout_audio = QHBoxLayout()
        path_layout_audio.addWidget(path_icon_audio, 0, Qt.AlignTop)
        path_layout_audio.addWidget(path_title_audio, 0, Qt.AlignVCenter)
        path_layout_audio.addStretch()
        content_layout.addLayout(path_layout_audio)

        path_edit_layout_audio = QHBoxLayout()
        self.path_edit_audio = QLineEdit()
        self.path_edit_audio.setReadOnly(True)
        self.path_edit_audio.setText(self.current_config.get('audio_path', 'sttaudio_guardados'))
        self.browse_button_audio = QPushButton("Examinar...")
        self.browse_button_audio.setObjectName("browseButton")
        path_edit_layout_audio.addWidget(self.path_edit_audio)
        path_edit_layout_audio.addWidget(self.browse_button_audio)
        content_layout.addLayout(path_edit_layout_audio)
        content_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- PIE DE PÁGINA ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border-top: 1px solid #3e4451;")
        content_layout.addWidget(line)
        
        footer_layout = QHBoxLayout()
        self.restore_button = QPushButton("Restaurar")
        self.restore_button.setObjectName("restoreButton")
        self.restore_button.setCursor(Qt.PointingHandCursor)
        self.restore_button.setToolTip("Restaura las carpetas a sus valores por defecto.")
        
        self.status_label = QLabel("Contactando a Ollama...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        
        self.save_button = QPushButton("✔️ Guardar")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setEnabled(False)
        
        footer_layout.addWidget(self.restore_button)
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_button)
        content_layout.addLayout(footer_layout)
        
        bg_layout.addWidget(content_frame)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.background_widget)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def _connect_signals(self):
        self.save_button.clicked.connect(self._save_config)
        self.close_button.clicked.connect(self.close)
        self.browse_button_txt.clicked.connect(lambda: self._browse_for_folder("txt"))
        self.browse_button_audio.clicked.connect(lambda: self._browse_for_folder("audio"))
        self.restore_button.clicked.connect(self._restore_defaults)

    def _browse_for_folder(self, folder_type):
        if folder_type == "txt":
            current_path = self.path_edit_txt.text()
            title = "Seleccionar Carpeta para Transcripciones"
            directory = QFileDialog.getExistingDirectory(self, title, current_path)
            if directory:
                self.path_edit_txt.setText(directory)
        elif folder_type == "audio":
            current_path = self.path_edit_audio.text()
            title = "Seleccionar Carpeta para Audios"
            directory = QFileDialog.getExistingDirectory(self, title, current_path)
            if directory:
                self.path_edit_audio.setText(directory)
        
        self.save_button.setEnabled(True)

    def _restore_defaults(self):
        """Restaura los campos de las rutas a sus valores predeterminados."""
        default_transcript_path = 'stt_guardados'
        default_audio_path = 'sttaudio_guardados'

        self.path_edit_txt.setText(default_transcript_path)
        self.path_edit_audio.setText(default_audio_path)

        self.save_button.setEnabled(True)
        self.status_label.setText("Rutas restauradas. Haz clic en Guardar para aplicar.")
        self.status_label.setProperty("class", "")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def load_models_async(self):
        self.model_combo.clear()
        current_model_name = self.current_config.get('ollama_model', '')
        try:
            response = requests.get(OLLAMA_API_TAGS_URL, timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if not models:
                    self.status_label.setText("Ollama funciona, pero no hay modelos instalados.")
                    self.status_label.setProperty("class", "error")
                    self.model_combo.addItem("Instala un modelo con 'ollama pull <nombre>'")
                    self.model_combo.setEnabled(False)
                else:
                    self.status_label.setText("Configuración cargada. Puedes guardar los cambios.")
                    self.status_label.setProperty("class", "")
                    for model in models:
                        self.model_combo.addItem(model["name"])
                    
                    if current_model_name and (index := self.model_combo.findText(current_model_name)) != -1:
                        self.model_combo.setCurrentIndex(index)
                    
                    self.model_combo.setEnabled(True)
                self.save_button.setEnabled(True)
            else:
                raise requests.exceptions.RequestException(f"Error de la API: {response.status_code}")
        
        except requests.exceptions.RequestException:
            self.status_label.setText("Asegúrate de que Ollama esté ejecutándose.")
            self.status_label.setProperty("class", "error")
            self.model_combo.addItem("Verifica que Ollama esté en ejecución.")
            self.model_combo.setEnabled(False)
            self.save_button.setEnabled(False)

        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _load_current_config(self):
        defaults = {
            'ollama_model': 'phi3:latest',
            'transcript_path': 'stt_guardados',
            'audio_path': 'sttaudio_guardados'
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    defaults.update(config)
        except (IOError, json.JSONDecodeError):
            pass
        return defaults

    def _save_config(self):
        config_data = self._load_current_config()
        
        config_data['ollama_model'] = self.model_combo.currentText()
        config_data['transcript_path'] = self.path_edit_txt.text()
        config_data['audio_path'] = self.path_edit_audio.text()

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.status_label.setText("¡Configuración guardada!")
            self.status_label.setProperty("class", "")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            self.config_saved.emit()
            QTimer.singleShot(1500, self.close)
        except IOError:
            QMessageBox.critical(self, "Error", "No se pudo escribir en el archivo de configuración.")

    def center_on_screen(self):
        """Centra la ventana en el medio de la pantalla."""
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            x = (rect.width() - self.width()) // 2
            y = (rect.height() - self.height()) // 2
            self.move(x, y)

# Bloque para probar la ventana de forma independiente
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConfiguracionIA()
    sys.exit(app.exec_())