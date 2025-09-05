import sys
import time
import subprocess
import os
import argostranslate.translate
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from transcripcion.vosk_utils import cargar_modelo
from .grabadora import TranscriptionWindow
from .terminos import TermsAndConditionsDialog  # Importar la ventana de términos


class DraggableDialog(QDialog):
    """QDialog personalizado que se puede arrastrar."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dragging = False
        self._drag_position = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()


class ModelLoaderThread(QThread):
    progress = pyqtSignal(str, int)  # Señal para actualizar el texto y la barra de progreso
    error = pyqtSignal(str)  # Señal para errores
    finished = pyqtSignal()  # Señal para indicar que la carga terminó

    def __init__(self, launcher):
        super().__init__(None)  # No pasar un parent, usar None
        self.launcher = launcher  # Almacenar referencia al objeto Launcher

    def run(self):
        try:
            # Cargar modelo de Vosk
            self.progress.emit("Cargando modelo de Vosk...", 33)
            self.launcher.model = cargar_modelo()

            # Iniciar Ollama
            self.progress.emit("Iniciando Ollama...", 66)
            self.launcher._start_ollama()

            # Cargar modelos de traducción
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
        dialog = DraggableDialog()  # 🔥 Ahora la ventana es arrastrable
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

        icon_label = QLabel("🎙️", dialog)
        icon_label.setStyleSheet("font-size: 48px; color: #e74c3c; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(15)
        icon_shadow.setColor(Qt.black)
        icon_shadow.setOffset(3, 3)
        icon_label.setGraphicsEffect(icon_shadow)

        text_label = QLabel("STTVAR", dialog)
        text_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #dddddd; background: transparent;")
        text_label.setAlignment(Qt.AlignCenter)
        text_shadow = QGraphicsDropShadowEffect()
        text_shadow.setBlurRadius(10)
        text_shadow.setColor(Qt.black)
        text_shadow.setOffset(2, 2)
        text_label.setGraphicsEffect(text_shadow)

        self.loading_label = QLabel("Cargando modelos...", dialog)
        self.loading_label.setStyleSheet("font-size: 14px; color: #bbbbbb; background: transparent;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        loading_shadow = QGraphicsDropShadowEffect()
        loading_shadow.setBlurRadius(8)
        loading_shadow.setColor(Qt.black)
        loading_shadow.setOffset(1, 1)
        self.loading_label.setGraphicsEffect(loading_shadow)

        self.progress_bar = QProgressBar(dialog)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #c0392b;
                border-radius: 5px;
                text-align: center;
                background: #4a4a4a;
                color: #dddddd;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)

        dialog.setLayout(layout)
        dialog.setMinimumSize(250, 200)
        dialog.setMaximumSize(300, 250)

        self.dialog = dialog

    def _start_ollama(self):
        """Inicia el proceso de Ollama en segundo plano."""
        ruta_ollama = r"C:\Users\LucasJs28\AppData\Local\Programs\Ollama\ollama.exe"
        if not os.path.exists(ruta_ollama):
            raise Exception("No se encontró el ejecutable de Ollama.")

        try:
            self.ollama_process = subprocess.Popen(
                [ruta_ollama, 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            time.sleep(3)  # Esperar a que el servidor esté activo
            return True
        except Exception as e:
            raise Exception(f"Error al iniciar Ollama: {str(e)}")

    def _load_translation_models(self):
        """Precarga los modelos de traducción de Argos Translate."""
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

        # Iniciar la carga asíncrona
        self.loader_thread = ModelLoaderThread(self)
        self.loader_thread.progress.connect(self.update_progress)
        self.loader_thread.error.connect(self.handle_error)
        self.loader_thread.finished.connect(self._on_loading_finished)
        self.loader_thread.start()

    def update_progress(self, text, value):
        """Actualiza el texto y el valor de la barra de progreso."""
        self.loading_label.setText(text)
        self.progress_bar.setValue(value)
        self.app.processEvents()

    def handle_error(self, error_message):
        """Maneja errores durante la carga."""
        self.dialog.close()
        if self.ollama_process:
            self.ollama_process.terminate()
        QMessageBox.critical(None, "Error", f"No se pudo cargar los modelos: {str(error_message)}")
        sys.exit(1)

    def _on_loading_finished(self):
        """Se ejecuta cuando la carga termina."""
        self.dialog.close()

        # Mostrar ventana de términos y condiciones
        terms_dialog = TermsAndConditionsDialog()
        if terms_dialog.exec_() == QDialog.Accepted:
            # Si el usuario acepta, abrir la ventana principal
            self.open_main_window()
        else:
            # Si el usuario no acepta, cerrar la aplicación
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
