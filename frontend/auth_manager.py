# auth_manager.py
"""
Authentication Manager for handling user authentication and server configuration.
"""
import json
import os
from typing import Optional, Dict


class AuthManager:
    """Manages authentication tokens and server configuration."""
    
    def __init__(self, 
                 config_file: str = "client_config.json",
                 server_config_file: str = "server_config.json"):
        self.config_file = config_file
        self.server_config_file = server_config_file
        self.auth_token: Optional[str] = None
        self.username: Optional[str] = None
        self.server_url: str = "http://3.19.244.138:8000"  # Default AWS EC2 IPv4
        
        self.load_configuration()
    
    def load_configuration(self):
        """Load server configuration and authentication credentials."""
        # Load server URL first
        self.load_server_config()
        
        # Then load auth credentials
        self.load_auth_token()
    
    def load_server_config(self):
        """Load server URL from config file or use default."""
        try:
            if os.path.exists(self.server_config_file):
                with open(self.server_config_file, "r") as f:
                    config = json.load(f)
                    self.server_url = config.get("server_url", self.server_url)
                    print(f"Server URL loaded from {self.server_config_file}: {self.server_url}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Could not load server config, using default: {e}")
        
        print(f"Using server: {self.server_url}")
    
    def load_auth_token(self):
        """Load authentication token from client_config.json."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    
                    if config.get("token") and config.get("username"):
                        self.auth_token = config.get("token")
                        self.username = config.get("username")
                        
                        # Override server URL if present in client config
                        if config.get("server_url"):
                            self.server_url = config.get("server_url")
                            print(f"Server URL overridden from client config: {self.server_url}")
                        
                        print(f"Authenticated as: {self.username}")
                    else:
                        print(f"Warning: {self.config_file} exists but missing token or username")
            else:
                print(f"Warning: {self.config_file} not found")
        except Exception as e:
            print(f"Error loading authentication: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.auth_token is not None and self.username is not None
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    def save_credentials(self, username: str, token: str) -> bool:
        """Save authentication credentials to config file."""
        try:
            config = {
                "username": username,
                "token": token,
                "server_url": self.server_url
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            
            self.username = username
            self.auth_token = token
            print(f"Credentials saved for {username}")
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def clear_credentials(self):
        """Clear authentication credentials."""
        self.auth_token = None
        self.username = None
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            print("Credentials cleared")
        except Exception as e:
            print(f"Error clearing credentials: {e}")
    
    def get_server_url(self) -> str:
        """Get the current server URL."""
        return self.server_url
    
    def set_server_url(self, url: str):
        """Set a new server URL."""
        self.server_url = url
        print(f"Server URL updated to: {self.server_url}")