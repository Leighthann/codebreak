#!/usr/bin/env python3
"""
CodeBreak Game Testing Suite
Tests all game components before deployment
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path

# ANSI colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(60)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}→ {text}{RESET}")

class GameTester:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.frontend_dir = self.project_root / "frontend"
        self.backend_dir = self.project_root / "backend"
        self.tests_passed = 0
        self.tests_failed = 0
        self.server_url = "http://3.19.244.138:8000"
        
    def test_directory_structure(self):
        """Test if all required directories exist"""
        print_header("Testing Directory Structure")
        
        required_dirs = [
            self.frontend_dir,
            self.frontend_dir / "fonts",
            self.frontend_dir / "spritesheets",
            self.frontend_dir / "sound_effects",
        ]
        
        for directory in required_dirs:
            if directory.exists():
                print_success(f"Found: {directory.relative_to(self.project_root)}")
                self.tests_passed += 1
            else:
                print_error(f"Missing: {directory.relative_to(self.project_root)}")
                self.tests_failed += 1
    
    def test_python_version(self):
        """Test if Python version is compatible"""
        print_header("Testing Python Version")
        
        version = sys.version_info
        print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
        
        if version.major == 3 and version.minor >= 8:
            print_success("Python version is compatible (3.8+)")
            self.tests_passed += 1
        else:
            print_error("Python 3.8 or higher is required")
            self.tests_failed += 1
    
    def test_dependencies(self):
        """Test if all required packages are installed"""
        print_header("Testing Dependencies")
        
        required_packages = {
            'pygame': 'pygame',
            'websockets': 'websockets',
            'requests': 'requests',
            'dotenv': 'python-dotenv',
            'pyperclip': 'pyperclip'
        }
        
        for import_name, package_name in required_packages.items():
            if importlib.util.find_spec(import_name):
                print_success(f"{package_name} is installed")
                self.tests_passed += 1
            else:
                print_error(f"{package_name} is NOT installed")
                print_info(f"   Install with: pip install {package_name}")
                self.tests_failed += 1
    
    def test_game_files(self):
        """Test if all required game files exist"""
        print_header("Testing Game Files")
        
        required_files = [
            "unified_game_launcher.py",
            "main.py",
            "game.py",
            "player.py",
            "enemy.py",
            "world.py",
            "ui_system.py",
            "auth_manager.py",
            "leaderboard_manager.py",
            "requirements.txt",
            "install_dependencies.py",
            "start_game.bat"
        ]
        
        for filename in required_files:
            filepath = self.frontend_dir / filename
            if filepath.exists():
                print_success(f"Found: {filename}")
                self.tests_passed += 1
            else:
                print_error(f"Missing: {filename}")
                self.tests_failed += 1
    
    def test_config_files(self):
        """Test configuration files"""
        print_header("Testing Configuration")
        
        config_file = self.frontend_dir / "client_config.json"
        server_config = self.frontend_dir / "server_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                required_keys = ['server_url', 'token', 'username']
                missing_keys = [key for key in required_keys if key not in config]
                
                if missing_keys:
                    print_warning(f"client_config.json missing keys: {', '.join(missing_keys)}")
                    print_info("   You may need to login first")
                else:
                    print_success("client_config.json is valid")
                    self.tests_passed += 1
                    
            except json.JSONDecodeError:
                print_error("client_config.json is not valid JSON")
                self.tests_failed += 1
        else:
            print_warning("client_config.json not found (will be created on first login)")
            print_info(f"   Login at: {self.server_url}/login")
        
        if server_config.exists():
            print_success("server_config.json found")
            self.tests_passed += 1
        else:
            print_warning("server_config.json not found (optional)")
    
    def test_server_connection(self):
        """Test if server is accessible"""
        print_header("Testing Server Connection")
        
        try:
            import requests
            print_info(f"Connecting to {self.server_url}...")
            
            response = requests.get(self.server_url, timeout=5)
            
            if response.status_code == 200:
                print_success(f"Server is online and responding")
                self.tests_passed += 1
                
                # Test specific endpoints
                endpoints = ['/login', '/register', '/db-viewer']
                for endpoint in endpoints:
                    try:
                        resp = requests.get(f"{self.server_url}{endpoint}", timeout=3)
                        if resp.status_code in [200, 401, 403]:  # Expected codes
                            print_success(f"  Endpoint {endpoint} is accessible")
                        else:
                            print_warning(f"  Endpoint {endpoint} returned {resp.status_code}")
                    except:
                        print_warning(f"  Endpoint {endpoint} timed out")
            else:
                print_error(f"Server returned status code {response.status_code}")
                self.tests_failed += 1
                
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to server - server may be down")
            print_info(f"   Check if server is running at {self.server_url}")
            self.tests_failed += 1
        except Exception as e:
            print_error(f"Error testing server: {str(e)}")
            self.tests_failed += 1
    
    def test_assets(self):
        """Test if required asset files exist"""
        print_header("Testing Game Assets")
        
        # Check fonts
        fonts_dir = self.frontend_dir / "fonts"
        if fonts_dir.exists():
            fonts = list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf"))
            if fonts:
                print_success(f"Found {len(fonts)} font file(s)")
                self.tests_passed += 1
            else:
                print_warning("No font files found")
        
        # Check spritesheets
        sprites_dir = self.frontend_dir / "spritesheets"
        if sprites_dir.exists():
            sprites = list(sprites_dir.glob("*.png"))
            if sprites:
                print_success(f"Found {len(sprites)} spritesheet(s)")
                self.tests_passed += 1
            else:
                print_error("No spritesheet files found")
                self.tests_failed += 1
        
        # Check sound effects
        sounds_dir = self.frontend_dir / "sound_effects"
        if sounds_dir.exists():
            sounds = list(sounds_dir.glob("*.wav")) + list(sounds_dir.glob("*.mp3"))
            if sounds:
                print_success(f"Found {len(sounds)} sound file(s)")
                self.tests_passed += 1
            else:
                print_warning("No sound files found (optional)")
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("CodeBreak Game Testing Suite")
        
        self.test_python_version()
        self.test_directory_structure()
        self.test_game_files()
        self.test_dependencies()
        self.test_config_files()
        self.test_assets()
        self.test_server_connection()
        
        # Print summary
        print_header("Test Summary")
        total_tests = self.tests_passed + self.tests_failed
        
        if self.tests_failed == 0:
            print_success(f"All {self.tests_passed} tests passed! ✓")
            print()
            print_info("Your game is ready to test!")
            print_info(f"Run: cd frontend && python unified_game_launcher.py")
        else:
            print_warning(f"Passed: {self.tests_passed}/{total_tests}")
            print_error(f"Failed: {self.tests_failed}/{total_tests}")
            print()
            print_info("Please fix the failed tests before running the game")
        
        print()
        return self.tests_failed == 0

def main():
    tester = GameTester()
    success = tester.run_all_tests()
    
    if success:
        print_info("Would you like to start the game now? (y/n)")
        try:
            response = input().lower().strip()
            if response == 'y':
                print_info("Starting game...")
                os.chdir(tester.frontend_dir)
                subprocess.run([sys.executable, "unified_game_launcher.py"])
        except KeyboardInterrupt:
            print("\n\nTest cancelled by user")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
