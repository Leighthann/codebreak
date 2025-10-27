# camera_system.py
"""
Camera System for managing camera position, offset, and screen shake effects.
"""
import random


class CameraSystem:
    """Manages camera position and effects like screen shake."""
    
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.shake_amount = 0
        self.shake_duration = 0
        self.target_x = 0
        self.target_y = 0
        self.smoothing = 0.1  # Camera smoothing factor
    
    def start_shake(self, amount: int, duration: float):
        """
        Start a screen shake effect.
        
        Args:
            amount: Maximum shake displacement in pixels
            duration: Duration of shake in frames
        """
        self.shake_amount = amount
        self.shake_duration = int(duration * 60)  # Convert to frames at 60 FPS
    
    def update(self):
        """Update camera shake effect."""
        if self.shake_duration > 0:
            self.shake_duration -= 1
            
            if self.shake_duration <= 0:
                # Shake finished, reset offsets
                self.offset_x = 0
                self.offset_y = 0
            else:
                # Apply random shake within amount range
                self.offset_x = random.randint(-self.shake_amount, self.shake_amount)
                self.offset_y = random.randint(-self.shake_amount, self.shake_amount)
    
    def follow_target(self, target_x: float, target_y: float, 
                     screen_width: int, screen_height: int):
        """
        Smoothly follow a target position.
        
        Args:
            target_x: Target x position
            target_y: Target y position
            screen_width: Screen width
            screen_height: Screen height
        """
        # Calculate desired camera position (center on target)
        desired_x = target_x - screen_width // 2
        desired_y = target_y - screen_height // 2
        
        # Smoothly interpolate towards desired position
        self.target_x += (desired_x - self.target_x) * self.smoothing
        self.target_y += (desired_y - self.target_y) * self.smoothing
    
    def get_offset(self) -> tuple:
        """Get current camera offset including shake."""
        return (self.offset_x, self.offset_y)
    
    def get_position(self) -> tuple:
        """Get camera position."""
        return (self.target_x, self.target_y)
    
    def apply_to_position(self, x: float, y: float) -> tuple:
        """
        Apply camera offset to world position.
        
        Args:
            x: World x position
            y: World y position
            
        Returns:
            Screen position tuple (x, y)
        """
        screen_x = x - self.target_x + self.offset_x
        screen_y = y - self.target_y + self.offset_y
        return (screen_x, screen_y)
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        """Convert world coordinates to screen coordinates."""
        return self.apply_to_position(world_x, world_y)
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple:
        """Convert screen coordinates to world coordinates."""
        world_x = screen_x + self.target_x - self.offset_x
        world_y = screen_y + self.target_y - self.offset_y
        return (world_x, world_y)
    
    def is_shaking(self) -> bool:
        """Check if camera is currently shaking."""
        return self.shake_duration > 0
    
    def stop_shake(self):
        """Stop any active shake effect."""
        self.shake_duration = 0
        self.offset_x = 0
        self.offset_y = 0
    
    def set_smoothing(self, smoothing: float):
        """Set camera smoothing factor (0.0 - 1.0)."""
        self.smoothing = max(0.0, min(1.0, smoothing))
    
    def reset(self):
        """Reset camera to default state."""
        self.offset_x = 0
        self.offset_y = 0
        self.shake_amount = 0
        self.shake_duration = 0
        self.target_x = 0
        self.target_y = 0