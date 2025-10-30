# leaderboard_manager.py
"""
Leaderboard Manager - Handles data fetching, caching, and UI rendering for leaderboards.
Consolidates leaderboard functionality into a single module.
"""
import pygame
import requests
import json
import time
import os
from typing import List, Dict, Optional
from datetime import datetime


class LeaderboardManager:
    """Manages leaderboard data fetching, caching, and rendering."""
    
    def __init__(self, server_url: str, auth_headers: Dict[str, str] = None):
        self.server_url = server_url
        self.auth_headers = auth_headers or {}
        self.entries: List[Dict] = []
        self.last_update: float = 0
        self.update_interval: float = 60  # Update every 60 seconds
        self.max_entries: int = 10
        self.error_message: Optional[str] = None
        self.loading: bool = False
        self.auth_token: Optional[str] = None
        self.username: Optional[str] = None
        self.current_game_id: Optional[str] = None  # Track current game session
        self.view_mode: str = "global"  # "global" or "game"
        
        # Load authentication from config if available
        self._load_auth_config()
    
    def _load_auth_config(self):
        """Load authentication token from client config."""
        try:
            config_path = "client_config.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    self.auth_token = config_data.get("token")
                    self.username = config_data.get("username")
                    
                    # Update auth headers if token exists
                    if self.auth_token:
                        self.auth_headers["Authorization"] = f"Bearer {self.auth_token}"
                    
                    print(f"Loaded auth for user: {self.username}")
        except Exception as e:
            print(f"Could not load auth config: {e}")
    
    def fetch_leaderboard(self, force: bool = False, game_id: str = None) -> bool:
        """
        Fetch leaderboard data from server.
        
        Args:
            force: Force update even if within update interval
            game_id: Optional game ID to fetch game-specific leaderboard (overrides view mode)
            
        Returns:
            True if fetch was successful, False otherwise
        """
        # Check if we need to update
        current_time = time.time()
        if not force and (current_time - self.last_update < self.update_interval):
            return False
        
        # Rate limiting - minimum 2 seconds between requests
        if not force and (current_time - self.last_update < 2):
            return False
        
        self.loading = True
        self.error_message = None
        
        try:
            # Determine which leaderboard to fetch
            # Priority: explicit game_id parameter > view mode + current_game_id > global
            fetch_game_id = game_id
            if not fetch_game_id and self.view_mode == "game" and self.current_game_id:
                fetch_game_id = self.current_game_id
            
            # Build URL with optional game_id parameter
            url = f"{self.server_url}/leaderboard"
            params = {}
            if fetch_game_id:
                params["game_id"] = fetch_game_id
            
            print(f"DEBUG: Fetching leaderboard from {url}")
            print(f"DEBUG: Params: {params}")
            print(f"DEBUG: Auth headers: {self.auth_headers}")
            
            response = requests.get(
                url,
                params=params,
                headers=self.auth_headers,
                timeout=5
            )
            
            print(f"DEBUG: Leaderboard fetch response: {response.status_code}")
            print(f"DEBUG: Response body: {response.text[:500]}")  # First 500 chars
            
            if response.status_code == 200:
                data = response.json()
                server_entries = data.get("leaderboard", [])
                
                # Convert server data to standardized format
                self.entries = []
                for entry in server_entries:
                    self.entries.append({
                        "name": entry.get("username", "Unknown"),
                        "score": entry.get("score", 0),
                        "time": entry.get("survival_time", entry.get("time", 0)),
                        "wave": entry.get("wave_reached", 0),
                        "last_login": entry.get("last_login", None),
                        "game_id": entry.get("game_id", None)
                    })
                
                # Sort by score (descending)
                self.entries.sort(key=lambda x: x.get("score", 0), reverse=True)
                
                # Keep only top entries
                self.entries = self.entries[:self.max_entries]
                self.last_update = current_time
                
                print(f"Leaderboard updated: {len(self.entries)} entries")
                self.loading = False
                return True
            else:
                self.error_message = f"Failed to fetch leaderboard: {response.status_code}"
                self.loading = False
                return False
                
        except requests.exceptions.Timeout:
            self.error_message = "Leaderboard fetch timed out"
            self.loading = False
            return False
        except Exception as e:
            self.error_message = f"Error fetching leaderboard: {str(e)}"
            self.loading = False
            return False
    
    def get_entries(self) -> List[Dict]:
        """Get current leaderboard entries."""
        return self.entries.copy()
    
    def get_top_n(self, n: int = 10) -> List[Dict]:
        """Get top N entries."""
        return self.entries[:n]
    
    def get_player_rank(self, username: str) -> Optional[int]:
        """
        Get the rank of a specific player.
        
        Returns:
            Player rank (1-indexed) or None if not found
        """
        for i, entry in enumerate(self.entries):
            if entry.get("name") == username:
                return i + 1
        return None
    
    def submit_score(self, username: str, score: int, survival_time: float = 0, wave_reached: int = 0, game_id: str = None) -> bool:
        """
        Submit a score to the server.
        
        Args:
            username: Player username
            score: Player score
            survival_time: How long the player survived
            wave_reached: Highest wave reached
            game_id: Optional game session ID for game-specific leaderboards
            
        Returns:
            True if submission was successful, False otherwise
        """
        if not self.auth_token:
            self.error_message = "You must be logged in to submit scores"
            print("DEBUG: Submit score failed - no auth token")
            return False
        
        try:
            payload = {
                "username": username,
                "score": score,
                "survival_time": survival_time,
                "wave_reached": wave_reached
            }
            
            # Add game_id if provided (for game-specific leaderboards)
            if game_id:
                payload["game_id"] = game_id
            
            print(f"DEBUG: Submitting score to {self.server_url}/leaderboard")
            print(f"DEBUG: Auth headers: {self.auth_headers}")
            print(f"DEBUG: Payload: {payload}")
            
            response = requests.post(
                f"{self.server_url}/leaderboard",
                json=payload,
                headers=self.auth_headers,
                timeout=5
            )
            
            print(f"DEBUG: Submit score response: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
            
            if response.status_code == 200:
                print(f"Score submitted successfully: {score}")
                # Force update after submission
                self.fetch_leaderboard(force=True, game_id=game_id)
                return True
            else:
                self.error_message = f"Failed to submit score: {response.status_code}"
                return False
                
        except Exception as e:
            self.error_message = f"Error submitting score: {str(e)}"
            return False
    
    def clear_cache(self):
        """Clear cached leaderboard data."""
        self.entries = []
        self.last_update = 0
    
    def update_auth_headers(self, headers: Dict[str, str]):
        """Update authentication headers."""
        self.auth_headers = headers
    
    def set_auth(self, token: str, username: str):
        """Set authentication token and username."""
        self.auth_token = token
        self.username = username
        self.auth_headers["Authorization"] = f"Bearer {token}"
    
    def set_update_interval(self, interval: float):
        """Set the update interval in seconds."""
        self.update_interval = interval
    
    def needs_update(self) -> bool:
        """Check if leaderboard needs updating."""
        return (time.time() - self.last_update) >= self.update_interval
    
    def get_error_message(self) -> Optional[str]:
        """Get the current error message if any."""
        return self.error_message
    
    def is_loading(self) -> bool:
        """Check if leaderboard is currently loading."""
        return self.loading
    
    def get_last_update_time(self) -> str:
        """Get formatted last update time."""
        if self.last_update > 0:
            return datetime.fromtimestamp(self.last_update).strftime("%H:%M:%S")
        return "Never"
    
    def set_game_id(self, game_id: Optional[str]):
        """Set the current game ID for game-specific leaderboards."""
        self.current_game_id = game_id
    
    def toggle_view_mode(self):
        """Toggle between global and game-specific leaderboard views."""
        if self.current_game_id:
            self.view_mode = "game" if self.view_mode == "global" else "global"
            self.clear_cache()  # Clear cache to force refresh
            return True
        return False  # Can't toggle if no game_id
    
    def set_view_mode(self, mode: str):
        """Set the leaderboard view mode ('global' or 'game')."""
        if mode in ["global", "game"]:
            self.view_mode = mode
            self.clear_cache()
    
    def get_view_mode(self) -> str:
        """Get the current view mode."""
        return self.view_mode
    
    def can_view_game_leaderboard(self) -> bool:
        """Check if game-specific leaderboard is available."""
        return self.current_game_id is not None


class LeaderboardUI:
    """Handles rendering of leaderboard UI elements."""
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (100, 100, 100)
    DARK_BLUE = (10, 10, 25)
    NEON_BLUE = (0, 195, 255)
    NEON_PINK = (255, 41, 117)
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)
    BRONZE = (205, 127, 50)
    
    def __init__(self, font_manager=None):
        """
        Initialize LeaderboardUI.
        
        Args:
            font_manager: Optional FontManager instance for custom fonts
        """
        self.font_manager = font_manager
    
    def draw_background(self, surface, width, height):
        """Draw cyberpunk-style background with grid and glow effects."""
        # Dark background
        background = pygame.Surface((width, height))
        background.fill(self.DARK_BLUE)
        
        # Grid lines
        for x in range(0, width + 1, 40):
            alpha = min(255, 100 + abs(((x % 120) - 60)))
            color = (0, 70, 100, alpha // 2)
            pygame.draw.line(background, color, (x, 0), (x, height))
            
        for y in range(0, height + 1, 40):
            alpha = min(255, 100 + abs(((y % 120) - 60)))
            color = (0, 70, 100, alpha // 2)
            pygame.draw.line(background, color, (0, y), (width, y))
        
        surface.blit(background, (0, 0))
        
        # Neon glow at top
        glow_surf = pygame.Surface((width, 200), pygame.SRCALPHA)
        for i in range(10):
            alpha = 20 - i * 2
            pygame.draw.rect(glow_surf, (*self.NEON_BLUE, alpha), (0, i * 5, width, 10))
        surface.blit(glow_surf, (0, 0))
    
    def draw_entry(self, surface, entry, index, y_pos, width, is_current_player=False, font=None):
        """Draw a single leaderboard entry."""
        if font is None:
            font = pygame.font.Font(None, 24)
        
        # Row background
        row_bg = pygame.Surface((width - 150, 40))
        if is_current_player:
            row_bg.fill((50, 10, 80))  # Highlight player
        elif index % 2 == 0:
            row_bg.fill((20, 20, 40))
        else:
            row_bg.fill((10, 10, 30))
        row_bg.set_alpha(200)
        surface.blit(row_bg, (75, y_pos))
        
        # Rank with medals for top 3
        rank = index + 1
        if rank <= 3:
            medal_colors = [self.GOLD, self.SILVER, self.BRONZE]
            pygame.draw.circle(surface, medal_colors[index], (100, y_pos + 20), 15)
            rank_text = font.render(str(rank), True, self.BLACK)
        else:
            rank_text = font.render(str(rank), True, self.WHITE)
        
        rank_rect = rank_text.get_rect(center=(100, y_pos + 20))
        surface.blit(rank_text, rank_rect)
        
        # Player name
        name_color = self.NEON_PINK if is_current_player else self.WHITE
        name_text = font.render(entry.get("name", "Unknown"), True, name_color)
        surface.blit(name_text, (160, y_pos + 10))
        
        # Score
        score_text = font.render(f"{entry.get('score', 0):,}", True, self.WHITE)
        surface.blit(score_text, (400, y_pos + 10))
        
        # Last played date
        last_login = entry.get("last_login")
        if last_login:
            try:
                if isinstance(last_login, str):
                    dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    date_str = dt.strftime("%m/%d/%Y")
                else:
                    date_str = "Unknown"
            except:
                date_str = "Unknown"
        else:
            date_str = "Unknown"
        
        small_font = pygame.font.Font(None, 18)
        date_text = small_font.render(date_str, True, self.GRAY)
        surface.blit(date_text, (550, y_pos + 12))
    
    def draw_header(self, surface, width, font=None):
        """Draw leaderboard table headers."""
        if font is None:
            font = pygame.font.Font(None, 24)
        
        headers = ["RANK", "PLAYER", "SCORE", "LAST PLAYED"]
        header_positions = [100, 160, 400, 550]
        
        # Header background
        header_bg = pygame.Surface((width - 150, 40))
        header_bg.fill((0, 30, 60))
        header_bg.set_alpha(200)
        surface.blit(header_bg, (75, 120))
        
        # Header text
        for i, header in enumerate(headers):
            header_text = font.render(header, True, self.NEON_BLUE)
            surface.blit(header_text, (header_positions[i], 130))
        
        # Separator line with glow
        pygame.draw.rect(surface, self.NEON_PINK, (75, 170, width - 150, 3))
        for i in range(5):
            pygame.draw.rect(surface, (*self.NEON_PINK, 50 - i * 10),
                           (75, 170 + i, width - 150, 1))
