from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QFrame
)
from .slider import FullSliderFrame
from .button import (
    ButtonGroup, ButtonMatrixFrame,
    SideButtonFrame, MidiMixSideButtonFrame
)
from .log import LogOutput
from .dial import DialMatrixFrame


class APC(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.widget_matrix = ButtonMatrixFrame()
        self.widget_side_btns = SideButtonFrame()
        self.widget_mute_shift_btns = ButtonGroup("apc_mute")
        self.widget_slider = FullSliderFrame(["Reverb", "Delay"])
        self._set_style()

    def _set_style(self) -> None:
        layout = QVBoxLayout()
        layout.addStretch()
        layout.setSpacing(6)
        layout_matrix = QHBoxLayout()
        layout_matrix.addWidget(self.widget_matrix)
        layout_matrix.addWidget(self.widget_side_btns)
        layout.addLayout(layout_matrix)
        layout.addWidget(self.widget_mute_shift_btns)
        layout.addWidget(self.widget_slider)
        self.setLayout(layout)

    def set_channel_value(self, channel: int, btns: int, value: str) -> None:
        self.widget_matrix.set_value(channel, btns, value)

    def change_channels(self, inc: bool, settings: dict) -> None:
        self.widget_matrix.switch_channels(inc, settings)

    def set_side_button(self, button_id: int) -> None:
        self.widget_side_btns.set_active(button_id)

    def set_shift_button(self, state: bool) -> None:
        self.widget_mute_shift_btns.set_shift_button(state)

    def set_mute_button(self, button_id: int, state: bool) -> None:
        self.widget_mute_shift_btns.set_button(button_id, state)

    def change_slider_value(
        self, slider_id: int, value: int, label: str
    ) -> None:
        self.widget_slider.change_value(slider_id, value, label)


class MidiMix(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.widget_dials = DialMatrixFrame()
        self.widget_side_btns = MidiMixSideButtonFrame()
        self.widget_mute_shift_btns = ButtonGroup("midimix_mute")
        self.widget_recarm_btns = ButtonGroup("midimix_recarm")
        self.widget_slider = FullSliderFrame(["Chorus", "Room", "BPM"])
        self._set_style()

    def _set_style(self) -> None:
        layout = QVBoxLayout()
        layout.addStretch()
        layout_matrix = QHBoxLayout()
        layout_matrix.addWidget(self.widget_dials)
        layout_matrix.addWidget(self.widget_side_btns)
        layout.addLayout(layout_matrix)
        layout.addWidget(self.widget_mute_shift_btns)
        layout.addWidget(self.widget_recarm_btns)
        layout.addWidget(self.widget_slider)
        self.setLayout(layout)

    def change_dial_value(
        self, channel_id: int, dial_id: int, value: int, label: str
    ) -> None:
        if not self.widget_dials.change_value(
                channel_id, dial_id, value, label
        ):
            return False

    def change_dial_channels(self, settings: dict) -> None:
        self.widget_dials.change_channels(settings)

    def set_mute_button(self, button_id: int, state: bool) -> None:
        self.widget_mute_shift_btns.set_button(button_id, state)

    def set_recarm_button(self, button_id: int, state: bool) -> None:
        self.widget_recarm_btns.set_button(button_id, state)

    def change_slider_value(
        self, slider_id: int, value: int, label: str
    ) -> None:
        self.widget_slider.change_value(slider_id, value, label)


class BaseFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.widget_apc = APC()
        self.widget_midimix = MidiMix()
        self.widget_log = LogOutput()
        self.apc_shift = False
        self.midimix_shift = False
        self._set_style()

    def _set_style(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout_controllers = QHBoxLayout()
        layout_controllers.setContentsMargins(10, 0, 10, 0)
        layout_controllers.setSpacing(10)
        layout_controllers.addWidget(self.widget_apc)
        layout_controllers.addWidget(self.widget_midimix)
        layout.addLayout(layout_controllers)
        layout.addWidget(self.widget_log)
        self.setLayout(layout)

    def change_dial_value(
        self, channel_id: int, dial_id: int, value: int, label: str
    ) -> None:
        self.widget_midimix.change_dial_value(
            channel_id, dial_id, value, label
        )

    def change_dial_channels(self, settings: dict) -> None:
        self.widget_midimix.change_dial_channels(settings)

    def set_apc_channel_value(
        self, channel: int, btns: int, value: str
    ) -> None:
        self.widget_apc.set_channel_value(channel, btns, value)

    def change_apc_channels(self, inc: bool, settings: dict) -> None:
        self.widget_apc.change_channels(inc, settings)

    def set_apc_side_button(self, button_id: int) -> None:
        self.widget_apc.set_side_button(button_id)

    def set_shift_button(self, state: bool, controller: str) -> None:
        if state and controller == "apc":
            self.apc_shift = True
            if not self.midimix_shift:
                self.widget_apc.set_shift_button(state)
        elif state and controller == "midimix":
            self.midimix_shift = True
            if not self.apc_shift:
                self.widget_apc.set_shift_button(state)
        elif not state and controller == "apc":
            self.apc_shift = False
            if not self.midimix_shift:
                self.widget_apc.set_shift_button(state)
        elif not state and controller == "midimix":
            self.midimix_shift = False
            if not self.apc_shift:
                self.widget_apc.set_shift_button(state)

    def set_apc_mute_button(self, button_id: int, state: bool) -> None:
        self.widget_apc.set_mute_button(button_id, state)

    def set_midimix_mute_button(self, button_id: int, state: bool) -> None:
        self.widget_midimix.set_mute_button(button_id, state)

    def set_midimix_recarm_button(self, button_id: int, state: bool) -> None:
        self.widget_midimix.set_recarm_button(button_id, state)

    def change_apc_slider_value(
        self, slider_id: int, value: int, label: str
    ) -> None:
        self.widget_apc.change_slider_value(slider_id, value, label)

    def change_midimix_slider_value(
        self, slider_id: int, value: int, label: str
    ) -> None:
        self.widget_midimix.change_slider_value(slider_id, value, label)
