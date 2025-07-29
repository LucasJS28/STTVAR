import sys
from PyQt5.QtWidgets import QApplication
from interfaz.launcher import Launcher  # Importa tu launcher personalizado

if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = Launcher(app)
    launcher.start()
    sys.exit(launcher.exec_())
