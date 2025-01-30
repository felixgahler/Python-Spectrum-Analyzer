import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_COLOR, GRID_COLOR, BARS_START_COLOR, BARS_END_COLOR

class SpectrumVisualizer:
    def __init__(self, screen, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, n_samples=1024, background_color=BACKGROUND_COLOR):
        """
        initializes SpectrumVisualizer with given screen, dimensions, sample count, and background color
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.n_samples = n_samples
        self.background_color = background_color
        self.frequencies = np.linspace(0, 44100 // 2, n_samples // 2)
        self.smoothed_magnitude = np.zeros(n_samples // 2)
        self.start_color = BARS_START_COLOR
        self.end_color = BARS_END_COLOR
        self.spectrum_surface = pygame.Surface((self.screen_width, self.screen_height))
        self.labels_frequencies = [500, 2500, 5000, 7500, 10000, 12500, 15000, 17500, 20000]
        self.x_offset = 50
        self.current_mode = "Balken"

    def draw_grid(self):
        """
        draws grid lines on the spectrum surface, including vertical frequency markers and horizontal intensity lines
        """
        grid_line_width = 1
        for freq in self.labels_frequencies:
            if freq <= max(self.frequencies):
                x_pos = int(np.interp(freq, self.frequencies, np.linspace(0, self.screen_width - self.x_offset, len(self.frequencies)))) + self.x_offset
                pygame.draw.line(self.spectrum_surface, GRID_COLOR, (x_pos, 0), (x_pos, self.screen_height), grid_line_width)

        num_lines = 10
        for i in range(1, num_lines):
            y_pos = self.screen_height - int(self.screen_height * i / num_lines)
            pygame.draw.line(self.spectrum_surface, GRID_COLOR, (0, y_pos), (self.screen_width, y_pos), grid_line_width)

    def update(self, audio_data):
        """
        - updates spectrum visualization with new audio data, applying FFT and smoothing the magnitude values
        - also redraws the grid and visualizes the frequency spectrum as bars

        :param audio_data: Array of audio samples to visualize
        """
        audio_data = audio_data.astype(np.float32)
        audio_data -= np.mean(audio_data)

        fft_data = fft(audio_data)
        magnitude = np.abs(fft_data[:self.n_samples // 2]) / (self.n_samples // 2)

        alpha = 0.7
        self.smoothed_magnitude = alpha * self.smoothed_magnitude + (1 - alpha) * magnitude

        self.spectrum_surface.fill(self.background_color)
        self.draw_grid()

        bar_width = self.screen_width // (self.n_samples // 2)
        if self.current_mode == "Balken":
            for i, height in enumerate(self.smoothed_magnitude):
                bar_height = int(np.log10(height + 1) * 200)
                bar_color = get_gradient_color(i, self.n_samples // 2 - 1, self.start_color, self.end_color)
                pygame.draw.rect(self.spectrum_surface, bar_color, pygame.Rect(i * bar_width, self.screen_height - bar_height, bar_width, bar_height))
        elif self.current_mode == "Wellen":
            points = []
            for i, height in enumerate(self.smoothed_magnitude):
                x = i * bar_width
                y = self.screen_height - int(np.log10(height + 1) * 200)
                points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(self.spectrum_surface, self.start_color, False, points, 2)
        elif self.current_mode == "Punkte":
            for i, height in enumerate(self.smoothed_magnitude):
                x = i * bar_width
                y = self.screen_height - int(np.log10(height + 1) * 200)
                color = get_gradient_color(i, self.n_samples // 2 - 1, self.start_color, self.end_color)
                pygame.draw.circle(self.spectrum_surface, color, (int(x), int(y)), 3)

        font = pygame.font.Font(None, 24)
        for freq in self.labels_frequencies:
            if freq <= max(self.frequencies):
                x_pos = int(np.interp(freq, self.frequencies, np.linspace(0, self.screen_width - self.x_offset, len(self.frequencies)))) + self.x_offset
                text = font.render(f"{freq} Hz", True, (234, 233, 252))
                text_width = text.get_width()
                text_pos = (x_pos - text_width // 2, self.screen_height - 30)
                self.spectrum_surface.blit(text, text_pos)

        self.screen.blit(self.spectrum_surface, (0, 0))
        pygame.display.flip()

    def clear(self):
        """
        Löscht die Visualisierung und zeigt nur das Grundraster
        """
        self.spectrum_surface.fill(self.background_color)
        self.draw_grid()
        self.screen.blit(self.spectrum_surface, (0, 0))

    def set_mode(self, mode):
        """
        Ändert den Visualisierungsmodus
        """
        self.current_mode = mode
        
    def set_colors(self, start_color, end_color):
        """
        Ändert das Farbschema
        """
        self.start_color = start_color
        self.end_color = end_color
