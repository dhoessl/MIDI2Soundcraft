#!/home/dhoessl/venvs/midi2soundcraft/bin/python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QApplication,
    QHBoxLayout, QVBoxLayout
)
from gui.slider import GroupedSliderFrame
from gui.button import (
    ButtonGroup, ButtonMatrixFrame,
    SideButtonFrame, MidiMixSideButtonFrame
)
from gui.log import LogOutput
from gui.config import WINDOW_CONFIG
from gui.dial import DialMatrixFrame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #A7AFB6;")
        self.setWindowTitle("Midi and Soundcraft")
        geo = WINDOW_CONFIG["geometry"]
        self.setGeometry(
            geo["x"], geo["y"],
            geo["width"], geo["height"]
        )

        layout_base = QVBoxLayout()
        layout_base.setContentsMargins(0, 0, 0, 0)
        layout_base.addStretch()

        layout_controllers = QHBoxLayout()
        layout_controllers.setContentsMargins(10, 0, 10, 0)
        layout_controllers.setSpacing(10)
        layout_base.addLayout(layout_controllers)

        layout_apc = self.setup_apc()
        layout_midimix = self.setup_midimix()
        layout_controllers.addLayout(layout_apc)
        layout_controllers.addLayout(layout_midimix)

        self.widget_log = LogOutput()
        layout_base.addWidget(self.widget_log)

        widget = QWidget()
        widget.setLayout(layout_base)
        self.setCentralWidget(widget)

    def setup_apc(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addStretch()
        layout.setSpacing(6)
        layout_matrix = QHBoxLayout()
        widget_matrix = ButtonMatrixFrame()
        widget_side_btns = SideButtonFrame()
        layout_matrix.addWidget(widget_matrix)
        layout_matrix.addWidget(widget_side_btns)
        widget_mute_shift_btns = ButtonGroup("apc_mute")
        widget_slider = GroupedSliderFrame(["Reverb", "Delay"])
        layout.addLayout(layout_matrix)
        layout.addWidget(widget_mute_shift_btns)
        layout.addWidget(widget_slider)
        return layout

    def setup_midimix(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addStretch()
        layout_matrix = QHBoxLayout()
        widget_dials = DialMatrixFrame()
        widget_side_btns = MidiMixSideButtonFrame()
        layout_matrix.addWidget(widget_dials)
        layout_matrix.addWidget(widget_side_btns)
        widget_mute_shift_btns = ButtonGroup("midimix_mute")
        widget_recarm_btns = ButtonGroup("midimix_recarm")
        widget_slider = GroupedSliderFrame(["Chorus", "Room", "BPM"])
        layout.addLayout(layout_matrix)
        layout.addWidget(widget_mute_shift_btns)
        layout.addWidget(widget_recarm_btns)
        layout.addWidget(widget_slider)
        return layout


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
