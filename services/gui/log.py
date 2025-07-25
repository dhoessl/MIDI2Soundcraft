from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtGui import QPalette, QColor


class LogOutput(QFrame):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        new_pallete = self.palette()
        new_pallete.setColor(
            QPalette.ColorRole.Window, QColor("black")
        )
        self.setPalette(new_pallete)
        layout = QVBoxLayout()

        self.setLayout(layout)
