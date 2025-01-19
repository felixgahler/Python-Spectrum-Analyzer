import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, VOLUME_FACTOR
from spectrum_visualizer import SpectrumVisualizer
from audio_stream import AudioStream
from helper import resource_path

def main():
    """
    inits Pygame env, sets up visualizer and audio stream,
    processes real-time audio data for visualization
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
    icon = pygame.image.load(resource_path("msv/src/assets/icon.png"))
    pygame.display.set_icon(icon)
    pygame.display.set_caption("Sound to Sprite - Frequenzspektrum in Echtzeit")
    clock = pygame.time.Clock()

    audio_stream = AudioStream()
    visualizer = SpectrumVisualizer(screen)

    try:
        print("Streaming audio and displaying spectrum visualization...")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

            audio_data = audio_stream.get_audio_data(volume_factor=VOLUME_FACTOR)
            visualizer.update(audio_data)

            clock.tick(60)

    except KeyboardInterrupt:
        print("Streaming stopped.")
    finally:
        audio_stream.stop()
        pygame.quit()

if __name__ == "__main__":
    main()
