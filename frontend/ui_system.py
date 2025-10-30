# ui_system.py
"""
UI System for managing all UI elements including buttons, sliders, toggles, and dropdowns.
"""
import pygame
from typing import Callable, List, Optional

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 41, 117)


class Button:
    """Interactive button widget."""
    
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        
    def draw(self, surface, font):
        base_color = NEON_BLUE
        hover_color = NEON_PINK
        text_color = WHITE
        
        color = hover_color if self.hovered else base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Prefer using the actual event position for click detection (more robust)
            try:
                pos = event.pos
            except AttributeError:
                pos = None

            if pos:
                if self.rect.collidepoint(pos):
                    print(f"UI DEBUG: Button '{self.text}' clicked at {pos}")
                    try:
                        self.callback()
                        print(f"UI DEBUG: Button '{self.text}' callback executed")
                    except Exception as e:
                        print(f"UI DEBUG: Button '{self.text}' callback raised: {e}")
                    return True
            else:
                # Fallback to hovered state if event has no position
                if self.hovered:
                    self.callback()
                    return True
        return False


class Slider:
    """Slider widget for adjusting values."""
    
    def __init__(self, x, y, width, height, label, value, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = value  # 0.0 to 1.0
        self.callback = callback
        self.active = False
        self.hovered = False
        self.handle_width = 15
        
    def draw(self, surface, font):
        label_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        pygame.draw.rect(surface, GRAY, self.rect, border_radius=3)
        
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, 
                               int(self.rect.width * self.value), self.rect.height)
        pygame.draw.rect(surface, NEON_BLUE, fill_rect, border_radius=3)
        
        handle_x = self.rect.x + int(self.rect.width * self.value) - self.handle_width // 2
        handle_rect = pygame.Rect(handle_x, self.rect.y - 2, 
                                 self.handle_width, self.rect.height + 4)
        pygame.draw.rect(surface, WHITE, handle_rect, border_radius=3)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if self.active:
            rel_x = max(0, min(mouse_pos[0] - self.rect.x, self.rect.width))
            self.value = rel_x / self.rect.width
            self.callback(self.value)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.active = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                self.active = False
                return True
        return False


class Toggle:
    """Toggle switch widget."""
    
    def __init__(self, x, y, label, value, callback):
        self.rect = pygame.Rect(x, y, 50, 25)
        self.label = label
        self.value = value
        self.callback = callback
        self.hovered = False
        
    def draw(self, surface, font):
        label_surf = font.render(self.label, True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        bg_color = NEON_BLUE if self.value else GRAY
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=12)
        
        switch_x = self.rect.x + 25 if self.value else self.rect.x + 5
        switch_rect = pygame.Rect(switch_x, self.rect.y + 2, 20, 20)
        pygame.draw.rect(surface, WHITE, switch_rect, border_radius=10)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.value = not self.value
                self.callback(self.value)
                return True
        return False


class Dropdown:
    """Dropdown menu widget."""
    
    def __init__(self, x, y, width, height, label, options, current_value, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.options = options
        self.current_value = current_value
        self.callback = callback
        self.hovered = False
        self.expanded = False
        self.option_height = height
        
        self.option_rects = []
        for i in range(len(options)):
            option_rect = pygame.Rect(x, y + (i + 1) * height, width, height)
            self.option_rects.append(option_rect)
    
    def draw(self, surface, font):
        label_surf = font.render(self.label, True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        pygame.draw.rect(surface, NEON_BLUE, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        value_surf = font.render(self.current_value, True, WHITE)
        value_rect = value_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(value_surf, value_rect)
        
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery + 5),
            (self.rect.right - 30, self.rect.centery + 5)
        ]
        pygame.draw.polygon(surface, WHITE, arrow_points)
        
        if self.expanded:
            for i, option_rect in enumerate(self.option_rects):
                hover_color = NEON_PINK if option_rect.collidepoint(pygame.mouse.get_pos()) else NEON_BLUE
                pygame.draw.rect(surface, hover_color, option_rect, border_radius=5)
                pygame.draw.rect(surface, WHITE, option_rect, 2, border_radius=5)
                
                option_surf = font.render(self.options[i], True, WHITE)
                option_rect_center = option_surf.get_rect(midleft=(option_rect.x + 10, option_rect.centery))
                surface.blit(option_surf, option_rect_center)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.expanded = not self.expanded
                return True
                
            if self.expanded:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.current_value = self.options[i]
                        self.callback(self.current_value)
                        self.expanded = False
                        return True
                        
            if self.expanded:
                self.expanded = False
                
        return False


class UIManager:
    """Manages all UI elements and button groups."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menu_buttons = []
        self.pause_buttons = []
        self.game_over_buttons = []
        self.settings_controls = []
        self.leaderboard_back_button = None
        
    def create_menu_buttons(self, callbacks):
        """Create main menu buttons."""
        button_width = 200
        button_height = 50
        button_x = self.screen_width // 2 - button_width // 2
        
        self.menu_buttons = [
            Button(button_x, 250, button_width, button_height, "START GAME", callbacks['start']),
            Button(button_x, 320, button_width, button_height, "LEADERBOARD", callbacks['leaderboard']),
            Button(button_x, 390, button_width, button_height, "SETTINGS", callbacks['settings']),
            Button(button_x, 460, button_width, button_height, "QUIT", callbacks['quit'])
        ]
    
    def create_pause_buttons(self, callbacks):
        """Create pause menu buttons."""
        button_width = 200
        button_height = 50
        button_x = self.screen_width // 2 - button_width // 2
        
        self.pause_buttons = [
            Button(button_x, 250, button_width, button_height, "RESUME", callbacks['resume']),
            Button(button_x, 320, button_width, button_height, "LEADERBOARD", callbacks['leaderboard']),
            Button(button_x, 390, button_width, button_height, "SETTINGS", callbacks['settings']),
            Button(button_x, 460, button_width, button_height, "QUIT TO MENU", callbacks['menu'])
        ]
    
    def create_game_over_buttons(self, callbacks):
        """Create game over menu buttons."""
        button_width = 200
        button_height = 50
        button_x = self.screen_width // 2 - button_width // 2
        
        self.game_over_buttons = [
            Button(button_x, 350, button_width, button_height, "PLAY AGAIN", callbacks['restart']),
            Button(button_x, 420, button_width, button_height, "LEADERBOARD", callbacks['leaderboard']),
            Button(button_x, 490, button_width, button_height, "QUIT TO MENU", callbacks['menu'])
        ]
    
    def create_leaderboard_button(self, callback):
        """Create leaderboard back button."""
        self.leaderboard_back_button = Button(
            self.screen_width // 2 - 75, self.screen_height - 80, 
            150, 40, "BACK", callback
        )
    
    def create_settings_controls(self, settings, callbacks):
        """Create settings menu controls."""
        button_width = 200
        button_height = 50
        button_x = self.screen_width // 2 - 100
        
        self.settings_controls = [
            Button(button_x, 450, button_width, button_height, 
                  "SAVE & RETURN", callbacks['save']),
            Slider(button_x, 150, 200, 20, "Sound Volume", 
                  settings["sound_volume"], callbacks['sound_volume']),
            Slider(button_x, 200, 200, 20, "Music Volume", 
                  settings["music_volume"], callbacks['music_volume']),
            Toggle(button_x, 250, "Screen Shake", 
                  settings["screen_shake"], callbacks['screen_shake']),
            Toggle(button_x, 300, "Show Damage", 
                  settings["show_damage"], callbacks['show_damage']),
            Dropdown(button_x, 350, 200, 30, "Difficulty", 
                    ["Easy", "Normal", "Hard"], 
                    settings["difficulty"], 
                    callbacks['difficulty'])
        ]
    
    def update_positions(self, screen_width, screen_height):
        """Update UI positions when screen is resized."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        scale_x = screen_width / 1280  # Original width
        scale_y = screen_height / 720   # Original height
        
        button_width = int(200 * scale_x)
        button_height = int(50 * scale_y)
        button_x = screen_width // 2 - button_width // 2
        
        # Update menu buttons
        if self.menu_buttons:
            positions = [250, 320, 390, 460]
            for i, button in enumerate(self.menu_buttons):
                button.rect.x = button_x
                button.rect.y = int(positions[i] * scale_y)
                button.rect.width = button_width
                button.rect.height = button_height
        
        # Update pause buttons
        if self.pause_buttons:
            positions = [250, 320, 390, 460]
            for i, button in enumerate(self.pause_buttons):
                button.rect.x = button_x
                button.rect.y = int(positions[i] * scale_y)
                button.rect.width = button_width
                button.rect.height = button_height
        
        # Update game over buttons
        if self.game_over_buttons:
            positions = [350, 420, 490]
            for i, button in enumerate(self.game_over_buttons):
                button.rect.x = button_x
                button.rect.y = int(positions[i] * scale_y)
                button.rect.width = button_width
                button.rect.height = button_height
        
        # Update leaderboard back button
        if self.leaderboard_back_button:
            back_width = int(150 * scale_x)
            back_height = int(40 * scale_y)
            self.leaderboard_back_button.rect.x = screen_width // 2 - back_width // 2
            self.leaderboard_back_button.rect.y = int((720 - 80) * scale_y)
            self.leaderboard_back_button.rect.width = back_width
            self.leaderboard_back_button.rect.height = back_height
    
    def update_widgets(self, widgets, mouse_pos):
        """Update all widgets with current mouse position."""
        for widget in widgets:
            widget.update(mouse_pos)
    
    def handle_events(self, widgets, event):
        """Handle events for all widgets."""
        for widget in widgets:
            if widget.handle_event(event):
                return True
        return False