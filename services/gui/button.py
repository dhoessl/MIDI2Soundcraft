from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from .config import BUTTON_GROUPS, SIDE_BUTTONS, WINDOW_CONFIG
from .models import StyledFrame, StyledLabel, StyledButton


class Button(StyledButton):
    def __init__(
            self,
            btn_id: str | int | float,
            text: str,
            width: int = 50, height: int = 50,
            active_color: str = None,
            shift_text: str = ""
    ) -> None:
        super().__init__(text)
        self.id = btn_id
        self.text = text
        self.shift_text = shift_text
        self.active_style = self.styleSheet()
        if active_color:
            self.active_style = f"background-color: {active_color};"
        self.default_style = self.styleSheet()
        self._set_style(height)

    def _set_style(self, height) -> None:
        self.setFixedSize(50, height)

    def set_active(self) -> None:
        self.setStyleSheet(self.active_style)

    def set_inactive(self) -> None:
        self.setStyleSheet(self.default_style)

    def shift(self) -> None:
        self.setText(self.shift_text)

    def unshift(self) -> None:
        self.setText(self.text)


class ButtonGroup(QFrame):
    def __init__(self, group_id) -> None:
        super().__init__()
        self.buttons = []
        self.shift_button = None
        self._create_buttons(group_id)
        self._set_style(group_id)

    def _create_buttons(self, group_id) -> None:
        self.shift_button = Button(
            -1, "Shift",
            height=BUTTON_GROUPS[group_id]["height"],
            active_color="yellow"
        )
        self.shift_button.pressed.connect(self.shift_button.set_active)
        self.shift_button.released.connect(self.shift_button.set_inactive)
        btn_settings = BUTTON_GROUPS[group_id]
        shift_text_list = []
        if "shift_text_list" in btn_settings:
            shift_text_list = btn_settings["shift_text_list"]
        for btn_id in range(btn_settings["count"]):
            active_color = btn_settings["active_color"] if "active_color" \
                in btn_settings else None
            new_btn = Button(
                btn_id,
                btn_settings["text"],
                height=btn_settings["height"],
                active_color=active_color,
                shift_text=shift_text_list[btn_id] if shift_text_list else None
            )
            new_btn.pressed.connect(new_btn.set_active)
            new_btn.released.connect(new_btn.set_inactive)
            self.buttons.append(new_btn)

    def _set_style(self, group_id) -> None:
        self.setMaximumHeight(WINDOW_CONFIG["height"]["lower_btns"])
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(25, 0, 0, 0)
        if BUTTON_GROUPS[group_id]["height"] == 25:
            layout.setContentsMargins(25, 10, 0, 10)
        layout.setSpacing(56)
        for btn in self.buttons:
            layout.addWidget(btn)
        layout.addWidget(self.shift_button)
        if not BUTTON_GROUPS[group_id]["shift"]:
            self.shift_button.hide()
        self.setLayout(layout)

    def set_shift_button(self, state: bool) -> None:
        if self.shift_button.isHidden():
            return None
        if state:
            self.shift_button.set_active()
            for button in self.buttons:
                button.shift()
        else:
            self.shift_button.set_inactive()
            for button in self.buttons:
                button.unshift()

    def set_button(self, button_id: int, state: bool) -> None:
        for button in self.buttons:
            if state and button.id == button_id:
                button.set_active(button_id)
                return True
            elif not state and button.id == button_id:
                button.set_inactive(button_id)
                return True
            else:
                continue


class MatrixButtonGroup(StyledFrame):
    def __init__(self, channel_id: int) -> None:
        super().__init__(3)
        self.channel_id = channel_id
        self.buttons = []
        self.label_name = StyledLabel(f"Channel {self.channel_id + 1}")
        self.label_value = StyledLabel("NaN")
        self._create_buttons()
        self._set_style()

    def _set_style(self) -> None:
        self.setMaximumWidth(100)
        self.setMinimumWidth(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(15)
        layout.addStretch()
        layout.addWidget(self.label_name)
        # [::-1] to reverse list and create a grid starting
        # on bottom left on x = 0, y = 0
        for btn in self.buttons[::-1]:
            layout.addWidget(btn)
            layout.setAlignment(btn, Qt.AlignHCenter)
        layout.addWidget(self.label_value)
        layout.setAlignment(self.label_name, Qt.AlignHCenter)
        layout.setAlignment(self.label_value, Qt.AlignHCenter)
        self.setLayout(layout)

    def _create_buttons(self) -> None:
        for y in range(8):
            btn = Button(y, "", active_color="red")
            btn.pressed.connect(btn.set_active)
            btn.released.connect(btn.set_inactive)
            self.buttons.append(btn)

    def set_value(self, btns: int, value_text: str) -> None:
        for button in self.buttons:
            if button.id in list(range(btns)):
                button.set_active()
            else:
                button.set_inactive()
        self.label_value.setText(value_text)

    def switch_channel(self, inc: bool, settings: dict) -> None:
        self.channel_id += 1 if inc else -1
        self.label_name.setText(f"Channel {self.channel_id + 1}")
        channel_settings = settings[self.button_id]
        self.set_value(channel_settings["btns"], channel_settings["value"])


class ButtonMatrixFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.vertical_groups = []
        for x in range(8):
            group = MatrixButtonGroup(x)
            self.vertical_groups.append(group)
        self._set_style()

    def _set_style(self) -> None:
        self.setMaximumHeight(WINDOW_CONFIG["height"]["apc_matrix"])
        layout = QHBoxLayout()
        layout.setContentsMargins(1.5, 0, 1.5, 0)
        layout.setSpacing(6)
        for group in self.vertical_groups:
            layout.addWidget(group)
        self.setLayout(layout)

    def set_value(self, channel: int, btns: int, value_text: str) -> None:
        for channel in self.vertical_groups:
            if channel.channel_id != channel:
                continue
            channel.set_value(btns, value_text)
            return None

    def switch_channels(self, inc: bool, settings: dict) -> None:
        for channel in self.vertical_groups:
            channel.switch_channel(inc, settings)


class SideButtonFrame(StyledFrame):
    def __init__(self) -> None:
        super().__init__(3)
        self.buttons = []
        for y in range(8):
            btn = Button(
                y,
                f"{SIDE_BUTTONS[y]['name']}",
                active_color="yellow"
            )
            btn.pressed.connect(btn.set_active)
            btn.released.connect(btn.set_inactive)
            self.buttons.append(btn)
        self._set_style()

    def _set_style(self) -> None:
        self.setMinimumWidth(100)
        self.setMaximumWidth(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 35)
        layout.setSpacing(15)
        layout.addStretch()
        for button in self.buttons:
            layout.addWidget(button)
            layout.setAlignment(button, Qt.AlignHCenter)
        self.setLayout(layout)

    def set_active(self, btn: int) -> None:
        for button in self.buttons:
            if button.id == btn:
                button.set_active()
            else:
                button.set_inactive()


class MidiMixSideButtonFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.buttons = []
        for y in range(3):
            btn = Button(
                y,
                BUTTON_GROUPS["midimix_side"]["names"][y],
            )
            self.buttons.append(btn)
        self._set_style()

    def _set_style(self) -> None:
        self.setMaximumHeight(WINDOW_CONFIG["height"]["midimix_knobs"])
        self.setMaximumWidth(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        for button in self.buttons:
            layout.addWidget(button)
            layout.setAlignment(button, Qt.AlignHCenter)
        self.setLayout(layout)
