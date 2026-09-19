import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QFont

class FloatingWindow(QWidget):
    response_received = pyqtSignal(str)
    visibility_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        
        # 1. Strip window borders and force it to stay on top
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        
        # 2. The Magic Flag: Tell Windows this app uses per-pixel alpha transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Measure screen and go fullscreen
        screen = QApplication.primaryScreen().size()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        # Add your text
        self.label = QLabel("How may I help you?", self)
        self.label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.label.setStyleSheet("color: #00ffcc;")
        self.label.move(20, 20)
        self.response_received.connect(self._update_response)
        self.visibility_changed.connect(self._update_visibility)

    def set_response(self, response):
        self.response_received.emit(response)

    def set_visible(self, visible):
        self.visibility_changed.emit(visible)

    @pyqtSlot(str)
    def _update_response(self, response):
        self.label.setText(response)
        self.label.adjustSize()

    @pyqtSlot(bool)
    def _update_visibility(self, visible):
        if visible:
            self.show()
        else:
            self.hide()

    def paintEvent(self, event):
        """This function automatically runs to draw the background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create a radial gradient starting at the top-left (0,0) with a 600px radius
        gradient = QRadialGradient(0, 0, 600)
        
        # Center of the circle: Solid Black (Red, Green, Blue, Alpha)
        gradient.setColorAt(0, QColor(0, 0, 0, 255))
        
        # Outer edge of the circle: 100% Transparent Black
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        
        # Draw a rectangle covering the whole screen to hold our gradient
        painter.drawRect(self.rect())

    def keyPressEvent(self, event):
        """Bind the Escape key to close so you don't get trapped."""
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())