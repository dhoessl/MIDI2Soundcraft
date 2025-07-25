from PySide6.QtWidgets import QSlider, QFrame, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from .models import StyledLabel, StyledFrame
from .config import SLIDER_EFFECTS


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
                background: ;
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
