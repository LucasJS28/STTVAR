import subprocess
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QApplication, QLabel, QComboBox, QFileDialog, QLineEdit, QInputDialog, QMenu
)
from PyQt5.QtCore import Qt, QPoint
from argostranslate import translate  # Para traducción local

class NuevaVentana(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Explorador de Transcripciones")
        self.setMinimumSize(900, 600)
        self.folder_path = "stt_guardados"
        self.current_file = None
        self.texto_original = ""
        self.is_dark_theme = False  # Estado inicial: modo claro

        # Estilo para modo claro
        self.light_theme = """
            QWidget#MainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f4f8, stop:1 #d9e2ec);
                border-radius: 15px;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                color: #2d3436;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 5px;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: #0984e3;
                color: #ffffff;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 13px;
                margin-top: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                transition: background-color 0.3s;
            }
            QPushButton:hover {
                background-color: #0652dd;
            }
            QPushButton:pressed {
                background-color: #0549b5;
            }
            QPushButton#themeButton {
                background-color: #ffffff;
                color: #0984e3;
                border: 1px solid #dfe6e9;
                padding: 4px;
                font-size: 14px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
                border-radius: 15px;
                margin: 0 5px;
            }
            QPushButton#themeButton:hover {
                background-color: #e6f0fa;
                color: #0652dd;
            }
            QPushButton#themeButton:pressed {
                background-color: #cce0ff;
                color: #0549b5;
            }
            QPushButton#backButton {
                background-color: #ffffff;
                color: #e17055;
                border: 1px solid #dfe6e9;
                padding: 4px 8px;
                font-size: 12px;
                margin: 0 5px;
            }
            QPushButton#backButton:hover {
                background-color: #ffebee;
                color: #d35400;
            }
            QPushButton#backButton:pressed {
                background-color: #ffcdd2;
                color: #b74700;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
                padding: 6px;
                font-size: 13px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            QComboBox#translateCombo {
                max-width: 130px;
                padding: 4px;
                font-size: 12px;
            }
            QLabel {
                font-weight: 600;
                font-size: 13px;
                color: #2d3436;
                margin-right: 8px;
            }
            #titleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #0984e3;
            }
            #headerContainer {
                background: transparent;
                padding: 5px 10px;
                margin: 0;
            }
            #exportContainer, #iaQueryContainer, #iaResponseContainer {
                background-color: #f0f4f8;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
                margin-top: 10px;
                padding: 12px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
        """

        # Estilo para modo oscuro
        self.dark_theme = """
            QWidget#MainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d3436, stop:1 #1e272e);
                border-radius: 15px;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                color: #dfe6e9;
            }
            QTextEdit {
                background-color: #353b48;
                border: 1px solid #4b5468;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                color: #dfe6e9;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            QListWidget {
                background-color: #353b48;
                border: 1px solid #4b5468;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                color: #dfe6e9;
            }
            QListWidget::item {
                padding: 10px 5px;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: #0984e3;
                color: #ffffff;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 13px;
                margin-top: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                transition: background-color 0.3s;
            }
            QPushButton:hover {
                background-color: #0652dd;
            }
            QPushButton:pressed {
                background-color: #0549b5;
            }
            QPushButton#themeButton {
                background-color: #2d3436;
                color: #74b9ff;
                border: 1px solid #4b5468;
                padding: 4px;
                font-size: 14px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
                border-radius: 15px;
                margin: 0 5px;
            }
            QPushButton#themeButton:hover {
                background-color: #34495e;
                color: #54a0ff;
            }
            QPushButton#themeButton:pressed {
                background-color: #2c3e50;
                color: #339af0;
            }
            QPushButton#backButton {
                background-color: #2d3436;
                color: #e17055;
                border: 1px solid #4b5468;
                padding: 4px 8px;
                font-size: 12px;
                margin: 0 5px;
            }
            QPushButton#backButton:hover {
                background-color: #34495e;
                color: #d35400;
            }
            QPushButton#backButton:pressed {
                background-color: #2c3e50;
                color: #b74700;
            }
            QComboBox {
                background-color: #353b48;
                border: 1px solid #4b5468;
                border-radius: 12px;
                padding: 6px;
                font-size: 13px;
                color: #dfe6e9;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }
            QComboBox#translateCombo {
                max-width: 130px;
                padding: 4px;
                font-size: 12px;
            }
            QLabel {
                font-weight: 600;
                font-size: 13px;
                color: #dfe6e9;
                margin-right: 8px;
            }
            #titleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #54a0ff;
            }
            #headerContainer {
                background: transparent;
                padding: 5px 10px;
                margin: 0;
            }
            #exportContainer, #iaQueryContainer, #iaResponseContainer {
                background-color: #2d3436;
                border: 1px solid #4b5468;
                border-radius: 12px;
                margin-top: 10px;
                padding: 12px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            QLineEdit {
                background-color: #353b48;
                border: 1px solid #4b5468;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                color: #dfe6e9;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }
        """

        # Establecer el tema claro por defecto
        self.setStyleSheet(self.light_theme)

        # Layout principal
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Contenedor para el título, micrófono, botón de volver y botón de tema
        header_container = QWidget()
        header_container.setObjectName("headerContainer")
        header_layout = QHBoxLayout()
        header_container.setLayout(header_layout)
        header_layout.setContentsMargins(5, 0, 5, 0)

        # Título STTVAR con micrófono
        title_label = QLabel("🎙️ STTVAR")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Botón de volver
        self.back_button = QPushButton("🔙")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back_to_transcription)
        header_layout.addWidget(self.back_button)

        # Botón de tema
        self.theme_button = QPushButton("☀")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_button)

        main_layout.addWidget(header_container)

        # Layout para el contenido principal
        layout = QHBoxLayout()
        main_layout.addLayout(layout)

        left_layout = QVBoxLayout()
        layout.addLayout(left_layout, 3)

        self.textbox = QTextEdit()
        self.textbox.setPlaceholderText("Selecciona un archivo para editarlo...")
        left_layout.addWidget(self.textbox)

        # Contenedor para respuesta de IA y traducción
        ia_response_container = QWidget()
        ia_response_container.setObjectName("iaResponseContainer")
        ia_response_layout = QVBoxLayout()
        ia_response_container.setLayout(ia_response_layout)

        self.ia_response_box = QTextEdit()
        self.ia_response_box.setReadOnly(True)
        self.ia_response_box.setPlaceholderText("Respuesta de IA aparecerá aquí...")
        self.ia_response_box.hide()
        ia_response_layout.addWidget(self.ia_response_box)

        # Bloque Traducir
        translate_container = QWidget()
        translate_layout = QHBoxLayout()
        translate_container.setLayout(translate_layout)

        translate_layout.addWidget(QLabel("🈯 Traducir a:"))

        self.translate_combo = QComboBox()
        self.translate_combo.setObjectName("translateCombo")
        self.translate_combo.addItems([
            "Español (es)",
            "Inglés (en)",
            "Portugués (pt)"
        ])
        self.translate_combo.currentIndexChanged.connect(self.handle_translation)
        translate_layout.addWidget(self.translate_combo)
        translate_layout.addStretch()
        translate_container.hide()
        ia_response_layout.addWidget(translate_container)

        left_layout.addWidget(ia_response_container)

        self.save_button = QPushButton("💾 Guardar cambios")
        self.save_button.clicked.connect(self.save_file)
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

        # Bloque Preguntar a IA
        ia_query_container = QWidget()
        ia_query_container.setObjectName("iaQueryContainer")
        ia_query_layout = QHBoxLayout()
        ia_query_container.setLayout(ia_query_layout)

        ia_query_layout.addWidget(QLabel("💬 Preguntar a IA:"))

        self.ia_query_input = QLineEdit()
        self.ia_query_input.setPlaceholderText("Escribe tu consulta aquí...")
        ia_query_layout.addWidget(self.ia_query_input)

        self.ia_query_button = QPushButton("🤖 Enviar")
        self.ia_query_button.clicked.connect(self.handle_ia_query)
        ia_query_layout.addWidget(self.ia_query_button)

        ia_query_layout.setSpacing(12)
        ia_query_layout.setContentsMargins(10, 5, 10, 5)
        left_layout.addWidget(ia_query_container)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar por nombre de archivo...")
        self.search_bar.textChanged.connect(self.load_file_list)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Ordenar: Nombre (A-Z)", "Nombre (Z-A)", "Fecha reciente", "Fecha antigua"])
        self.sort_combo.currentIndexChanged.connect(self.load_file_list)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_file_content)
        self.file_list.itemDoubleClicked.connect(self.rename_file)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        right_container = QVBoxLayout()
        right_container.addWidget(self.search_bar)
        right_container.addWidget(self.sort_combo)
        right_container.addWidget(self.file_list)
        layout.addLayout(right_container, 1)

        self.load_file_list()
        self.installed_languages = translate.get_installed_languages()
        self.translate_container = translate_container

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.setStyleSheet(self.dark_theme)
            self.theme_button.setText("🌙")
        else:
            self.setStyleSheet(self.light_theme)
            self.theme_button.setText("☀")

    def back_to_transcription(self):
        from interfaz.grabadora import TranscriptionWindow
        self.main_window = TranscriptionWindow()
        self.main_window.show()
        self.close()

    def get_code_from_selection(self):
        text = self.translate_combo.currentText()
        if "(" in text and ")" in text:
            return text.split("(")[-1].replace(")", "").strip()
        return "es"

    def handle_translation(self):
        if not self.texto_original:
            self.ia_response_box.hide()
            self.translate_container.hide()
            return

        idioma_destino = self.get_code_from_selection()
        idioma_origen = "es"

        if idioma_destino == idioma_origen:
            self.ia_response_box.setPlainText(self.texto_original)
            self.ia_response_box.show()
            self.translate_container.show()
            return

        idioma_origen_obj = next((i for i in self.installed_languages if i.code == idioma_origen), None)
        idioma_destino_obj = next((i for i in self.installed_languages if i.code == idioma_destino), None)

        if idioma_origen_obj is None or idioma_destino_obj is None:
            QMessageBox.critical(self, "Error", f"No está instalado el paquete de traducción para: {idioma_origen} -> {idioma_destino}")
            self.ia_response_box.hide()
            self.translate_container.hide()
            return

        traductor = idioma_origen_obj.get_translation(idioma_destino_obj)
        if traductor is None:
            QMessageBox.critical(self, "Error", f"No existe traducción directa para: {idioma_origen} -> {idioma_destino}")
            self.ia_response_box.hide()
            self.translate_container.hide()
            return

        try:
            traduccion = traductor.translate(self.texto_original)
            self.ia_response_box.setPlainText(traduccion)
            self.ia_response_box.show()
            self.translate_container.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al traducir: {e}")
            self.ia_response_box.hide()
            self.translate_container.hide()

    def load_file_list(self):
        self.file_list.clear()
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

        for filename in files:
            self.file_list.addItem(QListWidgetItem(filename))

        if not files:
            self.file_list.addItem(QListWidgetItem("⚠️ No se encontraron archivos."))

    def load_file_content(self, item: QListWidgetItem):
        filename = item.text()
        filepath = os.path.join(self.folder_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                self.textbox.setPlainText(content)
                self.current_file = filepath
            self.ia_response_box.clear()
            self.ia_response_box.hide()
            self.translate_container.hide()
            self.ia_query_input.clear()
            self.translate_combo.setCurrentIndex(0)
            self.texto_original = ""
        except Exception as e:
            self.textbox.setPlainText(f"⚠️ Error al leer el archivo: {e}")
            self.current_file = None
            self.ia_response_box.clear()
            self.ia_response_box.hide()
            self.translate_container.hide()
            self.ia_query_input.clear()
            self.texto_original = ""

    def save_file(self):
        if not self.current_file:
            QMessageBox.warning(self, "Advertencia", "No hay archivo seleccionado para guardar.")
            return
        try:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.textbox.toPlainText())
            QMessageBox.information(self, "Éxito", f"Archivo guardado correctamente:\n{os.path.basename(self.current_file)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{e}")

    def export_selected_format(self):
        if not self.current_file:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar un archivo para exportar.")
            return

        format_selected = self.export_combo.currentText()
        if "PDF" in format_selected:
            self.export_to_pdf()
        elif "Word" in format_selected:
            self.export_to_word()
        elif "Markdown" in format_selected:
            self.export_to_markdown()

    def export_to_pdf(self):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        export_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como PDF", self.current_file.replace(".txt", ".pdf"), "Archivos PDF (*.pdf)"
        )
        if not export_path:
            return

        try:
            text = self.textbox.toPlainText()
            c = canvas.Canvas(export_path, pagesize=letter)
            width, height = letter
            y = height - 40
            for line in text.splitlines():
                c.drawString(40, y, line[:100])
                y -= 15
                if y < 40:
                    c.showPage()
                    y = height - 40
            c.save()
            QMessageBox.information(self, "Exportado", f"Archivo exportado a PDF:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF:\n{e}")

    def export_to_word(self):
        from docx import Document

        export_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como Word", self.current_file.replace(".txt", ".docx"), "Documentos Word (*.docx)"
        )
        if not export_path:
            return

        try:
            text = self.textbox.toPlainText()
            doc = Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(export_path)
            QMessageBox.information(self, "Exportado", f"Archivo exportado a Word:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Word:\n{e}")

    def export_to_markdown(self):
        export_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como Markdown", self.current_file.replace(".txt", ".md"), "Archivos Markdown (*.md)"
        )
        if not export_path:
            return

        try:
            text = self.textbox.toPlainText()
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self, "Exportado", f"Archivo exportado a Markdown:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Markdown:\n{e}")

    def rename_file(self, item: QListWidgetItem):
        old_name = item.text()
        if old_name == "⚠️ No se encontraron archivos.":
            return

        new_name, ok = QInputDialog.getText(self, "Renombrar archivo", "Nuevo nombre:", text=old_name)
        if ok and new_name:
            old_path = os.path.join(self.folder_path, old_name)
            new_path = os.path.join(self.folder_path, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Ya existe un archivo con ese nombre.")
                return
            try:
                os.rename(old_path, new_path)
                self.load_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo renombrar el archivo:\n{e}")

    def show_context_menu(self, position: QPoint):
        item = self.file_list.itemAt(position)
        if item is None:
            return

        menu = QMenu()
        eliminar_action = menu.addAction("Eliminar archivo")
        action = menu.exec_(self.file_list.viewport().mapToGlobal(position))

        if action == eliminar_action:
            self.delete_file(item)

    def delete_file(self, item: QListWidgetItem):
        filename = item.text()
        filepath = os.path.join(self.folder_path, filename)

        if filename == "⚠️ No se encontraron archivos.":
            return

        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar el archivo:\n{filename}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(filepath)
                if self.current_file == filepath:
                    self.current_file = None
                    self.textbox.clear()
                    self.ia_response_box.clear()
                    self.ia_response_box.hide()
                    self.translate_container.hide()
                    self.ia_query_input.clear()
                    self.texto_original = ""
                self.load_file_list()
                QMessageBox.information(self, "Archivo eliminado", f"El archivo '{filename}' ha sido eliminado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo:\n{e}")

    def handle_ia_query(self):
        pregunta = self.ia_query_input.text().strip()
        if not pregunta:
            QMessageBox.warning(self, "Advertencia", "Debes escribir una pregunta para consultar.")
            return

        contenido = self.textbox.toPlainText().strip()
        if not contenido:
            QMessageBox.warning(self, "Advertencia", "El archivo está vacío, no hay contexto para la IA.")
            return

        prompt = (
            "Eres un asistente que responde en español de forma clara y concreta, "
            "usando el siguiente texto como referencia:\n\n"
            f"{contenido}\n\n"
            f"Pregunta: {pregunta}\n"
            "Respuesta:"
        )

        self.ia_response_box.setPlainText("Consultando a la IA, por favor espera...")
        self.ia_response_box.show()
        self.translate_container.show()
        QApplication.processEvents()

        respuesta = self.consultar_ollama(prompt)
        self.texto_original = respuesta
        self.ia_response_box.setPlainText(respuesta)
        self.ia_query_input.clear()
        self.translate_combo.setCurrentIndex(0)

    def consultar_ollama(self, prompt: str) -> str:
        ruta_ollama = r"C:\Users\LucasJs28\AppData\Local\Programs\Ollama\ollama.exe"
        if not os.path.exists(ruta_ollama):
            return "Error: No se encontró el ejecutable de Ollama."

        try:
            process = subprocess.Popen(
                [ruta_ollama, 'run', 'mistral:7b-instruct-q4_K_M'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate(prompt + "\n", timeout=60)
            if process.returncode != 0:
                return f"Error al ejecutar Ollama: {stderr.strip()}"
            return stdout.strip()
        except subprocess.TimeoutExpired:
            return "Error: La consulta a Ollama excedió el tiempo límite."
        except Exception as e:
            return f"Error inesperado: {str(e)}"

    def closeEvent(self, event):
        from interfaz.grabadora import TranscriptionWindow
        self.main_window = TranscriptionWindow()
        self.main_window.show()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NuevaVentana()
    window.show()
    sys.exit(app.exec_())