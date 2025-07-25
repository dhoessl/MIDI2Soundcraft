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
    },
    "midimix_side": {
        "names": {
            0: "X",
            1: "Prev",
            2: "Next"
        }
    }

}

WINDOW_CONFIG = {
    "geometry": {
        "x": 20,
        "y": 20,
        "width": 1800,
        "height": 1000
    },
    "title": "Midi and Soundcraft",
    "height": {
        "apc_matrix": 680,
        "midimix_knobs": 600,
        "lower_btns": 90,
        "fader": 200,
        "log": 150
    }
}

SIDE_BUTTONS = {
    0: {"name": "MIX"},
    1: {"name": ""},
    2: {"name": ""},
    3: {"name": ""},
    4: {"name": ""},
    5: {"name": ""},
    6: {"name": ""},
    7: {"name": "Master\nFx ret"}
}

DIAL_EFFECT_NAMES = {
    0: "Reverb",
    1: "Delay",
    2: "Chorus",
    3: "Room"
}
