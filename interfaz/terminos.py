from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QTextEdit,
    QHBoxLayout, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect


class TermsAndConditionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Términos y Condiciones - STTVAR")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2a2a2a, stop: 1 #4a4a4a
                );
                border: 2px solid #c0392b;
                border-radius: 20px;
                padding: 15px;
            }
            QLabel {
                color: #f2f2f2;
                font-family: 'Segoe UI';
                background: transparent;
            }
            QTextEdit {
                background: rgba(255, 255, 255, 0.07);
                color: #dddddd;
                font-family: 'Segoe UI';
                font-size: 13px;
                border: 1px solid #c0392b;
                border-radius: 10px;
                padding: 10px;
            }
            QCheckBox {
                color: #eeeeee;
                font-family: 'Segoe UI';
                font-size: 14px;
                padding: 6px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #c0392b;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: #e74c3c;
                border: 2px solid #c0392b;
            }
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #962d22;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Ícono y título
        icon_label = QLabel("🎙️")
        icon_label.setFont(QFont("Segoe UI", 36))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(15)
        icon_shadow.setColor(Qt.black)
        icon_shadow.setOffset(3, 3)
        icon_label.setGraphicsEffect(icon_shadow)

        title_label = QLabel("STTVAR - Términos y Condiciones")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(10)
        title_shadow.setColor(QColor(0, 0, 0, 150))
        title_shadow.setOffset(2, 2)
        title_label.setGraphicsEffect(title_shadow)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)

        # Texto de términos y condiciones
        terms_text = QTextEdit()
        terms_text.setReadOnly(True)
        terms_text.setText("""
        <h2 style='color: #e74c3c; text-align: center;'>Términos y Condiciones de Uso</h2>
            <p>
                Bienvenido a STTVAR. Al instalar y utilizar esta aplicación, usted ("el Usuario") acepta los siguientes términos y condiciones en su totalidad. Si no está de acuerdo con estos términos, no debe utilizar la aplicación.
                <br><br>
                <h4>1. Aceptación de los Términos</h4>
                El uso de STTVAR implica su aceptación expresa y sin reservas de todos los términos, condiciones y avisos contenidos en este documento.
                <br><br>
                <h4>2. Propósito y Uso de la Aplicación</h4>
                STTVAR está diseñada como una herramienta personal para la transcripción, análisis y gestión de audio y texto. Su uso está destinado únicamente para fines personales, educativos y no comerciales.
                <br><br>
                <h4>3. Privacidad y Procesamiento de Datos</h4>
                Usted reconoce y acepta que todas las grabaciones de audio, transcripciones y análisis de texto se procesan **de forma local** en su dispositivo. STTVAR no recopila, almacena, ni transmite a terceros ningún dato personal o de contenido. La responsabilidad de proteger su información recae en usted, ya que la aplicación no utiliza servicios en la nube para el procesamiento de datos.
                <br><br>
                <h4>4. Responsabilidad del Usuario</h4>
                Usted es el único responsable de obtener el consentimiento legal para grabar a cualquier individuo o para transcribir cualquier conversación. Al utilizar la aplicación, usted se compromete a cumplir con todas las leyes y regulaciones locales, nacionales e internacionales relacionadas con la privacidad, la grabación y el consentimiento. El autor de STTVAR no se hace responsable de ningún uso indebido o ilegal de esta herramienta por parte del usuario.
                <br><br>
                <h4>5. Limitación de Responsabilidad</h4>
                STTVAR se proporciona "tal cual" y sin garantías de ningún tipo, ya sean expresas o implícitas. El autor no garantiza que el funcionamiento de la aplicación sea ininterrumpido o libre de errores. En ningún caso el autor será responsable por daños directos, indirectos, incidentales o consecuentes derivados del uso o la imposibilidad de usar la aplicación.
                <br><br>
                <h4>6. Cambios en los Términos</h4>
                El autor se reserva el derecho de modificar estos Términos y Condiciones en cualquier momento, publicando una versión actualizada en el repositorio de GitHub del proyecto. El uso continuado de la aplicación después de dichas modificaciones constituirá su aceptación de los nuevos términos.
                <br><br>
                <p style='font-style: italic;'>
                Al marcar la casilla, usted confirma que ha leído, entendido y aceptado estos Términos y Condiciones.
                </p>
            </p>
        """)
        layout.addWidget(terms_text)

        # Checkbox
        self.accept_checkbox = QCheckBox("Acepto los términos y condiciones")
        checkbox_shadow = QGraphicsDropShadowEffect()
        checkbox_shadow.setBlurRadius(6)
        checkbox_shadow.setColor(QColor(0, 0, 0, 120))
        checkbox_shadow.setOffset(2, 2)
        self.accept_checkbox.setGraphicsEffect(checkbox_shadow)
        layout.addWidget(self.accept_checkbox, alignment=Qt.AlignCenter)

        # Botones
        button_layout = QHBoxLayout()
        accept_button = QPushButton("Aceptar")
        accept_button.clicked.connect(self.accept_terms)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject_terms)

        button_layout.addStretch()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumSize(480, 520)
        self.setMaximumSize(650, 550)

    def accept_terms(self):
        if self.accept_checkbox.isChecked():
            self.accept()
        else:
            QMessageBox.warning(self, "Advertencia", "Debes aceptar los términos para continuar.")

    def reject_terms(self):
        self.reject()
