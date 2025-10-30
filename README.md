# 🎮 CodeBreak

**A multiplayer survival game built with Python and Pygame, featuring real-time WebSocket communication and AWS cloud infrastructure.**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![AWS](https://img.shields.io/badge/AWS-RDS%20%7C%20EC2-orange.svg)](https://aws.amazon.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Game Mechanics](#game-mechanics)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## 🎯 Overview

CodeBreak is a multiplayer survival game where players battle waves of enemies, collect resources, craft items, and compete on both global and game-specific leaderboards. The game features real-time multiplayer functionality, persistent player data, and an achievement system.

**Live Server:** http://3.19.244.138:8000

---

## ✨ Features

### 🎮 Gameplay
- **Wave-based survival** with increasing difficulty
- **Resource collection** (code fragments, energy cores, data shards)
- **Crafting system** for weapons and tools
- **Real-time multiplayer** with WebSocket communication
- **Enemy AI** with pathfinding and collision detection
- **Player stats tracking** (score, health, inventory)

### 🏆 Progression System
- **Global leaderboards** - Track top players across all games
- **Game-specific leaderboards** - Compete within individual game sessions
- **Achievement system** - Unlock 6+ achievements
- **Player statistics** - Track games played, enemies defeated, resources collected
- **Persistent data** - Player progress saved to cloud database

### 🔐 Authentication & Security
- **User registration** with secure password hashing (BCrypt)
- **JWT-based authentication** for API access
- **Session management** with token expiration
- **Admin dashboard** for database management

### 🌐 Multiplayer Features
- **Create and join games** - Host or join multiplayer sessions
- **Real-time updates** - WebSocket-based player synchronization
- **In-game chat** - Communicate with other players
- **Game session history** - Track completed games and winners

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database (AWS RDS)
- **WebSockets** - Real-time bidirectional communication
- **JWT** - JSON Web Token authentication
- **BCrypt** - Password hashing
- **psycopg2** - PostgreSQL adapter

### Frontend
- **Pygame** - Game engine and graphics
- **Python** - Client-side logic
- **WebSocket Client** - Real-time server communication

### Infrastructure
- **AWS EC2** - Application server hosting
- **AWS RDS** - Managed PostgreSQL database
- **Ubuntu Linux** - Server operating system
- **systemd** - Service management
- **Nginx** (optional) - Reverse proxy

### Development Tools
- **Git/GitHub** - Version control
- **VS Code** - Development environment
- **DBeaver** - Database management (optional)

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Game Client   │
│    (Pygame)     │
└────────┬────────┘
         │ WebSocket + HTTP
         │
┌────────▼────────┐
│   EC2 Instance  │
│   FastAPI App   │
│   (Port 8000)   │
└────────┬────────┘
         │ PostgreSQL
         │
┌────────▼────────┐
│   AWS RDS       │
│   PostgreSQL    │
│   Database      │
└─────────────────┘
```

### Component Responsibilities

**Game Client (Frontend)**
- Renders game graphics
- Handles player input
- Manages local game state
- Communicates with server via WebSocket

**FastAPI Server (Backend)**
- Handles authentication
- Manages WebSocket connections
- Processes game events
- Updates database
- Broadcasts game state to clients

**PostgreSQL Database (RDS)**
- Stores user accounts
- Maintains player data
- Tracks leaderboards
- Records game sessions
- Manages achievements

---

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- PostgreSQL (local) or AWS RDS account
- Git

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/Leighthann/codebreak.git
cd codebreak
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Install frontend dependencies**
```bash
cd ../frontend
pip install -r requirements.txt
```

5. **Configure environment variables**
```bash
cd ../backend
cp .env.example .env
# Edit .env with your database credentials
```

6. **Initialize database**
```bash
# Option 1: Use init_database.sql for fresh setup
psql -U your_user -d your_database -f init_database.sql

# Option 2: Let server auto-migrate on first run
python server_postgres.py
```

7. **Run the server**
```bash
uvicorn server_postgres:app --reload --host 0.0.0.0 --port 8000
```

8. **Run the game client**
```bash
cd ../frontend
python main.py
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DB_HOST=your-database-host
DB_NAME=codebreak_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Client Configuration

Create `client_config.json` in the `frontend/` directory:

```json
{
  "server_url": "http://your-server-ip:8000",
  "token": "your-jwt-token",
  "username": "your-username"
}
```

---

## 🚀 Deployment

### AWS EC2 + RDS Deployment

#### 1. Set up RDS Instance

```bash
# Create PostgreSQL RDS instance via AWS Console
# - Engine: PostgreSQL 15+
# - Instance: db.t3.micro (free tier)
# - Public access: No (access from EC2 only)
# - Security group: Allow PostgreSQL (5432) from EC2 security group
```

#### 2. Set up EC2 Instance

```bash
# Launch Ubuntu EC2 instance
# - Instance type: t2.micro (free tier)
# - Security group: Allow HTTP (80), HTTPS (443), Custom TCP (8000), SSH (22)

# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. Install Dependencies on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and PostgreSQL client
sudo apt install python3-pip python3-venv postgresql-client -y

# Clone repository
git clone https://github.com/Leighthann/codebreak.git
cd codebreak

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### 4. Configure Database Connection

```bash
# Create .env file
nano .env

# Add your RDS credentials:
DB_HOST=your-rds-endpoint.amazonaws.com
DB_NAME=codebreak_db
DB_USER=codebreak_admin
DB_PASSWORD=your-password
DB_PORT=5432
SECRET_KEY=your-secret-key
```

#### 5. Initialize Database Schema

```bash
# Connect to RDS and create database
PGPASSWORD='your-password' psql -h your-rds-endpoint -U codebreak_admin -d postgres -c "CREATE DATABASE codebreak_db;"

# Initialize schema
PGPASSWORD='your-password' psql -h your-rds-endpoint -U codebreak_admin -d codebreak_db -f init_database.sql

# Or run migration script
python migrate_database.py
```

#### 6. Set up systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/codebreak.service
```

Add the following content:

```ini
[Unit]
Description=CodeBreak Game Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/codebreak/backend
Environment="PATH=/home/ubuntu/codebreak/venv/bin"
ExecStart=/home/ubuntu/codebreak/venv/bin/uvicorn server_postgres:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

StandardOutput=append:/var/log/codebreak-access.log
StandardError=append:/var/log/codebreak-error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable codebreak
sudo systemctl start codebreak
sudo systemctl status codebreak
```

#### 7. Set up Deployment Scripts

```bash
# Make scripts executable
chmod +x backend/deploy.sh
chmod +x backend/restart.sh

# Deploy updates
./backend/deploy.sh

# Quick restart
./backend/restart.sh
```

#### 8. View Logs

```bash
# Real-time logs
sudo tail -f /var/log/codebreak-error.log
sudo tail -f /var/log/codebreak-access.log

# Service logs
sudo journalctl -u codebreak -f
```

---

## 🎮 Game Mechanics

### Core Gameplay Loop

1. **Spawn** - Player starts with basic stats
2. **Collect Resources** - Gather code fragments, energy cores, data shards
3. **Craft Items** - Combine resources to create weapons and tools
4. **Battle Enemies** - Survive increasingly difficult waves
5. **Level Up** - Increase stats and unlock abilities
6. **Compete** - Climb the leaderboards

### Resources

| Resource | Description | Uses |
|----------|-------------|------|
| **Code Fragments** | Basic resource | Crafting, upgrades |
| **Energy Cores** | Power resource | Advanced crafting |
| **Data Shards** | Rare resource | Legendary items |

### Achievements

- **First Blood** - Defeat your first enemy (10 points)
- **Score Master** - Reach a score of 1000 (25 points)
- **Survivor** - Survive for 10 minutes (50 points)
- **Resource Hoarder** - Collect 100 resources (15 points)
- **Legendary Collector** - Collect 500 resources (50 points)
- **Victory Royale** - Win your first game (100 points)

---

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /register/user
Content-Type: application/json

{
  "username": "player1",
  "password": "secure_password"
}
```

#### Login
```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=player1&password=secure_password
```

#### Web Login (Form-based)
```http
POST /web-login
Content-Type: application/x-www-form-urlencoded

username=player1&password=secure_password
```

### Game Endpoints

#### Get Player Info
```http
GET /players/{username}
Authorization: Bearer {token}
```

#### Get Leaderboard
```http
GET /leaderboard?limit=10&game_id={optional}
Authorization: Bearer {token}
```

#### Submit Score
```http
POST /leaderboard
Authorization: Bearer {token}
Content-Type: application/json

{
  "score": 1500,
  "wave_reached": 10,
  "survival_time": 600,
  "game_id": "optional-game-id"
}
```

#### Create Game
```http
POST /create_game
Authorization: Bearer {token}
```

#### Join Game
```http
POST /join_game/{game_id}
Authorization: Bearer {token}
```

#### Get Active Games
```http
GET /active_games
Authorization: Bearer {token}
```

### WebSocket Connection

```javascript
ws://server-url:8000/ws/{username}?token={jwt_token}&game_id={optional}
```

**Events:**
- `player_joined` - New player connected
- `player_left` - Player disconnected
- `player_moved` - Player position update
- `chat_message` - Chat message received
- `update_position` - Send position update

### Admin Endpoints

#### Admin Login
```http
POST /admin-login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin_password
```

#### Database Viewer
```http
GET /db-viewer
# Requires admin authentication
```

---

## 🗄️ Database Schema

### Core Tables

#### users
```sql
- id (SERIAL PRIMARY KEY)
- username (VARCHAR(50) UNIQUE)
- hashed_password (VARCHAR(255))
- email (VARCHAR(255))
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
- is_active (BOOLEAN)
- is_admin (BOOLEAN)
```

#### players
```sql
- id (SERIAL PRIMARY KEY)
- username (VARCHAR(50) UNIQUE)
- health (INTEGER)
- x, y (INTEGER) - Position
- score (INTEGER)
- inventory (JSONB)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

#### leaderboard
```sql
- id (SERIAL PRIMARY KEY)
- username (VARCHAR(50))
- score (INTEGER)
- wave_reached (INTEGER)
- survival_time (FLOAT)
- date (TIMESTAMP)
- game_id (VARCHAR(255)) - NULL for global
```

#### active_games
```sql
- id (SERIAL PRIMARY KEY)
- game_id (VARCHAR(255) UNIQUE)
- host_username (VARCHAR(50))
- created_at (TIMESTAMP)
- is_active (BOOLEAN)
- game_mode (VARCHAR(50))
```

#### game_sessions
```sql
- session_id (SERIAL PRIMARY KEY)
- game_id (VARCHAR(255) UNIQUE)
- created_at (TIMESTAMP)
- ended_at (TIMESTAMP)
- duration_seconds (INTEGER)
- total_players (INTEGER)
- winner_username (VARCHAR(255))
```

#### player_stats
```sql
- stat_id (SERIAL PRIMARY KEY)
- username (VARCHAR(255) UNIQUE)
- total_games_played (INTEGER)
- total_games_won (INTEGER)
- total_score (INTEGER)
- highest_score (INTEGER)
- enemies_defeated (INTEGER)
- resources_collected (INTEGER)
```

#### achievements
```sql
- achievement_id (SERIAL PRIMARY KEY)
- achievement_name (VARCHAR(100) UNIQUE)
- description (TEXT)
- points (INTEGER)
- icon_path (VARCHAR(255))
```

#### player_achievements
```sql
- id (SERIAL PRIMARY KEY)
- username (VARCHAR(255))
- achievement_id (INTEGER)
- unlocked_at (TIMESTAMP)
- UNIQUE(username, achievement_id)
```

### Indexes

- `idx_users_username` - Fast user lookups
- `idx_players_username` - Fast player queries
- `idx_players_score` - Leaderboard sorting
- `idx_leaderboard_game_id` - Game-specific leaderboards
- `idx_leaderboard_game_score` - Optimized leaderboard queries
- `idx_leaderboard_unique_player_game` - Prevent duplicate entries
- `idx_game_sessions_game_id` - Game history queries
- `idx_player_stats_total_score` - Statistics ranking

---

## 💻 Development

### Project Structure

```
CodeBreak/
├── backend/
│   ├── server_postgres.py       # Main FastAPI server
│   ├── auth.py                  # Authentication utilities
│   ├── db.py                    # Database utilities
│   ├── init_database.sql        # Database schema
│   ├── migrate_database.py      # Migration script
│   ├── test_schema.py           # Schema verification
│   ├── deploy.sh                # Deployment script
│   ├── restart.sh               # Quick restart script
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables
│   ├── templates/               # HTML templates
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── launch.html
│   │   ├── launch_instructions.html
│   │   ├── db_viewer.html
│   │   └── admin_login.html
│   └── static/                  # Static assets
│       ├── fonts/
│       └── sound_effects/
├── frontend/
│   ├── main.py                  # Game launcher
│   ├── game.py                  # Main game logic
│   ├── player.py                # Player class
│   ├── enemy.py                 # Enemy AI
│   ├── world.py                 # World/map system
│   ├── worldObject.py           # Game objects
│   ├── crafting.py              # Crafting system
│   ├── ui_system.py             # UI rendering
│   ├── camera_system.py         # Camera controls
│   ├── effects.py               # Visual effects
│   ├── auth_manager.py          # Client authentication
│   ├── leaderboard_manager.py   # Leaderboard UI
│   ├── state_manager.py         # Game state management
│   ├── settings_manager.py      # Settings UI
│   ├── font_manager.py          # Font handling
│   ├── requirements.txt         # Python dependencies
│   ├── client_config.json       # Server configuration
│   ├── game_settings.json       # Game settings
│   ├── server_config.json       # Server defaults
│   ├── spritesheets/            # Game graphics
│   ├── fonts/                   # Font files
│   └── sound_effects/           # Audio files
├── POSTGRES_EC2_COMMANDS.txt    # EC2 command reference
├── RDS_CODEBREAK_INFO.txt       # RDS configuration info
├── README.md                    # This file
└── .gitignore                   # Git ignore rules
```

### Running Locally

**Backend:**
```bash
cd backend
source ../venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn server_postgres:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
source ../venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

### Testing

```bash
# Test database schema
cd backend
python test_schema.py

# Test game locally
cd frontend
python test_game.py

# Run migration
cd backend
python migrate_database.py
```

### Database Management

```bash
# Connect to database
psql -h your-db-host -U your-user -d codebreak_db

# List tables
\dt

# View table structure
\d table_name

# Run migration
python migrate_database.py

# Backup database
pg_dump -h your-db-host -U your-user -d codebreak_db > backup.sql

# Restore database
psql -h your-db-host -U your-user -d codebreak_db < backup.sql
```

---

## 🐛 Troubleshooting

### Common Issues

#### Server Won't Start

**Problem:** `Database connection error`

**Solution:**
```bash
# Check database credentials in .env
cat backend/.env

# Test database connection
psql -h your-db-host -U your-user -d codebreak_db

# Check server logs
sudo tail -f /var/log/codebreak-error.log
```

#### Can't Connect to Game

**Problem:** `Connection refused` or `WebSocket error`

**Solution:**
```bash
# Verify server is running
curl http://your-server:8000/

# Check firewall allows port 8000
sudo ufw status

# Verify WebSocket connection
wscat -c ws://your-server:8000/ws/testuser
```

#### Database Migration Fails

**Problem:** `Column already exists` or `Table not found`

**Solution:**
```bash
# Run schema verification
python test_schema.py

# Check current schema
psql -h your-db-host -U your-user -d codebreak_db -c "\dt"

# Reset database (WARNING: Deletes all data)
psql -h your-db-host -U your-user -d postgres -c "DROP DATABASE codebreak_db;"
psql -h your-db-host -U your-user -d postgres -c "CREATE DATABASE codebreak_db;"
psql -h your-db-host -U your-user -d codebreak_db -f init_database.sql
```

#### Clipboard Copy Not Working

**Problem:** Copy to clipboard button doesn't work

**Solution:** This is fixed in the latest version. The issue was HTTPS-only API on HTTP connection. Pull latest changes:
```bash
git pull origin master
sudo systemctl restart codebreak
```

### Logs

```bash
# Server logs
sudo tail -f /var/log/codebreak-error.log
sudo tail -f /var/log/codebreak-access.log

# System logs
sudo journalctl -u codebreak -f

# Database logs (on RDS, check CloudWatch)
# AWS Console → RDS → Your Instance → Logs & Events
```

---

## 📝 License

This project is created for educational and portfolio purposes.

---

## 🤝 Contributing

This is a personal portfolio project. Feedback and suggestions are welcome!

---

## 👤 Author

**Leigh-Ann**
- GitHub: [@Leighthann](https://github.com/Leighthann)
- Project: [CodeBreak](https://github.com/Leighthann/codebreak)

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Pygame for the game engine
- AWS for cloud infrastructure
- PostgreSQL for reliable data storage

---

## 📸 Screenshots

*(Add screenshots of your game here)*

---

## 🔮 Future Enhancements

- [ ] Mobile client support
- [ ] Additional game modes (team deathmatch, capture the flag)
- [ ] More achievements and unlockables
- [ ] Player profiles and customization
- [ ] Friends system and parties
- [ ] In-game store and currency
- [ ] Tournament mode
- [ ] Spectator mode
- [ ] Replay system
- [ ] Advanced analytics dashboard

---

## 📊 Current Status

- ✅ Core gameplay implemented
- ✅ Multiplayer functionality working
- ✅ Database migrations complete
- ✅ AWS deployment successful
- ✅ Achievement system active
- ✅ Leaderboard system operational
- ✅ Admin dashboard functional
- 🔄 Ongoing balance adjustments
- 🔄 Performance optimizations

---

**Last Updated:** October 30, 2025
