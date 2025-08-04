from PySide6.QtWidgets import QFrame, QVBoxLayout
from .config import WINDOW_CONFIG


class LogOutput(QFrame):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setMinimumHeight(WINDOW_CONFIG["height"]["log"])
        self.setMaximumHeight(WINDOW_CONFIG["height"]["log"])
        self.setStyleSheet("background-color: 'black';")
        layout = QVBoxLayout()

        self.setLayout(layout)
