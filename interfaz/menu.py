import subprocess
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QApplication, QLabel, QComboBox, QFileDialog, QLineEdit, QInputDialog, QMenu
)
from PyQt5.QtCore import Qt, QPoint

class NuevaVentana(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Explorador de Transcripciones")
        self.setMinimumSize(900, 600)
        self.folder_path = "stt_guardados"
        self.current_file = None

        self.setStyleSheet("""
            QWidget#MainWindow {
                border-radius: 15px;
                background-color: #ffffff;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                color: #333;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 5px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: #ffffff;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 15px;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2c5da3;
            }
            QComboBox {
                padding: 6px;
                border-radius: 12px;
                border: 1px solid #aaa;
                font-size: 13px;
                background-color: white;
            }
            QLabel {
                font-weight: bold;
                font-size: 13px;
                margin-right: 8px;
            }
            #exportContainer, #iaQueryContainer {
                border: 1px solid #c0c0c0;
                border-radius: 12px;
                margin-top: 10px;
                padding: 10px;
                background-color: #f4f7fa;
            }
            QLineEdit {
                padding: 8px;
                font-size: 13px;
                border-radius: 12px;
                border: 1px solid #aaa;
            }
        """)

        layout = QHBoxLayout()
        self.setLayout(layout)

        left_layout = QVBoxLayout()
        layout.addLayout(left_layout, 3)

        self.textbox = QTextEdit()
        self.textbox.setPlaceholderText("Selecciona un archivo para editarlo...")
        left_layout.addWidget(self.textbox)

        self.ia_response_box = QTextEdit()
        self.ia_response_box.setReadOnly(True)
        self.ia_response_box.setPlaceholderText("Respuesta de IA aparecerá aquí...")
        self.ia_response_box.hide()
        left_layout.addWidget(self.ia_response_box)

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

        # 🔍 Buscador y orden
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar por nombre de archivo...")
        self.search_bar.textChanged.connect(self.load_file_list)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Ordenar: Nombre (A-Z)", "Nombre (Z-A)", "Fecha reciente", "Fecha antigua"])
        self.sort_combo.currentIndexChanged.connect(self.load_file_list)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_file_content)
        self.file_list.itemDoubleClicked.connect(self.rename_file)

        # Habilitar menú contextual personalizado para eliminar archivos
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        right_container = QVBoxLayout()
        right_container.addWidget(self.search_bar)
        right_container.addWidget(self.sort_combo)
        right_container.addWidget(self.file_list)
        layout.addLayout(right_container, 1)

        self.load_file_list()

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
            return  # No hacer nada si no hay archivos reales

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
                    self.ia_query_input.clear()
                self.load_file_list()
                QMessageBox.information(self, "Archivo eliminado", f"El archivo '{filename}' ha sido eliminado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo:\n{e}")

    # --- El resto del código igual ---

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
        QApplication.processEvents()

        respuesta = self.consultar_ollama(prompt)
        self.ia_response_box.setPlainText(respuesta)
        self.ia_query_input.clear()

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
            self.ia_query_input.clear()
        except Exception as e:
            self.textbox.setPlainText(f"⚠️ Error al leer el archivo: {e}")
            self.current_file = None
            self.ia_response_box.clear()
            self.ia_response_box.hide()
            self.ia_query_input.clear()

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
            doc.add_heading(os.path.basename(export_path), level=1)
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
            with open(export_path, "w", encoding="utf-8") as md_file:
                md_file.write("# " + os.path.basename(export_path) + "\n\n")
                md_file.write(text)
            QMessageBox.information(self, "Exportado", f"Archivo exportado a Markdown:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Markdown:\n{e}")

    def rename_file(self, item: QListWidgetItem):
        old_name = item.text()
        old_path = os.path.join(self.folder_path, old_name)

        new_name, ok = QInputDialog.getText(
            self, "Renombrar archivo", "Nuevo nombre del archivo:", text=old_name
        )

        if ok and new_name:
            if not new_name.endswith(".txt"):
                new_name += ".txt"
            new_path = os.path.join(self.folder_path, new_name)

            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Ya existe un archivo con ese nombre.")
                return

            try:
                os.rename(old_path, new_path)
                if self.current_file == old_path:
                    self.current_file = new_path
                self.load_file_list()
                QMessageBox.information(self, "Renombrado", f"Archivo renombrado a:\n{new_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo renombrar el archivo:\n{e}")

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
