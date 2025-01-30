import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, VOLUME_FACTOR, COLOR_SCHEMES, VISUALIZATION_MODES
from spectrum_visualizer import SpectrumVisualizer
from audio_stream import AudioStream
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QSlider, QLabel, QHBoxLayout, QComboBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
import wave
import struct

class ControlWindow(QMainWindow):
    def __init__(self, audio_callback):
        super().__init__()
        self.audio_callback = audio_callback
        self.is_recording = False
        self.is_saving = False
        self.volume = 1.0
        self.recorded_data = []
        
        # Default frequency range for visualization
        self.low_freq_cut = 20
        self.high_freq_cut = 20000
        
        # Simple 3-band EQ (low, mid, high) 
        # -> Gains are multipliers on the magnitude
        self.eq_low_gain = 1.0
        self.eq_mid_gain = 1.0
        self.eq_high_gain = 1.0

        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Controls')
        # Increase the height to accommodate extra sliders
        self.setGeometry(0, SCREEN_HEIGHT + 50, SCREEN_WIDTH, 260)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --------------------------------------------------------
        # Top row (Play / Record / Viz Mode / Color Scheme)
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
        
        # --------------------------------------------------------
        # Middle row (Volume Slider)
        middle_row = QHBoxLayout()
        
        volume_label = QLabel('Lautstärke:')
        middle_row.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(200)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        middle_row.addWidget(self.volume_slider)
        
        main_layout.addLayout(middle_row)
        
        # --------------------------------------------------------
        # Bottom row #1 (Global Cut Sliders)
        bottom_row_1 = QHBoxLayout()
        
        # Low-frequency cutoff
        self.low_freq_label = QLabel(f"LowCut: {self.low_freq_cut} Hz")
        bottom_row_1.addWidget(self.low_freq_label)
        
        self.low_cut_slider = QSlider(Qt.Horizontal)
        self.low_cut_slider.setMinimum(20)
        self.low_cut_slider.setMaximum(20000)
        self.low_cut_slider.setValue(self.low_freq_cut)
        self.low_cut_slider.setSingleStep(10)
        self.low_cut_slider.setTickPosition(QSlider.TicksBelow)
        self.low_cut_slider.valueChanged.connect(self.update_low_cut)
        bottom_row_1.addWidget(self.low_cut_slider)
        
        # High-frequency cutoff
        self.high_freq_label = QLabel(f"HighCut: {self.high_freq_cut} Hz")
        bottom_row_1.addWidget(self.high_freq_label)
        
        self.high_cut_slider = QSlider(Qt.Horizontal)
        self.high_cut_slider.setMinimum(20)
        self.high_cut_slider.setMaximum(20000)
        self.high_cut_slider.setValue(self.high_freq_cut)
        self.high_cut_slider.setSingleStep(10)
        self.high_cut_slider.setTickPosition(QSlider.TicksBelow)
        self.high_cut_slider.valueChanged.connect(self.update_high_cut)
        bottom_row_1.addWidget(self.high_cut_slider)
        
        main_layout.addLayout(bottom_row_1)
        
        # --------------------------------------------------------
        # Bottom row #2 (EQ Sliders)
        # We create 3 more sliders for the 3 EQ bands
        bottom_row_2 = QHBoxLayout()
        
        # Low Band
        self.eq_low_label = QLabel(f"Low Gain: {self.eq_low_gain:.2f}x")
        bottom_row_2.addWidget(self.eq_low_label)
        
        self.eq_low_slider = QSlider(Qt.Horizontal)
        self.eq_low_slider.setMinimum(0)
        self.eq_low_slider.setMaximum(200)  # 0..200 mapped to 0..2.0
        self.eq_low_slider.setValue(100)    # default 1.0 (100)
        self.eq_low_slider.valueChanged.connect(self.update_eq_low)
        bottom_row_2.addWidget(self.eq_low_slider)
        
        # Mid Band
        self.eq_mid_label = QLabel(f"Mid Gain: {self.eq_mid_gain:.2f}x")
        bottom_row_2.addWidget(self.eq_mid_label)
        
        self.eq_mid_slider = QSlider(Qt.Horizontal)
        self.eq_mid_slider.setMinimum(0)
        self.eq_mid_slider.setMaximum(200)
        self.eq_mid_slider.setValue(100)
        self.eq_mid_slider.valueChanged.connect(self.update_eq_mid)
        bottom_row_2.addWidget(self.eq_mid_slider)
        
        # High Band
        self.eq_high_label = QLabel(f"High Gain: {self.eq_high_gain:.2f}x")
        bottom_row_2.addWidget(self.eq_high_label)
        
        self.eq_high_slider = QSlider(Qt.Horizontal)
        self.eq_high_slider.setMinimum(0)
        self.eq_high_slider.setMaximum(200)
        self.eq_high_slider.setValue(100)
        self.eq_high_slider.valueChanged.connect(self.update_eq_high)
        bottom_row_2.addWidget(self.eq_high_slider)
        
        main_layout.addLayout(bottom_row_2)
        # --------------------------------------------------------
        
    # --------------------------- EQ SLIDERS ----------------------------
    def update_eq_low(self):
        # Convert [0..200] slider to [0..2.0] multiplier
        val = self.eq_low_slider.value() / 100.0
        self.eq_low_gain = val
        self.eq_low_label.setText(f"Low Gain: {self.eq_low_gain:.2f}x")
        
    def update_eq_mid(self):
        val = self.eq_mid_slider.value() / 100.0
        self.eq_mid_gain = val
        self.eq_mid_label.setText(f"Mid Gain: {self.eq_mid_gain:.2f}x")
        
    def update_eq_high(self):
        val = self.eq_high_slider.value() / 100.0
        self.eq_high_gain = val
        self.eq_high_label.setText(f"High Gain: {self.eq_high_gain:.2f}x")

    # -------------------------- Low/High Cut Sliders --------------------
    def update_low_cut(self):
        self.low_freq_cut = self.low_cut_slider.value()
        if self.low_freq_cut >= self.high_freq_cut:
            self.low_freq_cut = self.high_freq_cut - 1
            self.low_cut_slider.setValue(self.low_freq_cut)
        self.low_freq_label.setText(f"LowCut: {self.low_freq_cut} Hz")
        
    def update_high_cut(self):
        self.high_freq_cut = self.high_cut_slider.value()
        if self.high_freq_cut <= self.low_freq_cut:
            self.high_freq_cut = self.low_freq_cut + 1
            self.high_cut_slider.setValue(self.high_freq_cut)
        self.high_freq_label.setText(f"HighCut: {self.high_freq_cut} Hz")
    
    # ---------------------------- Recording -----------------------------
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
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                "Aufnahme speichern", 
                "recording.wav",
                "WAV Files (*.wav)"
            )
            if file_name:
                audio_data = np.array(self.recorded_data).flatten()
                audio_data = np.int16(audio_data * 32767)
                
                import wave, struct
                with wave.open(file_name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(44100)
                    
                    for sample in audio_data:
                        wav_file.writeframes(struct.pack('h', sample))
                
                print(f"Aufnahme gespeichert als: {file_name}")
        
    def update_volume(self):
        self.volume = self.volume_slider.value() / 100.0
        
    # --------------------------- State Getter ---------------------------
    def get_state(self):
        """
        Collects all dynamic parameters that the main loop or SpectrumVisualizer might need.
        """
        return {
            'is_recording': self.is_recording,
            'is_saving': self.is_saving,
            'volume': self.volume,
            'viz_mode': self.viz_mode_combo.currentText(),
            'color_scheme': self.color_scheme_combo.currentText(),
            'low_cut': self.low_freq_cut,
            'high_cut': self.high_freq_cut,
            # 3-band EQ gains
            'eq_low_gain': self.eq_low_gain,
            'eq_mid_gain': self.eq_mid_gain,
            'eq_high_gain': self.eq_high_gain
        }

def main():
    pygame.init()
    
    # Create the PyQt app
    app = QApplication([])
    
    # Main window for Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("FourierLab")
    icon = pygame.image.load("src/assets/icon.png")
    pygame.display.set_icon(icon)
    
    audio_stream = AudioStream()
    visualizer = SpectrumVisualizer(screen)
    clock = pygame.time.Clock()
    
    # Create ControlWindow
    control_window = ControlWindow(None)
    control_window.show()
    
    def update():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.quit()
                return
        
        # State from the control window
        state = control_window.get_state()
        
        # Update frequency range
        visualizer.set_frequency_range(state['low_cut'], state['high_cut'])
        
        # Update per-band EQ gains
        visualizer.set_eq_gains(state['eq_low_gain'], state['eq_mid_gain'], state['eq_high_gain'])
        
        if state['is_recording']:
            audio_data = audio_stream.get_audio_data(volume_factor=state['volume'])
            if state['is_saving']:
                control_window.recorded_data.append(audio_data.copy())
            
            visualizer.set_mode(state['viz_mode'])
            color_scheme = COLOR_SCHEMES[state['color_scheme']]
            visualizer.set_colors(*color_scheme)
            
            visualizer.update(audio_data)
        else:
            visualizer.clear()
        
        pygame.display.flip()
        clock.tick(60)
    
    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(16)  # ~60 FPS
    
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
