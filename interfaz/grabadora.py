from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
import sounddevice as sd
from transcripcion.transcriber import TranscriberThread
import os
from datetime import datetime

class TranscriptionWindow(QWidget):
    transcription_status_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎙 Transcriptor en Tiempo Real")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setMinimumSize(600, 100)
        self.resize(600, 150)

        self.transcriber_thread = None
        self.transcription_active = False
        self.current_transcription_filepath = None

        self._setup_ui()
        self._populate_devices()
        self._connect_signals()
        self._initialize_ui_state()

    def _setup_ui(self):
        self.device_label = QLabel("🎧 Dispositivo de entrada:")
        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Selecciona tu micrófono o dispositivo de entrada de audio.")
        self.device_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 3px;
                background-color: #ffffff;
                selection-background-color: #a8d9ff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #dcdcdc;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAECAYAAADgjg5zAAAAAXNSR0IArs4c6QAAADhJREFUCB1jfPD/PwM+QzAXhBjo3//f/3/C6YxNDIwMgw0MjAwMDAwMA8MgwMDAoJABcDAxMBkYGAAAB3sN6/wH7wAAAABJRU5ErkJggg==);
            }
            QComboBox:hover {
                border: 1px solid #a8d9ff;
            }
        """)

        self.mute_button = QPushButton("🎙️")
        self.mute_button.setCheckable(True)
        self.mute_button.setToolTip("Micrófono activo. Haz clic para silenciar.")
        self.mute_button.setCursor(Qt.PointingHandCursor)
        self.mute_button.setFixedWidth(32)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #f44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)

        self.toggle_recording_button = QPushButton("🔴 Iniciar Grabación")
        self.toggle_recording_button.setToolTip("Haz clic para comenzar a grabar y transcribir.")
        self.toggle_recording_button.setCursor(Qt.PointingHandCursor)
        self.toggle_recording_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedWidth(32)
        self.settings_button.setToolTip("Configuración")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                border-radius: 5px;
                padding: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Transcribiendo... Habla ahora.")
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 15px;
                padding: 10px;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                color: #333;
                selection-background-color: #a8d9ff;
            }
        """)

        self.control_layout = QHBoxLayout()
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(10)
        self.control_layout.addWidget(self.device_label)
        self.control_layout.addWidget(self.device_combo, 1)
        self.control_layout.addWidget(self.mute_button)               # <-- agregado botón mute
        self.control_layout.addWidget(self.toggle_recording_button)
        self.control_layout.addWidget(self.settings_button)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addWidget(self.text_area)
        self.vertical_spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(self.vertical_spacer)
        self.setLayout(self.main_layout)

    def _connect_signals(self):
        self.toggle_recording_button.clicked.connect(self._toggle_recording)
        self.transcription_status_changed.connect(self._update_ui_for_transcription_status)
        self.settings_button.clicked.connect(self._open_new_window)
        self.mute_button.clicked.connect(self._toggle_mute)          # <-- conectar botón mute

    def _initialize_ui_state(self):
        self.device_label.setVisible(True)
        self.device_combo.setVisible(True)
        self.text_area.setVisible(False)
        self.setFixedHeight(self.sizeHint().height())

    def _populate_devices(self):
        try:
            self.devices = sd.query_devices()
            self.input_devices = [
                (i, d['name']) for i, d in enumerate(self.devices)
                if d['max_input_channels'] > 0
            ]
            if not self.input_devices:
                self.device_combo.addItem("No se encontraron dispositivos de audio.")
                self.toggle_recording_button.setEnabled(False)
                QMessageBox.warning(self, "Sin dispositivos",
                                    "No se encontraron dispositivos de entrada de audio.")
                return

            for idx, name in self.input_devices:
                self.device_combo.addItem(f"{name}", idx)
            self.toggle_recording_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error de Audio", str(e))
            self.toggle_recording_button.setEnabled(False)

    def _toggle_recording(self):
        if self.transcription_active:
            self._stop_transcription()
        else:
            self._start_transcription()

    def _start_transcription(self):
        device_index = self.device_combo.currentData()
        if device_index is None:
            QMessageBox.warning(self, "Selección Requerida",
                                "Selecciona un dispositivo de entrada de audio.")
            return

        output_dir = "stt_guardados"
        os.makedirs(output_dir, exist_ok=True)
        self.current_transcription_filepath = datetime.now().strftime(f"{output_dir}/%Y-%m-%d_%H-%M-%S.txt")

        try:
            self.transcriber_thread = TranscriberThread(device_index, self.current_transcription_filepath)
            self.transcriber_thread.new_text.connect(self._update_text_area)
            self.transcriber_thread.finished.connect(self._on_transcription_finished)
            self.transcriber_thread.start()
            self.transcription_active = True
            self.transcription_status_changed.emit(True)
            self.text_area.setPlaceholderText("Transcribiendo... Habla ahora.")
            self.text_area.clear()

            # Asegurarse que mute esté sincronizado al iniciar
            self.transcriber_thread.set_mute(self.mute_button.isChecked())

        except Exception as e:
            QMessageBox.critical(self, "Error al Iniciar", str(e))
            self.transcription_active = False
            self.transcription_status_changed.emit(False)
            self.current_transcription_filepath = None

    def _stop_transcription(self):
        if self.transcriber_thread and self.transcriber_thread.isRunning():
            self.transcriber_thread.stop()
            self.transcriber_thread.wait()
            self.transcription_active = False
            self.transcription_status_changed.emit(False)
            self.text_area.setPlaceholderText("Grabación detenida. La transcripción se ha guardado.")
            self.prompt_save_or_discard()
        else:
            self.transcription_active = False
            self.transcription_status_changed.emit(False)
            self.text_area.setPlaceholderText("Haz clic en 'Iniciar Grabación' para comenzar.")

    def _toggle_mute(self):
        muted = self.mute_button.isChecked()
        if muted:
            self.mute_button.setToolTip("Micrófono silenciado. Haz clic para activar.")
            self.mute_button.setText("🔇")
        else:
            self.mute_button.setToolTip("Micrófono activo. Haz clic para silenciar.")
            self.mute_button.setText("🎙️")

        if self.transcriber_thread and self.transcriber_thread.isRunning():
            self.transcriber_thread.set_mute(muted)

    def _update_ui_for_transcription_status(self, active: bool):
        self.device_label.setVisible(not active)
        self.device_combo.setVisible(not active)
        self.text_area.setVisible(active)

        if active:
            self.main_layout.removeItem(self.vertical_spacer)
            self.text_area.setFixedHeight(100)
            self.setMinimumHeight(200)
            self.resize(self.width(), 250)
        else:
            self.main_layout.addItem(self.vertical_spacer)
            self.text_area.setFixedHeight(0)
            self.setMinimumHeight(100)
            self.resize(self.width(), self.sizeHint().height())

        if active:
            self.toggle_recording_button.setText("■ Detener Grabación")
            self.toggle_recording_button.setToolTip("Haz clic para detener.")
            self.toggle_recording_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
        else:
            self.toggle_recording_button.setText("🔴 Iniciar Grabación")
            self.toggle_recording_button.setToolTip("Haz clic para grabar.")
            self.toggle_recording_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)

    def _update_text_area(self, text: str):
        self.text_area.setPlainText(text)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

    def _on_transcription_finished(self):
        if self.transcription_active:
            self.transcription_active = False
            self.transcription_status_changed.emit(False)
            self.text_area.setPlaceholderText("Grabación finalizada inesperadamente.")
            self.prompt_save_or_discard()

    def prompt_save_or_discard(self):
        if self.current_transcription_filepath and os.path.exists(self.current_transcription_filepath):
            reply = QMessageBox.question(self, "Guardar Transcripción",
                                         "¿Deseas guardar la transcripción?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                try:
                    os.remove(self.current_transcription_filepath)
                except OSError as e:
                    QMessageBox.warning(self, "Error al eliminar", str(e))
        self.current_transcription_filepath = None
        self.transcriber_thread = None

    def _open_new_window(self):
        from interfaz.menu import NuevaVentana
        self.new_window = NuevaVentana()
        self.new_window.show()
        self.close()  # Cierra la ventana actual


    def closeEvent(self, event):
        if self.transcriber_thread and self.transcriber_thread.isRunning():
            reply = QMessageBox.question(self, "Transcripción Activa",
                                         "¿Detener y cerrar?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._stop_transcription()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
