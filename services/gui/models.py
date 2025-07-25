from PySide6.QtWidgets import QLabel, QFrame
from PySide6.QtGui import QFont


class StyledLabel(QLabel):
    def __init__(self, text, font_size=12, label_max_size=15) -> None:
        super().__init__(text)
        font = QFont("MesloLGS NF Regular", font_size)
        self.setFont(font)
        self.setMaximumHeight(label_max_size)


class StyledFrame(QFrame):
    def __init__(self, line_width) -> None:
        super().__init__()
        self.setLineWidth(line_width)
        self.setFrameShape(QFrame.StyledPanel)
