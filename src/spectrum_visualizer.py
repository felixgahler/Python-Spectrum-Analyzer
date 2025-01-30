import pygame
import numpy as np
from scipy.fftpack import fft
from utilities import get_gradient_color
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_COLOR, GRID_COLOR, BARS_START_COLOR, BARS_END_COLOR
from matplotlib import cm
import time
import math

class SpectrumVisualizer:
    def __init__(self, screen, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, n_frequency_bins=512):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.n_frequency_bins = n_frequency_bins
        self.background_color = BACKGROUND_COLOR
        
        # Audio settings
        self.sample_rate = 44100  # Standard Audio Sample Rate
        
        # Visualization parameters
        self.plot_audio_history = True
        self.add_slow_bars = True
        self.add_fast_bars = True
        
        # Definiere Bereiche für Visualisierung und Labels
        self.label_height = 30
        self.vis_height = self.screen_height - self.label_height
        self.y_ext = [round(0.05*self.vis_height), self.vis_height]  # Visualisierungsbereich
        
        # Sensitivity settings
        self.amplification = 0.25  # Leicht reduziert für die höhere Auflösung
        self.noise_threshold = 0.003  # Angepasst für feinere Details
        self.smoothing_factor = 0.3
        self.previous_magnitude = None
        
        # Scaling settings
        self.scale_factor = 100.0  # Erhöht für bessere Sichtbarkeit
        self.log_scale = True
        self.log_base = 2  # Angepasste Log-Basis für bessere Hochfrequenz-Darstellung
        
        # Frequency weighting
        self.apply_frequency_weighting = True
        self.weighting_factors = self.create_frequency_weighting()
        
        # Frequency labels settings
        self.show_frequency_labels = True
        self.frequency_points = [0, 100, 500, 1000, 2000, 5000, 10000, 15000, 20000]  # Hz
        
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
        self.slow_bar_thickness = max(0.00002*self.screen_height, 0.5 / self.n_frequency_bins)  # Dünnere Slow-Bars
        self.decay_speed = 0.06
        self.inter_bar_distance = int(0.05*self.screen_width / self.n_frequency_bins)  # Reduzierter Abstand zwischen Balken
        self.bar_width = max(1, (self.screen_width / self.n_frequency_bins) - self.inter_bar_distance)  # Mindestbreite 1 Pixel
        
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
        self.bin_font = pygame.font.Font(None, round(0.03*self.screen_height))  # Größere Schrift
        
        # History mode settings
        if self.plot_audio_history:
            self.prev_screen = self.screen.copy()
            self.alpha_multiplier = 0.85  # Schnelleres Verblassen
            self.move_fraction = 0.05  # Stärkere seitliche Bewegung
            self.shrink_f = 0.95  # Stärkeres Schrumpfen
        
        # Peak line settings
        self.show_peak_line = True
        self.peak_line_color = (255, 255, 255)  # Weiß
        self.peak_line_thickness = 2

    def setup_bars(self):
        self.slow_bars, self.fast_bars, self.bar_x_positions = [], [], []
        for i in range(self.n_frequency_bins):
            x = int(i * self.screen_width / self.n_frequency_bins)
            fast_bar = [int(x), int(self.y_ext[0]), math.ceil(self.bar_width), None]
            slow_bar = [int(x), None, math.ceil(self.bar_width), None]
            self.bar_x_positions.append(x)
            self.fast_bars.append(fast_bar)
            self.slow_bars.append(slow_bar)

    def create_frequency_weighting(self):
        """Erstellt Gewichtungsfaktoren für verschiedene Frequenzbereiche"""
        frequencies = np.linspace(0, self.sample_rate/2, self.n_frequency_bins)
        weighting = np.ones(self.n_frequency_bins)
        
        # Verstärkung für hohe Frequenzen
        high_freq_idx = frequencies > 5000
        weighting[high_freq_idx] = np.linspace(1, 4, np.sum(high_freq_idx))  # Progressive Verstärkung
        
        # Extra Verstärkung für sehr hohe Frequenzen
        very_high_freq_idx = frequencies > 10000
        weighting[very_high_freq_idx] *= 1.5
        
        return weighting

    def update(self, audio_data):
        if audio_data is None:
            return
            
        # Calculate FFT
        fft_data = fft(audio_data)
        magnitude = np.abs(fft_data[:self.n_frequency_bins]) / (len(audio_data) // 2)
        
        # Apply frequency weighting
        if self.apply_frequency_weighting:
            magnitude = magnitude * self.weighting_factors
        
        # Apply noise gate
        magnitude[magnitude < self.noise_threshold] = 0
        
        # Apply logarithmic scaling if enabled
        if self.log_scale:
            # Verwende log2 statt log10 für bessere Hochfrequenz-Darstellung
            magnitude = np.log2(magnitude * self.scale_factor + 1)
        else:
            magnitude = magnitude * self.scale_factor
        
        # Smoothing with frequency-dependent factors
        if self.previous_magnitude is None:
            self.previous_magnitude = magnitude
        else:
            # Stärkeres Smoothing für hohe Frequenzen
            smooth_factors = np.linspace(self.smoothing_factor, self.smoothing_factor * 0.7, len(magnitude))
            magnitude = smooth_factors * magnitude + (1 - smooth_factors) * self.previous_magnitude
            self.previous_magnitude = magnitude
        
        # Update FPS
        if self.start_time is None:
            self.start_time = time.time()
        self.vis_steps += 1
        if self.vis_steps % self.fps_interval == 0:
            self.fps = self.fps_interval / (time.time() - self.start_time)
            self.start_time = time.time()
        
        # Clear entire screen
        self.screen.fill(self.background_color)
        
        # Create separate surface for visualization
        vis_surface = pygame.Surface((self.screen_width, self.vis_height))
        vis_surface.fill(self.background_color)
        
        # Draw history if enabled
        if self.plot_audio_history and hasattr(self, 'prev_screen'):
            # History-Transformation für 3D-Effekt
            new_w = int(self.shrink_f * self.screen_width)
            new_h = int(self.shrink_f * self.vis_height)
            prev_screen = pygame.transform.scale(self.prev_screen, (new_w, new_h))
            
            # Position für 3D-Effekt (nach rechts und leicht nach oben)
            x_offset = self.screen_width - new_w - int(self.move_fraction * self.screen_width)
            y_offset = int(self.move_fraction * self.vis_height * 0.5)  # Reduzierte vertikale Bewegung
            new_pos = (x_offset, y_offset)
            
            vis_surface.blit(prev_screen, new_pos)
        
        # Draw bars without peak line for history
        self.draw_bars(magnitude, vis_surface, draw_peak_line=False)
        
        # Create surface for current frame
        current_surface = pygame.Surface((self.screen_width, self.vis_height))
        current_surface.fill(self.background_color)
        
        # Draw current bars with peak line
        self.draw_bars(magnitude, current_surface, draw_peak_line=True)
        
        # Combine surfaces
        vis_surface.blit(current_surface, (0, 0))
        
        # Draw the visualization surface on the main screen
        self.screen.blit(vis_surface, (0, 0))
        
        # Draw frequency labels below visualization
        self.draw_frequency_labels()
        
        # Update history with current frame
        if self.plot_audio_history:
            self.prev_screen = current_surface.copy().convert_alpha()
            self.prev_screen.set_alpha(int(255 * self.alpha_multiplier))
        
        pygame.display.flip()

    def draw_bars(self, magnitude, surface, draw_peak_line=True):
        local_height = self.y_ext[1] - self.y_ext[0]
        peak_points = []
        
        # Draw fast bars
        if self.add_fast_bars:
            for i in range(self.n_frequency_bins):
                feature_value = magnitude[i] * local_height * self.amplification
                height = int(feature_value)
                x = self.bar_x_positions[i]
                y = self.vis_height  # Start von unten
                rect = [x, y - height, math.ceil(self.bar_width), height]  # y-height für Wachstum nach oben
                pygame.draw.rect(surface, self.fast_bar_colors[i], rect, 0)
                
                # Collect peak points only if needed
                if draw_peak_line and self.show_peak_line:
                    peak_x = x + self.bar_width / 2
                    peak_y = y - height  # Peak-Position anpassen
                    peak_points.append((int(peak_x), int(peak_y)))
        
        # Draw slow bars
        if self.add_slow_bars:
            for i in range(self.n_frequency_bins):
                feature_value = magnitude[i] * local_height * self.amplification
                decay = min(0.99, 1 - max(0, self.decay_speed))
                slow_feature_value = max(self.slow_features[i]*decay, feature_value)
                self.slow_features[i] = slow_feature_value
                
                height = int(self.slow_bar_thickness * local_height)
                x = self.bar_x_positions[i]
                y = self.vis_height - slow_feature_value  # Position von unten
                rect = [x, y, math.ceil(self.bar_width), height]
                pygame.draw.rect(surface, self.slow_bar_colors[i], rect, 0)
        
        # Draw peak line only if requested
        if draw_peak_line and self.show_peak_line and len(peak_points) > 1:
            # Ensure points are within bounds
            peak_points = [(x, max(self.y_ext[0], min(y, self.y_ext[1]))) 
                         for x, y in peak_points]
            pygame.draw.lines(surface, self.peak_line_color, False, peak_points, self.peak_line_thickness)

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

    def draw_frequency_labels(self):
        """Zeichnet Frequenz-Labels unterhalb der Visualisierung"""
        if not self.show_frequency_labels:
            return
            
        label_y = self.vis_height + self.label_height // 2  # Zentriert in der Label-Zone
        
        for freq in self.frequency_points:
            if freq > self.sample_rate / 2:
                continue
                
            # Berechne die x-Position für die Frequenz
            bin_index = int(freq * self.n_frequency_bins / (self.sample_rate / 2))
            if bin_index >= self.n_frequency_bins:
                continue
                
            x_pos = self.bar_x_positions[bin_index]
            
            # Rendere das Label
            if freq >= 1000:
                label = f"{freq/1000:.0f}k"
            else:
                label = str(freq)
                
            text_surface = self.bin_font.render(label, True, (200, 200, 200))
            text_rect = text_surface.get_rect()
            text_rect.centerx = x_pos + self.bar_width / 2
            text_rect.centery = label_y
            
            self.screen.blit(text_surface, text_rect)
