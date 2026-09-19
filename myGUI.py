import math
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QPainterPath, QRadialGradient, QLinearGradient, QColor, QFont, QPen

class FloatingWindow(QWidget):
    response_received = pyqtSignal(str)
    visibility_changed = pyqtSignal(bool)
    wave_requested = pyqtSignal()

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
        self.label.setFixedWidth(screen.width() // 2)
        self.label.setWordWrap(True)
        self.label.move(20, 20)
        self.wave_progress = -1.0
        self.wave_elapsed = 0
        self.wave_timer = QTimer(self)
        self.wave_timer.setInterval(16)
        self.wave_timer.timeout.connect(self._advance_wave)
        self.response_received.connect(self._update_response)
        self.visibility_changed.connect(self._update_visibility)
        self.wave_requested.connect(self._start_wave)

    def set_response(self, response):
        self.response_received.emit(response)

    def set_visible(self, visible):
        self.visibility_changed.emit(visible)

    def trigger_wave(self):
        self.wave_requested.emit()

    @pyqtSlot()
    def _start_wave(self):
        self.show()
        self.wave_progress = 0.0
        self.wave_elapsed = 0
        self.wave_timer.start()
        self.update()

    def _advance_wave(self):
        self.wave_elapsed += self.wave_timer.interval()
        linear_progress = min(1.0, self.wave_elapsed / 1100.0)
        self.wave_progress = 1.0 - (1.0 - linear_progress) ** 3

        if linear_progress >= 1.0:
            self.wave_progress = -1.0
            self.wave_timer.stop()
        self.update()

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

        if self.wave_progress >= 0.0:
            width = self.width()
            height = self.height()
            front = width * self.wave_progress
            wave_width = max(150.0, width * 0.18)
            fade = min(1.0, max(0.0, (1.0 - self.wave_progress) / 0.18))

            wave_gradient = QLinearGradient(0, 0, width, 0)
            wave_gradient.setColorAt(0.0, QColor(0, 255, 204, int(20 * fade)))
            wave_gradient.setColorAt(max(0.0, (front - wave_width) / width), QColor(0, 255, 204, int(75 * fade)))
            wave_gradient.setColorAt(min(1.0, front / width), QColor(80, 180, 255, int(150 * fade)))
            wave_gradient.setColorAt(min(1.0, (front + 50.0) / width), QColor(255, 70, 190, 0))

            path = QPainterPath()
            path.moveTo(0, 0)
            path.lineTo(front, 0)
            for y in range(0, height + 24, 24):
                normalized_y = y / max(1, height)
                edge = front + 28 * (
                    math.sin(normalized_y * 12.0 + self.wave_progress * 8.0)
                )
                path.lineTo(edge, y)
            path.lineTo(0, height)
            path.closeSubpath()

            painter.setBrush(wave_gradient)
            painter.drawPath(path)

            for glow_width, alpha in ((42, 18), (26, 28), (12, 48)):
                glow_path = QPainterPath()
                glow_path.moveTo(front, 0)
                for y in range(0, height + 24, 24):
                    normalized_y = y / max(1, height)
                    edge = front + 28 * (
                        math.sin(normalized_y * 12.0 + self.wave_progress * 8.0)
                    )
                    glow_path.lineTo(edge, y)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(100, 220, 255, int(alpha * fade)), glow_width))
                painter.drawPath(glow_path)

    def keyPressEvent(self, event):
        """Bind the Escape key to close so you don't get trapped."""
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())