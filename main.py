import sys
from PyQt5.QtWidgets import QApplication
from interfaz.grabadora import TranscriptionWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = TranscriptionWindow()  # ✅ Sin argumentos
    ventana.show()
    sys.exit(app.exec_())
