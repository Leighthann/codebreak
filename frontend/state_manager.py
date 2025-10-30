# state_manager.py
"""
State Manager for handling game state transitions and state-related logic.
"""
import pygame
import random
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game


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
        
        # Reference to game instance (set externally)
        self.game: Optional['Game'] = None
        
        # Menu animation properties
        self.title_y = -100
        self.title_target_y = 100
        self.subtitle_alpha = 0
        self.grid_offset = 0
        self.grid_speed = 0.5
        self.buttons_alpha = 0
        
        # Menu background and particles
        self.menu_background = None
        self.data_particles = []
    
    def set_game_instance(self, game: 'Game'):
        """Set reference to game instance for state handlers."""
        self.game = game
        # Initialize menu background when game is set
        if game:
            self.initialize_menu_background(game.screen.get_width(), game.screen.get_height())
    
    def initialize_menu_background(self, width, height):
        """Initialize the cyberpunk menu background and data particles."""
        # Create background surface
        self.menu_background = pygame.Surface((width, height))
        self.generate_cyberpunk_background(width, height)
        
        # Create data particles
        self.data_particles = []
        NEON_BLUE = (0, 195, 255)
        NEON_GREEN = (57, 255, 20)
        NEON_PINK = (255, 41, 117)
        NEON_PURPLE = (191, 64, 191)
        
        for _ in range(50):
            self.data_particles.append({
                "x": random.randint(0, width),
                "y": random.randint(0, height),
                "size": random.randint(1, 3),
                "speed": random.uniform(0.2, 1.0),
                "color": random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK, NEON_PURPLE])
            })
    
    def generate_cyberpunk_background(self, width, height):
        """Create a cyberpunk-style grid background."""
        if not self.menu_background:
            return
            
        BG_COLOR = (10, 10, 30)  # Dark blue base
        NEON_BLUE = (0, 195, 255)
        NEON_PINK = (255, 41, 117)
        NEON_GREEN = (57, 255, 20)
        
        self.menu_background.fill(BG_COLOR)
        
        # Draw horizontal grid lines
        for y in range(0, height, 20):
            alpha = random.randint(20, 100)
            line_color = (0, 100, 255)
            pygame.draw.line(self.menu_background, line_color, (0, y), (width, y), 1)
        
        # Draw vertical grid lines
        for x in range(0, width, 40):
            alpha = random.randint(20, 100)
            line_color = (0, 100, 255)
            pygame.draw.line(self.menu_background, line_color, (x, 0), (x, height), 1)
        
        # Add "data nodes" at grid intersections
        for x in range(0, width, 40):
            for y in range(0, height, 20):
                if random.random() < 0.1:  # 10% chance
                    size = random.randint(1, 3)
                    color_choice = random.random()
                    if color_choice < 0.6:
                        color = NEON_BLUE
                    elif color_choice < 0.8:
                        color = NEON_PINK
                    else:
                        color = NEON_GREEN
                    pygame.draw.circle(self.menu_background, color, (x, y), size)
    
    def update_menu_animations(self, width, height):
        """Update menu animations."""
        # Update title animation
        if self.title_y < self.title_target_y:
            self.title_y += (self.title_target_y - self.title_y) * 0.1
        
        # Update subtitle fade-in
        if self.subtitle_alpha < 255:
            self.subtitle_alpha += 5
        
        # Update button fade-in
        if self.buttons_alpha < 255:
            self.buttons_alpha += 5
        
        # Update grid animation
        self.grid_offset += self.grid_speed
        if self.grid_offset > height:
            self.grid_offset = 0
        
        # Update data particles
        for particle in self.data_particles:
            particle["y"] += particle["speed"]
            if particle["y"] > height:
                particle["y"] = 0
                particle["x"] = random.randint(0, width)
    
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

        # Debug log for transitions
        print(f"Transition requested: {new_state} (fade={fade})")

        if fade:
            self.fading_out = True
            self.next_state = new_state
            self.transition_timer = self.transition_duration
        else:
            # Cancel any ongoing fades and switch immediately
            self.fading_out = False
            self.fading_in = False
            self.next_state = None
            self.transition_timer = 0
            self.previous_state = self.current_state
            self.current_state = new_state
            print(f"State changed: {self.previous_state} -> {self.current_state}")
            # Notify game instance of immediate state enter
            try:
                if self.game and hasattr(self.game, 'on_state_enter'):
                    self.game.on_state_enter(self.current_state, self.previous_state)
            except Exception as e:
                print("Error calling on_state_enter:", e)
    
    def update_transition(self):
        """Update transition animation state."""
        if self.fading_out:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.fading_out = False
                self.previous_state = self.current_state
                self.current_state = self.next_state
                
                # Skip fade-in for gameplay to make it immediately playable
                if self.current_state == "gameplay":
                    self.fading_in = False
                    self.next_state = None
                    self.transition_timer = 0
                    print(f"State changed: {self.previous_state} -> {self.current_state} (no fade-in)")
                else:
                    self.fading_in = True
                    self.transition_timer = self.transition_duration
                    print(f"State changed: {self.previous_state} -> {self.current_state}")
                
                # Notify game instance that we entered the new state after fade
                try:
                    if self.game and hasattr(self.game, 'on_state_enter'):
                        self.game.on_state_enter(self.current_state, self.previous_state)
                except Exception as e:
                    print("Error calling on_state_enter after fade:", e)
        
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
    
    # ==================== STATE HANDLERS ====================
    
    async def handle_menu_state(self, events, mouse_pos):
        """Handle menu state with animated cyberpunk background."""
        if not self.game:
            return
        
        # Initialize background if not already done
        if not self.menu_background:
            self.initialize_menu_background(self.game.current_width, self.game.current_height)
        
        # Update animations
        self.update_menu_animations(self.game.current_width, self.game.current_height)
        
        # Draw cyberpunk background
        self.game.screen.blit(self.menu_background, (0, 0))
        
        # Draw animated grid overlay
        grid_surface = pygame.Surface((self.game.current_width, self.game.current_height), pygame.SRCALPHA)
        for y in range(int(-self.grid_offset), self.game.current_height, 20):
            alpha = int(100 * (1 - (abs(y - self.game.current_height/2) / (self.game.current_height/2))))
            line_color = (0, 150, 255)
            pygame.draw.line(grid_surface, line_color, (0, y), (self.game.current_width, y), 1)
        self.game.screen.blit(grid_surface, (0, 0))
        
        # Draw data particles
        for particle in self.data_particles:
            pygame.draw.circle(self.game.screen, particle["color"], 
                             (int(particle["x"]), int(particle["y"])), 
                             particle["size"])
        
        # Draw title with glow effect
        title_text = "CODEBREAK"
        title_font = self.game.font_manager.get_title_font()
        subtitle_font = self.game.font_manager.get_info_font()
        
        # Colors
        NEON_BLUE = (0, 195, 255)
        WHITE = (255, 255, 255)
        
        # Add glow effect to title
        glow_size = title_font.size(title_text)
        glow_surf = pygame.Surface((glow_size[0] + 20, glow_size[1] + 20), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = 20 - i*2
            size = i*2
            pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), 
                           (10-i, 10-i, glow_size[0]+size, glow_size[1]+size), 
                           border_radius=10)
        self.game.screen.blit(glow_surf, (self.game.current_width // 2 - (glow_size[0] + 20) // 2, int(self.title_y) - 10))
        
        # Draw title and subtitle
        title_surf = title_font.render(title_text, True, WHITE)
        title_rect = title_surf.get_rect(center=(self.game.current_width // 2, int(self.title_y)))
        self.game.screen.blit(title_surf, title_rect)
        
        # Draw subtitle with fade-in
        subtitle_surf = subtitle_font.render("A Digital Survival Game", True, (180, 180, 255))
        subtitle_surf.set_alpha(int(self.subtitle_alpha))
        subtitle_rect = subtitle_surf.get_rect(center=(self.game.current_width // 2, int(self.title_y) + 60))
        self.game.screen.blit(subtitle_surf, subtitle_rect)
        
        # Update and draw buttons
        self.game.ui_manager.update_widgets(self.game.ui_manager.menu_buttons, mouse_pos)
        for button in self.game.ui_manager.menu_buttons:
            button.draw(self.game.screen, self.game.font_manager.get_button_font())
        
        # Draw version info
        version_text = subtitle_font.render("v1.0", True, (100, 100, 150))
        self.game.screen.blit(version_text, (self.game.current_width - version_text.get_width() - 10, 
                                            self.game.current_height - version_text.get_height() - 10))
        
        # Handle button clicks
        for event in events:
            self.game.ui_manager.handle_events(self.game.ui_manager.menu_buttons, event)
    
    async def handle_pause_state(self, events, mouse_pos):
        """Handle pause state."""
        if not self.game:
            return
            
        # Draw game in background (paused)
        self.game.draw_gameplay_elements()
        
        # Colors
        BLACK = (0, 0, 0)
        NEON_PINK = (255, 41, 117)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.game.current_width, self.game.current_height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.game.screen.blit(overlay, (0, 0))
        
        # Draw pause text
        pause_surf = self.game.font_manager.get_xl_font().render("PAUSED", True, NEON_PINK)
        pause_rect = pause_surf.get_rect(center=(self.game.current_width // 2, 150))
        self.game.screen.blit(pause_surf, pause_rect)
        
        # Update and draw buttons
        self.game.ui_manager.update_widgets(self.game.ui_manager.pause_buttons, mouse_pos)
        for button in self.game.ui_manager.pause_buttons:
            button.draw(self.game.screen, self.game.font_manager.get_button_font())
        
        # Handle button clicks
        for event in events:
            self.game.ui_manager.handle_events(self.game.ui_manager.pause_buttons, event)
    
    async def handle_game_over_state(self, events, mouse_pos):
        """Handle game over state."""
        if not self.game:
            return
            
        # Colors
        BG_COLOR = (10, 10, 25)
        NEON_RED = (255, 49, 49)
        WHITE = (255, 255, 255)
        
        self.game.screen.fill(BG_COLOR)
        
        # Submit score if not already submitted
        if not self.game.score_submitted and self.game.auth_manager.is_authenticated():
            self.game.leaderboard_manager.submit_score(
                self.game.auth_manager.username,
                self.game.score,
                self.game.survival_time,
                self.game.wave_number,
                self.game.game_id  # Pass game_id for game-specific leaderboards
            )
            self.game.score_submitted = True
        
        # Draw game over text
        game_over_surf = self.game.font_manager.get_xl_font().render("GAME OVER", True, NEON_RED)
        game_over_rect = game_over_surf.get_rect(center=(self.game.current_width // 2, 150))
        self.game.screen.blit(game_over_surf, game_over_rect)
        
        # Draw score
        score_surf = self.game.font_manager.get_lg_font().render(
            f"Score: {self.game.score}", True, WHITE
        )
        score_rect = score_surf.get_rect(center=(self.game.current_width // 2, 220))
        self.game.screen.blit(score_surf, score_rect)
        
        # Draw survival time
        time_surf = self.game.font_manager.get_md_font().render(
            f"Survived: {int(self.game.survival_time)}s", True, WHITE
        )
        time_rect = time_surf.get_rect(center=(self.game.current_width // 2, 270))
        self.game.screen.blit(time_surf, time_rect)
        
        # Update and draw buttons
        self.game.ui_manager.update_widgets(self.game.ui_manager.game_over_buttons, mouse_pos)
        for button in self.game.ui_manager.game_over_buttons:
            button.draw(self.game.screen, self.game.font_manager.get_button_font())
        
        # Handle button clicks
        for event in events:
            self.game.ui_manager.handle_events(self.game.ui_manager.game_over_buttons, event)
    
    async def handle_leaderboard_state(self, events, mouse_pos):
        """Handle leaderboard state."""
        if not self.game:
            return
            
        # Colors
        BG_COLOR = (10, 10, 25)
        NEON_BLUE = (0, 195, 255)
        NEON_PINK = (255, 41, 117)
        WHITE = (255, 255, 255)
        GRAY = (150, 150, 150)
        
        self.game.screen.fill(BG_COLOR)
        
        # Set game_id in leaderboard manager if not already set
        if self.game.game_id and not self.game.leaderboard_manager.current_game_id:
            self.game.leaderboard_manager.set_game_id(self.game.game_id)
        
        # Fetch leaderboard if needed
        if self.game.leaderboard_manager.needs_update():
            self.game.leaderboard_manager.fetch_leaderboard()
        
        # Draw title with view mode indicator
        view_mode = self.game.leaderboard_manager.get_view_mode()
        title_text = "GLOBAL LEADERBOARD" if view_mode == "global" else "GAME LEADERBOARD"
        title_surf = self.game.font_manager.get_xl_font().render(title_text, True, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(self.game.current_width // 2, 80))
        self.game.screen.blit(title_surf, title_rect)
        
        # Draw toggle buttons if game leaderboard is available
        if self.game.leaderboard_manager.can_view_game_leaderboard():
            button_y = 130
            button_width = 150
            button_height = 35
            spacing = 20
            total_width = (button_width * 2) + spacing
            start_x = (self.game.current_width - total_width) // 2
            
            # Global button
            global_color = NEON_BLUE if view_mode == "global" else GRAY
            global_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            pygame.draw.rect(self.game.screen, global_color, global_rect, 2)
            global_text = self.game.font_manager.get_sm_font().render("GLOBAL", True, global_color)
            global_text_rect = global_text.get_rect(center=global_rect.center)
            self.game.screen.blit(global_text, global_text_rect)
            
            # Game button
            game_color = NEON_PINK if view_mode == "game" else GRAY
            game_rect = pygame.Rect(start_x + button_width + spacing, button_y, button_width, button_height)
            pygame.draw.rect(self.game.screen, game_color, game_rect, 2)
            game_text = self.game.font_manager.get_sm_font().render("THIS GAME", True, game_color)
            game_text_rect = game_text.get_rect(center=game_rect.center)
            self.game.screen.blit(game_text, game_text_rect)
            
            # Handle toggle button clicks
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if global_rect.collidepoint(event.pos):
                        self.game.leaderboard_manager.set_view_mode("global")
                        self.game.leaderboard_manager.fetch_leaderboard(force=True)
                    elif game_rect.collidepoint(event.pos):
                        self.game.leaderboard_manager.set_view_mode("game")
                        self.game.leaderboard_manager.fetch_leaderboard(force=True)
        
        # Draw leaderboard entries
        entries = self.game.leaderboard_manager.get_entries()
        y_offset = 180 if self.game.leaderboard_manager.can_view_game_leaderboard() else 150
        
        for i, entry in enumerate(entries[:10]):
            rank_text = f"{i + 1}. {entry['name']}: {entry['score']}"
            rank_surf = self.game.font_manager.get_md_font().render(rank_text, True, WHITE)
            rank_rect = rank_surf.get_rect(center=(self.game.current_width // 2, y_offset))
            self.game.screen.blit(rank_surf, rank_rect)
            y_offset += 40
        
        # Update and draw back button
        if self.game.ui_manager.leaderboard_back_button:
            self.game.ui_manager.leaderboard_back_button.update(mouse_pos)
            self.game.ui_manager.leaderboard_back_button.draw(
                self.game.screen, 
                self.game.font_manager.get_button_font()
            )
        
        # Handle button clicks
        for event in events:
            # Prefer direct handling for leaderboard back button to ensure the callback runs
            if self.game.ui_manager.leaderboard_back_button and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    pos = event.pos
                except AttributeError:
                    pos = None

                if pos and self.game.ui_manager.leaderboard_back_button.rect.collidepoint(pos):
                    print("UI DEBUG: Leaderboard BACK clicked at", pos)
                    try:
                        self.game.ui_manager.leaderboard_back_button.callback()
                    except Exception as e:
                        print("UI DEBUG: Leaderboard BACK callback raised:", e)
                    continue
            if self.game.ui_manager.leaderboard_back_button:
                self.game.ui_manager.leaderboard_back_button.handle_event(event)
    
    async def handle_settings_state(self, events, mouse_pos):
        """Handle settings state."""
        if not self.game:
            return
            
        # Colors
        BG_COLOR = (10, 10, 25)
        NEON_BLUE = (0, 195, 255)
        
        self.game.screen.fill(BG_COLOR)
        
        # Draw title
        title_surf = self.game.font_manager.get_xl_font().render("SETTINGS", True, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(self.game.current_width // 2, 80))
        self.game.screen.blit(title_surf, title_rect)
        
        # Update and draw controls
        self.game.ui_manager.update_widgets(self.game.ui_manager.settings_controls, mouse_pos)
        for control in self.game.ui_manager.settings_controls:
            control.draw(self.game.screen, self.game.font_manager.get_md_font())
        
        # Handle control events
        for event in events:
            self.game.ui_manager.handle_events(self.game.ui_manager.settings_controls, event)
    
    def draw_fade_overlay(self):
        """Draw fade transition overlay."""
        if not self.game:
            return
            
        alpha = self.get_fade_alpha()
        if alpha > 0:
            BLACK = (0, 0, 0)
            overlay = pygame.Surface((self.game.current_width, self.game.current_height))
            overlay.set_alpha(alpha)
            overlay.fill(BLACK)
            self.game.screen.blit(overlay, (0, 0))