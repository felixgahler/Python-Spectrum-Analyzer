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
            file_name, _ = QFileDialog.getSaveFileName(self, 
                "Aufnahme speichern", 
                "recording.npy",
                "NumPy Files (*.npy)")
            if file_name:
                np.save(file_name, np.array(self.recorded_data))
                print(f"Aufnahme gespeichert als: {file_name}")
        
    def update_volume(self):
        self.volume = self.volume_slider.value() / 100.0
        
    def get_state(self):
        return {
            'is_recording': self.is_recording,
            'is_saving': self.is_saving,
            'volume': self.volume,
            'viz_mode': self.viz_mode_combo.currentText(),
            'color_scheme': self.color_scheme_combo.currentText()
        }

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
