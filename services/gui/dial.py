from PySide6.QtWidgets import QDial, QFrame, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from .models import StyledFrame, StyledLabel
from .config import DIAL_EFFECT_NAMES, WINDOW_CONFIG


class CustomDial(QDial):
    def __init__(
        self, dial_id: str | int,
        value: int = 0, vmin: int = 0, vmax: int = 127
    ) -> None:
        super().__init__()
        self.id = dial_id
        self.saved_value = value
        self._set_style(value, vmin, vmax)

    def _set_style(self, value: int, vmin: int, vmax: int) -> None:
        self.setMinimum(vmin)
        self.setMaximum(vmax)
        self.setValue(value)

    def change_value(self, value: int) -> None:
        self.saved_value = value
        self.reset_value()

    def reset_value(self) -> None:
        self.setValue(self.saved_value)


class DialFrame(QFrame):
    def __init__(
        self, dial_id: str | int,
        value: int = 0,
        value_text: str = "NaN",
        name: str = "Dial"
    ) -> None:
        super().__init__()
        self.dial = CustomDial(dial_id, value)
        self.dial.valueChanged.connect(self.dial.reset_value)
        self.label_name = StyledLabel(name)
        self.label_value = StyledLabel(value_text)
        self._set_style()

    def _set_style(self) -> None:
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

    def change_value(self, dial_id: int, value: int, label: str) -> bool:
        if self.dial.id == dial_id:
            self.dial.change_value(value)
            self.label_value.setText(f"{label}")
            return True
        return False


class ChannelDialFrame(StyledFrame):
    def __init__(self, channel_id: int) -> None:
        super().__init__(3)
        self.id = channel_id
        # 0: Reverb, 1: Delay, 2: Chorus, 3: Room
        self.dials = []
        self.label = StyledLabel(f"Channel {self.id + 1}", 14, 20)
        for x in range(4):
            self.dials.append(DialFrame(x, name=DIAL_EFFECT_NAMES[x]))
        self._set_style()

    def _set_style(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setAlignment(self.label, Qt.AlignHCenter)
        layout_dials = QHBoxLayout()
        layout_dials.setContentsMargins(5, 0, 5, 0)
        layout_dials.setSpacing(3)
        for widget_dial in self.dials:
            layout_dials.addWidget(widget_dial)
        layout.addLayout(layout_dials)
        self.setLayout(layout)

    def change_value(
        self,
        channel_id: int, dial_id: int,
        value: int, label: str
    ) -> bool:
        if not channel_id == self.id:
            return False
        for dial in self.dials:
            if dial.change_value(dial_id, value, label):
                return True
        return False

    def change_channel(self, settings: dict) -> None:
        self.id = self.id - 6 if self.id > 5 else self.id + 6
        self.label.setText(f"Channel {self.id + 1}")
        for dial_id in settings[self.id]:
            self.change_value(
                self.id, dial_id,
                settings[self.id][dial_id]["value"],
                settings[self.id][dial_id]["label"]
            )


class DualChannelDialFrame(QFrame):
    def __init__(self, start_channel_id: int) -> None:
        super().__init__()
        self.channels = []
        for x in range(2):
            self.channels.append(ChannelDialFrame(start_channel_id + x))
        self._set_style()

    def _set_style(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        for widget in self.channels:
            layout.addWidget(widget)
        self.setLayout(layout)

    def change_value(
        self, channel_id: int, dial_id: int,
        value: int, label: str
    ) -> bool:
        for channel in self.channels:
            if channel.change_value(channel_id, dial_id, value, label):
                return True
        return False

    def change_channels(self, settings: dict) -> None:
        for channel in self.channels:
            channel.change_channel(settings)


class DialMatrixFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.frames = []
        for frame_id in range(3):
            self.frames.append(DualChannelDialFrame(frame_id * 2))
        self._set_style()

    def _set_style(self) -> None:
        self.setMaximumHeight(WINDOW_CONFIG["height"]["midimix_knobs"])
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch()
        for frame in self.frames:
            layout.addWidget(frame)
        self.setLayout(layout)

    def change_value(
        self,
        channel_id: int, dial_id: int, value: int,
        label: str
    ) -> bool:
        for frame in self.frames:
            if frame.change_value(channel_id, dial_id, value, label):
                return True
        return False

    def change_channels(self, settings: dict) -> None:
        for frame in self.frames:
            frame.change_channels(settings)
