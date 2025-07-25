from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from .config import BUTTON_GROUPS, SIDE_BUTTONS, WINDOW_CONFIG
from .models import StyledFrame, StyledLabel, StyledButton


class Button(StyledButton):
    def __init__(
            self,
            btn_id: str | int | float,
            text: str,
            width: int = 50,
            height: int = 50,
            active_color: str = None,
            shift_text: str = None
    ) -> None:
        super().__init__(text)
        self.id = btn_id
        self.shift_text = shift_text
        if not active_color:
            self.active_style = self.styleSheet()
        else:
            self.active_style = f"background-color: {active_color};"
        self.default_style = self.styleSheet()
        self.setFixedSize(50, height)

    def set_active(self) -> None:
        self.setStyleSheet(self.active_style)

    def set_inactive(self) -> None:
        self.setStyleSheet(self.default_style)


class ButtonGroup(QFrame):
    def __init__(self, group_id) -> None:
        super().__init__()
        self.setMaximumHeight(WINDOW_CONFIG["height"]["lower_btns"])
        self.buttons = []
        self.shift_btn = Button(
            -1,
            "Shift",
            height=BUTTON_GROUPS[group_id]["height"],
            active_color="yellow"
        )
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(25, 0, 0, 0)
        if BUTTON_GROUPS[group_id]["height"] == 25:
            layout.setContentsMargins(25, 10, 0, 10)
        layout.setSpacing(56)
        self.shift_btn.pressed.connect(self.shift_btn.set_active)
        self.shift_btn.released.connect(self.shift_btn.set_inactive)
        shift_text_list = None
        if "shift_text_list" in BUTTON_GROUPS[group_id]:
            shift_text_list = BUTTON_GROUPS[group_id]["shift_text_list"]
        for btn_id in range(BUTTON_GROUPS[group_id]["count"]):
            active_color = None
            if "active_color" in BUTTON_GROUPS[group_id]:
                active_color = BUTTON_GROUPS[group_id]["active_color"]
            new_btn = Button(
                btn_id,
                BUTTON_GROUPS[group_id]["text"],
                height=BUTTON_GROUPS[group_id]["height"],
                active_color=active_color,
                shift_text=shift_text_list[btn_id] if shift_text_list else None
            )
            new_btn.pressed.connect(new_btn.set_active)
            new_btn.released.connect(new_btn.set_inactive)
            self.buttons.append(new_btn)
            layout.addWidget(new_btn)
        layout.addWidget(self.shift_btn)
        if not BUTTON_GROUPS[group_id]["shift"]:
            self.shift_btn.hide()
        self.setLayout(layout)


class MatrixButtonGroup(StyledFrame):
    def __init__(self, channel_id) -> None:
        super().__init__(3)
        self.setMaximumWidth(100)
        self.setMinimumWidth(100)
        self.buttons = []
        self.label_name = StyledLabel(channel_id)
        self.label_value = StyledLabel("Mix Value")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(15)
        layout.addStretch()
        self.create_buttons()
        layout.addWidget(self.label_name)
        for btn in self.buttons[::-1]:
            layout.addWidget(btn)
            layout.setAlignment(btn, Qt.AlignHCenter)
        layout.addWidget(self.label_value)
        layout.setAlignment(self.label_name, Qt.AlignHCenter)
        layout.setAlignment(self.label_value, Qt.AlignHCenter)
        self.setLayout(layout)

    def create_buttons(self) -> None:
        for y in range(8):
            btn = Button(y, "", active_color="red")
            btn.pressed.connect(btn.set_active)
            btn.released.connect(btn.set_inactive)
            self.buttons.append(btn)


class ButtonMatrixFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setMaximumHeight(WINDOW_CONFIG["height"]["apc_matrix"])
        self.vertical_groups = []
        layout = QHBoxLayout()
        layout.setContentsMargins(1.5, 0, 1.5, 0)
        layout.setSpacing(6)
        for x in range(8):
            group = MatrixButtonGroup(f"Channel {x+1}")
            self.vertical_groups.append(group)
            layout.addWidget(group)
        self.setLayout(layout)


class SideButtonFrame(StyledFrame):
    def __init__(self) -> None:
        super().__init__(3)
        self.buttons = []
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 35)
        layout.setSpacing(15)
        layout.addStretch()
        for y in range(8):
            btn = Button(
                y,
                f"{SIDE_BUTTONS[y]['name']}",
                active_color="yellow"
            )
            btn.pressed.connect(btn.set_active)
            btn.released.connect(btn.set_inactive)
            self.buttons.append(btn)
            layout.addWidget(btn)
            layout.setAlignment(btn, Qt.AlignHCenter)
        self.setLayout(layout)


class MidiMixSideButtonFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.buttons = []
        self.setMaximumHeight(WINDOW_CONFIG["height"]["midimix_knobs"])
        self.setMaximumWidth(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        for y in range(3):
            btn = Button(
                y,
                BUTTON_GROUPS["midimix_side"]["names"][y],
            )
            self.buttons.append(btn)
            layout.addWidget(btn)
            layout.setAlignment(btn, Qt.AlignHCenter)
        self.setLayout(layout)
