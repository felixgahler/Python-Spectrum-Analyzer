SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (1, 1, 4)
GRID_COLOR = (50, 50, 50)
VOLUME_FACTOR = 1.5
BARS_START_COLOR = (0, 0, 255)  
BARS_END_COLOR = (128, 0, 128)

# Kontrollfenster-Konfiguration
CONTROL_WINDOW_WIDTH = 800
CONTROL_WINDOW_HEIGHT = 200

# Farbschemata
COLOR_SCHEMES = {
    "Blau-Lila": [(0, 0, 255), (128, 0, 128)],
    "Rot-Gelb": [(255, 0, 0), (255, 255, 0)],
    "Grün-Cyan": [(0, 255, 0), (0, 255, 255)],
    "Rainbow": [(255, 0, 0), (0, 255, 0)]
}

# Visualisierungsmodi
VISUALIZATION_MODES = ["Balken", "Wellen", "Punkte"]

# Equalizer Frequenzbänder (Hz)
EQ_BANDS = [
    31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000
]

# Standard EQ Einstellungen
DEFAULT_EQ_GAINS = [1.0] * 10  # Alle Bänder auf 1.0 (neutral)

# Audio-Effekt Einstellungen
EFFECTS = {
    "Echo": {
        "enabled": False,
        "delay": 0.1,
        "feedback": 0.3
    },
    "Reverb": {
        "enabled": False,
        "room_size": 0.5,
        "damping": 0.5,
        "wet_level": 0.3
    },
    "Flanger": {
        "enabled": False,
        "depth": 0.5,     # 0-1
        "rate": 0.5,      # Hz
        "feedback": 0.5,  # 0-1
        "wet": 0.5       # 0-1
    },
    "AutoTune": {
        "enabled": False,
        "key": "C",       # Grundton
        "scale": "major", # Tonleiter
        "strength": 0.5   # 0-1
    },
    "Sidechain": {
        "enabled": False,
        "threshold": -20,  # dB
        "ratio": 4,       # Kompressionsverhältnis
        "attack": 0.1,    # Sekunden
        "release": 0.2    # Sekunden
    },
    "Ducking": {
        "enabled": False,
        "threshold": -20,  # dB
        "reduction": 0.5,  # 0-1
        "attack": 0.1,    # Sekunden
        "release": 0.2    # Sekunden
    }
}

# Tonleiter für Auto-Tune
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10]
}

# Grundtöne für Auto-Tune
KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
