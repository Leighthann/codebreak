# font_manager.py
"""
Font Manager for loading and managing game fonts.
"""
import pygame
from typing import Dict, Optional


class FontManager:
    """Manages game fonts with fallback support."""
    
    def __init__(self):
        pygame.font.init()
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.load_fonts()
    
    def load_fonts(self):
        """Load all game fonts with fallback to system fonts."""
        font_configs = [
            ("title", "frontend/fonts/PropolishRufftu-BLLyd.ttf", 60),
            ("button", "frontend/fonts/GlitchGoblin-2O87v.ttf", 40),
            ("info", "frontend/fonts/VeniteAdoremusStraight-Yzo6v.ttf", 24),
            ("xl", "frontend/fonts/Cyberbang-7O9OB.ttf", 48),
            ("lg", "frontend/fonts/Cyberbang-7O9OB.ttf", 36),
            ("md", "frontend/fonts/Cyberbang-7O9OB.ttf", 24),
            ("sm", "frontend/fonts/Cyberbang-7O9OB.ttf", 18)
        ]
        
        for name, path, size in font_configs:
            try:
                self.fonts[name] = pygame.font.Font(path, size)
                print(f"Loaded font '{name}' from {path}")
            except Exception as e:
                print(f"Warning: Could not load font '{name}' from {path}: {e}")
                print(f"Using system font for '{name}'")
                self.fonts[name] = pygame.font.Font(None, size)
    
    def get_font(self, name: str) -> Optional[pygame.font.Font]:
        """Get a font by name."""
        return self.fonts.get(name)
    
    def get_title_font(self) -> pygame.font.Font:
        """Get title font."""
        return self.fonts.get("title", pygame.font.Font(None, 60))
    
    def get_button_font(self) -> pygame.font.Font:
        """Get button font."""
        return self.fonts.get("button", pygame.font.Font(None, 40))
    
    def get_info_font(self) -> pygame.font.Font:
        """Get info font."""
        return self.fonts.get("info", pygame.font.Font(None, 24))
    
    def get_xl_font(self) -> pygame.font.Font:
        """Get extra large font."""
        return self.fonts.get("xl", pygame.font.Font(None, 48))
    
    def get_lg_font(self) -> pygame.font.Font:
        """Get large font."""
        return self.fonts.get("lg", pygame.font.Font(None, 36))
    
    def get_md_font(self) -> pygame.font.Font:
        """Get medium font."""
        return self.fonts.get("md", pygame.font.Font(None, 24))
    
    def get_sm_font(self) -> pygame.font.Font:
        """Get small font."""
        return self.fonts.get("sm", pygame.font.Font(None, 18))
    
    def add_custom_font(self, name: str, path: str, size: int) -> bool:
        """
        Add a custom font.
        
        Args:
            name: Font identifier
            path: Path to font file
            size: Font size
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.fonts[name] = pygame.font.Font(path, size)
            print(f"Added custom font '{name}'")
            return True
        except Exception as e:
            print(f"Error adding custom font '{name}': {e}")
            return False