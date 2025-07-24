#!/home/dhoessl/venvs/midi2soundcraft/bin/python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QApplication, QHBoxLayout, QVBoxLayout,
    QSlider, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont
import sys


SLIDER_EFFECTS = {
    "Reverb": {
        "identifier_start": 0,
        "effects": ["Time", "HF", "Bass Gain", "LPF", "HPF"],
        "color": "#ADD8E6"
    },
    "Delay": {
        "identifier_start": 5,
        "effects": ["Time", "Sub DIV", "Feedback", "LPF"],
        "color": "#FDAA48"
    },
    "Chorus": {
        "identifier_start": 9,
        "effects": ["Detune", "Density", "LPF"],
        "color": "#FF66FF"
    },
    "Room": {
        "identifier_start": 12,
        "effects": ["Time", "HF", "Bass Gain", "LPF", "HPF"],
        "color": "#66CC33"
    },
    "BPM": {
        "identifier_start": 17,
        "effects": ["BPM"],
        "color": "#ADD8E6"
    }
}

BUTTON_GROUPS = {
    "apc_mute": {
        "count": 8,
        "text": "Mute",
        "height": 50,
        "active_color": "red",
        "shift": True
    },
    "midimix_mute": {
        "count": 8,
        "text": "",
        "height": 25,
        "active_color": "red",
        "shift": True
    },
    "midimix_recarm": {
        "count": 8,
        "text": "",
        "height": 25,
        "active_color": "red",
        "shift": False
    }
}


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

        layout_apc = QVBoxLayout()
        layout_apc.addStretch()

        widget_apc_mute_shift = ButtonGroup("apc_mute")
        layout_apc.addWidget(widget_apc_mute_shift)

        widget_apc_slider = GroupedSliderFrame(["Reverb", "Delay"])
        layout_apc.addWidget(widget_apc_slider)

        layout_midimix = QVBoxLayout()
        layout_midimix.addStretch()

        widget_midimix_mute_shift = ButtonGroup("midimix_mute")
        layout_midimix.addWidget(widget_midimix_mute_shift)
        widget_midimix_recarm = ButtonGroup("midimix_recarm")
        layout_midimix.addWidget(widget_midimix_recarm)

        widget_midimix_slider = GroupedSliderFrame(["Chorus", "Room", "BPM"])
        layout_midimix.addWidget(widget_midimix_slider)

        layout_controllers.addLayout(layout_apc)
        layout_controllers.addLayout(layout_midimix)

        self.widget_log = LogOutput()
        layout_base.addWidget(self.widget_log)

        widget = QWidget()
        widget.setLayout(layout_base)
        self.setCentralWidget(widget)


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


class Button(QPushButton):
    def __init__(
            self, btn_id, text,
            height=50,
            active_color="white",
            shift_text=None
    ) -> None:
        super().__init__(text)
        self.id = btn_id
        self.shift_text = shift_text
        self.active_color = active_color
        self.default_style = self.styleSheet()
        self.setFixedSize(50, height)

    def set_active(self) -> None:
        self.setStyleSheet(f"background-color: {self.active_color};")

    def set_inactive(self) -> None:
        self.setStyleSheet(self.default_style)

    def pressed_event(self) -> None:
        self.set_active()

    def released_event(self) -> None:
        self.set_inactive()


class ButtonGroup(QFrame):
    def __init__(self, group_id) -> None:
        super().__init__()
        self.setMaximumHeight(90)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(29, 0, 0, 0)
        if BUTTON_GROUPS[group_id]["height"] == 25:
            layout.setContentsMargins(29, 10, 0, 15)
        layout.setSpacing(55)
        self.buttons = []
        self.shift_btn = Button(
            -1,
            "Shift",
            BUTTON_GROUPS[group_id]["height"],
            "yellow"
        )
        self.shift_btn.pressed.connect(self.shift_btn.set_active)
        self.shift_btn.released.connect(self.shift_btn.set_inactive)
        for btn_id in range(BUTTON_GROUPS[group_id]["count"]):
            new_btn = Button(
                btn_id,
                BUTTON_GROUPS[group_id]["text"],
                BUTTON_GROUPS[group_id]["height"],
                BUTTON_GROUPS[group_id]["active_color"] if "active_color" in BUTTON_GROUPS[group_id] else "white",  # noqa: E501
                BUTTON_GROUPS[group_id]["shift_text"] if "shift_text" in BUTTON_GROUPS[group_id] else ""  # noqa: E501
            )
            new_btn.pressed.connect(new_btn.pressed_event)
            new_btn.released.connect(new_btn.released_event)
            self.buttons.append(new_btn)
            layout.addWidget(new_btn)
        layout.addWidget(self.shift_btn)
        if not BUTTON_GROUPS[group_id]["shift"]:
            self.shift_btn.hide()
        self.setLayout(layout)


class GroupedSliderFrame(StyledFrame):
    def __init__(self, effects) -> None:
        super().__init__(3)
        self.slider = []
        self.setMaximumHeight(180)
        self.setMinimumHeight(180)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for effect in effects:
            layout.addWidget(self.get_effect_frame(effect))
        self.setLayout(layout)

    def get_effect_frame(self, effect) -> StyledFrame:
        frame = StyledFrame(2)
        if "color" in SLIDER_EFFECTS[effect]:
            frame.setStyleSheet(
                f"background-color: {SLIDER_EFFECTS[effect]['color']};"
            )
        layout = QVBoxLayout()
        layout.setContentsMargins(1.5, 0, 1.5, 0)
        layout.setSpacing(0)
        label = StyledLabel(effect)
        layout.addWidget(label)
        layout.setAlignment(label, Qt.AlignHCenter)
        layout_slider = QHBoxLayout()
        layout_slider.setSpacing(5)
        sliders = self.create_slider(effect)
        for slider in sliders:
            layout_slider.addWidget(slider)
        layout.addLayout(layout_slider)
        frame.setLayout(layout)
        return frame

    def create_slider(self, effect) -> list:
        identifier = SLIDER_EFFECTS[effect]["identifier_start"]
        sliders = []
        for effect in SLIDER_EFFECTS[effect]["effects"]:
            slider = SliderFrame(identifier, effect, 50)
            self.slider.append(slider)
            sliders.append(slider)
            identifier += 1
        return sliders


class CustomSlider(QSlider):
    def __init__(self, pos=0) -> None:
        super().__init__()
        self.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.setTickInterval(8)
        self.setMinimum(0)
        self.setMaximum(127)
        self.setMaximumHeight(130)
        self.setValue(pos)
        self.saved_value = pos
        self.setStyleSheet("""
            QSlider::handle:vertical {
                background: #CC3300;
            }
            QSlider::add-page:vertical {
                background: #CC3300;
            }
        """)

    def change_value(self, value) -> None:
        self.setValue(value)
        self.saved_value = value

    def reset_value(self) -> None:
        self.setValue(self.saved_value)


class SliderFrame(QFrame):
    def __init__(self, fid, name, slider_pos=0):
        super().__init__()
        self.setLineWidth(3)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMaximumHeight(160)
        self.setMaximumWidth(100)
        self.id = fid
        self.name = name
        layout = QVBoxLayout()
        label_id = StyledLabel(self.name)
        layout.addWidget(label_id)
        self.slider = CustomSlider(slider_pos)
        self.slider.valueChanged.connect(self.on_slider_value_changed)
        layout.addWidget(self.slider)
        self.label_value = StyledLabel("Some Value")
        layout.addWidget(self.label_value)
        layout.setAlignment(label_id, Qt.AlignHCenter)
        layout.setAlignment(self.label_value, Qt.AlignHCenter)
        layout.setAlignment(self.slider, Qt.AlignHCenter)
        self.setLayout(layout)

    def on_slider_value_changed(self, value) -> None:
        self.slider.reset_value()

    def change_slider_value(self, value) -> None:
        self.slider.change_value(value)

    def change_display_value(self, value) -> None:
        self.label_value.setText(value)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
