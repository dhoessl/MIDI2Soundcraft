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
        "shift": False
    },
    "midimix_recarm": {
        "count": 8,
        "text": "",
        "height": 25,
        "active_color": "red",
        "shift": False
    }
}
