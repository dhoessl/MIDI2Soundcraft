from PySide6.QtWidgets import (
    QMainWindow, QWidget, QApplication, QHBoxLayout, QVBoxLayout
)
from PySide6.QtGui import QColor, QPalette
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Midi and Soundcraft")
        self.setGeometry(100, 100, 1200, 800)

        layout_base = QVBoxLayout()
        layout_base.setContentsMargins(20, 0, 20, 0)
        layout_base.setSpacing(20)

        layout_controllers = QHBoxLayout()
        layout_base.addLayout(layout_controllers)

        layout_apc = QVBoxLayout()
        layout_midimix = QVBoxLayout()

        layout_controllers.addLayout(layout_apc)
        layout_controllers.addLayout(layout_midimix)

        layout_log = QHBoxLayout()

        colored_widget = QWidget()
        colored_widget.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("black"))
        colored_widget.setPalette(palette)
        layout_log.addWidget(colored_widget)

        layout_base.addLayout(layout_log)

        widget = QWidget()
        widget.setLayout(layout_base)
        self.setCentralWidget(widget)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
