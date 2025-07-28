from PySide6.QtWidgets import QSlider, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from .models import StyledLabel, StyledFrame
from .config import SLIDER_EFFECTS, WINDOW_CONFIG


class CustomSlider(QSlider):
    def __init__(self, slider_position: int = 0) -> None:
        super().__init__()
        self.saved_position = slider_position
        self._set_style()

    def _set_style(self) -> None:
        self.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.setTickInterval(16)
        self.setMinimum(0)
        self.setMaximum(127)
        self.setValue(self.saved_position)
        self.setStyleSheet("""
            QSlider::handle:vertical {
                background: #CC3300;
            }
            QSlider::add-page:vertical {
                background: #CC3300;
            }
        """)

    def change_value(self, position) -> None:
        self.setValue(position)
        self.saved_position = position

    def reset_value(self) -> None:
        self.setValue(self.saved_position)


class SliderFrame(StyledFrame):
    def __init__(
        self,
        slider_id: str | int,
        slider_name: str,
        slider_position: int = 0
    ) -> None:
        super().__init__(3)
        self.id = slider_id
        self.slider_name = slider_name
        self.label_value = StyledLabel("NaN")
        self.slider = CustomSlider(slider_position)
        # Reset Value if Fader has been changed
        self.slider.valueChanged.connect(self.slider.reset_value)
        self._set_style()

    def _set_style(self) -> None:
        label_id = StyledLabel(self.slider_name)
        # Make sure Sliders are in fixed width
        self.setMaximumWidth(100)
        self.setMinimumWidth(100)
        layout = QVBoxLayout()
        layout.addWidget(label_id)
        layout.addWidget(self.slider)
        layout.addWidget(self.label_value)
        layout.setAlignment(label_id, Qt.AlignHCenter)
        layout.setAlignment(self.label_value, Qt.AlignHCenter)
        layout.setAlignment(self.slider, Qt.AlignHCenter)
        self.setLayout(layout)

    def change_value(self, value: int, label: str) -> None:
        self.label_value.setText(label)
        self.slider.change_value(value)


class SliderFrameGroup(StyledFrame):
    def __init__(self, effect: str = None) -> None:
        super().__init__(2)
        self.sliders = []
        self._create_slider(effect)
        self._set_style(effect)

    def _create_slider(self, effect) -> None:
        identifier = SLIDER_EFFECTS[effect]["identifier_start"]
        for effect_method in SLIDER_EFFECTS[effect]["effects"]:
            self.sliders.append(SliderFrame(identifier, effect_method, 0))
            identifier += 1

    def _set_style(self, effect) -> None:
        self.setStyleSheet(
            f"background-color: {SLIDER_EFFECTS[effect]['color']};"
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(5)
        layout_slider = QHBoxLayout()
        layout_slider.setSpacing(3)

        label = StyledLabel(effect)
        layout.addWidget(label)
        layout.setAlignment(label, Qt.AlignHCenter)
        # sliders = self.create_slider(effect)
        for slider in self.sliders:
            layout_slider.addWidget(slider)
        layout.addLayout(layout_slider)
        self.setLayout(layout)

    def change_value(self, slider_id: int, value: int, label: str) -> bool:
        for slider in self.sliders:
            if slider_id == slider.id:
                slider.change_value(value, label)
                return True
        return False


class FullSliderFrame(StyledFrame):
    def __init__(self, effects) -> None:
        super().__init__(3)
        self.effects = []
        for effect in effects:
            self.effects.append(SliderFrameGroup(effect))
        self._set_style(effects)

    def _set_style(self, effects) -> None:
        self.setMaximumHeight(WINDOW_CONFIG["height"]["fader"])
        self.setMinimumHeight(WINDOW_CONFIG["height"]["fader"])
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for effect in self.effects:
            layout.addWidget(effect)
        self.setLayout(layout)

    def change_value(self, slider_id: int, value: int, label: str) -> bool:
        for effect in self.effects:
            if effect.change_value(slider_id, value, label):
                return True
        return False
