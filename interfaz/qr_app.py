import sys
import socket
import webbrowser
from threading import Thread
from flask import Flask, render_template
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QDialog, QHBoxLayout, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QPainter, QPainterPath, QColor, QPen
from PyQt5.QtCore import Qt, QTimer, QRectF
from PIL import Image
from io import BytesIO
import qrcode

# ---- Obtener IP local ----
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"  # Fallback to localhost if unable to get IP
    finally:
        s.close()
    return ip

# ---- Flask Server ----
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ---- PyQt5 QR Dialog with Rounded Red Border ----
class QRDialog(QDialog):
    def __init__(self, qr_image, url):
        super().__init__()
        self.setWindowTitle("Código QR - STTTVAR")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.center_window()

        self._is_dragging = False
        self._drag_pos = None
        self.url = url

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        # ---- Botón de cierre ----
        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 32)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""QPushButton { 
            font-size:14px; font-weight:600; color:#fff;
            background:#FF6B6B; border:none; border-radius:16px; }
            QPushButton:hover { background:#D65A51; }""")
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_button)
        layout.addLayout(close_layout)

        # ---- Logo + título ----
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_label = QLabel("🎤")
        logo_label.setFont(QFont("Inter", 22, QFont.Bold))
        logo_label.setStyleSheet("color:#FF6B6B;")
        title_label = QLabel("STTTVAR")
        title_label.setFont(QFont("Inter", 18, QFont.Bold))
        title_label.setStyleSheet("color:#fff;")
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(title_label)
        layout.addLayout(logo_layout)

        # ---- Instrucción ----
        instruction_label = QLabel("Escanea el código QR o abre la página")
        instruction_label.setFont(QFont("Inter", 13))
        instruction_label.setStyleSheet("color:#fff; padding:6px;")
        instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label)

        # ---- QR code ----
        qr_label = QLabel()
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        qim = QImage()
        qim.loadFromData(buffer.getvalue(), "PNG")
        qr_label.setPixmap(QPixmap.fromImage(qim).scaled(
            220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr_label.setStyleSheet("background:#fff; border-radius:8px; padding:8px;")
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        # ---- URL + Copiar ----
        url_layout = QHBoxLayout()
        url_layout.setAlignment(Qt.AlignCenter)
        self.url_label = QLabel(url)
        self.url_label.setFont(QFont("Inter", 12))
        self.url_label.setStyleSheet("""
            color:#fff;
            background:rgba(255,255,255,0.15);
            border-radius:8px;
            padding:6px 10px;
        """)
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setWordWrap(True)
        self.url_label.setMinimumWidth(220)
        url_layout.addWidget(self.url_label)

        copy_button = QPushButton("Copiar")
        copy_button.setFixedSize(80, 32)
        copy_button.clicked.connect(lambda: self.copy_ip(url))
        copy_button.setStyleSheet("""QPushButton {
            font-size:13px; font-weight:600; color:#fff;
            background:#FF6B6B; border:none; border-radius:8px; }
            QPushButton:hover { background:#D65A51; }""")
        url_layout.addWidget(copy_button)
        layout.addLayout(url_layout)

        # ---- Botón abrir navegador ----
        open_button = QPushButton("🌐 Abrir página")
        open_button.setFixedSize(120, 32)
        open_button.setStyleSheet("""QPushButton {
            font-size:13px; font-weight:600; color:#fff;
            background:#FF6B6B; border:none; border-radius:8px; }
            QPushButton:hover { background:#D65A51; }""")
        open_button.clicked.connect(self.open_in_browser)
        layout.addWidget(open_button, alignment=Qt.AlignCenter)

        # ---- Mensaje de confirmación ----
        self.message_label = QLabel("")
        self.message_label.setFont(QFont("Inter", 11, QFont.Medium))
        self.message_label.setStyleSheet("""
            color: #90EE90;
            padding: 5px;
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()
        layout.addWidget(self.message_label)

        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, 20, 20)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#404040"))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(255, 107, 107), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def copy_ip(self, url):
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        self.message_label.setText("✅ Dirección copiada al portapapeles")
        self.message_label.show()
        QTimer.singleShot(2000, self.message_label.hide)

    def open_in_browser(self):
        webbrowser.open(self.url)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self._drag_pos = None
        event.accept()

# ---- Iniciar Flask en un hilo separado y PyQt5 ----
if __name__ == "__main__":
    # Iniciar Flask en un hilo separado
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True  # Hilo demonio para que termine al cerrar la app
    flask_thread.start()

    # Iniciar aplicación PyQt5
    app_qt = QApplication(sys.argv)
    ip = get_local_ip()
    url = f"http://{ip}:5000/"
    qr = qrcode.make(url, box_size=10, border=4)
    qr_image = qr.convert("RGB")
    qr_dialog = QRDialog(qr_image, url)
    qr_dialog.show()
    sys.exit(app_qt.exec_())