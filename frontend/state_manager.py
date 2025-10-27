# state_manager.py
"""
State Manager for handling game state transitions and state-related logic.
"""
import pygame
from typing import Optional, Callable


class StateManager:
    """Manages game states and transitions."""
    
    # Valid game states
    VALID_STATES = {
        "menu", "gameplay", "pause", "game_over", 
        "leaderboard", "settings", "loading"
    }
    
    def __init__(self, initial_state: str = "menu", transition_duration: int = 15):
        self.current_state = initial_state
        self.previous_state: Optional[str] = None
        self.next_state: Optional[str] = None
        
        # Transition animation
        self.transition_duration = transition_duration
        self.transition_timer = 0
        self.fading_in = False
        self.fading_out = False
        
        # Error handling
        self.error_message: Optional[str] = None
    
    def transition_to(self, new_state: str, fade: bool = True):
        """
        Transition to a new game state.
        
        Args:
            new_state: The state to transition to
            fade: Whether to use fade transition
        """
        if new_state not in self.VALID_STATES:
            print(f"Warning: Invalid state '{new_state}'")
            return
        
        if fade:
            self.fading_out = True
            self.next_state = new_state
            self.transition_timer = self.transition_duration
        else:
            self.previous_state = self.current_state
            self.current_state = new_state
            print(f"State changed: {self.previous_state} -> {self.current_state}")
    
    def update_transition(self):
        """Update transition animation state."""
        if self.fading_out:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.fading_out = False
                self.fading_in = True
                self.previous_state = self.current_state
                self.current_state = self.next_state
                self.transition_timer = self.transition_duration
                print(f"State changed: {self.previous_state} -> {self.current_state}")
        
        elif self.fading_in:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.fading_in = False
                self.next_state = None
    
    def get_fade_alpha(self) -> int:
        """Get current fade alpha value (0-255)."""
        if self.fading_out or self.fading_in:
            progress = self.transition_timer / self.transition_duration
            return int(255 * progress)
        return 0
    
    def is_transitioning(self) -> bool:
        """Check if currently in a transition."""
        return self.fading_in or self.fading_out
    
    def get_state(self) -> str:
        """Get current state."""
        return self.current_state
    
    def get_previous_state(self) -> Optional[str]:
        """Get previous state."""
        return self.previous_state
    
    def set_error(self, message: str):
        """Set an error message."""
        self.error_message = message
    
    def clear_error(self):
        """Clear error message."""
        self.error_message = None
    
    def get_error(self) -> Optional[str]:
        """Get current error message."""
        return self.error_message
    
    def reset(self):
        """Reset state manager to initial state."""
        self.current_state = "menu"
        self.previous_state = None
        self.next_state = None
        self.transition_timer = 0
        self.fading_in = False
        self.fading_out = False
        self.error_message = None