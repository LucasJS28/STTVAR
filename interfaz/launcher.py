import sys
import time
import subprocess
import os
import argostranslate.translate
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QMessageBox, QProgressBar,
    QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor
from transcripcion.vosk_utils import cargar_modelo
from .grabadora import TranscriptionWindow
from .terminos import TermsAndConditionsDialog


class DraggableDialog(QDialog):
    """QDialog personalizado que se puede arrastrar."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() & Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None


class ModelLoaderThread(QThread):
    progress = pyqtSignal(str, int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, launcher):
        super().__init__(None)
        self.launcher = launcher

    def run(self):
        try:
            self.progress.emit("Cargando modelo de Vosk...", 33)
            self.launcher.model = cargar_modelo()

            self.progress.emit("Iniciando Ollama...", 66)
            self.launcher._start_ollama()

            self.progress.emit("Cargando modelos de traducción...", 100)
            self.launcher._load_translation_models()

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class Launcher:
    def __init__(self, app):
        self.app = app
        self.model = None
        self.ollama_process = None
        self.main_window = None
        self.dialog = None

    def create_loading_dialog(self):
        dialog = DraggableDialog()
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground) # Importante para la sombra
        dialog.setFixedSize(400, 280)

        # Contenedor principal para aplicar sombra y bordes
        container = QWidget(dialog)
        container.setObjectName("containerWidget")
        
        # Sombra sutil para un efecto elevado
        shadow = QGraphicsDropShadowEffect(dialog)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 180))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        icon_label = QLabel("🎙️", container)
        icon_label.setObjectName("iconLabel")
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("STTVAR", container)
        text_label.setObjectName("titleLabel")
        text_label.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel("Iniciando...", container)
        self.loading_label.setObjectName("statusLabel")
        self.loading_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar(container)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setTextVisible(False) # Ocultamos el texto por defecto
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # --- NUEVO: Animación para la barra de progreso ---
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(400) # Duración de la animación en ms
        self.progress_animation.setEasingCurve(QEasingCurve.InOutCubic)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addSpacing(10)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)

        # Layout principal para el diálogo (necesario para la sombra)
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(container)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self._apply_styles(dialog)
        self.dialog = dialog

    def _apply_styles(self, dialog):
        dialog.setStyleSheet("""
            #containerWidget {
                background-color: #2c2c2c;
                border-radius: 22px;
                border: 2px solid #E74C3C;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #iconLabel {
                font-size: 48px;
                background: transparent;
            }
            #titleLabel {
                color: #f0f0f0;
                font-size: 28px;
                font-weight: 600;
                background: transparent;
            }
            #statusLabel {
                color: #a0a0a0;
                font-size: 14px;
                background: transparent;
            }
            #progressBar {
                border: 1px solid #4a4a4a;
                border-radius: 9px;
                background-color: #212121;
                height: 18px; /* Altura fija para un mejor look */
            }
            #progressBar::chunk {
                background-color: #E74C3C;
                border-radius: 8px;
            }
        """)

    def _start_ollama(self):
        ruta_ollama = r"C:\Users\LucasJs28\AppData\Local\Programs\Ollama\ollama.exe"
        if not os.path.exists(ruta_ollama):
            raise Exception("No se encontró el ejecutable de Ollama.")
        try:
            self.ollama_process = subprocess.Popen(
                [ruta_ollama, 'serve'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(3)
            return True
        except Exception as e:
            raise Exception(f"Error al iniciar Ollama: {str(e)}")

    def _load_translation_models(self):
        try:
            installed_languages = argostranslate.translate.get_installed_languages()
            language_codes = ["es", "en", "pt"]
            for from_code in language_codes:
                for to_code in language_codes:
                    if from_code != to_code:
                        from_lang = next((lang for lang in installed_languages if lang.code == from_code), None)
                        to_lang = next((lang for lang in installed_languages if lang.code == to_code), None)
                        if from_lang and to_lang:
                            from_lang.get_translation(to_lang)
        except Exception as e:
            raise Exception(f"Error al cargar modelos de traducción: {str(e)}")

    def start(self):
        self.create_loading_dialog()
        self.dialog.show()
        self.app.processEvents()

        self.loader_thread = ModelLoaderThread(self)
        self.loader_thread.progress.connect(self.update_progress)
        self.loader_thread.error.connect(self.handle_error)
        self.loader_thread.finished.connect(self._on_loading_finished)
        self.loader_thread.start()

    def update_progress(self, text, value):
        self.loading_label.setText(text)
        # Inicia la animación hacia el nuevo valor
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()
        self.app.processEvents()

    def handle_error(self, error_message):
        self.dialog.close()
        if self.ollama_process:
            self.ollama_process.terminate()
        QMessageBox.critical(None, "Error", f"No se pudo cargar los modelos: {str(error_message)}")
        sys.exit(1)

    def _on_loading_finished(self):
        self.dialog.close()
        terms_dialog = TermsAndConditionsDialog()
        if terms_dialog.exec_() == QDialog.Accepted:
            self.open_main_window()
        else:
            if self.ollama_process:
                self.ollama_process.terminate()
            sys.exit(0)

    def open_main_window(self):
        self.main_window = TranscriptionWindow(self.model)
        self.main_window.show()

    def exec_(self):
        try:
            return self.app.exec_()
        finally:
            if self.ollama_process:
                self.ollama_process.terminate()