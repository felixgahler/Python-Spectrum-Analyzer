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
        
        # Frequencies for half of the FFT range
        self.frequencies = np.linspace(0, 44100 // 2, n_samples // 2)
        
        # Keep track of a smoothed spectrum
        self.smoothed_magnitude = np.zeros(n_samples // 2)
        
        # Default color transitions
        self.start_color = BARS_START_COLOR
        self.end_color = BARS_END_COLOR
        
        self.spectrum_surface = pygame.Surface((self.screen_width, self.screen_height))
        
        # Example frequency labels
        self.labels_frequencies = [500, 2500, 5000, 7500, 10000, 12500, 15000, 17500, 20000]
        self.x_offset = 50
        
        # Visualization mode: "Balken", "Wellen", or "Punkte"
        self.current_mode = "Balken"
        
        # EQ Range (low/high cut)
        self.low_cut = 20
        self.high_cut = 20000
        
        # 3-band EQ gains
        self.eq_low_gain = 1.0
        self.eq_mid_gain = 1.0
        self.eq_high_gain = 1.0

    def set_frequency_range(self, low_cut, high_cut):
        self.low_cut = low_cut
        self.high_cut = high_cut

    def set_eq_gains(self, low_gain, mid_gain, high_gain):
        self.eq_low_gain = low_gain
        self.eq_mid_gain = mid_gain
        self.eq_high_gain = high_gain

    def apply_eq_range(self, magnitude):
        """
        1. Zero out frequencies outside [low_cut, high_cut].
        2. Multiply frequencies within each sub-band by the band's gain.
        """
        filtered_magnitude = magnitude.copy()
        
        for i, freq in enumerate(self.frequencies):
            # Global cut
            if freq < self.low_cut or freq > self.high_cut:
                filtered_magnitude[i] = 0.0
            else:
                # Basic 3-band split
                if freq < 400:
                    filtered_magnitude[i] *= self.eq_low_gain
                elif freq < 4000:
                    filtered_magnitude[i] *= self.eq_mid_gain
                else:
                    filtered_magnitude[i] *= self.eq_high_gain
        
        return filtered_magnitude

    def draw_grid(self):
        grid_line_width = 1
        for freq in self.labels_frequencies:
            if freq <= max(self.frequencies):
                x_pos = int(
                    np.interp(freq, self.frequencies,
                              np.linspace(0, self.screen_width - self.x_offset, len(self.frequencies)))
                ) + self.x_offset
                pygame.draw.line(self.spectrum_surface, GRID_COLOR, (x_pos, 0), (x_pos, self.screen_height), grid_line_width)

        num_lines = 10
        for i in range(1, num_lines):
            y_pos = self.screen_height - int(self.screen_height * i / num_lines)
            pygame.draw.line(self.spectrum_surface, GRID_COLOR, (0, y_pos), (self.screen_width, y_pos), grid_line_width)

    def update(self, audio_data):
        """
        - Updates spectrum visualization with new audio data, applying FFT and smoothing the magnitude values.
        - Then applies the EQ band gains and global low/high cutoff.
        """
        audio_data = audio_data.astype(np.float32)
        audio_data -= np.mean(audio_data)

        fft_data = fft(audio_data)
        magnitude = np.abs(fft_data[:self.n_samples // 2]) / (self.n_samples // 2)

        # Smooth with exponential moving average
        alpha = 0.7
        self.smoothed_magnitude = alpha * self.smoothed_magnitude + (1 - alpha) * magnitude
        
        # Apply eq range and band gains
        displayed_magnitude = self.apply_eq_range(self.smoothed_magnitude)

        # Clear the old image
        self.spectrum_surface.fill(self.background_color)
        self.draw_grid()

        bar_width = max(1, self.screen_width // (self.n_samples // 2))
        
        if self.current_mode == "Balken":
            for i, height in enumerate(displayed_magnitude):
                bar_height = int(np.log10(height + 1) * 200)
                bar_color = get_gradient_color(i, self.n_samples // 2 - 1, self.start_color, self.end_color)
                pygame.draw.rect(
                    self.spectrum_surface, 
                    bar_color, 
                    pygame.Rect(i * bar_width, self.screen_height - bar_height, bar_width, bar_height)
                )
        elif self.current_mode == "Wellen":
            points = []
            for i, height in enumerate(displayed_magnitude):
                x = i * bar_width
                y = self.screen_height - int(np.log10(height + 1) * 200)
                points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(self.spectrum_surface, self.start_color, False, points, 2)
        elif self.current_mode == "Punkte":
            for i, height in enumerate(displayed_magnitude):
                x = i * bar_width
                y = self.screen_height - int(np.log10(height + 1) * 200)
                color = get_gradient_color(i, self.n_samples // 2 - 1, self.start_color, self.end_color)
                pygame.draw.circle(self.spectrum_surface, color, (int(x), int(y)), 3)

        # Frequency labels
        font = pygame.font.Font(None, 24)
        for freq in self.labels_frequencies:
            if freq <= max(self.frequencies):
                x_pos = int(
                    np.interp(freq, self.frequencies,
                              np.linspace(0, self.screen_width - self.x_offset, len(self.frequencies)))
                ) + self.x_offset
                text = font.render(f"{freq} Hz", True, (234, 233, 252))
                text_rect = text.get_rect(center=(x_pos, self.screen_height - 15))
                self.spectrum_surface.blit(text, text_rect)

        self.screen.blit(self.spectrum_surface, (0, 0))
        pygame.display.flip()

    def clear(self):
        """
        Clears the visualization and shows only the grid
        """
        self.spectrum_surface.fill(self.background_color)
        self.draw_grid()
        self.screen.blit(self.spectrum_surface, (0, 0))

    def set_mode(self, mode):
        """
        Changes the visualization mode
        """
        self.current_mode = mode

    def set_colors(self, start_color, end_color):
        """
        Changes the color scheme
        """
        self.start_color = start_color
        self.end_color = end_color
