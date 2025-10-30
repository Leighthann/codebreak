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
from enemy import Enemy
from world import WorldGenerator
from worldObject import WorldObject, Resource
from player import Player

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
    # Use a 5-second fade (duration measured in frames). FPS is defined above.
        self.state_manager = StateManager(initial_state="menu", transition_duration=int(5 * self.FPS))
        self.state_manager.set_game_instance(self)  # Set game reference for state handlers
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
        
        # Screen shake effect
        self.screen_shake_amount = 0
        self.screen_shake_duration = 0
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        
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

        # Pending actions (used for fade transitions)
        self.pending_restart = False
        
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
            'start': lambda: self.start_game_with_fade(),
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
        # Make restart synchronous enough to give immediate visual feedback
        # by doing an immediate transition (fade=False) and schedule the async
        # reset work. This avoids the user having to click twice.
        self.ui_manager.create_game_over_buttons({
            'restart': lambda: self.request_restart_with_fade(),
            # Make leaderboard and menu transitions immediate from game over
            'leaderboard': lambda: self.state_manager.transition_to("leaderboard", fade=False),
            'menu': lambda: self.state_manager.transition_to("menu", fade=False)
        })
        
        # Leaderboard back button
        # Use fade=False for the Back button so returning from leaderboard is immediate
        self.ui_manager.create_leaderboard_button(
            lambda: self.state_manager.transition_to(
                self.state_manager.get_previous_state()
                if self.state_manager.get_previous_state() in ["menu", "game_over"]
                else "menu",
                fade=False
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
        # Initialize game world if needed (only if player doesn't exist AND we haven't just initialized)
        if not self.player:
            # Check if we're in the middle of a fade - if so, skip async init
            # because sync init was already called before the fade started
            if not self.state_manager.is_transitioning():
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
            elif event.type == pygame.KEYDOWN:
                # Resource sharing removed
                
                # Crafting menu toggle
                if event.key == pygame.K_c:
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
            
            # Check for resource collection
            if self.player and self.resources:
                collected = self.player.check_resource_collision(self.resources)
                for resource in collected:
                    self.resources.remove(resource)
            
            # Check if player is dead
            if self.player and self.player.health <= 0:
                print("Player defeated! Transitioning to game over...")
                self.final_score = self.score
                self.final_survival_time = (pygame.time.get_ticks() - self.game_start_time) // 1000
                # Switch immediately to game over (no fade) so the screen appears right away.
                self.state_manager.transition_to("game_over", fade=False)
                return
            
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
        
        # Show score (top right)
        score_text = self.font_manager.get_md_font().render(
            f"Score: {self.score}",
            True, WHITE
        )
        self.screen.blit(score_text, (self.current_width - score_text.get_width() - 20, 20))
        
        # Show survival timer (top right, below score)
        minutes = int(self.survival_time // 60)
        seconds = int(self.survival_time % 60)
        time_text = self.font_manager.get_md_font().render(
            f"Time: {minutes:02d}:{seconds:02d}", 
            True, WHITE
        )
        self.screen.blit(time_text, (self.current_width - time_text.get_width() - 20, 50))
        
        # Show wave (top left)
        wave_text = self.font_manager.get_md_font().render(
            f"Wave: {self.wave_number}",
            True, WHITE
        )
        self.screen.blit(wave_text, (10, 10))
        
        # Show health (top left, below wave)
        health_text = self.font_manager.get_md_font().render(
            f"Health: {self.player.health}/{self.player.max_health}",
            True, GREEN if self.player.health > 50 else RED
        )
        self.screen.blit(health_text, (10, 40))
        
        # Show resources (top left, below health)
        y_offset = 70
        for resource, amount in self.player.resources.items():
            resource_name = resource.replace("_", " ").title()
            resource_text = self.font_manager.get_sm_font().render(
                f"{resource_name}: {amount}",
                True, CYAN
            )
            self.screen.blit(resource_text, (10, y_offset))
            y_offset += 25
    
    # ==================== GAME WORLD METHODS ====================
    
    def load_resource_sprites(self):
        """Load resource sprite images from disk."""
        if self.resource_sprites:
            # Already loaded
            return
        
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        
        for resource_type in resource_types:
            try:
                sprite_path = os.path.join(
                    os.path.dirname(__file__), 
                    "spritesheets", 
                    "resources", 
                    f"{resource_type}.png"
                )
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.resource_sprites[resource_type] = sprite
                print(f"Loaded resource sprite: {resource_type}")
            except Exception as e:
                print(f"Could not load resource sprite {resource_type}: {e}")
                # Create a fallback colored surface
                fallback_colors = {
                    "code_fragments": (0, 255, 255),    # Cyan
                    "energy_cores": (255, 215, 0),      # Gold
                    "data_shards": (255, 41, 117)       # Pink
                }
                fallback = pygame.Surface((24, 24), pygame.SRCALPHA)
                fallback.fill(fallback_colors.get(resource_type, (255, 255, 255)))
                self.resource_sprites[resource_type] = fallback
    
    async def initialize_game_world(self):
        """Initialize the game world."""
        print("Initializing game world...")
        
        # Load resource sprites
        self.load_resource_sprites()
        
        # Create world generator
        if not self.world_generator:
            self.world_generator = WorldGenerator(WIDTH, HEIGHT, TILE_SIZE)
        
        # Create player
        if not self.player:
            spawn_x = WIDTH // 2
            spawn_y = HEIGHT // 2
            
            # Load player sprite sheet if needed
            if not self.player_sprite_sheet:
                try:
                    import os
                    sprite_path = os.path.join(os.path.dirname(__file__), "spritesheets", "player-spritesheet.png")
                    self.player_sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                    print(f"Loaded player sprite sheet from {sprite_path}")
                except Exception as e:
                    print(f"Could not load player sprite: {e}")
                    # Create a simple colored surface as fallback
                    self.player_sprite_sheet = pygame.Surface((32, 32))
                    self.player_sprite_sheet.fill(NEON_BLUE)
            
            self.player = Player(self.player_sprite_sheet, spawn_x, spawn_y)
            
            # Set up player callbacks for effects and sounds
            self.player.set_callbacks(
                sound_callback=self.play_sound,
                effect_callback=self.add_effect,
                screen_shake_callback=self.start_screen_shake
            )
        
        # Initialize game state
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.effects_list = []
        self.score = 0
        self.survival_time = 0
        self.game_start_time = pygame.time.get_ticks()
        
        # Start first wave
        self.wave_number = 1
        self.spawn_wave()
        
        # Spawn initial resources across the map
        self.spawn_initial_resources()
        
        print("Game world initialized successfully!")

    def initialize_game_world_sync(self):
        """Synchronous version of game world initialization used for immediate restarts.

        This mirrors the logic in the async initializer but runs synchronously so
        the UI shows the gameplay screen immediately after the Play Again click.
        """
        try:
            print("Initializing game world (sync)...")
            
            # Load resource sprites
            self.load_resource_sprites()

            # Create world generator
            if not self.world_generator:
                self.world_generator = WorldGenerator(WIDTH, HEIGHT, TILE_SIZE)

            # Create player
            if not self.player:
                spawn_x = WIDTH // 2
                spawn_y = HEIGHT // 2

                # Load player sprite sheet if needed
                if not self.player_sprite_sheet:
                    try:
                        import os
                        sprite_path = os.path.join(os.path.dirname(__file__), "spritesheets", "player-spritesheet.png")
                        self.player_sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                        print(f"Loaded player sprite sheet from {sprite_path}")
                    except Exception as e:
                        print(f"Could not load player sprite: {e}")
                        self.player_sprite_sheet = pygame.Surface((32, 32))
                        self.player_sprite_sheet.fill(NEON_BLUE)

                self.player = Player(self.player_sprite_sheet, spawn_x, spawn_y)

                # Set up player callbacks for effects and sounds
                self.player.set_callbacks(
                    sound_callback=self.play_sound,
                    effect_callback=self.add_effect,
                    screen_shake_callback=self.start_screen_shake
                )

            # Initialize game state
            self.enemies = []
            self.resources = []
            self.power_ups = []
            self.effects_list = []
            self.score = 0
            self.survival_time = 0
            self.game_start_time = pygame.time.get_ticks()

            # Start first wave
            self.wave_number = 1
            self.spawn_wave()
            
            # Spawn initial resources across the map
            self.spawn_initial_resources()

            print("Game world initialized successfully! (sync)")
        except Exception as e:
            print("Error during synchronous game world initialization:", e)
    
    async def update_game_world(self, dt):
        """Update game world state."""
        # Update screen shake
        self.update_camera_shake(dt)
        
        # Update enemies (they handle their own animation and AI)
        for enemy in self.enemies[:]:
            await enemy.update(self.player)
            enemy.animate()
            
            # Check if enemy is dead
            if enemy.health <= 0:
                # Spawn resources from defeated enemy
                self.spawn_resource_from_enemy(enemy.x, enemy.y)
                
                self.enemies.remove(enemy)
                # Score calculation: 100 points × wave_number per defeated enemy
                self.score += 100 * self.wave_number
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
        """Start a new enemy wave with visual and audio effects."""
        self.wave_number += 1
        self.next_wave_timer = 0
        print(f"Starting wave {self.wave_number}")
        
        # Calculate enemies based on wave and difficulty
        base_enemies = 2 + self.wave_number
        difficulty_mult = {"Easy": 0.7, "Normal": 1.0, "Hard": 2.0}
        difficulty_factor = difficulty_mult.get(
            self.settings_manager.get_setting("difficulty"), 
            1.0
        )
        
        self.enemies_to_spawn = max(3, int(base_enemies * difficulty_factor))
        
        # Show wave notification - BIG TEXT ON SCREEN
        self.add_effect(
            "text", 
            WIDTH // 2, 
            HEIGHT // 2, 
            text=f"WAVE {self.wave_number}", 
            color=NEON_BLUE, 
            size=60, 
            duration=120  # 2 seconds at 60 FPS
        )
        
        # Play sound
        if hasattr(self.effects, 'play_sound'):
            self.effects.play_sound("level_up")
        
        # Start screen shake
        self.start_screen_shake(20, 0.5)
        
        # Spawn the wave
        self.spawn_wave()
    
    def start_screen_shake(self, amount, duration):
        """Start screen shake effect."""
        self.screen_shake_amount = amount      # How intense (pixels offset)
        self.screen_shake_duration = duration  # How long (seconds)
    
    def update_camera_shake(self, dt):
        """Update screen shake effect."""
        if self.screen_shake_duration > 0:
            # Decrease duration
            self.screen_shake_duration -= dt
            
            # Calculate offset
            if self.settings_manager.get_setting("screen_shake"):
                intensity = min(self.screen_shake_amount, 10)  # Cap at 10 pixels
                self.camera_offset_x = random.randint(-intensity, intensity)
                self.camera_offset_y = random.randint(-intensity, intensity)
            else:
                self.camera_offset_x = 0
                self.camera_offset_y = 0
                
            # Reset when done
            if self.screen_shake_duration <= 0:
                self.screen_shake_duration = 0
                self.camera_offset_x = 0
                self.camera_offset_y = 0
    
    def spawn_wave(self):
        """Spawn enemies for the current wave."""
        # Load enemy sprite sheet if needed
        if not self.enemy_sprite_sheet:
            try:
                import os
                sprite_path = os.path.join(os.path.dirname(__file__), "spritesheets", "enemy-spritesheet.png")
                self.enemy_sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                print(f"Loaded enemy sprite sheet from {sprite_path}")
            except Exception as e:
                print(f"Could not load enemy sprite: {e}")
                # Create a simple colored surface as fallback
                self.enemy_sprite_sheet = pygame.Surface((32, 32))
                self.enemy_sprite_sheet.fill(NEON_RED)
        
        # Calculate number of enemies based on wave
        num_enemies = 3 + (self.wave_number * 2)
        
        # Get server URL from auth manager
        server_url = self.auth_manager.get_server_url()
        
        # Spawn enemies at random positions around the map edges
        for i in range(num_enemies):
            # Random spawn position (edge of map)
            side = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
            
            if side == 0:  # Top
                x = random.randint(0, WIDTH)
                y = 0
            elif side == 1:  # Right
                x = WIDTH
                y = random.randint(0, HEIGHT)
            elif side == 2:  # Bottom
                x = random.randint(0, WIDTH)
                y = HEIGHT
            else:  # Left
                x = 0
                y = random.randint(0, HEIGHT)
            
            # Create enemy with sprite sheet and server URL
            enemy = Enemy(self.enemy_sprite_sheet, x, y, server_url)
            
            # Scale enemy health based on wave number for progressive difficulty
            # Base health: 50, increases by 20 per wave
            # Wave 1: 50 HP, Wave 2: 70 HP, Wave 3: 90 HP, Wave 4: 110 HP, etc.
            base_health = 50
            health_per_wave = 20
            enemy.health = base_health + (health_per_wave * (self.wave_number - 1))
            enemy.max_health = enemy.health  # Update max health to match
            
            self.enemies.append(enemy)
        
        # Calculate the health for this wave for debug message
        wave_enemy_health = base_health + (health_per_wave * (self.wave_number - 1))
        print(f"Spawned {num_enemies} enemies for wave {self.wave_number} (HP: {wave_enemy_health})")
    
    def spawn_initial_resources(self):
        """Spawn initial resources randomly across the map."""
        # Number of each resource type to spawn initially
        resource_counts = {
            "code_fragments": random.randint(8, 12),
            "energy_cores": random.randint(5, 8),
            "data_shards": random.randint(3, 6)
        }
        
        for resource_type, count in resource_counts.items():
            for _ in range(count):
                # Random position with some padding from edges
                x = random.randint(100, WIDTH - 100)
                y = random.randint(100, HEIGHT - 100)
                
                # Random amount (1-3)
                amount = random.randint(1, 3)
                
                # Get sprite for this resource type
                sprite = self.resource_sprites.get(resource_type, None)
                
                # Create resource with sprite
                resource = Resource(x, y, resource_type, amount, sprite)
                self.resources.append(resource)
        
        print(f"Spawned initial resources: {sum(resource_counts.values())} total")
    
    def spawn_resource_from_enemy(self, enemy_x, enemy_y):
        """Spawn resources when an enemy is defeated."""
        # Chance to drop resources (80% chance)
        if random.random() < 0.8:
            # Determine what to drop
            drop_chances = {
                "code_fragments": 0.5,   # 50% chance
                "energy_cores": 0.3,     # 30% chance
                "data_shards": 0.2       # 20% chance
            }
            
            # Randomly select resource type based on weights
            resource_type = random.choices(
                list(drop_chances.keys()),
                weights=list(drop_chances.values()),
                k=1
            )[0]
            
            # Random amount (1-2 for common, 1 for rare)
            if resource_type == "data_shards":
                amount = 1
            else:
                amount = random.randint(1, 2)
            
            # Spawn near enemy position with slight random offset
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            
            # Get sprite for this resource type
            sprite = self.resource_sprites.get(resource_type, None)
            
            resource = Resource(enemy_x + offset_x, enemy_y + offset_y, resource_type, amount, sprite)
            self.resources.append(resource)
            
            # Visual feedback
            self.add_effect("text", enemy_x, enemy_y - 30,
                          text=f"+{amount} {resource_type.replace('_', ' ').title()}",
                          color=resource.base_color,
                          size=16,
                          duration=1.5)
    
    def draw_gameplay_elements(self):
        """Draw all gameplay elements."""
        # Draw world map with 3D blocks and animated background
        if self.world_generator:
            self.world_generator.draw_map(self.screen)
        else:
            # Fallback if world not initialized yet
            self.screen.fill(BG_COLOR)
        
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
            
            # For large screen-centered text (like wave announcements), don't apply camera offset
            if size >= 60:
                # Center the text on screen with screen shake offset
                text_rect = text_surf.get_rect(center=(x + self.camera_offset_x, y + self.camera_offset_y))
                self.screen.blit(text_surf, text_rect)
            else:
                # Apply camera offset for world-space text
                screen_pos = self.camera_system.world_to_screen(x, y)
                self.screen.blit(text_surf, (screen_pos[0] + self.camera_offset_x, 
                                            screen_pos[1] + self.camera_offset_y))
        
        elif effect_type == 'explosion':
            # Draw explosion effect with screen shake
            radius = int(20 - (effect['timer'] / 3))
            if radius > 0:
                screen_pos = self.camera_system.world_to_screen(x, y)
                pygame.draw.circle(self.screen, YELLOW, 
                                 (int(screen_pos[0] + self.camera_offset_x), 
                                  int(screen_pos[1] + self.camera_offset_y)), 
                                 radius)
    
    # ==================== RESOURCE SHARING ====================
    # Resource sharing feature removed
    
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
        # Use immediate transition here as a safety, but the UI wrapper usually
        # triggers a synchronous transition first for visual feedback.
        self.state_manager.transition_to("gameplay", fade=False)

    def restart_game_sync(self):
        """Synchronous wrapper used by UI callbacks.

        Performs an immediate (no-fade) transition so the player sees the
        gameplay screen right away, then schedules the async reset to run
        on the event loop to finish clearing state.
        """
        print("UI DEBUG: Restart requested - immediate transition to gameplay (sync)")
        # Immediate visual transition
        self.state_manager.transition_to("gameplay", fade=True)

        # Perform synchronous minimal initialization so gameplay appears instantly
        try:
            # Reset basic state first
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
            self.camera_system.reset()

            # Initialize world and player synchronously
            self.initialize_game_world_sync()
        except Exception as e:
            print("UI DEBUG: Synchronous restart failed:", e)

    def request_restart_with_fade(self):
        """Request a restart but use the fade transition.

        Initialize immediately so the world is ready when the fade completes,
        giving instant visual feedback.
        """
        print("UI DEBUG: Play Again clicked - restarting with fade")
        
        # Reset state immediately (during fade-out)
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
        self.camera_system.reset()

        # Initialize world synchronously so it's ready when fade completes
        self.initialize_game_world_sync()
        
        # Now start the fade transition - world is already initialized
        self.state_manager.transition_to("gameplay", fade=True)
    
    def start_game_with_fade(self):
        """Start game from menu with fade transition.
        
        Initialize immediately so the world is ready when fade completes.
        """
        print("UI DEBUG: Start Game clicked - initializing with fade")
        
        # Initialize world synchronously so it's ready when fade completes
        # (Player and world will be created if not already present)
        self.initialize_game_world_sync()
        
        # Now start the fade transition - world is already initialized
        self.state_manager.transition_to("gameplay", fade=True)

    def on_state_enter(self, state, from_state):
        """Called by StateManager when a state is entered (immediately or after fade).
        
        No longer needed for pending restart since we now initialize before the fade.
        Kept for future use if needed.
        """
        pass
    
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
            
            # During fade transitions, render the target state (not the old state)
            # This prevents bouncing back to the previous screen during fade
            if self.state_manager.is_transitioning() and self.state_manager.next_state:
                render_state = self.state_manager.next_state
            else:
                render_state = current_state
            
            if render_state == "menu":
                await self.state_manager.handle_menu_state(events, mouse_pos)
            elif render_state == "gameplay":
                await self.handle_gameplay_state(events, dt)
            elif render_state == "pause":
                await self.state_manager.handle_pause_state(events, mouse_pos)
            elif render_state == "game_over":
                await self.state_manager.handle_game_over_state(events, mouse_pos)
            elif render_state == "leaderboard":
                await self.state_manager.handle_leaderboard_state(events, mouse_pos)
            elif render_state == "settings":
                await self.state_manager.handle_settings_state(events, mouse_pos)
            
            # Draw fade overlay if transitioning
            if self.state_manager.is_transitioning():
                self.state_manager.draw_fade_overlay()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())