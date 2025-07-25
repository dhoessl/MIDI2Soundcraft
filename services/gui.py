#!/home/dhoessl/venvs/midi2soundcraft/bin/python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QApplication, QHBoxLayout, QVBoxLayout,
)
from gui.slider import GroupedSliderFrame
from gui.button import ButtonGroup
from gui.log import LogOutput


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Midi and Soundcraft")
        self.setGeometry(20, 20, 1800, 900)

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
        widget_mute_shift_btns = ButtonGroup("apc_mute")
        widget_slider = GroupedSliderFrame(["Reverb", "Delay"])
        layout.addWidget(widget_mute_shift_btns)
        layout.addWidget(widget_slider)
        return layout

    def setup_midimix(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addStretch()
        widget_mute_shift_btns = ButtonGroup("midimix_mute")
        widget_recarm_btns = ButtonGroup("midimix_recarm")
        widget_slider = GroupedSliderFrame(["Chorus", "Room", "BPM"])
        layout.addWidget(widget_mute_shift_btns)
        layout.addWidget(widget_recarm_btns)
        layout.addWidget(widget_slider)
        return layout


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
