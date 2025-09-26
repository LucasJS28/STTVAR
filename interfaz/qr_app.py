import sys
import qrcode
from io import BytesIO
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt, QPoint, QTimer

class QRDialog(QDialog):
    """
    Una ventana de diálogo para compartir con un diseño premium, sin bordes y totalmente personalizada.
    - Encabezado de marca con icono y nombre de la aplicación.
    - Estética refinada con un borde temático y espaciado mejorado.
    - Funcionalidad de arrastre, cambio de vista y copia al portapapeles.
    """
    def __init__(self, local_url, ngrok_url, parent=None):
        super().__init__(parent)
        self.local_url = local_url
        self.ngrok_url = ngrok_url
        self.old_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 660)
        
        self._setup_ui()
        self._show_public_qr()

    def _setup_ui(self):
        """Construye la interfaz de usuario completa y aplica los estilos."""
        
        container = QWidget(self)
        container.setObjectName("containerWidget")
        
        # --- EFECTO DE SOMBRA SUTIL ---
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 180))
        container.setGraphicsEffect(shadow)

        # --- ENCABEZADO DE MARCA PERSONALIZADO ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 5, 10)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        main_title = QLabel("🎙️ STTVAR")
        main_title.setObjectName("mainTitleLabel")
        
        subtitle = QLabel("Compartir Transcripción en Vivo")
        subtitle.setObjectName("subtitleLabel")
        
        title_layout.addWidget(main_title)
        title_layout.addWidget(subtitle)
        
        close_button = QPushButton("✕")
        close_button.setObjectName("closeButtonCustom")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.accept)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(close_button, 0, Qt.AlignTop)

        # --- CONTENIDO PRINCIPAL ---
        self.qr_label = QLabel()
        self.qr_label.setObjectName("qrContainerLabel")
        self.qr_label.setFixedSize(320, 320)
        # Se asegura que el contenido (la imagen QR) también esté centrado dentro del QLabel
        self.qr_label.setAlignment(Qt.AlignCenter)

        # Grupo URL + Copiar
        url_group_frame = QFrame()
        url_group_frame.setObjectName("urlGroupFrame")
        url_layout = QHBoxLayout(url_group_frame)
        url_layout.setContentsMargins(20, 0, 5, 0)
        url_layout.setSpacing(10)

        self.url_label = QLabel()
        self.url_label.setObjectName("urlDisplayLabel")
        self.copy_button = QPushButton("Copiar")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(self._copy_url_to_clipboard)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.copy_button)

        # Botones de Selección
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        self.local_button = QPushButton("🏠 Red Local")
        self.ngrok_button = QPushButton("🌐 Público")
        self.local_button.setCursor(Qt.PointingHandCursor)
        self.ngrok_button.setCursor(Qt.PointingHandCursor)
        self.local_button.clicked.connect(self._show_local_qr)
        self.ngrok_button.clicked.connect(self._show_public_qr)
        buttons_layout.addWidget(self.local_button)
        buttons_layout.addWidget(self.ngrok_button)
        
        # --- LAYOUT GENERAL ---
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(30, 25, 30, 35)
        content_layout.setSpacing(0)
        
        content_layout.addLayout(header_layout)
        content_layout.addSpacing(30)
        # El segundo argumento Qt.AlignCenter centra el widget QLabel en el layout
        content_layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        content_layout.addSpacing(30)
        content_layout.addWidget(url_group_frame)
        content_layout.addSpacing(20)
        content_layout.addLayout(buttons_layout)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(container)
        
        self._setup_styles()

    def _setup_styles(self):
        """Define la hoja de estilos para un acabado premium y moderno."""
        self.setStyleSheet("""
            #containerWidget {
                background-color: #2c2c2c;
                border-radius: 22px;
                /* --- ¡NUEVO! Borde rojo para el modal --- */
                border: 2px solid #E74C3C;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #mainTitleLabel {
                color: #f0f0f0;
                font-size: 24px;
                font-weight: 600;
            }
            #subtitleLabel {
                color: #a0a0a0;
                font-size: 14px;
            }
            #closeButtonCustom {
                background-color: transparent; color: #aaa; border: none;
                font-size: 20px; font-weight: bold; padding: 5px 10px;
                border-radius: 10px;
            }
            #closeButtonCustom:hover {
                background-color: #E81123; color: white;
            }
            #qrContainerLabel {
                background-color: white;
                border: 4px solid #E74C3C;
                border-radius: 18px;
                padding: 10px;
            }
            #urlGroupFrame {
                background-color: #212121;
                border: 1px solid #4a4a4a;
                border-radius: 12px;
            }
            #urlDisplayLabel {
                color: #e0e0e0; font-size: 14px;
                background-color: transparent; border: none;
            }
            #copyButton {
                background-color: #505050; color: #fff;
                border: none; border-radius: 10px;
                padding: 11px 20px; font-weight: 600; font-size: 13px;
                margin: 4px;
            }
            #copyButton:hover { background-color: #626262; }
            #copyButton:pressed { background-color: #454545; }
            
            QPushButton {
                background-color: #3c3c3c; color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 12px;
                padding: 14px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover {
                border-color: #E74C3C;
            }
            QPushButton:pressed { background-color: #333; }
            
            QPushButton.active {
                background-color: #E74C3C;
                border: 2px solid #F1948A;
                color: white;
            }
        """)

    # --- Métodos para arrastrar la ventana ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = None
    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            
    # --- Métodos de funcionalidad ---
    def generate_qr(self, url):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, "PNG")
        pixmap = QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
        # No es necesario escalar aquí, ya que el pixmap se centrará en el QLabel de tamaño fijo
        return pixmap

    def _copy_url_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.url_label.text())
        self.copy_button.setText("¡Copiado!")
        QTimer.singleShot(1500, lambda: self.copy_button.setText("Copiar"))

    def _update_view(self, url, is_public):
        self.qr_label.setPixmap(self.generate_qr(url))
        self.url_label.setText(url)
        self.ngrok_button.setProperty("class", "active" if is_public else "")
        self.local_button.setProperty("class", "active" if not is_public else "")
        self._refresh_styles()

    def _show_local_qr(self): self._update_view(self.local_url, is_public=False)
    def _show_public_qr(self): self._update_view(self.ngrok_url, is_public=True)
    def _refresh_styles(self):
        self.style().unpolish(self)
        self.style().polish(self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    local_url_arg = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.1.100:5000"
    ngrok_url_arg = sys.argv[2] if len(sys.argv) > 2 else "https://d61e552eed09.ngrok-free.app"
    dialog = QRDialog(local_url_arg, ngrok_url_arg)
    dialog.show()
    sys.exit(app.exec_())