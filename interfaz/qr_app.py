import sys
import qrcode
from io import BytesIO
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QDesktopServices
from PyQt5.QtCore import Qt, QPoint, QTimer, QUrl

class QRDialog(QDialog):
    """
    Una ventana de diálogo para compartir con un diseño premium, sin bordes y totalmente personalizada.
    - Encabezado de marca con icono y nombre de la aplicación.
    - Estética refinada con un borde temático y espaciado mejorado.
    - Funcionalidad de arrastre, cambio de vista y copia al portapapeles.
    - Botón para abrir el enlace directamente en el navegador.
    """
    def __init__(self, local_url, ngrok_url, parent=None):
        super().__init__(parent)
        self.local_url = local_url
        self.ngrok_url = ngrok_url
        self.current_url = ngrok_url
        self.old_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 680) # Aumentamos ligeramente la altura para el nuevo layout
        
        self._setup_ui()
        self._show_public_qr()

    def _setup_ui(self):
        """Construye la interfaz de usuario completa y aplica los estilos."""
        
        container = QWidget(self)
        container.setObjectName("containerWidget")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 180))
        container.setGraphicsEffect(shadow)

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

        self.qr_label = QLabel()
        self.qr_label.setObjectName("qrContainerLabel")
        self.qr_label.setFixedSize(320, 320)
        self.qr_label.setAlignment(Qt.AlignCenter)

        # --- NUEVO COMPONENTE PARA URL Y ACCIONES (LAYOUT VERTICAL) ---
        url_actions_frame = QFrame()
        url_actions_frame.setObjectName("urlActionsFrame")
        url_actions_layout = QVBoxLayout(url_actions_frame)
        url_actions_layout.setContentsMargins(15, 15, 15, 15)
        url_actions_layout.setSpacing(15)

        self.url_label = QLabel()
        self.url_label.setObjectName("urlDisplayLabel")
        self.url_label.setWordWrap(True) # Asegura que la URL se vea completa
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # Permite copiar a mano

        # Layout para los botones de acción ("Copiar", "Abrir")
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setSpacing(10)

        self.copy_button = QPushButton("Copiar Enlace")
        self.copy_button.setObjectName("copyUrlButton")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(self._copy_url_to_clipboard)

        self.open_button = QPushButton("Abrir")
        self.open_button.setObjectName("openLinkButton")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(self._open_url_in_browser)
        
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.copy_button)
        action_buttons_layout.addWidget(self.open_button)
        action_buttons_layout.addStretch()
        
        # Añadimos los widgets al layout vertical del frame
        url_actions_layout.addWidget(self.url_label)
        url_actions_layout.addLayout(action_buttons_layout)

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
        content_layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        content_layout.addSpacing(25)
        content_layout.addWidget(url_actions_frame)
        content_layout.addSpacing(25)
        content_layout.addLayout(buttons_layout)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(container)
        
        self._setup_styles()

    def _setup_styles(self):
        """Define la hoja de estilos para un acabado premium y moderno."""
        self.setStyleSheet("""
            #containerWidget {
                background-color: #2c2c2c; border-radius: 22px;
                border: 2px solid #E74C3C; font-family: 'Segoe UI', Arial, sans-serif;
            }
            #mainTitleLabel { color: #f0f0f0; font-size: 24px; font-weight: 600; }
            #subtitleLabel { color: #a0a0a0; font-size: 14px; }
            #closeButtonCustom {
                background-color: transparent; color: #aaa; border: none; font-size: 20px;
                font-weight: bold; padding: 5px 10px; border-radius: 10px;
            }
            #closeButtonCustom:hover { background-color: #E81123; color: white; }
            #qrContainerLabel {
                background-color: white; border: 4px solid #E74C3C;
                border-radius: 18px; padding: 10px;
            }
            
            /* --- ESTILOS DEL COMPONENTE DE URL Y ACCIONES --- */
            #urlActionsFrame {
                background-color: #212121; border: 1px solid #4a4a4a;
                border-radius: 12px;
            }
            #urlDisplayLabel {
                color: #e0e0e0; font-size: 14px;
                background-color: transparent; border: none;
                padding: 5px; /* Pequeño padding para que no se pegue a los bordes */
            }

            /* Estilo para botones de acción (Copiar, Abrir) */
            #copyUrlButton, #openLinkButton {
                border: none; border-radius: 8px; font-weight: 600; font-size: 13px;
                padding: 10px 22px; /* Más padding horizontal para mejor apariencia */
                min-width: 120px; /* Ancho mínimo para consistencia */
            }
            #copyUrlButton { background-color: #505050; color: white; }
            #copyUrlButton:hover { background-color: #626262; }
            #copyUrlButton:pressed { background-color: #454545; }
            
            #openLinkButton { background-color: #E74C3C; color: white; }
            #openLinkButton:hover { background-color: #C0392B; }
            #openLinkButton:pressed { background-color: #A93226; }

            /* Estilo para los botones inferiores (Local/Público) */
            QPushButton {
                background-color: #3c3c3c; color: #e0e0e0;
                border: 1px solid #5a5a5a; border-radius: 12px;
                padding: 14px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { border-color: #E74C3C; }
            QPushButton:pressed { background-color: #333; }
            
            QPushButton.active {
                background-color: #E74C3C; border: 2px solid #F1948A;
                color: white;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = None
    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            
    def generate_qr(self, url):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, "PNG")
        pixmap = QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
        return pixmap

    def _copy_url_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_url)
        self.copy_button.setText("¡Copiado!")
        QTimer.singleShot(1500, lambda: self.copy_button.setText("Copiar Enlace"))

    def _open_url_in_browser(self):
        QDesktopServices.openUrl(QUrl(self.current_url))

    def _update_view(self, url, is_public):
        self.current_url = url
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
    # URL larga para probar el ajuste de texto
    ngrok_url_arg = sys.argv[2] if len(sys.argv) > 2 else "https://una-url-publica-muy-larga-generada-por-ngrok-para-probar.ngrok-free.app"
    dialog = QRDialog(local_url_arg, ngrok_url_arg)
    dialog.show()
    sys.exit(app.exec_())