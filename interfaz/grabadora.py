from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation
import sounddevice as sd
from transcripcion.transcriber import TranscriberThread
import os
from datetime import datetime
from interfaz.menu import NuevaVentana
import sys

class TranscriptionWindow(QWidget):
    transcription_status_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎙 Transcriptor en Tiempo Real")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMinimumSize(650, 110)
        self.resize(650, 110)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.transcriber_thread = None
        self.transcription_active = False
        self.current_transcription_filepath = None
        self.current_audio_filepath = None  # Nuevo atributo para el archivo de audio
        self._already_stopped = False  # Para evitar doble llamado

        self._setup_ui()
        self._populate_devices()
        self._connect_signals()
        self._initialize_ui_state()

        self.old_pos = None

        self._hide_button_timer = QTimer(self)
        self._hide_button_timer.setSingleShot(True)
        self._hide_button_timer.timeout.connect(self._fade_out_buttons)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def enterEvent(self, event):
        if self.transcription_active:
            self._hide_button_timer.stop()
            self._fade_in_buttons()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.transcription_active:
            self._hide_button_timer.start(300)
        super().leaveEvent(event)

    def _setup_ui(self):
        self.base_widget = QWidget(self)
        self.base_widget.setObjectName("baseWidget")
        self.base_widget.setMouseTracking(True)
        self.setMouseTracking(True)

        self.base_widget.setStyleSheet("""
            #baseWidget {
                background-color: rgba(30, 30, 30, 200);
                border: 1px solid rgba(70, 70, 70, 150);
                border-radius: 10px;
            }
        """)

        self.title_bar_layout = QHBoxLayout()
        self.title_bar_layout.setContentsMargins(10, 5, 5, 0)

        self.window_title_label = QLabel("🎙 STTVAR")
        self.window_title_label.setStyleSheet("color: #bbbbbb; font-size: 13px; font-weight: bold;")

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip("Cerrar")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #bbbbbb;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
                color: white;
            }
        """)
        self.close_button.clicked.connect(self.close)

        self.title_bar_layout.addWidget(self.window_title_label)
        self.title_bar_layout.addStretch()
        self.title_bar_layout.addWidget(self.close_button)

        self.device_label = QLabel("🎧 Dispositivo de entrada:")
        self.device_label.setStyleSheet("color: #bbbbbb; font-size: 13px;")

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Selecciona tu micrófono.")
        self.device_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #505050;
                border-radius: 5px;
                padding: 3px;
                background-color: #3a3a3a;
                color: #e0e0e0;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                selection-background-color: #557799;
            }
        """)

        self.toggle_recording_button = QPushButton("🔴 Iniciar Grabación")
        self.toggle_recording_button.setCursor(Qt.PointingHandCursor)
        self.toggle_recording_button.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a8322a;
            }
        """)

        self.mute_button = QPushButton("🎙️")
        self.mute_button.setCheckable(True)
        self.mute_button.setToolTip("Micrófono activo.")
        self.mute_button.setCursor(Qt.PointingHandCursor)
        self.mute_button.setFixedSize(36, 36)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 2px solid #666666;
                border-radius: 18px;
                color: #dddddd;
                font-size: 18px;
                padding: 0;
            }
            QPushButton:checked {
                background-color: #c0392b;
                border-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                border-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a8322a;
                border-color: #911f1a;
            }
        """)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(10)
        self.buttons_layout.addWidget(self.toggle_recording_button)
        self.buttons_layout.addWidget(self.mute_button)

        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                color: #dddddd;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Transcribiendo... Habla ahora.")
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0);
                font-family: 'Segoe UI';
                font-size: 18px;
                padding: 5px 10px;
                border: none;
                color: #f0f0f0;
            }
        """)

        self.control_layout = QHBoxLayout()
        self.control_layout.setContentsMargins(10, 5, 10, 5)
        self.control_layout.setSpacing(8)
        self.control_layout.addWidget(self.device_label)
        self.control_layout.addWidget(self.device_combo, 1)
        self.control_layout.addLayout(self.buttons_layout)
        self.control_layout.addWidget(self.settings_button)

        self.main_layout = QVBoxLayout(self.base_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.main_layout.addLayout(self.title_bar_layout)
        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addWidget(self.text_area)
        self.main_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.base_widget)

    def _connect_signals(self):
        self.toggle_recording_button.clicked.connect(self._toggle_recording)
        self.transcription_status_changed.connect(self._update_ui_for_transcription_status)
        self.settings_button.clicked.connect(self._open_settings_window)
        self.mute_button.clicked.connect(self._toggle_mute)

    def _initialize_ui_state(self):
        self.device_label.setVisible(True)
        self.device_combo.setVisible(True)
        self.text_area.setVisible(False)
        self.toggle_recording_button.setVisible(True)
        self.toggle_recording_button.setWindowOpacity(1)
        self.mute_button.setVisible(False)
        self.mute_button.setWindowOpacity(0)

    def _populate_devices(self):
        try:
            devices = sd.query_devices()
            input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            if not input_devices:
                self.device_combo.addItem("No se encontraron dispositivos.")
                self.toggle_recording_button.setEnabled(False)
                return
            for idx, name in input_devices:
                self.device_combo.addItem(name, idx)
        except Exception as e:
            QMessageBox.critical(self, "Error al detectar dispositivos", str(e))

    def _toggle_recording(self):
        if self.transcription_active:
            self._stop_transcription()
        else:
            self._start_transcription()

    def _start_transcription(self):
        device_index = self.device_combo.currentData()
        if device_index is None:
            QMessageBox.warning(self, "Falta dispositivo", "Selecciona un micrófono.")
            return

        output_dir = "stt_guardados"
        audio_output_dir = "sttaudio_guardados"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(audio_output_dir, exist_ok=True)

        # Generar nombre base para ambos archivos
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_transcription_filepath = f"{output_dir}/{timestamp}.txt"
        self.current_audio_filepath = f"{audio_output_dir}/{timestamp}.wav"

        try:
            self.transcriber_thread = TranscriberThread(device_index, self.current_transcription_filepath, self.current_audio_filepath)
            self.transcriber_thread.new_text.connect(self._update_text_area)
            self.transcriber_thread.finished.connect(self._on_transcription_finished)
            self.transcriber_thread.start()
            self.transcriber_thread.set_mute(self.mute_button.isChecked())

            self.transcription_active = True
            self.transcription_status_changed.emit(True)
            self.text_area.clear()

            self._already_stopped = False

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _stop_transcription(self):
        if self._already_stopped:
            return
        self._already_stopped = True

        if self.transcriber_thread:
            self.transcriber_thread.stop()
            self.transcriber_thread.wait()
            self.transcriber_thread = None

        self.transcription_active = False
        self.transcription_status_changed.emit(False)
        self._prompt_save_or_discard()

    def _toggle_mute(self):
        muted = self.mute_button.isChecked()
        self.mute_button.setText("🔇" if muted else "🎙️")
        if self.transcriber_thread:
            self.transcriber_thread.set_mute(muted)

    def _fade_in_buttons(self):
        for btn in [self.toggle_recording_button, self.mute_button]:
            btn.setVisible(True)
            anim = QPropertyAnimation(btn, b"windowOpacity")
            anim.setDuration(200)
            anim.setStartValue(btn.windowOpacity() if btn.isVisible() else 0)
            anim.setEndValue(1)
            anim.start()
            setattr(btn, "_anim", anim)  # Evitar que el GC elimine animaciones

    def _fade_out_buttons(self):
        for btn in [self.toggle_recording_button, self.mute_button]:
            anim = QPropertyAnimation(btn, b"windowOpacity")
            anim.setDuration(200)
            anim.setStartValue(btn.windowOpacity())
            anim.setEndValue(0)
            anim.finished.connect(lambda b=btn: b.setVisible(False))
            anim.start()
            setattr(btn, "_anim", anim)

    def _update_ui_for_transcription_status(self, active: bool):
        self.device_label.setVisible(not active)
        self.device_combo.setVisible(not active)
        self.text_area.setVisible(active)
        self.settings_button.setVisible(not active)
        self.close_button.setVisible(not active)
        self.window_title_label.setVisible(not active)

        if active:
            self.toggle_recording_button.setText("■ Detener Grabación")
            self.mute_button.setText("🎙️" if not self.mute_button.isChecked() else "🔇")
            # Ocultamos ambos botones hasta que hover los muestre
            self.toggle_recording_button.setVisible(False)
            self.toggle_recording_button.setWindowOpacity(0)
            self.mute_button.setVisible(False)
            self.mute_button.setWindowOpacity(0)
        else:
            self.toggle_recording_button.setText("🔴 Iniciar Grabación")
            self.toggle_recording_button.setVisible(True)
            self.toggle_recording_button.setWindowOpacity(1)
            self.mute_button.setVisible(False)
            self.mute_button.setWindowOpacity(0)

    def _update_text_area(self, text: str):
        self.text_area.setPlainText(text)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

    def _on_transcription_finished(self):
        self._stop_transcription()

    def _prompt_save_or_discard(self):
        if self.current_transcription_filepath and os.path.exists(self.current_transcription_filepath):
            reply = QMessageBox.question(
                self, "Guardar Transcripción",
                "¿Deseas guardar la transcripción y el audio?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.No:
                try:
                    if os.path.exists(self.current_transcription_filepath):
                        os.remove(self.current_transcription_filepath)
                    if self.current_audio_filepath and os.path.exists(self.current_audio_filepath):
                        os.remove(self.current_audio_filepath)
                except Exception as e:
                    QMessageBox.warning(self, "Error al eliminar", str(e))
        self.current_transcription_filepath = None
        self.current_audio_filepath = None

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

    def _open_settings_window(self):
        from .menu import NuevaVentana
        self.settings_window = NuevaVentana()
        self.settings_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptionWindow()
    window.show()
    sys.exit(app.exec_())