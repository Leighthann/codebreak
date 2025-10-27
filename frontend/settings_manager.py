# settings_manager.py
"""
Settings Manager for handling game settings, loading, and saving.
"""
import json
import os
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages game settings including loading, saving, and updates."""
    
    DEFAULT_SETTINGS = {
        "sound_volume": 0.7,
        "music_volume": 0.5,
        "screen_shake": True,
        "show_damage": True,
        "difficulty": "Normal"
    }
    
    def __init__(self, settings_file: str = "game_settings.json"):
        self.settings_file = settings_file
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or use defaults."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.settings.update(loaded_settings)
                    print(f"Settings loaded from {self.settings_file}")
            else:
                print("No settings file found, using defaults")
                self.save_settings()  # Create default settings file
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
        
        return self.settings
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a single setting."""
        if key in self.settings:
            self.settings[key] = value
            return True
        return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        return self.settings.copy()
    
    def apply_audio_settings(self, effects_manager, music_manager=None):
        """Apply audio settings to effects and music managers."""
        if effects_manager:
            effects_manager.set_volume(self.settings["sound_volume"])
        if music_manager:
            music_manager.set_volume(self.settings["music_volume"])