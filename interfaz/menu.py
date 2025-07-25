from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QApplication, QLabel, QComboBox, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt
import os
import sys

class NuevaVentana(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Explorador de Transcripciones")
        self.setMinimumSize(900, 600)
        self.folder_path = "stt_guardados"
        self.current_file = None

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                color: #333;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 5px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: #ffffff;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 6px;
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
                border-radius: 5px;
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
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                background-color: #f4f7fa;
            }
            QLineEdit {
                padding: 8px;
                font-size: 13px;
                border-radius: 5px;
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

        # Caja para mostrar respuesta de IA (oculta al inicio)
        self.ia_response_box = QTextEdit()
        self.ia_response_box.setReadOnly(True)
        self.ia_response_box.setPlaceholderText("Respuesta de IA aparecerá aquí...")
        self.ia_response_box.hide()  # Oculta por defecto
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

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_file_content)
        layout.addWidget(self.file_list, 1)

        self.load_file_list()

    def handle_ia_query(self):
        pregunta = self.ia_query_input.text().strip()
        if not pregunta:
            QMessageBox.warning(self, "Advertencia", "Debes escribir una pregunta para consultar.")
            return

        # Simulación de respuesta (puedes conectar a FastAPI aquí)
        respuesta = f"Respuesta generada para: {pregunta}"

        self.ia_response_box.setPlainText(respuesta)
        self.ia_response_box.show()
        self.ia_query_input.clear()

    def load_file_list(self):
        self.file_list.clear()
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".txt"):
                item = QListWidgetItem(filename)
                self.file_list.addItem(item)
        if self.file_list.count() == 0:
            QMessageBox.information(self, "Información", "No se encontraron archivos .txt en la carpeta 'stt_guardados'.")

    def load_file_content(self, item: QListWidgetItem):
        filename = item.text()
        filepath = os.path.join(self.folder_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                self.textbox.setPlainText(content)
                self.current_file = filepath
        except Exception as e:
            self.textbox.setPlainText(f"⚠️ Error al leer el archivo: {e}")
            self.current_file = None

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
