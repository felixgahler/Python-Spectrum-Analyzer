import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        """
        Initialisiert einen Button mit Position, Größe und Aussehen
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        """
        Zeichnet den Button auf dem Bildschirm
        """
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=12)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        """
        Behandelt Mausevents für den Button
        """
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.text = text
        self.sliding = False
        self.font = pygame.font.Font(None, 24)
        
    def draw(self, screen):
        # Slider-Hintergrund
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        
        # Slider-Position berechnen
        pos = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        
        # Slider-Knopf
        pygame.draw.circle(screen, (200, 200, 200), (int(pos), self.rect.centery), 10)
        
        # Text und Wert
        text_surface = self.font.render(f"{self.text}: {self.value:.2f}", True, (255, 255, 255))
        screen.blit(text_surface, (self.rect.x, self.rect.y - 20))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.sliding = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.sliding = False
            
        elif event.type == pygame.MOUSEMOTION and self.sliding:
            rel_x = event.pos[0] - self.rect.x
            self.value = self.min_val + (self.max_val - self.min_val) * (rel_x / self.rect.width)
            self.value = max(self.min_val, min(self.max_val, self.value))
            return True
        return False

class Dropdown:
    def __init__(self, x, y, width, height, options, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected = options[0]
        self.text = text
        self.is_open = False
        self.font = pygame.font.Font(None, 24)
        
    def draw(self, screen):
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        text_surface = self.font.render(f"{self.text}: {self.selected}", True, (255, 255, 255))
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
        if self.is_open:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i+1)*self.rect.height,
                                       self.rect.width, self.rect.height)
                pygame.draw.rect(screen, (80, 80, 80), option_rect)
                text_surface = self.font.render(option, True, (255, 255, 255))
                screen.blit(text_surface, (option_rect.x + 5, option_rect.y + 5))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return False
            
            if self.is_open:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x, self.rect.y + (i+1)*self.rect.height,
                                           self.rect.width, self.rect.height)
                    if option_rect.collidepoint(event.pos):
                        self.selected = option
                        self.is_open = False
                        return True
        return False 