import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, VOLUME_FACTOR
from spectrum_visualizer import SpectrumVisualizer
from audio_stream import AudioStream
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QSlider, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer

class ControlWindow(QMainWindow):
    def __init__(self, audio_callback):
        super().__init__()
        self.audio_callback = audio_callback
        self.is_recording = False
        self.volume = 1.0
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Controls')
        self.setGeometry(0, SCREEN_HEIGHT + 50, SCREEN_WIDTH, 100)
        
        # Zentrales Widget und Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Play/Stop Button
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.play_button)
        
        # Lautstärke Label
        volume_label = QLabel('Lautstärke:')
        layout.addWidget(volume_label)
        
        # Lautstärke Slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(200)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        layout.addWidget(self.volume_slider)
        
    def toggle_recording(self):
        self.is_recording = not self.is_recording
        self.play_button.setText('Stop' if self.is_recording else 'Play')
        print("Aufnahme gestartet..." if self.is_recording else "Aufnahme gestoppt.")
        
    def update_volume(self):
        self.volume = self.volume_slider.value() / 100.0
        
    def get_state(self):
        return self.is_recording, self.volume

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
        is_recording, volume = control_window.get_state()
        
        # Visualisierung aktualisieren
        if is_recording:
            audio_data = audio_stream.get_audio_data(volume_factor=volume)
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
