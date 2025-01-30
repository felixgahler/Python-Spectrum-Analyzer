import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_COLOR, GRID_COLOR, BARS_START_COLOR, BARS_END_COLOR
from matplotlib import cm
import time
import math

class SpectrumVisualizer:
    def __init__(self, screen, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, n_frequency_bins=100):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.n_frequency_bins = n_frequency_bins
        self.background_color = BACKGROUND_COLOR
        
        # Visualization parameters
        self.plot_audio_history = True
        self.add_slow_bars = True
        self.add_fast_bars = True
        self.y_ext = [round(0.05*self.screen_height), self.screen_height]
        
        # Sensitivity settings
        self.amplification = 0.3  # Stark reduziert für bessere Skalierung
        self.noise_threshold = 0.005
        self.smoothing_factor = 0.3
        self.previous_magnitude = None
        
        # Scaling settings
        self.scale_factor = 50.0  # Skalierungsfaktor für die Magnitude
        self.log_scale = True  # Logarithmische Skalierung für bessere Dynamik
        
        # Color settings
        self.available_colormaps = {
            'Viridis': cm.viridis,
            'Rainbow': self.create_custom_rainbow,
            'Blue Sky': cm.Blues,
            'Sunset': cm.hot,
            'Mono': cm.Greys
        }
        self.current_colormap = 'Viridis'
        self.cm = self.available_colormaps[self.current_colormap]
        self.update_colors()
        
        # Bar settings
        self.slow_bar_thickness = max(0.00002*self.screen_height, 1.25 / self.n_frequency_bins)
        self.decay_speed = 0.06
        self.inter_bar_distance = int(0.2*self.screen_width / self.n_frequency_bins)
        self.bar_width = (self.screen_width / self.n_frequency_bins) - self.inter_bar_distance
        
        # Initialize bars
        self.slow_features = [0]*self.n_frequency_bins
        self.setup_bars()
        
        # Performance monitoring
        self.start_time = None
        self.vis_steps = 0
        self.fps_interval = 10
        self.fps = 0
        
        # Font setup
        pygame.font.init()
        self.bin_font = pygame.font.Font(None, round(0.025*self.screen_height))
        
        # History mode settings
        if self.plot_audio_history:
            self.prev_screen = self.screen.copy()
            self.alpha_multiplier = 0.995
            self.move_fraction = 0.0099
            self.shrink_f = 0.994

    def setup_bars(self):
        self.slow_bars, self.fast_bars, self.bar_x_positions = [], [], []
        for i in range(self.n_frequency_bins):
            x = int(i * self.screen_width / self.n_frequency_bins)
            fast_bar = [int(x), int(self.y_ext[0]), math.ceil(self.bar_width), None]
            slow_bar = [int(x), None, math.ceil(self.bar_width), None]
            self.bar_x_positions.append(x)
            self.fast_bars.append(fast_bar)
            self.slow_bars.append(slow_bar)

    def update(self, audio_data):
        if audio_data is None:
            return
            
        # Calculate FFT
        fft_data = fft(audio_data)
        magnitude = np.abs(fft_data[:self.n_frequency_bins]) / (len(audio_data) // 2)
        
        # Apply noise gate
        magnitude[magnitude < self.noise_threshold] = 0
        
        # Apply logarithmic scaling if enabled
        if self.log_scale:
            # Add small constant to avoid log(0)
            magnitude = np.log10(magnitude * self.scale_factor + 1)
        else:
            magnitude = magnitude * self.scale_factor
        
        # Smoothing
        if self.previous_magnitude is None:
            self.previous_magnitude = magnitude
        else:
            magnitude = self.smoothing_factor * magnitude + (1 - self.smoothing_factor) * self.previous_magnitude
            self.previous_magnitude = magnitude
        
        # Update FPS
        if self.start_time is None:
            self.start_time = time.time()
        self.vis_steps += 1
        if self.vis_steps % self.fps_interval == 0:
            self.fps = self.fps_interval / (time.time() - self.start_time)
            self.start_time = time.time()
        
        # Clear screen
        self.screen.fill(self.background_color)
        
        # Draw history if enabled
        if self.plot_audio_history and hasattr(self, 'prev_screen'):
            new_w = int((2+self.shrink_f)/3*self.screen_width)
            new_h = int(self.shrink_f*self.screen_height)
            prev_screen = pygame.transform.scale(self.prev_screen, (new_w, new_h))
            new_pos = (int(self.move_fraction*self.screen_width - (0.0133*self.screen_width)), 
                      int(self.move_fraction*self.screen_height))
            self.screen.blit(pygame.transform.rotate(prev_screen, 180), new_pos)
        
        # Update and draw bars
        self.draw_bars(magnitude)
        
        # Update history
        if self.plot_audio_history:
            self.prev_screen = self.screen.copy().convert_alpha()
            self.prev_screen.set_alpha(int(255 * self.alpha_multiplier))
        
        pygame.display.flip()

    def draw_bars(self, magnitude):
        local_height = self.y_ext[1] - self.y_ext[0]
        
        for i in range(self.n_frequency_bins):
            feature_value = magnitude[i] * local_height * self.amplification
            
            # Update fast bars
            self.fast_bars[i][3] = int(feature_value)
            if self.plot_audio_history:
                self.fast_bars[i][3] = int(feature_value + 0.02*self.screen_height)
            
            # Update slow bars
            if self.add_slow_bars:
                decay = min(0.99, 1 - max(0, self.decay_speed))
                slow_feature_value = max(self.slow_features[i]*decay, feature_value)
                self.slow_features[i] = slow_feature_value
                self.slow_bars[i][1] = int(self.fast_bars[i][1] + slow_feature_value)
                self.slow_bars[i][3] = int(self.slow_bar_thickness * local_height)
        
        # Draw fast bars
        if self.add_fast_bars:
            for i, fast_bar in enumerate(self.fast_bars):
                pygame.draw.rect(self.screen, self.fast_bar_colors[i], fast_bar, 0)
        
        # Draw slow bars
        if self.add_slow_bars:
            for i, slow_bar in enumerate(self.slow_bars):
                pygame.draw.rect(self.screen, self.slow_bar_colors[i], slow_bar, 0)
        
        # Mirror the visualization
        self.screen.blit(pygame.transform.rotate(self.screen, 180), (0, 0))

    def create_custom_rainbow(self, x):
        """Erstellt einen angepassten Regenbogen-Farbverlauf"""
        # Definiert custom RGB-Werte für einen kräftigeren Regenbogen
        colors = [
            (1, 0, 0),     # Rot
            (1, 0.5, 0),   # Orange
            (1, 1, 0),     # Gelb
            (0, 1, 0),     # Grün
            (0, 0, 1),     # Blau
            (0.5, 0, 1)    # Violett
        ]
        
        # Konvertiert den Eingabewert in einen Index
        if isinstance(x, np.ndarray):
            return np.array([self._interpolate_rainbow(xi, colors) for xi in x])
        return self._interpolate_rainbow(x, colors)

    def _interpolate_rainbow(self, x, colors):
        """Interpoliert zwischen den Regenbogenfarben"""
        n_colors = len(colors)
        idx = x * (n_colors - 1)
        idx_low = int(np.floor(idx))
        idx_high = int(np.ceil(idx))
        
        if idx_low == idx_high:
            return colors[idx_low]
        
        frac = idx - idx_low
        color1 = np.array(colors[idx_low])
        color2 = np.array(colors[idx_high])
        
        return tuple(color1 * (1 - frac) + color2 * frac)

    def update_colors(self):
        """Aktualisiert die Farben basierend auf der aktuellen Colormap"""
        self.cm = self.available_colormaps[self.current_colormap]
        
        # Spezielle Behandlung für verschiedene Colormaps
        if self.current_colormap == 'Blue Sky':
            # Hellere Blautöne mit mehr Kontrast
            self.fast_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0.4, 1, self.n_frequency_bins).astype(float)]
            self.slow_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0.6, 1, self.n_frequency_bins).astype(float)]
        elif self.current_colormap == 'Rainbow':
            # Kräftigerer, angepasster Regenbogen-Effekt
            self.fast_bar_colors = [list((255*np.array(self.cm(i)))[:3].astype(int)) 
                                  for i in np.linspace(0, 1, self.n_frequency_bins).astype(float)]
            self.slow_bar_colors = [list(np.clip((255*1.2*np.array(self.cm(i)))[:3].astype(int), 0, 255)) 
                                  for i in np.linspace(0, 1, self.n_frequency_bins).astype(float)]
        elif self.current_colormap == 'Sunset':
            # Warme Sonnenuntergangsfarben
            self.fast_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0.2, 0.9, self.n_frequency_bins).astype(float)]
            self.slow_bar_colors = [list(np.clip((255*1.3*np.array(self.cm(i))[:3]).astype(int), 0, 255)) 
                                  for i in np.linspace(0.3, 1, self.n_frequency_bins).astype(float)]
        elif self.current_colormap == 'Mono':
            # Schwarz-Weiß mit hohem Kontrast
            self.fast_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0.3, 0.9, self.n_frequency_bins).astype(float)]
            self.slow_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0.5, 1, self.n_frequency_bins).astype(float)]
        else:
            # Standard-Verhalten für Viridis
            self.fast_bar_colors = [list((255*np.array(self.cm(i))[:3]).astype(int)) 
                                  for i in np.linspace(0,1,self.n_frequency_bins).astype(float)]
            self.slow_bar_colors = [list(np.clip((255*1.5*np.array(self.cm(i))[:3]).astype(int), 0, 255)) 
                                  for i in np.linspace(0,1,self.n_frequency_bins).astype(float)]
        
        # Farbreihenfolge umkehren für besseren visuellen Effekt
        self.fast_bar_colors = self.fast_bar_colors[::-1]
        self.slow_bar_colors = self.slow_bar_colors[::-1]

    def set_colormap(self, colormap_name):
        """Ändert das aktuelle Farbschema"""
        if colormap_name in self.available_colormaps:
            self.current_colormap = colormap_name
            self.update_colors()
