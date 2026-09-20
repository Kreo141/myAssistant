import math
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import (
    QPainter,
    QPainterPath,
    QRadialGradient,
    QLinearGradient,
    QColor,
    QFont,
    QPen
)


class FloatingWindow(QWidget):
    response_received = pyqtSignal(str)
    visibility_changed = pyqtSignal(bool)
    wave_requested = pyqtSignal()
    scan_requested = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # 1. Strip window borders and force it to stay on top
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )

        # 2. Enable per-pixel alpha transparency
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Measure screen and go fullscreen
        screen = QApplication.primaryScreen().size()
        self.setGeometry(0, 0, screen.width(), screen.height())

        # Add your text
        self.label = QLabel("How may I help you?", self)
        self.label.setFont(QFont("Segoe UI", 10, QFont.Normal))
        self.label.setStyleSheet("color: #00ffcc;")
        self.label.setFixedWidth(screen.width() // 2)
        self.label.setWordWrap(True)
        self.label.move(20, 20)

        self.wave_progress = -1.0
        self.wave_elapsed = 0
        self.scan_active = False
        self.scan_phase = 0.0
        self.scan_opacity = 0.0
        self.response_text = "How may I help you?"
        self.response_index = len(self.response_text)

        self.wave_timer = QTimer(self)
        self.wave_timer.setInterval(16)
        self.wave_timer.timeout.connect(self._advance_wave)

        self.scan_timer = QTimer(self)
        self.scan_timer.setInterval(16)
        self.scan_timer.timeout.connect(self._advance_scan)

        self.response_timer = QTimer(self)
        self.response_timer.setInterval(15)
        self.response_timer.timeout.connect(self._advance_response)

        self.response_received.connect(self._update_response)
        self.visibility_changed.connect(self._update_visibility)
        self.wave_requested.connect(self._start_wave)
        self.scan_requested.connect(self._set_scan_state)

    def set_response(self, response):
        self.response_received.emit(response)

    def set_visible(self, visible):
        self.visibility_changed.emit(visible)

    def trigger_wave(self):
        self.wave_requested.emit()

    def trigger_scan(self, enabled):
        self.scan_requested.emit(bool(enabled))

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

        # Ease-out cubic
        self.wave_progress = 1.0 - (1.0 - linear_progress) ** 3

        if linear_progress >= 1.0:
            self.wave_progress = -1.0
            self.wave_timer.stop()

        self.update()

    @pyqtSlot(bool)
    def _set_scan_state(self, enabled):
        if enabled:
            self.scan_active = True
            self.show()
            if not self.scan_timer.isActive():
                self.scan_timer.start()
        else:
            self.scan_active = False
            if not self.scan_timer.isActive() and self.scan_opacity > 0.0:
                self.scan_timer.start()

        self.update()

    def _advance_scan(self):
        if self.scan_active:
            self.scan_phase = (self.scan_phase + 0.008) % 1.0
            self.scan_opacity = min(1.0, self.scan_opacity + 0.08)
        else:
            self.scan_opacity = max(0.0, self.scan_opacity - 0.08)
            if self.scan_opacity == 0.0:
                self.scan_timer.stop()

        self.update()

    def _advance_response(self):
        if self.response_index >= len(self.response_text):
            self.response_timer.stop()
            return

        self.response_index += 1
        self.label.setText(self.response_text[:self.response_index])
        self.label.adjustSize()

    @pyqtSlot(str)
    def _update_response(self, response):
        self.response_timer.stop()
        self.response_text = response or ""
        self.response_index = 0
        self.label.setText("")
        self.label.adjustSize()

        if self.response_text:
            self.response_timer.start()

    @pyqtSlot(bool)
    def _update_visibility(self, visible):
        if visible:
            self.show()
        else:
            self.hide()

    def paintEvent(self, event):
        """Draw the transparent background and animated wave."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ---------------------------------------------------------
        # Background radial gradient
        # ---------------------------------------------------------

        gradient = QRadialGradient(0, 0, 600)

        gradient.setColorAt(
            0,
            QColor(0, 0, 0, 255)
        )

        gradient.setColorAt(
            1,
            QColor(0, 0, 0, 0)
        )

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)

        painter.drawRect(self.rect())

        # ---------------------------------------------------------
        # Animated wave
        # ---------------------------------------------------------

        if self.wave_progress >= 0.0:

            width = self.width()
            height = self.height()

            front = width * self.wave_progress

            wave_width = max(
                150.0,
                width * 0.18
            )

            fade = min(
                1.0,
                max(
                    0.0,
                    (1.0 - self.wave_progress) / 0.18
                )
            )

            # -----------------------------------------------------
            # Wave gradient
            #
            # #C847FF = Purple
            # #FF47DA = Magenta
            # #FF477E = Pink/Red
            # -----------------------------------------------------

            wave_gradient = QLinearGradient(
                0,
                0,
                width,
                0
            )

            wave_gradient.setColorAt(
                0.0,
                QColor(
                    200, 71, 255,
                    int(20 * fade)
                )
            )

            wave_gradient.setColorAt(
                max(
                    0.0,
                    (front - wave_width) / width
                ),
                QColor(
                    200, 71, 255,
                    int(75 * fade)
                )
            )

            wave_gradient.setColorAt(
                min(
                    1.0,
                    front / width
                ),
                QColor(
                    255, 71, 218,
                    int(150 * fade)
                )
            )

            wave_gradient.setColorAt(
                min(
                    1.0,
                    (front + 50.0) / width
                ),
                QColor(
                    255, 71, 126,
                    0
                )
            )

            # -----------------------------------------------------
            # Wave shape
            # -----------------------------------------------------

            path = QPainterPath()

            path.moveTo(0, 0)
            path.lineTo(front, 0)

            for y in range(0, height + 24, 24):

                normalized_y = y / max(
                    1,
                    height
                )

                edge = front + 28 * (
                    math.sin(
                        normalized_y * 12.0
                        + self.wave_progress * 8.0
                    )
                )

                path.lineTo(edge, y)

            path.lineTo(0, height)
            path.closeSubpath()

            painter.setBrush(wave_gradient)
            painter.drawPath(path)

            # -----------------------------------------------------
            # Glowing wave edge
            # -----------------------------------------------------

            for glow_width, alpha in (
                (42, 18),
                (26, 28),
                (12, 48)
            ):

                glow_path = QPainterPath()

                glow_path.moveTo(front, 0)

                for y in range(0, height + 24, 24):

                    normalized_y = y / max(
                        1,
                        height
                    )

                    edge = front + 28 * (
                        math.sin(
                            normalized_y * 12.0
                            + self.wave_progress * 8.0
                        )
                    )

                    glow_path.lineTo(edge, y)

                painter.setBrush(Qt.NoBrush)

                # Pink/red glow using #FF477E
                painter.setPen(
                    QPen(
                        QColor(
                            255,
                            71,
                            126,
                            int(alpha * fade)
                        ),
                        glow_width
                    )
                )

                painter.drawPath(glow_path)

        # ---------------------------------------------------------
        # Continuous screen-analysis scan
        # ---------------------------------------------------------

        if self.scan_opacity > 0.0:
            width = self.width()
            height = self.height()
            opacity = self.scan_opacity
            scan_y = height * (0.18 + 0.64 * self.scan_phase)
            pulse = 0.75 + 0.25 * math.sin(self.scan_phase * math.pi * 8.0)

            glow_gradient = QLinearGradient(0, scan_y - 70, 0, scan_y + 70)
            glow_gradient.setColorAt(0.0, QColor(0, 255, 204, 0))
            glow_gradient.setColorAt(
                0.5,
                QColor(0, 255, 204, int(30 * opacity * pulse))
            )
            glow_gradient.setColorAt(1.0, QColor(0, 255, 204, 0))

            painter.setBrush(glow_gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, int(scan_y - 70), width, 140)

            for line_width, alpha in ((12, 18), (4, 55), (1, 190)):
                painter.setPen(
                    QPen(
                        QColor(0, 255, 204, int(alpha * opacity * pulse)),
                        line_width
                    )
                )
                painter.drawLine(24, int(scan_y), width - 24, int(scan_y))

            bracket_left = 24
            bracket_right = min(width - 24, max(180, width // 2))
            bracket_top = max(30, int(scan_y - 32))
            bracket_bottom = min(height - 30, int(scan_y + 32))
            bracket_pen = QPen(
                QColor(0, 255, 204, int(95 * opacity * pulse)),
                1
            )
            painter.setPen(bracket_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(bracket_left, bracket_top, bracket_left + 18, bracket_top)
            painter.drawLine(bracket_left, bracket_top, bracket_left, bracket_top + 18)
            painter.drawLine(bracket_right, bracket_bottom, bracket_right - 18, bracket_bottom)
            painter.drawLine(bracket_right, bracket_bottom, bracket_right, bracket_bottom - 18)

    def keyPressEvent(self, event):
        """Bind Escape to close the overlay."""
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = FloatingWindow()
    window.trigger_wave()
    window.show()

    sys.exit(app.exec_())
