# player.py (Enhanced - with methods moved from game.py)
import pygame
import requests
import asyncio
import websockets
import json
from effects import GameEffects

class Player:
    def __init__(self, sprite_sheet, x, y, speed=5):
        """Initialize the player."""
        # Position and movement
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = "down"
        self.width = 48
        self.height = 48
        self.game_ref = None 
        
        # Stats
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.shield = 0
        self.score = 0
        
        # State
        self.attacking = False
        self.is_dashing = False
        self.is_invincible = False
        self.is_moving = False
        
        # Timers
        self.attack_start_time = 0
        self.attack_duration = 300
        self.invincibility_timer = 0
        self.invincibility_duration = 1000
        self.last_projectile_time = 0
        self.projectile_cooldown = 500
        
        # Projectiles
        self.projectiles = []
        self.projectile_speed = 7
        
        # Animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.sprite = None
        
        # Resources (formerly inventory)
        self.resources = {
            "code_fragments": 0,
            "energy_cores": 0,
            "data_shards": 0
        }
        
        # Keep inventory for backward compatibility
        self.inventory = self.resources
        
        self.username = "Player1"
        
        # Server configuration
        try:
            with open("server_config.json", "r") as f:
                config = json.load(f)
                self.server_url = config.get("server_url", "http://3.19.244.138:8000")
        except (FileNotFoundError, json.JSONDecodeError):
            self.server_url = "http://3.19.244.138:8000"
        
        self.ws = None
        self.connected = False
        self.pending_init = True
        
        # Equipment
        self.equipped_weapon = None
        self.equipped_tool = None
        self.crafted_items = []
        
        # Crafting recipes
        self.crafting_recipes = {
            "energy_sword": {
                "code_fragments": 5,
                "energy_cores": 3,
                "data_shards": 1,
                "stats": {"damage": 20, "speed": 1.5}
            },
            "data_shield": {
                "code_fragments": 3,
                "energy_cores": 2,
                "data_shards": 3,
                "stats": {"defense": 15, "duration": 10}
            },
            "hack_tool": {
                "code_fragments": 4,
                "energy_cores": 4,
                "data_shards": 2,
                "stats": {"range": 100, "cooldown": 5}
            }
        }
        
        # Load animations
        if sprite_sheet.get_width() == self.sprite_width and sprite_sheet.get_height() == self.sprite_height:
            self.is_single_sprite = True
            self.sprite = sprite_sheet
            self.walk_right = [sprite_sheet] * 4
            self.walk_left = [sprite_sheet] * 4
            self.walk_up = [sprite_sheet] * 4
            self.walk_down = [sprite_sheet] * 4
            self.crafting = [sprite_sheet] * 4
            self.attack = [sprite_sheet] * 4
            self.idle = sprite_sheet
        else:
            self.is_single_sprite = False
            self.load_animations(sprite_sheet)
        
        # Effects
        self.effects = GameEffects()
        
        # Active effects
        self.active_effects = {}
        
        # Callbacks for game integration
        self.sound_callback = None
        self.effect_callback = None
        self.screen_shake_callback = None

    # ==================== CALLBACKS ====================
    
    def set_callbacks(self, sound_callback=None, effect_callback=None, screen_shake_callback=None):
        """Set callback functions for game integration."""
        self.sound_callback = sound_callback
        self.effect_callback = effect_callback
        self.screen_shake_callback = screen_shake_callback
    
    def play_sound(self, sound_name):
        """Play sound through callback."""
        if self.sound_callback:
            self.sound_callback(sound_name)
    
    def add_effect(self, effect_type, x, y, **kwargs):
        """Add visual effect through callback."""
        if self.effect_callback:
            self.effect_callback(effect_type, x, y, **kwargs)
    
    def trigger_screen_shake(self, amount, duration):
        """Trigger screen shake through callback."""
        if self.screen_shake_callback:
            self.screen_shake_callback(amount, duration)

    # ==================== UPDATE METHOD ====================
    
    async def update(self, dt, keys, enemies, world_generator=None):
        """Main update method - handles all player state updates."""
        # Update energy regeneration
        self.update_energy(dt)
        
        # Handle movement
        moving = await self.move(keys, world_generator)
        self.is_moving = moving
        
        # Handle tool usage with E key (if equipped)
        if keys[pygame.K_e] and self.equipped_tool:
            await self.use_equipped_tool()
        
        # Update animation
        if asyncio.iscoroutinefunction(self.animate):
            self.sprite = await self.animate(moving, keys, enemies)
        else:
            self.sprite = self.animate(moving, keys, enemies)
        
        # Update projectiles
        await self.update_projectiles(enemies)
        
        return moving
    
    async def use_equipped_tool(self):
        """Use the currently equipped tool with visual/audio feedback."""
        if not self.equipped_tool:
            self.add_effect("text", self.x, self.y - 30,
                           text="No tool equipped!",
                           color=(255, 0, 0), size=20, duration=2.0)
            return False
        
        # Call the actual tool use logic
        result = await self.use_tool()
        
        if result:
            # Play sound
            self.play_sound("level_up")
            
            # Add visual effects based on tool type
            tool_name = self.equipped_tool["name"]
            
            if tool_name == "data_shield":
                self.add_effect("text", self.x, self.y - 30,
                               text="Shield activated!",
                               color=(0, 255, 255), size=20, duration=1.0)
            elif tool_name == "hack_tool":
                self.add_effect("text", self.x, self.y - 30,
                               text="Hack activated!",
                               color=(0, 255, 0), size=20, duration=1.0)
                self.trigger_screen_shake(5, 0.5)
            elif tool_name == "energy_sword":
                self.add_effect("text", self.x, self.y - 30,
                               text="Energy blade activated!",
                               color=(0, 195, 255), size=20, duration=1.0)
                self.add_effect("explosion", self.x, self.y)
            else:
                self.add_effect("text", self.x, self.y - 30,
                               text="Tool activated!",
                               color=(255, 255, 255), size=20, duration=1.0)
        
        return result

    # ==================== DRAWING METHODS (MOVED FROM GAME.PY) ====================
    
    def draw(self, surface, camera_system):
        """Draw the player on the surface with camera offset."""
        if not self.sprite:
            return
        
        # Get screen position from camera system
        screen_x, screen_y = camera_system.world_to_screen(self.x, self.y)
        
        # Draw the sprite
        surface.blit(self.sprite, (screen_x, screen_y))
        
        # Draw health bar above player
        self.draw_health_bar(surface, screen_x, screen_y)
        
        # Draw shield indicator if active
        if self.shield > 0:
            self.draw_shield_indicator(surface, screen_x, screen_y)
        
        # Flash effect when invincible
        if self.is_invincible:
            current_time = pygame.time.get_ticks()
            if (current_time // 100) % 2 == 0:  # Flash every 100ms
                # Draw semi-transparent white overlay
                overlay = pygame.Surface((self.width, self.height))
                overlay.set_alpha(128)
                overlay.fill((255, 255, 255))
                surface.blit(overlay, (screen_x, screen_y))
    
    def draw_health_bar(self, surface, screen_x, screen_y):
        """Draw health bar above player."""
        bar_width = 40
        bar_height = 4
        bar_x = screen_x + (self.width - bar_width) // 2
        bar_y = screen_y - 10
        
        # Background (red)
        pygame.draw.rect(surface, (255, 0, 0), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Foreground (green) based on health percentage
        health_percentage = self.health / self.max_health
        health_width = int(bar_width * health_percentage)
        pygame.draw.rect(surface, (0, 255, 0), 
                        (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pygame.draw.rect(surface, (255, 255, 255), 
                        (bar_x, bar_y, bar_width, bar_height), 1)
    
    def draw_shield_indicator(self, surface, screen_x, screen_y):
        """Draw shield indicator around player."""
        # Draw a blue circle around the player
        center_x = screen_x + self.width // 2
        center_y = screen_y + self.height // 2
        radius = self.width // 2 + 5
        
        # Pulsing effect
        current_time = pygame.time.get_ticks()
        pulse = abs((current_time % 1000) - 500) / 500.0  # 0 to 1 to 0
        alpha = int(100 + 100 * pulse)
        
        # Create shield surface
        shield_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(shield_surf, (0, 191, 255, alpha), 
                          (radius + 5, radius + 5), radius, 3)
        surface.blit(shield_surf, (center_x - radius - 5, center_y - radius - 5))
    
    def draw_projectiles(self, surface, camera_system):
        """Draw all player projectiles."""
        for projectile in self.projectiles:
            screen_x, screen_y = camera_system.world_to_screen(
                projectile["x"], 
                projectile["y"]
            )
            
            # Draw projectile as a glowing circle
            color = (0, 255, 255)  # Cyan
            pygame.draw.circle(surface, color, 
                             (int(screen_x), int(screen_y)), 
                             projectile.get("width", 5))
            
            # Draw glow effect
            glow_color = (0, 191, 255, 100)
            glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, glow_color, (10, 10), 10)
            surface.blit(glow_surf, (screen_x - 10, screen_y - 10))

    # ==================== RESOURCE COLLECTION (MOVED FROM GAME.PY) ====================
    
    def collect_resource(self, resource_type, amount=1):
        """Collect a resource and add to inventory."""
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            self.effects.play_hit_sound()  # Play collection sound
            return True
        return False
    
    async def collect_energy_core(self, amount):
        """Handle energy core collection with energy restoration."""
        base_energy_restore = 20
        bonus_energy = amount * 5
        
        # Add to resources
        self.collect_resource("energy_cores", amount)
        
        # Restore energy
        self.energy = min(self.max_energy, self.energy + base_energy_restore + bonus_energy)
        
        # Send update to server
        await self.send_update()
    
    def add_score(self, points):
        """Add points to player score."""
        self.score += points

    # ==================== COLLISION DETECTION (MOVED FROM GAME.PY) ====================
    
    def get_rect(self):
        """Get player's collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def collides_with(self, other_rect):
        """Check collision with another rectangle."""
        return self.get_rect().colliderect(other_rect)
    
    def collides_with_point(self, x, y):
        """Check if a point collides with the player."""
        return self.get_rect().collidepoint(x, y)
    
    def check_resource_collision(self, resources):
        """Check collision with resources and collect them."""
        player_rect = self.get_rect()
        collected = []
        
        for resource in resources:
            if hasattr(resource, 'get_rect'):
                resource_rect = resource.get_rect()
                if player_rect.colliderect(resource_rect):
                    # Collect the resource
                    resource_type = resource.type if hasattr(resource, 'type') else "code_fragments"
                    amount = resource.amount if hasattr(resource, 'amount') else 1
                    self.collect_resource(resource_type, amount)
                    collected.append(resource)
        
        return collected
    
    def check_powerup_collision(self, powerups):
        """Check collision with power-ups and collect them."""
        player_rect = self.get_rect()
        collected = []
        
        for powerup in powerups:
            if hasattr(powerup, 'get_rect'):
                powerup_rect = powerup.get_rect()
                if player_rect.colliderect(powerup_rect):
                    # Apply power-up effect
                    self.apply_powerup(powerup)
                    collected.append(powerup)
        
        return collected
    
    def apply_powerup(self, powerup):
        """Apply power-up effect to player."""
        if hasattr(powerup, 'effect_type'):
            if powerup.effect_type == "health":
                self.health = min(self.max_health, self.health + 25)
            elif powerup.effect_type == "energy":
                self.energy = min(self.max_energy, self.energy + 50)
            elif powerup.effect_type == "shield":
                self.shield = min(100, self.shield + 30)
            elif powerup.effect_type == "speed":
                # Temporary speed boost
                self.active_effects["speed_boost"] = {
                    "duration": 5000,  # 5 seconds
                    "start_time": pygame.time.get_ticks()
                }

    # ==================== EXISTING METHODS (KEEP AS IS) ====================
    
    def set_game_reference(self, game):
        """Set a reference to the game instance"""
        self.game_ref = game

    async def register_user(self, username, password):
        """Register a new user with the backend"""
        try:
            url = f"{self.server_url}/register/user"
            data = {"username": username, "password": password}
            response = requests.post(url, json=data)
        
            if response.status_code == 200:
                print(f"Successfully registered user: {username}")
                self.username = username
                return response.json()
            else:
                print(f"Failed to register user. Status code: {response.status_code}")
                print(response.text)
            return None
        except Exception as e:
            print(f"Error registering user: {e}")
        return None

    async def login(self, username, password):
        """Login and get authentication token"""
        try:
            url = f"{self.server_url}/token"
            data = {"username": username, "password": password}
            response = requests.post(url, data=data)
        
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.username = username
                print(f"Successfully logged in as: {username}")
                return token_data
            else:
                print(f"Failed to login. Status code: {response.status_code}")
                print(response.text)
            return None
        except Exception as e:
            print(f"Error logging in: {e}")
        return None

    async def connect_to_server_with_auth(self):
        """Opens WebSocket connection with authentication token"""
        try:
            if not hasattr(self, 'auth_token'):
                print("Not authenticated, connecting without token")
                self.ws = await websockets.connect(f"ws://localhost:8000/ws/{self.username}")
            else:
                self.ws = await websockets.connect(
                    f"ws://localhost:8000/ws/{self.username}?token={self.auth_token}"
                )
            
            self.connected = True
            print(f"Connected to WebSocket as {self.username}")
            
            if self.ws:
                try:
                    request_data = {"action": "get_all_players"}
                    await self.ws.send(json.dumps(request_data))
                except Exception as e:
                    print(f"Failed to request player list: {e}")
        
            self.listener_task = asyncio.create_task(self.listen_for_server_messages())
            self.refresh_task = asyncio.create_task(self.periodic_refresh())
            
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to WebSocket: {e}")
            
    async def periodic_refresh(self):
        """Periodically requests all players from the server"""
        refresh_interval = 10
        
        try:
            while self.connected and self.ws:
                await asyncio.sleep(refresh_interval)
                
                if self.ws:
                    try:
                        request_data = {"action": "get_all_players"}
                        await self.ws.send(json.dumps(request_data))
                    except Exception as e:
                        print(f"Failed to request player list during refresh: {e}")
                        if not self.connected:
                            break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in periodic refresh: {e}")
            if self.connected:
                self.connected = False

    async def end_game_session(self, session_id, score, enemies_defeated, waves_completed):
        """End the current game session with stats"""
        if not hasattr(self, 'auth_token'):
            print("Not authenticated, cannot end game session")
            return None    
        try:
            url = f"{self.server_url}/game-sessions/{session_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            data = {
                "score": score,
                "enemies_defeated": enemies_defeated,
                "waves_completed": waves_completed
            }
            response = requests.put(url, json=data, headers=headers)
        
            if response.status_code == 200:
                print("Successfully ended game session")
                return response.json()
            else:
                print(f"Failed to end game session. Status code: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Error ending game session: {e}")
        return None

    async def initialize_server_connection(self, username=None, password=None):
        """Initialize all server connections with optional authentication"""
        try:
            if username and password:
                login_result = await self.login(username, password)
                if not login_result:
                    register_result = await self.register_user(username, password)
                    if register_result:
                        login_result = await self.login(username, password)
        
            await self.connect_to_server_with_auth()
            await self.send_update()
            self.pending_init = False
        except Exception as e:
            print(f"Failed to initialize server connection: {e}")

    def register_player(self):
        """Registers player with the FastAPI backend"""
        try:
            url = f"{self.server_url}/register/"
            data = {
                "username": self.username,
                "health": self.health,
                "x": self.x,
                "y": self.y
            }
            response = requests.post(url, params=data)
            if response.status_code == 200:
                print(f"Successfully registered player: {self.username}")
                print(response.json())
            else:
                print(f"Failed to register player. Status code: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error registering player: {e}")
            return None
        return response.json()

    async def connect_to_server(self):
        """Opens WebSocket connection for real-time interactions"""
        try:
            self.ws = await websockets.connect(f"ws://localhost:8000/ws/{self.username}")
            self.connected = True
            print(f"Connected to WebSocket as {self.username}")
            
            self.listener_task = asyncio.create_task(self.listen_for_server_messages())
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to WebSocket: {e}")

    async def disconnect(self):
        """Gracefully disconnect from the server and clean up tasks"""
        self.connected = False
        
        if hasattr(self, 'refresh_task') and self.refresh_task:
            try:
                self.refresh_task.cancel()
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error cancelling refresh task: {e}")
                
        if hasattr(self, 'ws') and self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                print(f"Error closing websocket: {e}")
                
        print("Disconnected from server")

    async def listen_for_server_messages(self):
        """Listen for incoming messages from the server"""
        if not self.connected or not self.ws:
            print("WebSocket not connected, cannot listen for messages")
            return
            
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                print(f"Received from server: {data}")
                
                if "event" in data:
                    await self.handle_server_event(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            await self.disconnect()
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
            await self.disconnect()

    async def handle_server_event(self, data):
        """Handle different types of server events"""
        event_type = data.get("event")
    
        if event_type == "player_joined":
            joined_username = data.get('username')
            print(f"Player joined: {joined_username}")
            if joined_username != self.username:
                if hasattr(self, "game_ref") and self.game_ref:
                    self.game_ref.other_players[joined_username] = {
                        "x": 0,
                        "y": 0,
                        "direction": "down",
                        "last_update": pygame.time.get_ticks(),
                        "sprite": self.idle
                    }
                if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                    if self.game_ref and hasattr(self.game_ref, "chat_system"):
                        self.game_ref.chat_system.add_message("", f"{joined_username} joined the game", system_message=True)
    
        elif event_type == "player_left":
            left_username = data.get("username", "Unknown")
            print(f"Player left: {left_username}")
            if hasattr(self, "game_ref") and self.game_ref and left_username in self.game_ref.other_players:
                del self.game_ref.other_players[left_username]
            if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                if self.game_ref and hasattr(self.game_ref, "chat_system") and self.game_ref.chat_system:
                    self.game_ref.chat_system.add_message("", f"{left_username} left the game", system_message=True)
    
        elif event_type == "item_drop":
            print(f"Item dropped at x:{data.get('x')}, y:{data.get('y')}")
    
        elif event_type == "server_message":
            print(f"Server message: {data.get('message')}")
    
        elif event_type == "update":
            print(f"{data['player']['username']} moved to {data['player']['position']}")
    
        elif event_type == "chat_message":
            sender = data.get("username", "Unknown")
            message = data.get("message", "")
            if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                if self.game_ref and hasattr(self.game_ref, "chat_system") and self.game_ref.chat_system:
                    self.game_ref.chat_system.add_message(sender, message)
            print(f"Chat: {sender}: {message}")

        elif event_type == "player_moved":
            username = data.get("username")
            position = data.get("position")
            direction = data.get("direction", "down")
            
            if username != self.username and position:
                if hasattr(self, "game_ref") and self.game_ref:
                    if not hasattr(self.game_ref, "other_players"):
                        self.game_ref.other_players = {}
                        
                    if username not in self.game_ref.other_players:
                        self.game_ref.other_players[username] = {
                            "x": position["x"],
                            "y": position["y"],
                            "direction": direction,
                            "last_update": pygame.time.get_ticks(),
                            "sprite": self.idle
                        }
                    else:
                        self.game_ref.other_players[username]["x"] = position["x"]
                        self.game_ref.other_players[username]["y"] = position["y"]
                        self.game_ref.other_players[username]["direction"] = direction
                        self.game_ref.other_players[username]["last_update"] = pygame.time.get_ticks()
                        self.game_ref.other_players[username]["prev_x"] = position["x"]
                        self.game_ref.other_players[username]["prev_y"] = position["y"]

        elif event_type == "all_players":
            players_list = data.get("players", [])
            print(f"Received list of {len(players_list)} players from server")
            
            if hasattr(self, "game_ref") and self.game_ref:
                if not hasattr(self.game_ref, "other_players"):
                    self.game_ref.other_players = {}
                
                for player_data in players_list:
                    player_username = player_data.get("username")
                    
                    if player_username == self.username:
                        continue
                        
                    if player_username not in self.game_ref.other_players:
                        self.game_ref.other_players[player_username] = {
                            "x": player_data.get("x", 0),
                            "y": player_data.get("y", 0),
                            "direction": "down",
                            "last_update": pygame.time.get_ticks(),
                            "sprite": self.idle
                        }
                    else:
                        self.game_ref.other_players[player_username]["x"] = player_data.get("x", 0)
                        self.game_ref.other_players[player_username]["y"] = player_data.get("y", 0)
                        self.game_ref.other_players[player_username]["last_update"] = pygame.time.get_ticks()

    async def send_update(self):
        """Sends updated player data to the server"""
        if self.ws:
            update_data = {
                "action": "update_position",
                "x": self.x,
                "y": self.y,
                "health": self.health,
                "inventory": self.resources,  # Use resources instead of inventory
                "direction": self.direction
            }
            await self.ws.send(json.dumps(update_data))

    def load_animations(self, sheet):
        """Load all animation frames from sprite sheet."""
        try:
            if sheet.get_width() >= self.sprite_width * 4 and sheet.get_height() >= self.sprite_height * 6:
                self.walk_right = [self.get_frame(sheet, i, 0) for i in range(4)]
                self.walk_left = [self.get_frame(sheet, i, 1) for i in range(4)]
                self.walk_up = [self.get_frame(sheet, i, 2) for i in range(4)]
                self.walk_down = [self.get_frame(sheet, i, 3) for i in range(4)]
                self.crafting = [self.get_frame(sheet, i, 4) for i in range(4)]
                self.attack = [self.get_frame(sheet, i, 5) for i in range(4)]
                self.idle = self.walk_down[0]
            else:
                print("Warning: Sprite sheet too small, using as single sprite")
                self.walk_right = [sheet] * 4
                self.walk_left = [sheet] * 4
                self.walk_up = [sheet] * 4
                self.walk_down = [sheet] * 4
                self.crafting = [sheet] * 4
                self.attack = [sheet] * 4
                self.idle = sheet
        except Exception as e:
            print(f"Error loading animations: {e}")
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255))
            self.walk_right = [fallback] * 4
            self.walk_left = [fallback] * 4
            self.walk_up = [fallback] * 4
            self.walk_down = [fallback] * 4
            self.crafting = [fallback] * 4
            self.attack = [fallback] * 4
            self.idle = fallback
            
        self.sprite = self.idle

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from sprite sheet."""
        return sheet.subsurface(pygame.Rect(
            frame * self.sprite_width,
            row * self.sprite_height,
            self.sprite_width,
            self.sprite_height
        ))

    async def move(self, keys, world_generator):
        """Handle player movement based on key input."""
        moving = False
        original_x = self.x
        original_y = self.y
        
        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.direction = "up"
            moving = True
            
        if keys[pygame.K_DOWN]:
            self.y += self.speed
            self.direction = "down"
            moving = True
            
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = "left"
            moving = True
            
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = "right"
            moving = True
        
        if moving and world_generator:
            player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
            if not world_generator.is_valid_position(self.x, self.y):
                self.x = original_x
                self.y = original_y
                moving = False
                return moving
            
            for obj in world_generator.objects:
                if obj.collides_with(player_rect):
                    self.x = original_x
                    self.y = original_y
                    moving = False
                    return moving
        
        if moving:
            await self.send_update()
            
        return moving

    async def animate(self, moving, keys, enemies):
        """Update player animation and handle actions."""
        current_time = pygame.time.get_ticks()
        action_taken = False
        
        if self.is_invincible and current_time - self.invincibility_timer >= self.invincibility_duration:
            self.is_invincible = False
        
        if keys[pygame.K_SPACE]:
            self.attacking = True
            action_taken = True
            self.attack_start_time = current_time
            self.effects.play_attack_sound()
            self.damage = self.use_equipped_item()
        
        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            await self.fire_projectile()
            self.last_projectile_time = current_time
            action_taken = True
            
        if keys[pygame.K_e] and self.equipped_tool:
            await self.use_tool()
            action_taken = True
        
        if self.attacking:
            self.frame_index = (current_time // 100) % 3
            if self.direction in ["right", "left"]:
                self.sprite = self.attack[self.frame_index]
            else:
                self.sprite = self.idle
            
            if current_time - self.attack_start_time > self.attack_duration:
                self.attacking = False
                self.damage = 10
                
        elif moving:
             # Walking animation
            self.frame_index = (current_time // 150) % 4
            
            if self.direction == "right":
                self.sprite = self.walk_right[self.frame_index]
            elif self.direction == "left":
                self.sprite = self.walk_left[self.frame_index]
            elif self.direction == "up":
                self.sprite = self.walk_up[self.frame_index]
            elif self.direction == "down":
                self.sprite = self.walk_down[self.frame_index]
        else:
            # Idle animation - use direction-appropriate first frame
            if self.direction == "right":
                self.sprite = self.walk_right[0]
            elif self.direction == "left":
                self.sprite = self.walk_left[0]
            elif self.direction == "up":
                self.sprite = self.walk_up[0]
            else:  # down or default
                self.sprite = self.walk_down[0]
        
        # Update projectiles
        await self.update_projectiles(enemies)

        # Send state update if any action was taken
        if action_taken:
            await self.send_update()
        
        return self.sprite
    
       
    async def fire_projectile(self):
        """Create a new projectile in the current direction."""
        projectile_cost = 10.0  # Energy cost for firing projectile
        
        # Check if player has enough energy
        if self.energy < projectile_cost:
            return False
        
        # Consume energy
        self.energy = max(0, self.energy - projectile_cost)
        
        # Calculate spawn position (center of player)
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Create projectile
        self.projectiles.append({
            "x": center_x,
            "y": center_y,
            "dir": self.direction,
            "width": 5,
            "height": 5
        })
        
        # Play sound
        self.effects.play_hit_sound()

        # Send update to server
        await self.send_update()

        return True  # Indicate projectile was fired    

    async def update_projectiles(self, enemies):
        """Update projectile positions and check for collisions."""
        # Get screen dimensions
        screen = pygame.display.get_surface()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Update each projectile
        projectile_hit = False  # Initialize projectile_hit
        for projectile in self.projectiles[:]:
            # Move projectile
            if projectile["dir"] == "right":
                projectile["x"] += self.projectile_speed
            elif projectile["dir"] == "left":
                projectile["x"] -= self.projectile_speed
            elif projectile["dir"] == "up":
                projectile["y"] -= self.projectile_speed
            elif projectile["dir"] == "down":
                projectile["y"] += self.projectile_speed
            
            # Check if out of bounds
            if (projectile["x"] < 0 or
                projectile["x"] > screen_width or
                projectile["y"] < 0 or
                projectile["y"] > screen_height):
                # Remove projectile
                self.projectiles.remove(projectile)
                continue
            
            # Check collisions with enemies
            for enemy in enemies[:]:
                if enemy.collides_with(projectile):
                    # Remove projectile
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    projectile_hit = True  # Set projectile_hit to True
                    break
        
        # If a projectile hit something, we'll update the server
        if projectile_hit:
            await self.send_update()

    async def decrease_health(self, amount):
        """Decrease player health if not invincible."""
        if not self.is_invincible:
            # Apply shield if available
            if self.shield > 0:
                # Absorb damage with shield
                absorbed = min(self.shield, amount)
                self.shield -= absorbed
                amount -= absorbed
            
            # Apply remaining damage to health
            if amount > 0:
                self.health = max(0, self.health - amount)
                
                # Become invincible briefly
                self.is_invincible = True
                self.invincibility_timer = pygame.time.get_ticks()

                # Check if player died
                if self.health <= 0 and self.game_ref:
                    self.game_ref.handle_player_defeat()
                
                # Notify server of damage taken
                if self.connected and self.ws:
                    try:
                        damage_data = {
                            "action": "damage_taken",
                            "amount": amount,
                            "health": self.health
                        }
                        await self.ws.send(json.dumps(damage_data))
                    except Exception as e:
                        print(f"Failed to send damage data: {e}")
                        self.connected = False
                
                # Send general update
                await self.send_update()
                
                return True  # Damage was dealt
                
        return False  # No damage was dealt

    def can_craft(self, item_name):
        """Check if player has enough resources to craft an item."""
        if item_name not in self.crafting_recipes:
            return False
            
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats" and self.inventory.get(resource, 0) < amount:
                return False
        return True
    
    async def craft_item(self, item_name):
        """Attempt to craft an item using resources."""
        print(f"DEBUG: Player.craft_item called for {item_name}")
        
        if item_name not in self.crafting_recipes:
            print(f"DEBUG: Recipe {item_name} not found in recipes: {self.crafting_recipes.keys()}")
            return False
            
        if not self.can_craft(item_name):
            print(f"DEBUG: Cannot craft {item_name}, insufficient resources")
            for resource, amount in self.crafting_recipes[item_name].items():
                if resource != "stats":
                    has_amount = self.inventory.get(resource, 0)
                    print(f"DEBUG:   {resource}: have {has_amount}, need {amount}")
            return False
            
        # Deduct resources
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats":
                self.inventory[resource] -= amount
        
        # Create the crafted item
        crafted_item = {
            "name": item_name,
            "stats": recipe["stats"].copy(),
            "durability": 100
        }
        
        # Add to crafted items
        self.crafted_items.append(crafted_item)
        print(f"DEBUG: Added {item_name} to crafted_items: {self.crafted_items}")
        
        # Auto-equip the newly crafted item - always equip as tool regardless of type
        # This allows all items to be used with the E key
        self.equipped_tool = crafted_item
        print(f"DEBUG: Auto-equipped {item_name} as tool")

        await self.send_update()
        return True

    async def equip_item(self, item_index):
        """Equip a crafted item."""
        if 0 <= item_index < len(self.crafted_items):
            item = self.crafted_items[item_index]
            if item["name"].endswith(("sword", "blade")):
                self.equipped_weapon = item
            else:
                self.equipped_tool = item
             # Notify server of equipment change
            if self.connected and self.ws:
                try:
                    equip_data = {
                        "action": "equip_item",
                        "item_name": item["name"],
                        "item_type": "weapon" if item["name"].endswith(("sword", "blade")) else "tool"
                    }
                    await self.ws.send(json.dumps(equip_data))
                except Exception as e:
                    print(f"Failed to send equip data: {e}")
                    self.connected = False
            
            await self.send_update()
                
    def use_equipped_item(self):
        """Use the currently equipped item."""
        if self.equipped_weapon:
            # Apply weapon effects (e.g., increased damage)
            base_damage = 10
            weapon_damage = self.equipped_weapon["stats"].get("damage", 0)
            total_damage = base_damage + weapon_damage
            
            # Decrease durability
            self.equipped_weapon["durability"] -= 1
            if self.equipped_weapon["durability"] <= 0:
                self.crafted_items.remove(self.equipped_weapon)
                self.equipped_weapon = None
                
            return total_damage
            
        return 10  # Base damage if no weapon equipped

    async def use_tool(self):
        """Use the currently equipped tool."""
        print(f"DEBUG: Player.use_tool called")
        
        if not self.equipped_tool:
            print("DEBUG: No tool equipped")
            return False
        
        # Define energy costs for tools
        tool_costs = {
            "energy_sword": 20,
            "data_shield": 25,
            "hack_tool": 15
        }
        
        # Get energy cost for current tool
        energy_cost = tool_costs.get(self.equipped_tool["name"], 10)
        
        # Check if player has enough energy
        if self.energy < energy_cost:
            print("DEBUG: Not enough energy to use tool")
            return False
        
        # Consume energy
        self.energy = max(0, self.energy - energy_cost)
        
        print(f"DEBUG: Using tool: {self.equipped_tool['name']}")
            
        # Apply tool effects based on type
        if self.equipped_tool["name"] == "data_shield":
            # Apply shield effect
            shield_amount = self.equipped_tool["stats"]["defense"]
            duration = self.equipped_tool["stats"]["duration"]
            self.shield = min(100, self.shield + shield_amount)
            print(f"DEBUG: Applied data_shield, shield now at {self.shield}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "hack_tool":
            # Apply hack effect (e.g., temporarily disable nearby enemies)
            hack_range = self.equipped_tool["stats"]["range"]
            cooldown = self.equipped_tool["stats"]["cooldown"]
            
            # Temporary effect - increases energy
            self.energy = min(self.max_energy, self.energy + 20)
            print(f"DEBUG: Used hack_tool with range {hack_range}, energy now at {self.energy}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "energy_sword":
            # Apply damage boost effect
            damage_boost = self.equipped_tool["stats"]["damage"]
            speed_boost = self.equipped_tool["stats"]["speed"]
            
            # Temporary effect - provides temporary invincibility
            self.is_invincible = True
            self.invincibility_timer = pygame.time.get_ticks()
            self.invincibility_duration = 2000  # 2 seconds of invincibility
            
            print(f"DEBUG: Used energy_sword with damage {damage_boost}, invincibility activated")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
            
        # Notify server of tool use
        if self.connected and self.ws:
            try:
                tool_data = {
                    "action": "use_tool",
                    "tool_name": self.equipped_tool["name"] if self.equipped_tool else "none",
                    "energy": self.energy,
                    "shield": self.shield
                }
                await self.ws.send(json.dumps(tool_data))
            except Exception as e:
                print(f"Failed to send tool use data: {e}")
                self.connected = False
        
        # Send general update
        await self.send_update()
        
        return True  # Indicate tool was used

    def update_energy(self, dt):
        """Update player energy regeneration."""
        # Base regeneration rate (energy per second)
        base_regen_rate = 2.0
        
        # Modify regeneration based on conditions
        if hasattr(self, 'is_moving') and self.is_moving:
            regen_rate = base_regen_rate * 0.5  # Reduced regeneration while moving
        elif self.attacking:
            regen_rate = base_regen_rate * 0.25  # Greatly reduced while attacking
        else:
            regen_rate = base_regen_rate  # Full regeneration while idle
        
        # Apply regeneration
        self.energy = min(self.max_energy, self.energy + regen_rate * dt)

    async def collect_energy_core(self, amount):
        """Handle energy core collection."""
        base_energy_restore = 20
        bonus_energy = amount * 5  # Scale with core value
        
        self.energy = min(self.max_energy, self.energy + base_energy_restore + bonus_energy)

        # Send update to server
        await self.send_update()