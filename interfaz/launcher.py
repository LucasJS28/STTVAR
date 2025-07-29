import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from transcripcion.vosk_utils import cargar_modelo
from .grabadora import TranscriptionWindow


class Launcher:
    def __init__(self, app):
        self.app = app
        self.model = None
        self.main_window = None
        self.dialog = None

    def create_loading_dialog(self):
        dialog = QDialog()
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2a2a2a, stop: 1 #4a4a4a
                );
                border: 2px solid #c0392b;
                border-radius: 15px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        # 🎙️ Ícono micrófono
        icon_label = QLabel("🎙️", dialog)
        icon_label.setStyleSheet("font-size: 48px; color: #e74c3c; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(15)
        icon_shadow.setColor(Qt.black)
        icon_shadow.setOffset(3, 3)
        icon_label.setGraphicsEffect(icon_shadow)

        # STTVAR texto
        text_label = QLabel("STTVAR", dialog)
        text_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #dddddd; background: transparent;")
        text_label.setAlignment(Qt.AlignCenter)
        text_shadow = QGraphicsDropShadowEffect()
        text_shadow.setBlurRadius(10)
        text_shadow.setColor(Qt.black)
        text_shadow.setOffset(2, 2)
        text_label.setGraphicsEffect(text_shadow)

        # Cargando...
        loading_label = QLabel("Cargando modelo...", dialog)
        loading_label.setStyleSheet("font-size: 14px; color: #bbbbbb; background: transparent;")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_shadow = QGraphicsDropShadowEffect()
        loading_shadow.setBlurRadius(8)
        loading_shadow.setColor(Qt.black)
        loading_shadow.setOffset(1, 1)
        loading_label.setGraphicsEffect(loading_shadow)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(loading_label)

        dialog.setLayout(layout)
        dialog.setMinimumSize(250, 200)
        dialog.setMaximumSize(300, 250)

        self.dialog = dialog

    def start(self):
        self.create_loading_dialog()
        self.dialog.show()
        self.app.processEvents()

        try:
            time.sleep(1)  # Simulación de carga
            self.model = cargar_modelo()
        except Exception as e:
            self.dialog.close()
            QMessageBox.critical(None, "Error", f"No se pudo cargar el modelo: {str(e)}")
            sys.exit(1)

        self.dialog.close()
        self.open_main_window()

    def open_main_window(self):
        self.main_window = TranscriptionWindow(self.model)
        self.main_window.show()

    def exec_(self):
        return self.app.exec_()
