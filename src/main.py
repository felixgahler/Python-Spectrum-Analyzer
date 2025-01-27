import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, VOLUME_FACTOR, COLOR_SCHEMES, VISUALIZATION_MODES, EQ_BANDS, EFFECTS, SCALES, KEYS
from spectrum_visualizer import SpectrumVisualizer
from audio_stream import AudioStream
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QSlider, QLabel, QHBoxLayout, QComboBox, QFileDialog, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
import soundfile as sf  # statt pydub, io und wave

class ControlWindow(QMainWindow):
    def __init__(self, audio_callback):
        super().__init__()
        self.audio_callback = audio_callback
        self.is_recording = False
        self.is_saving = False
        self.volume = 1.0
        self.recorded_data = []
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Controls')
        self.setGeometry(0, SCREEN_HEIGHT + 50, SCREEN_WIDTH, 150)  # Höhe vergrößert
        
        # Zentrales Widget und Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Obere Reihe
        top_row = QHBoxLayout()
        
        # Start/Stop Button
        self.play_button = QPushButton('Start')
        self.play_button.clicked.connect(self.toggle_recording)
        top_row.addWidget(self.play_button)
        
        # Aufnahme Button
        self.record_button = QPushButton('Aufnahme Start')
        self.record_button.clicked.connect(self.toggle_recording_save)
        top_row.addWidget(self.record_button)
        
        # Visualisierungsmodus Dropdown
        viz_label = QLabel('Visualisierung:')
        top_row.addWidget(viz_label)
        self.viz_mode_combo = QComboBox()
        self.viz_mode_combo.addItems(VISUALIZATION_MODES)
        top_row.addWidget(self.viz_mode_combo)
        
        # Farbschema Dropdown
        color_label = QLabel('Farbschema:')
        top_row.addWidget(color_label)
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems(COLOR_SCHEMES.keys())
        top_row.addWidget(self.color_scheme_combo)
        
        main_layout.addLayout(top_row)
        
        # Untere Reihe
        bottom_row = QHBoxLayout()
        
        # Lautstärke Label und Slider
        volume_label = QLabel('Lautstärke:')
        bottom_row.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(200)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        bottom_row.addWidget(self.volume_slider)
        
        main_layout.addLayout(bottom_row)
        
        # Equalizer Bereich
        eq_group = QGroupBox("Equalizer")
        eq_layout = QHBoxLayout()
        
        # 10 Slider für den Equalizer
        self.eq_sliders = []
        for i, freq in enumerate(EQ_BANDS):
            slider_container = QWidget()
            slider_layout = QVBoxLayout(slider_container)
            
            # Frequenz-Label
            freq_label = QLabel(f"{freq}Hz")
            freq_label.setAlignment(Qt.AlignCenter)
            slider_layout.addWidget(freq_label)
            
            # Slider
            slider = QSlider(Qt.Vertical)
            slider.setMinimum(0)
            slider.setMaximum(200)
            slider.setValue(100)  # Standardwert = 1.0
            slider.setFixedHeight(100)
            slider.valueChanged.connect(lambda v, idx=i: self.update_eq(idx, v))
            slider_layout.addWidget(slider)
            
            # dB-Label
            db_label = QLabel("0 dB")
            db_label.setAlignment(Qt.AlignCenter)
            slider_layout.addWidget(db_label)
            
            eq_layout.addWidget(slider_container)
            self.eq_sliders.append((slider, db_label))
        
        eq_group.setLayout(eq_layout)
        main_layout.addWidget(eq_group)
        
        # Effekte Bereich
        effects_group = QGroupBox("Effekte")
        effects_layout = QVBoxLayout()
        
        # Echo Controls
        echo_layout = QHBoxLayout()
        self.echo_checkbox = QCheckBox("Echo")
        self.echo_checkbox.stateChanged.connect(self.update_effects)
        echo_layout.addWidget(self.echo_checkbox)
        
        echo_delay_label = QLabel("Delay:")
        echo_layout.addWidget(echo_delay_label)
        self.echo_delay_slider = QSlider(Qt.Horizontal)
        self.echo_delay_slider.setRange(1, 50)  # 10-500ms
        self.echo_delay_slider.setValue(10)
        self.echo_delay_slider.valueChanged.connect(self.update_effects)
        echo_layout.addWidget(self.echo_delay_slider)
        
        effects_layout.addLayout(echo_layout)
        
        # Reverb Controls
        reverb_layout = QHBoxLayout()
        self.reverb_checkbox = QCheckBox("Reverb")
        self.reverb_checkbox.stateChanged.connect(self.update_effects)
        reverb_layout.addWidget(self.reverb_checkbox)
        
        reverb_size_label = QLabel("Room Size:")
        reverb_layout.addWidget(reverb_size_label)
        self.reverb_size_slider = QSlider(Qt.Horizontal)
        self.reverb_size_slider.setRange(0, 100)
        self.reverb_size_slider.setValue(50)
        self.reverb_size_slider.valueChanged.connect(self.update_effects)
        reverb_layout.addWidget(self.reverb_size_slider)
        
        effects_layout.addLayout(reverb_layout)
        
        # Flanger Controls
        flanger_layout = QHBoxLayout()
        self.flanger_checkbox = QCheckBox("Flanger")
        self.flanger_checkbox.stateChanged.connect(self.update_effects)
        flanger_layout.addWidget(self.flanger_checkbox)
        
        flanger_rate_label = QLabel("Rate:")
        flanger_layout.addWidget(flanger_rate_label)
        self.flanger_rate_slider = QSlider(Qt.Horizontal)
        self.flanger_rate_slider.setRange(1, 100)
        self.flanger_rate_slider.setValue(50)
        self.flanger_rate_slider.valueChanged.connect(self.update_effects)
        flanger_layout.addWidget(self.flanger_rate_slider)
        
        effects_layout.addLayout(flanger_layout)
        
        # Auto-Tune Controls
        autotune_layout = QHBoxLayout()
        self.autotune_checkbox = QCheckBox("Auto-Tune")
        self.autotune_checkbox.stateChanged.connect(self.update_effects)
        autotune_layout.addWidget(self.autotune_checkbox)
        
        self.key_combo = QComboBox()
        self.key_combo.addItems(KEYS)
        autotune_layout.addWidget(self.key_combo)
        
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(SCALES.keys())
        autotune_layout.addWidget(self.scale_combo)
        
        effects_layout.addLayout(autotune_layout)
        
        # Sidechain/Ducking Controls
        dynamics_layout = QHBoxLayout()
        self.sidechain_checkbox = QCheckBox("Sidechain")
        self.sidechain_checkbox.stateChanged.connect(self.update_effects)
        dynamics_layout.addWidget(self.sidechain_checkbox)
        
        self.ducking_checkbox = QCheckBox("Ducking")
        self.ducking_checkbox.stateChanged.connect(self.update_effects)
        dynamics_layout.addWidget(self.ducking_checkbox)
        
        effects_layout.addLayout(dynamics_layout)
        
        effects_group.setLayout(effects_layout)
        main_layout.addWidget(effects_group)
        
    def toggle_recording(self):
        self.is_recording = not self.is_recording
        self.play_button.setText('Stop' if self.is_recording else 'Start')
        print("Aufnahme gestartet..." if self.is_recording else "Aufnahme gestoppt.")
        
    def toggle_recording_save(self):
        self.is_saving = not self.is_saving
        if self.is_saving:
            self.recorded_data = []
            self.record_button.setText('Aufnahme Stop')
            print("Aufnahme wird gespeichert...")
        else:
            self.record_button.setText('Aufnahme Start')
            self.save_recording()
            
    def save_recording(self):
        if self.recorded_data:
            try:
                # Dialog zum Speichern der Datei
                file_name, _ = QFileDialog.getSaveFileName(self, 
                    "Aufnahme speichern", 
                    "recording.wav",
                    "Audio Files (*.wav)")
                
                if file_name:
                    # Konvertiere die Numpy Arrays in ein einzelnes Array
                    audio_data = np.concatenate(self.recorded_data)
                    
                    # Als WAV-Datei speichern
                    sf.write(file_name, audio_data, 44100)  # 44100 ist die Sample Rate
                    
                    print(f"Aufnahme gespeichert als: {file_name}")
            except Exception as e:
                print(f"Fehler beim Speichern: {str(e)}")
        
    def update_volume(self):
        self.volume = self.volume_slider.value() / 100.0
        
    def update_eq(self, band_index, value):
        """
        Aktualisiert die EQ-Einstellungen
        """
        gain = value / 100.0  # Konvertiere Slider-Wert zu Gain
        db_value = 20 * np.log10(gain)  # Konvertiere zu dB
        self.eq_sliders[band_index][1].setText(f"{db_value:.1f} dB")
        
    def update_effects(self):
        effects = {
            "Echo": {
                "enabled": self.echo_checkbox.isChecked(),
                "delay": self.echo_delay_slider.value() / 100.0,
                "feedback": 0.3
            },
            "Reverb": {
                "enabled": self.reverb_checkbox.isChecked(),
                "room_size": self.reverb_size_slider.value() / 100.0,
                "damping": 0.5,
                "wet_level": 0.3
            },
            "Flanger": {
                "enabled": self.flanger_checkbox.isChecked(),
                "depth": 0.5,
                "rate": self.flanger_rate_slider.value() / 100.0,
                "feedback": 0.5,
                "wet": 0.5
            },
            "AutoTune": {
                "enabled": self.autotune_checkbox.isChecked(),
                "key": self.key_combo.currentText(),
                "scale": self.scale_combo.currentText(),
                "strength": 0.8
            },
            "Sidechain": {
                "enabled": self.sidechain_checkbox.isChecked(),
                "threshold": -20,
                "ratio": 4,
                "attack": 0.1,
                "release": 0.2
            },
            "Ducking": {
                "enabled": self.ducking_checkbox.isChecked(),
                "threshold": -20,
                "reduction": 0.5,
                "attack": 0.1,
                "release": 0.2
            }
        }
        return effects

    def get_state(self):
        state = {
            'is_recording': self.is_recording,
            'is_saving': self.is_saving,
            'volume': self.volume,
            'viz_mode': self.viz_mode_combo.currentText(),
            'color_scheme': self.color_scheme_combo.currentText()
        }
        # EQ-Einstellungen hinzufügen
        state['eq_gains'] = [slider[0].value() / 100.0 for slider in self.eq_sliders]
        state['effects'] = self.update_effects()
        return state

def main():
    """
    inits Pygame env, sets up visualizer and audio stream,
    processes real-time audio data for visualization
    """
    pygame.init()
    
    # PyQt5 App initialisieren
    app = QApplication([])
    
    # Hauptfenster für Visualisierung
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spectrum Analyzer")
    icon = pygame.image.load("src/assets/icon.png")
    pygame.display.set_icon(icon)
    
    audio_stream = AudioStream()
    visualizer = SpectrumVisualizer(screen)
    clock = pygame.time.Clock()
    
    # Kontrollfenster erstellen
    control_window = ControlWindow(None)
    control_window.show()
    
    # Timer für Updates
    def update():
        # Pygame Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.quit()
                return
        
        # Status vom Kontrollfenster holen
        state = control_window.get_state()
        
        # Visualisierung aktualisieren
        if state['is_recording']:
            # EQ-Einstellungen aktualisieren
            for i, gain in enumerate(state['eq_gains']):
                audio_stream.set_eq_gain(i, gain)
                
            audio_data = audio_stream.get_audio_data(volume_factor=state['volume'])
            if state['is_saving']:
                control_window.recorded_data.append(audio_data.copy())
            
            # Visualisierungsmodus und Farbschema aktualisieren
            visualizer.set_mode(state['viz_mode'])
            color_scheme = COLOR_SCHEMES[state['color_scheme']]
            visualizer.set_colors(*color_scheme)
            
            visualizer.update(audio_data)
        else:
            visualizer.clear()
        
        pygame.display.flip()
        clock.tick(60)
    
    # Timer für regelmäßige Updates einrichten
    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(16)  # Ca. 60 FPS
    
    print("Bereit zur Audioaufnahme. Drücken Sie Play zum Starten...")
    
    try:
        app.exec_()
    except KeyboardInterrupt:
        print("Programm beendet.")
    finally:
        audio_stream.stop()
        pygame.quit()

if __name__ == "__main__":
    main()
