from PySide6.QtWidgets import QPushButton, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from .config import BUTTON_GROUPS


class Button(QPushButton):
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
            active_color="yellow"
        )
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
