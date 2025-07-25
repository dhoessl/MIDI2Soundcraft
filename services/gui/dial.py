from PySide6.QtWidgets import QDial, QFrame, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from .models import StyledFrame, StyledLabel
from .config import DIAL_EFFECT_NAMES, WINDOW_CONFIG


class CustomDial(QDial):
    def __init__(self, dial_id, value=0, vmin=0, vmax=127) -> None:
        super().__init__()
        self.id = dial_id
        self.setMinimum(vmin)
        self.setMaximum(vmax)
        self.setValue(value)
        self.saved_value = value

    def change_value(self, value) -> None:
        self.setValue(value)
        self.saved_value = value

    def reset_value(self) -> None:
        self.setValue(self.saved_value)


class DialFrame(QFrame):
    def __init__(self, dial_id, value=0, value_text="None", name="Dial"):
        super().__init__()
        self.dial = CustomDial(dial_id, value)
        self.dial.valueChanged.connect(self.dial.reset_value)
        self.label_name = StyledLabel(name)
        self.label_value = StyledLabel(value_text)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(5)
        layout.addWidget(self.label_name)
        layout.addWidget(self.dial)
        layout.addWidget(self.label_value)
        layout.setAlignment(self.label_name, Qt.AlignHCenter)
        layout.setAlignment(self.dial, Qt.AlignHCenter)
        layout.setAlignment(self.label_value, Qt.AlignHCenter)
        self.setLayout(layout)

    def change_value(self, value) -> None:
        self.dial.setValue(value)

    def get_dial_id(self) -> str | int:
        return self.dial.id


class ChannelDialFrame(StyledFrame):
    def __init__(self, channel_id) -> None:
        super().__init__(3)
        self.id = channel_id
        # 0: Reverb, 1: Delay, 2: Chorus, 3: Room
        self.dials = []
        self.label = StyledLabel(f"Channel {self.id}", 14, 20)
        layout_outer = QVBoxLayout()
        layout_outer.addWidget(self.label)
        layout_outer.setAlignment(self.label, Qt.AlignHCenter)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(3)
        for x in range(4):
            widget_dial = DialFrame(x, name=DIAL_EFFECT_NAMES[x])
            self.dials.append(widget_dial)
            layout.addWidget(widget_dial)
        layout_outer.addLayout(layout)
        self.setLayout(layout_outer)

    def change_value(self, dial_id, value) -> None:
        for dial in self.dials:
            if dial.get_dial_id() == dial_id:
                dial.change_value(value)

    def change_channel(self, channel_id) -> None:
        self.id = channel_id
        self.label.setText(f"Channel {self.id}")


class DialMatrixFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.channels = []
        self.setMaximumHeight(WINDOW_CONFIG["height"]["midimix_knobs"])
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch()
        for y in range(3):
            layout_dials = self.create_dial_hbox(y)
            layout.addLayout(layout_dials)
        self.setLayout(layout)

    def create_dial_hbox(self, counter) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        for x in range(2):
            channel_dials = ChannelDialFrame((counter * 2) + x)
            layout.addWidget(channel_dials)
            self.channels.append(channel_dials)
        return layout

    def change_value(self, channel_id, dial_id, value) -> None:
        for channel in self.channels:
            if channel.id == channel_id:
                channel.change_value(dial_id, value)

    def change_channels(self) -> None:
        pass
