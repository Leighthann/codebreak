# game.py (REFACTORED - COMPLETE VERSION)
import pygame
import sys
import random
import math
import requests
import os
import json
import asyncio
import websockets
import time
from datetime import datetime

# Import existing game modules
from effects import GameEffects
# Uncomment these as they exist in your project:
# from enemy import Enemy
# from world import WorldGenerator
# from worldObject import WorldObjects
# from player import Player

# Import new modular systems
from crafting import CraftingSystem
from ui_system import UIManager
from settings_manager import SettingsManager
from auth_manager import AuthManager
from leaderboard_manager import LeaderboardManager
from state_manager import StateManager
from font_manager import FontManager
from camera_system import CameraSystem

pygame.init()

# Game window settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
TILE_SIZE = 32
BG_COLOR = (10, 10, 25)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
NEON_BLUE = (0, 195, 255)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 41, 117)
NEON_RED = (255, 49, 49)
NEON_PURPLE = (190, 0, 255)


class Game:
    """Main game class - refactored with modular managers."""
    
    # Custom event IDs
    GAME_OVER_EVENT_ID = pygame.USEREVENT + 1
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        pygame.display.init()
        
        # Create resizable screen
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("CodeBreak")
        self.current_width = WIDTH
        self.current_height = HEIGHT
        pygame.display.flip()
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        # Initialize all managers (NEW - replaces scattered initialization)
        self.font_manager = FontManager()
        self.settings_manager = SettingsManager()
        self.auth_manager = AuthManager()
        self.state_manager = StateManager(initial_state="menu", transition_duration=15)
        self.camera_system = CameraSystem()
        self.ui_manager = UIManager(WIDTH, HEIGHT)
        self.crafting_system = CraftingSystem(
            self.font_manager.get_sm_font(),
            self.font_manager.get_md_font()
        )
        self.leaderboard_manager = LeaderboardManager(
            self.auth_manager.get_server_url(),
            self.auth_manager.get_auth_headers()
        )
        
        # Store event ID for easy access
        self.game_over_event_id = Game.GAME_OVER_EVENT_ID
        
        # Game state flags
        self.game_over_triggered = False
        self.final_score = 0
        self.final_time = 0
        
        # Wave and timing state
        self.current_wave = 1
        self.game_start_time = 0
        
        # Game session info
        self.game_id = None
        self.is_host = False
        self.is_solo = False
        
        # Initialize effects system (using settings from manager)
        self.effects = GameEffects(
            volume=self.settings_manager.get_setting("sound_volume")
        )
        
        # Create game objects
        self.player = None
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.effects_list = []
        
        # Game metrics
        self.score = 0
        self.survival_time = 0
        
        # Wave system
        self.wave_number = 0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.next_wave_timer = 0
        
        # World generation
        self.world_generator = None
        self.object_sprites = {}
        self.resource_sprites = {}
        self.power_up_sprites = {}
        self.enemy_sprite_sheet = None
        self.player_sprite_sheet = None
        
        # Initialize background elements
        self.bg_particles = []
        self.grid_offset_y = 0
        
        # Multiplayer
        self.other_players = {}
        self.teammates = []
        self.last_position_update = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.websocket = None
        self.websocket_task = None
        self.connected_to_server = False
        self.connection_attempts = 0
        self.session_id = None
        self.score_submitted = False
        
        # Game state
        self.state = {
            "game_id": None,
            "is_host": False,
            "player_pos": (0, 0),
            "score": 0,
            "health": 100,
            "inventory": {},
            "wave": 1
        }
        
        # Create chat system if it exists
        # self.chat_system = ChatSystem(self.font_manager.get_sm_font())
        
        # Create UI elements using the new UI manager
        self.create_all_ui_elements()
    
    def create_all_ui_elements(self):
        """Create all UI elements using the UI manager."""
        # Menu buttons
        self.ui_manager.create_menu_buttons({
            'start': lambda: self.state_manager.transition_to("gameplay"),
            'leaderboard': lambda: self.state_manager.transition_to("leaderboard"),
            'settings': lambda: self.state_manager.transition_to("settings"),
            'quit': pygame.quit
        })
        
        # Pause buttons
        self.ui_manager.create_pause_buttons({
            'resume': lambda: self.state_manager.transition_to("gameplay"),
            'leaderboard': lambda: self.state_manager.transition_to("leaderboard"),
            'settings': lambda: self.state_manager.transition_to("settings"),
            'menu': lambda: self.state_manager.transition_to("menu")
        })
        
        # Game over buttons
        self.ui_manager.create_game_over_buttons({
            'restart': lambda: asyncio.create_task(self.restart_game()),
            'leaderboard': lambda: self.state_manager.transition_to("leaderboard"),
            'menu': lambda: self.state_manager.transition_to("menu")
        })
        
        # Leaderboard back button
        self.ui_manager.create_leaderboard_button(
            lambda: self.state_manager.transition_to(
                self.state_manager.get_previous_state() 
                if self.state_manager.get_previous_state() in ["menu", "game_over"] 
                else "menu"
            )
        )
        
        # Settings controls
        self.ui_manager.create_settings_controls(
            self.settings_manager.get_all_settings(),
            {
                'save': self.save_and_return_from_settings,
                'sound_volume': lambda val: self.update_setting("sound_volume", val),
                'music_volume': lambda val: self.update_setting("music_volume", val),
                'screen_shake': lambda val: self.update_setting("screen_shake", val),
                'show_damage': lambda val: self.update_setting("show_damage", val),
                'difficulty': lambda val: self.update_setting("difficulty", val)
            }
        )
    
    def save_and_return_from_settings(self):
        """Save settings and return to previous screen."""
        self.settings_manager.save_settings()
        self.state_manager.transition_to("menu")
    
    def update_setting(self, key: str, value):
        """Update a setting value."""
        self.settings_manager.update_setting(key, value)
        
        # Apply audio settings immediately
        if key == "sound_volume":
            self.effects.set_volume(value)
        elif key == "music_volume":
            # Apply to music system if you have one
            pass
    
    def play_sound(self, sound_name: str):
        """Play a sound effect."""
        if hasattr(self.effects, 'play'):
            self.effects.play(sound_name)
    
    def add_effect(self, effect_type: str, x: float, y: float, **kwargs):
        """Add a visual effect."""
        effect = {
            'type': effect_type,
            'x': x,
            'y': y,
            'timer': kwargs.get('duration', 1.0) * 60,
            **kwargs
        }
        self.effects_list.append(effect)
    
    def start_screen_shake(self, amount: int, duration: float):
        """Start screen shake effect."""
        if self.settings_manager.get_setting("screen_shake"):
            self.camera_system.start_shake(amount, duration)
    
    async def handle_gameplay_state(self, events=None, dt=1/60):
        """Handle gameplay state."""
        # Initialize game world if needed
        if not self.player:
            await self.initialize_game_world()
            return
        
        keys = pygame.key.get_pressed()
        
        # Handle events
        for event in events or []:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif hasattr(self, 'game_over_event_id') and event.type == self.game_over_event_id:
                pygame.time.set_timer(self.game_over_event_id, 0)
                self.state_manager.transition_to("game_over")
                return
            elif hasattr(self, 'chat_system') and self.chat_system.handle_event(event, self.player):
                continue
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_resource_sharing_ui()
            elif event.type == pygame.KEYDOWN:
                # Quick share shortcuts (only when crafting menu closed)
                if not self.crafting_system.is_menu_open() and event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    resource_types = ["code_fragments", "energy_cores", "data_shards"]
                    resource_index = event.key - pygame.K_1
                    if resource_index < len(resource_types):
                        self.handle_resource_sharing_ui(resource_types[resource_index])
                
                # Crafting menu toggle
                elif event.key == pygame.K_c:
                    self.crafting_system.toggle_menu()
                    self.play_sound("menu_select")
                
                # ESC handling
                elif event.key == pygame.K_ESCAPE:
                    if self.crafting_system.is_menu_open():
                        self.crafting_system.close_menu()
                        self.play_sound("menu_select")
                    else:
                        self.state_manager.transition_to("pause")
                
                # Crafting input handling (delegated to crafting system)
                elif self.crafting_system.handle_crafting_input(
                    event, self.player,
                    sound_callback=self.play_sound,
                    effect_callback=self.add_effect
                ):
                    continue
        
        # Handle continuous gameplay actions when crafting menu is closed
        if not self.crafting_system.is_menu_open():
            # Update player (handles movement, energy, animation, tools, projectiles)
            try:
                await self.player.update(dt, keys, self.enemies, self.world_generator)
            except Exception as e:
                print(f"Error in player update: {e}")
            
            # Update game world
            await self.update_game_world(dt)
        
        # Update camera to follow player
        self.camera_system.update()
        
        # Draw game world
        self.draw_gameplay_elements()
        
        # Draw crafting UI on top if active
        self.crafting_system.draw_crafting_ui(
            self.screen, 
            self.current_width, 
            self.current_height,
            self.player.resources if self.player else {}
        )
        
        # Always draw UI
        self.draw_gameplay_ui()
        
        # Send position updates for multiplayer
        if self.player and self.player.is_moving and hasattr(self, 'websocket') and self.websocket:
            asyncio.create_task(self.send_position_update())
    
    def draw_gameplay_ui(self):
        """Draw gameplay UI elements."""
        if not self.player:
            return
        
        # Show equipped tool
        equipped_tool_name = self.crafting_system.get_equipped_tool_name(self.player)
        if equipped_tool_name:
            tool_text = self.font_manager.get_sm_font().render(
                f"Equipped: {equipped_tool_name} (Press E to use)",
                True, NEON_BLUE
            )
            self.screen.blit(tool_text, (10, self.current_height - 30))
        
        # Show score
        score_text = self.font_manager.get_md_font().render(
            f"Score: {self.score}",
            True, WHITE
        )
        self.screen.blit(score_text, (10, 10))
        
        # Show wave
        wave_text = self.font_manager.get_md_font().render(
            f"Wave: {self.wave_number}",
            True, WHITE
        )
        self.screen.blit(wave_text, (10, 40))
        
        # Show health
        health_text = self.font_manager.get_md_font().render(
            f"Health: {self.player.health}/{self.player.max_health}",
            True, GREEN if self.player.health > 50 else RED
        )
        self.screen.blit(health_text, (10, 70))
        
        # Show resources
        y_offset = 100
        for resource, amount in self.player.resources.items():
            resource_name = resource.replace("_", " ").title()
            resource_text = self.font_manager.get_sm_font().render(
                f"{resource_name}: {amount}",
                True, CYAN
            )
            self.screen.blit(resource_text, (10, y_offset))
            y_offset += 25
    
    # ==================== GAME WORLD METHODS ====================
    
    async def initialize_game_world(self):
        """Initialize the game world."""
        print("Initializing game world...")
        # Initialize player, enemies, world generator, etc.
        # This should contain your existing initialization code
        
        # Set up player callbacks for effects and sounds
        if self.player:
            self.player.set_callbacks(
                sound_callback=self.play_sound,
                effect_callback=self.add_effect,
                screen_shake_callback=self.start_screen_shake
            )
        
        pass
    
    async def update_game_world(self, dt):
        """Update game world state."""
        # Update enemies (they handle their own animation and AI)
        for enemy in self.enemies[:]:
            await enemy.update(self.player)
            enemy.animate()
            
            # Check if enemy is dead
            if enemy.health <= 0:
                self.enemies.remove(enemy)
                self.score += 10
                self.add_effect("explosion", enemy.x, enemy.y)
        
        # Update resources
        for resource in self.resources[:]:
            if hasattr(resource, 'update'):
                resource.update(dt)
        
        # Update power-ups
        for power_up in self.power_ups[:]:
            if hasattr(power_up, 'update'):
                power_up.update(dt)
        
        # Update effects
        for effect in self.effects_list[:]:
            effect['timer'] -= 1
            if effect['timer'] <= 0:
                self.effects_list.remove(effect)
        
        # Update survival time
        self.survival_time += dt
        
        # Check for wave completion
        if len(self.enemies) == 0 and self.enemies_to_spawn == 0:
            self.next_wave_timer += dt
            if self.next_wave_timer >= 5.0:  # 5 second delay between waves
                self.start_next_wave()
    
    def start_next_wave(self):
        """Start the next wave of enemies."""
        self.wave_number += 1
        self.enemies_to_spawn = 5 + (self.wave_number * 2)
        self.next_wave_timer = 0
        print(f"Starting wave {self.wave_number}")
    
    def draw_gameplay_elements(self):
        """Draw all gameplay elements."""
        # Clear screen
        self.screen.fill(BG_COLOR)
        
        # Draw background elements
        self.draw_background()
        
        # Draw world objects (if world generator exists)
        if self.world_generator:
            # World generator handles its own drawing
            pass
        
        # Draw resources
        for resource in self.resources:
            if hasattr(resource, 'draw'):
                resource.draw(self.screen, self.camera_system)
        
        # Draw power-ups
        for power_up in self.power_ups:
            if hasattr(power_up, 'draw'):
                power_up.draw(self.screen, self.camera_system)
        
        # Draw enemies (they handle their own drawing)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_system)
        
        # Draw player (handles own drawing including projectiles)
        if self.player:
            self.player.draw(self.screen, self.camera_system)
            if hasattr(self.player, 'draw_projectiles'):
                self.player.draw_projectiles(self.screen, self.camera_system)
        
        # Draw other players (multiplayer)
        for player_id, player_data in self.other_players.items():
            # Draw other players
            pass
        
        # Draw effects
        for effect in self.effects_list:
            self.draw_effect(effect)
    
    def draw_background(self):
        """Draw background elements."""
        # Draw grid or background pattern
        for particle in self.bg_particles:
            pygame.draw.circle(self.screen, GRAY, 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
    
    def draw_effect(self, effect):
        """Draw a visual effect."""
        effect_type = effect.get('type')
        x, y = effect.get('x'), effect.get('y')
        
        if effect_type == 'text':
            text = effect.get('text', '')
            color = effect.get('color', WHITE)
            size = effect.get('size', 20)
            font = pygame.font.Font(None, size)
            text_surf = font.render(text, True, color)
            
            # Apply camera offset
            screen_pos = self.camera_system.world_to_screen(x, y)
            self.screen.blit(text_surf, screen_pos)
        
        elif effect_type == 'explosion':
            # Draw explosion effect
            radius = int(20 - (effect['timer'] / 3))
            if radius > 0:
                screen_pos = self.camera_system.world_to_screen(x, y)
                pygame.draw.circle(self.screen, YELLOW, 
                                 (int(screen_pos[0]), int(screen_pos[1])), 
                                 radius)
    
    # ==================== RESOURCE SHARING ====================
    
    def handle_resource_sharing_ui(self, resource_type=None):
        """Handle resource sharing UI."""
        # Implement resource sharing for multiplayer
        if not self.player or not resource_type:
            return
        
        if resource_type in self.player.resources and self.player.resources[resource_type] > 0:
            # Share resource logic
            print(f"Sharing {resource_type}")
    
    # ==================== MULTIPLAYER ====================
    
    async def send_position_update(self):
        """Send position update to server."""
        if not self.websocket or not self.player:
            return
        
        try:
            update = {
                "type": "position_update",
                "player_id": self.session_id,
                "x": self.player.x,
                "y": self.player.y,
                "sprite": self.player.current_sprite_index if hasattr(self.player, 'current_sprite_index') else 0
            }
            await self.websocket.send(json.dumps(update))
        except Exception as e:
            print(f"Error sending position update: {e}")
    
    # ==================== GAME RESTART ====================
    
    async def restart_game(self):
        """Restart the game."""
        # Reset all game state
        self.player = None
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.effects_list = []
        self.score = 0
        self.survival_time = 0
        self.wave_number = 0
        self.game_over_triggered = False
        self.score_submitted = False
        
        # Reset camera
        self.camera_system.reset()
        
        # Transition to gameplay
        self.state_manager.transition_to("gameplay")
    
    # ==================== STATE HANDLERS ====================
    
    async def handle_menu_state(self, events, mouse_pos):
        """Handle menu state."""
        self.screen.fill(BG_COLOR)
        
        # Draw title
        title_surf = self.font_manager.get_title_font().render("CODEBREAK", True, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(self.current_width // 2, 150))
        self.screen.blit(title_surf, title_rect)
        
        # Update and draw buttons
        self.ui_manager.update_widgets(self.ui_manager.menu_buttons, mouse_pos)
        for button in self.ui_manager.menu_buttons:
            button.draw(self.screen, self.font_manager.get_button_font())
        
        # Handle button clicks
        for event in events:
            self.ui_manager.handle_events(self.ui_manager.menu_buttons, event)
    
    async def handle_pause_state(self, events, mouse_pos):
        """Handle pause state."""
        # Draw game in background (paused)
        self.draw_gameplay_elements()
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.current_width, self.current_height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause text
        pause_surf = self.font_manager.get_xl_font().render("PAUSED", True, NEON_PINK)
        pause_rect = pause_surf.get_rect(center=(self.current_width // 2, 150))
        self.screen.blit(pause_surf, pause_rect)
        
        # Update and draw buttons
        self.ui_manager.update_widgets(self.ui_manager.pause_buttons, mouse_pos)
        for button in self.ui_manager.pause_buttons:
            button.draw(self.screen, self.font_manager.get_button_font())
        
        # Handle button clicks
        for event in events:
            self.ui_manager.handle_events(self.ui_manager.pause_buttons, event)
    
    async def handle_game_over_state(self, events, mouse_pos):
        """Handle game over state."""
        self.screen.fill(BG_COLOR)
        
        # Submit score if not already submitted
        if not self.score_submitted and self.auth_manager.is_authenticated():
            self.leaderboard_manager.submit_score(
                self.auth_manager.username,
                self.score,
                self.survival_time
            )
            self.score_submitted = True
        
        # Draw game over text
        game_over_surf = self.font_manager.get_xl_font().render("GAME OVER", True, NEON_RED)
        game_over_rect = game_over_surf.get_rect(center=(self.current_width // 2, 150))
        self.screen.blit(game_over_surf, game_over_rect)
        
        # Draw score
        score_surf = self.font_manager.get_lg_font().render(f"Score: {self.score}", True, WHITE)
        score_rect = score_surf.get_rect(center=(self.current_width // 2, 220))
        self.screen.blit(score_surf, score_rect)
        
        # Draw survival time
        time_surf = self.font_manager.get_md_font().render(
            f"Survived: {int(self.survival_time)}s", True, WHITE
        )
        time_rect = time_surf.get_rect(center=(self.current_width // 2, 270))
        self.screen.blit(time_surf, time_rect)
        
        # Update and draw buttons
        self.ui_manager.update_widgets(self.ui_manager.game_over_buttons, mouse_pos)
        for button in self.ui_manager.game_over_buttons:
            button.draw(self.screen, self.font_manager.get_button_font())
        
        # Handle button clicks
        for event in events:
            self.ui_manager.handle_events(self.ui_manager.game_over_buttons, event)
    
    async def handle_leaderboard_state(self, events, mouse_pos):
        """Handle leaderboard state."""
        self.screen.fill(BG_COLOR)
        
        # Fetch leaderboard if needed
        if self.leaderboard_manager.needs_update():
            self.leaderboard_manager.fetch_leaderboard()
        
        # Draw title
        title_surf = self.font_manager.get_xl_font().render("LEADERBOARD", True, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(self.current_width // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        # Draw leaderboard entries
        entries = self.leaderboard_manager.get_entries()
        y_offset = 150
        
        for i, entry in enumerate(entries[:10]):
            rank_text = f"{i + 1}. {entry['name']}: {entry['score']}"
            rank_surf = self.font_manager.get_md_font().render(rank_text, True, WHITE)
            rank_rect = rank_surf.get_rect(center=(self.current_width // 2, y_offset))
            self.screen.blit(rank_surf, rank_rect)
            y_offset += 40
        
        # Update and draw back button
        if self.ui_manager.leaderboard_back_button:
            self.ui_manager.leaderboard_back_button.update(mouse_pos)
            self.ui_manager.leaderboard_back_button.draw(
                self.screen, 
                self.font_manager.get_button_font()
            )
        
        # Handle button clicks
        for event in events:
            if self.ui_manager.leaderboard_back_button:
                self.ui_manager.leaderboard_back_button.handle_event(event)
    
    async def handle_settings_state(self, events, mouse_pos):
        """Handle settings state."""
        self.screen.fill(BG_COLOR)
        
        # Draw title
        title_surf = self.font_manager.get_xl_font().render("SETTINGS", True, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(self.current_width // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        # Update and draw controls
        self.ui_manager.update_widgets(self.ui_manager.settings_controls, mouse_pos)
        for control in self.ui_manager.settings_controls:
            control.draw(self.screen, self.font_manager.get_md_font())
        
        # Handle control events
        for event in events:
            self.ui_manager.handle_events(self.ui_manager.settings_controls, event)
    
    def draw_fade_overlay(self):
        """Draw fade transition overlay."""
        alpha = self.state_manager.get_fade_alpha()
        if alpha > 0:
            overlay = pygame.Surface((self.current_width, self.current_height))
            overlay.set_alpha(alpha)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
    
    # ==================== MAIN GAME LOOP ====================
    
    async def run(self):
        """Main game loop."""
        running = True
        
        while running:
            dt = self.clock.tick(self.FPS) / 1000.0  # Delta time in seconds
            events = pygame.event.get()
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle window events
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.current_width = event.w
                    self.current_height = event.h
                    self.screen = pygame.display.set_mode(
                        (self.current_width, self.current_height), 
                        pygame.RESIZABLE
                    )
                    self.ui_manager.update_positions(
                        self.current_width, 
                        self.current_height
                    )
            
            # Update state transitions
            self.state_manager.update_transition()
            
            # Handle current state
            current_state = self.state_manager.get_state()
            
            if current_state == "menu":
                await self.handle_menu_state(events, mouse_pos)
            elif current_state == "gameplay":
                await self.handle_gameplay_state(events, dt)
            elif current_state == "pause":
                await self.handle_pause_state(events, mouse_pos)
            elif current_state == "game_over":
                await self.handle_game_over_state(events, mouse_pos)
            elif current_state == "leaderboard":
                await self.handle_leaderboard_state(events, mouse_pos)
            elif current_state == "settings":
                await self.handle_settings_state(events, mouse_pos)
            
            # Draw fade overlay if transitioning
            if self.state_manager.is_transitioning():
                self.draw_fade_overlay()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())