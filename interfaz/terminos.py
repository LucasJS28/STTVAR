import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QCheckBox, QPushButton, QTextEdit,
    QHBoxLayout, QMessageBox, QLabel, QWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPoint, QUrl
from PyQt5.QtGui import QColor, QCursor, QDesktopServices

class DraggableDialog(QDialog):
    """QDialog personalizado y arrastrable sin bordes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_pos = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() & Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

class TermsAndConditionsDialog(DraggableDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Términos y Condiciones - STTVAR")
        self.setMinimumSize(620, 700)
        self.init_ui()
        self._apply_styles()

    def init_ui(self):
        # Contenedor principal con sombra y bordes
        container = QWidget(self)
        container.setObjectName("containerWidget")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 160))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- CABECERA DE MARCA ---
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 20, 15, 15)

        title_group_layout = QVBoxLayout()
        title_group_layout.setSpacing(2)
        main_title = QLabel("🎙️ STTVAR")
        main_title.setObjectName("mainTitleLabel")
        subtitle = QLabel("Términos y Condiciones")
        subtitle.setObjectName("subtitleLabel")
        title_group_layout.addWidget(main_title)
        title_group_layout.addWidget(subtitle)

        close_button = QPushButton("✕")
        close_button.setObjectName("closeButtonCustom")
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.clicked.connect(self.reject)

        header_layout.addLayout(title_group_layout)
        header_layout.addStretch()
        header_layout.addWidget(close_button, 0, Qt.AlignTop)
        layout.addWidget(header_frame)
        
        # --- SEPARADOR DE CABECERA ---
        header_separator = QFrame()
        header_separator.setObjectName("separatorLine")
        header_separator.setFrameShape(QFrame.HLine)
        layout.addWidget(header_separator)
        
        # --- CONTENIDO DE TÉRMINOS ---
        self.terms_text = QTextEdit()
        self.terms_text.setObjectName("termsText")
        self.terms_text.setReadOnly(True)
        self.terms_text.setHtml(self.get_terms_html())
        
        text_container_layout = QHBoxLayout()
        text_container_layout.setContentsMargins(25, 20, 25, 20)
        text_container_layout.addWidget(self.terms_text)
        layout.addLayout(text_container_layout)
        
        # --- FOOTER CON ACCIONES ---
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setSpacing(18)
        footer_layout.setContentsMargins(25, 20, 25, 25)

        self.accept_checkbox = QCheckBox("He leído y acepto los Términos y Condiciones.")
        self.accept_checkbox.setObjectName("acceptCheckbox")
        footer_layout.addWidget(self.accept_checkbox)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # --- BOTÓN AÑADIDO ---
        self.learn_more_button = QPushButton("Saber más sobre STTVAR")
        self.learn_more_button.setObjectName("learnMoreButton")
        self.learn_more_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.learn_more_button.clicked.connect(self.open_link)
        button_layout.addWidget(self.learn_more_button)
        # --- FIN DEL BOTÓN AÑADIDO ---

        self.cancel_button = QPushButton("Rechazar")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.clicked.connect(self.reject)

        self.accept_button = QPushButton("Aceptar")
        self.accept_button.setObjectName("acceptButton")
        self.accept_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.accept_button.clicked.connect(self.accept_terms)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.accept_button)
        footer_layout.addLayout(button_layout)
        
        layout.addWidget(footer_frame)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(container)
        main_layout.setContentsMargins(20, 20, 20, 20)

    def get_terms_html(self):
        return """
        <style>
            body { color: #c0c0c0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            h4 { color: #E74C3C; margin-bottom: 5px; }
            p { margin-top: 0px; margin-bottom: 12px; line-height: 1.5; }
            ul { list-style-type: none; padding-left: 0; margin: 0; }
            li { padding-left: 20px; position: relative; margin-bottom: 12px; }
            li::before {
                content: '■'; color: #E74C3C; position: absolute; left: 0; top: 1px; font-size: 12px;
            }
            strong { color: #f0f0f0; font-weight: 600; }
        </style>
        <body>
            <p>Para usar STTVAR, por favor, revisa y acepta los siguientes puntos clave:</p>
            <ul>
                <li>
                    <h4>Privacidad y Procesamiento Local</h4>
                    <p>Todos sus datos, incluyendo audio y transcripciones, se procesan <strong>exclusivamente en su dispositivo</strong>. STTVAR no recopila, almacena ni transmite su información a ningún servidor externo.</p>
                </li>
                <li>
                    <h4>Responsabilidad del Usuario</h4>
                    <p>Usted es el único responsable de obtener el consentimiento legal para grabar o transcribir cualquier conversación, cumpliendo con todas las leyes de privacidad aplicables. El autor no se hace responsable del uso indebido de esta herramienta.</p>
                </li>
                <li>
                    <h4>Sin Garantías</h4>
                    <p>STTVAR se proporciona "tal cual". No se ofrecen garantías y el autor no será responsable de ningún daño derivado de su uso.</p>
                </li>
            </ul>
        </body>
        """

    def accept_terms(self):
        if not self.accept_checkbox.isChecked():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Debe aceptar los términos para poder continuar.")
            msg_box.setWindowTitle("Advertencia")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setStyleSheet("""
                QMessageBox { background-color: #383838; } 
                QLabel { color: white; font-size: 14px; } 
                QPushButton { 
                    background-color: #E74C3C; color: white; border-radius: 8px; 
                    padding: 8px 20px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            msg_box.exec_()
        else:
            self.accept()

    def open_link(self):
        """Abre la URL del proyecto en el navegador."""
        url = QUrl("https://lucasjs28.github.io/STTVAR")
        QDesktopServices.openUrl(url)

    def _apply_styles(self):
        self.setStyleSheet("""
            #containerWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 45, 255), stop:1 rgba(30, 30, 30, 255));
                border-radius: 22px;
                border: 2px solid #E74C3C;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #mainTitleLabel { color: #f0f0f0; font-size: 24px; font-weight: 600; }
            #subtitleLabel { color: #a0a0a0; font-size: 14px; }
            #closeButtonCustom {
                background-color: transparent; color: #aaa; border: none;
                font-size: 20px; font-weight: bold; padding: 5px 10px; border-radius: 10px;
            }
            #closeButtonCustom:hover { background-color: #E81123; color: white; }
            #separatorLine { border: 1px solid #3a3a3a; }
            
            #termsText { background-color: transparent; border: none; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 12px; margin: 0; border-radius: 6px;
            }
            QScrollBar::handle:vertical { background: #4a4a4a; min-height: 25px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #E74C3C; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            
            #footerFrame { background-color: rgba(0, 0, 0, 0.1); border-top: 1px solid #3a3a3a; }
            
            #acceptCheckbox { color: #b0b0b0; font-size: 13px; spacing: 10px; }
            #acceptCheckbox::indicator {
                width: 18px; height: 18px; border: 2px solid #555;
                border-radius: 6px; background-color: #333;
            }
            #acceptCheckbox::indicator:hover { border-color: #E74C3C; }
            #acceptCheckbox::indicator:checked {
                background-color: #E74C3C; border-color: #F1948A;
            }
            
            QPushButton {
                border-radius: 10px; padding: 11px 24px; font-size: 14px; font-weight: 600; border: none;
            }
            #acceptButton {
                background-color: #E74C3C; color: white;
            }
            #acceptButton:hover { background-color: #D35400; }
            #acceptButton:pressed { background-color: #C0392B; }
            
            #cancelButton { background-color: #383838; color: #a0a0a0; }
            #cancelButton:hover { background-color: #444; color: #e0e0e0; }
            #cancelButton:pressed { background-color: #2f2f2f; }
            
            /* --- ESTILOS PARA EL NUEVO BOTÓN --- */
            #learnMoreButton {
                background-color: transparent;
                color: #a0a0a0;
                border: 2px solid #555;
            }
            #learnMoreButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e0e0;
                border-color: #777;
            }
            #learnMoreButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = TermsAndConditionsDialog()
    dialog.exec_()
    sys.exit()