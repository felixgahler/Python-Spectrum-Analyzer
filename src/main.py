import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, VOLUME_FACTOR
from spectrum_visualizer import SpectrumVisualizer
from audio_stream import AudioStream
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

def main():
    """
    inits Pygame env, sets up visualizer and audio stream,
    processes real-time audio data for visualization
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
    icon = pygame.image.load("src/assets/icon.png")
    pygame.display.set_icon(icon)
    pygame.display.set_caption("Spectrum Analyzer")
    clock = pygame.time.Clock()

    # AudioStream und Visualizer initialisieren
    # audio_stream = AudioStream()
    visualizer = SpectrumVisualizer(screen)

    try:
        print("Streaming audio and displaying spectrum visualization...")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

            # audio_data = audio_stream.get_audio_data(volume_factor=VOLUME_FACTOR)
            visualizer.update(None)

            clock.tick(60)

    except KeyboardInterrupt:
        print("Streaming stopped.")
    finally:
        # audio_stream.stop()
        pygame.quit()

class ControlWindow(QtWidgets.QWidget):
    def __init__(self, audio_stream, visualizer):
        super().__init__()
        self.audio_stream = audio_stream
        self.visualizer = visualizer
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Control Panel')
        self.setGeometry(100, 100, 300, 100)
        self.start_button = QtWidgets.QPushButton('Start', self)
        self.start_button.clicked.connect(self.toggle_stream)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_button)
        self.setLayout(layout)

    def update_visualization(self):
        if self.audio_stream and hasattr(self.audio_stream, 'stream') and self.audio_stream.stream.is_active():
            audio_data = self.audio_stream.get_audio_data(volume_factor=VOLUME_FACTOR)
            self.visualizer.update(audio_data)

    def toggle_stream(self):
        if self.audio_stream and hasattr(self.audio_stream, 'stream') and self.audio_stream.stream.is_active():
            self.audio_stream.stop()
            self.start_button.setText('Start')
            self.audio_stream = None
        else:
            self.audio_stream = AudioStream()
            self.start_button.setText('Stop')

app = QtWidgets.QApplication([])

# Pygame initialisieren
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
icon = pygame.image.load("src/assets/icon.png")
pygame.display.set_icon(icon)
pygame.display.set_caption("Spectrum Analyzer")

# AudioStream und Visualizer initialisieren
# audio_stream = AudioStream()
visualizer = SpectrumVisualizer(screen)

# PyQt5 Fenster erstellen
control_window = ControlWindow(None, visualizer)
control_window.show()

# QTimer für Pygame-Visualisierung
clock = pygame.time.Clock()
timer = QTimer()
timer.timeout.connect(control_window.update_visualization)
timer.start(1000 // 60)  # 60 FPS

try:
    app.exec_()
except KeyboardInterrupt:
    print("Streaming stopped.")
finally:
    # audio_stream.stop()
    pygame.quit()

if __name__ == "__main__":
    main()
