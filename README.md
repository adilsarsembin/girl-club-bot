# 🌸 GirlClub Bot

A beautiful and warm Telegram bot for girls' community management, built with Python and aiogram. Features motivational quotes, photos, event management, and anonymous messaging with a focus on creating a supportive and positive environment.

## ✨ Features

### 🤖 User Features
- **Motivational Content**: Choose between inspirational quotes and photos
- **Event Calendar**: View upcoming community events
- **Anonymous Messaging**: Send private messages to administrators
- **Warm Interface**: Designed specifically for girls and women with encouraging language

### 👑 Admin Features
- **Content Management**: Add inspirational quotes and photos
- **Event Management**: Create, view, and delete community events
- **User Communication**: Send broadcast messages to all users
- **Access Control**: Role-based permissions system

### 🔧 Technical Features
- **Memory-Efficient**: Optimized for limited environments (PythonAnywhere)
- **Comprehensive Logging**: Detailed logging with automatic rotation
- **Database Integration**: MySQL with automatic table creation
- **Proxy Support**: Optional proxy configuration for production
- **Error Handling**: Robust error handling and user feedback

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or MariaDB
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd girl-club-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

#### Option A: Docker (Recommended)
```bash
# Start MySQL with Docker
docker run --name mysql-gc-bot -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=girl_club_bot -p 3306:3306 -d mysql:8.0

# Or use Docker Compose
docker-compose up -d
```

#### Option B: Local MySQL
```bash
# Install MySQL and create database
mysql -u root -p < database_setup.sql
```

Or run the SQL commands manually:

```sql
-- Run this SQL script to create the database and user
CREATE DATABASE IF NOT EXISTS girl_club_bot;
CREATE USER IF NOT EXISTS 'botuser'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON girl_club_bot.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Note:** The bot will automatically create all tables on first run.

### 3. Configuration

Copy the example environment file and configure it:
```bash
cp env_example.txt .env
```

Edit `.env` with your settings:
```bash
# Telegram Bot Configuration
TELEGRAM_API_TOKEN=your_bot_token_from_botfather

# Database Configuration
DB_HOST=localhost
DB_NAME=girl_club_bot
DB_USER=botuser  # or root for Docker
DB_PASSWORD=your_password

# Admin Configuration (comma-separated Telegram user IDs)
ADMIN_IDS=123456789,987654321

# Proxy Configuration (leave empty for local development)
PROXY_URL=

# Logging Configuration
LOG_PRESET=production  # or development/minimal
```

### 4. Initialize Database

The bot will automatically create all necessary tables on first run. You can also run the setup script:
```bash
python setup_local.py
```

### 5. Run the Bot
```bash
python main.py
```

You should see:
```
2024-11-03 10:00:00 - root - INFO - === GirlClub Bot Starting Up ===
2024-11-03 10:00:00 - root - INFO - Running without proxy (local mode)
2024-11-03 10:00:00 - root - INFO - Database initialized successfully
2024-11-03 10:00:00 - root - INFO - Starting polling...
```

## 📋 Database Schema

The bot automatically creates these tables:

### Users Table
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'user'
);
```

### Quotes Table
```sql
CREATE TABLE quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Photos Table
```sql
CREATE TABLE photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL,
    file_unique_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    caption TEXT,
    uploaded_by BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Events Table
```sql
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    planned_at DATETIME NOT NULL,
    theme TEXT NOT NULL,
    place TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Anonymous Messages Table
```sql
CREATE TABLE anonymous_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎮 Available Commands

### For All Users
- `/start` - Start the bot and get personalized menu
- `/help` - Show available commands
- `/motivation` - Choose between quotes and photos
- `/events` - View upcoming events
- `/anonymous_message` - Send private message to admins

### For Administrators Only
- `/manage_quotes` - Quote management (add/list/delete)
- `/manage_photos` - Photo management (add/list/delete)
- `/manage_events` - Event management (add/list/delete)
- `/send_all` - Broadcast message to all users

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_API_TOKEN` | Bot token from BotFather | Required |
| `DB_HOST` | Database host | localhost |
| `DB_NAME` | Database name | girl_club_bot |
| `DB_USER` | Database user | Required |
| `DB_PASSWORD` | Database password | Required |
| `ADMIN_IDS` | Admin Telegram IDs (comma-separated) | Required |
| `PROXY_URL` | Proxy URL for production | Empty |
| `LOG_PRESET` | Logging preset | production |
| `LOG_FILE` | Custom log file path | girl_club_bot.log |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_MAX_BYTES` | Max log file size | 5242880 (5MB) |
| `LOG_BACKUP_COUNT` | Number of log backups | 2 |
| `DISABLE_FILE_LOGGING` | Disable file logging for cloud | false |

### Logging Presets

- **production**: INFO level, 5MB files, 2 backups (15MB total max)
- **development**: DEBUG level, 10MB files, 3 backups
- **cloud**: INFO level to console (Railway/Heroku), no file logging
- **minimal**: WARNING level, 2MB files, 1 backup

**Note**: Cloud environments auto-detect Railway/Heroku and use `cloud` preset

## 📊 Monitoring & Logs

### Log Files
```
girl_club_bot.log      # Current log
girl_club_bot.log.1    # First backup
girl_club_bot.log.2    # Second backup
```

### Log Analysis
```bash
# View recent logs
tail -f girl_club_bot.log

# Search for errors
grep "ERROR" girl_club_bot.log

# Count user registrations
grep "New user registered" girl_club_bot.log | wc -l

# View admin actions
grep "Admin" girl_club_bot.log
```

### Log Rotation
Logs automatically rotate when they reach the size limit, preventing disk space issues.

## 🚀 Deployment

### Railway Deployment (Recommended)
1. Create Railway account and Hobby plan ($5/month)
2. Deploy from GitHub repo or Railway dashboard
3. Add PostgreSQL plugin
4. Set environment variables (TELEGRAM_API_TOKEN, ADMIN_IDS, LOG_PRESET=production)
5. Railway auto-detects cloud environment and enables console logging
6. Monitor logs in Railway dashboard → Deployments → View Logs

### PythonAnywhere Deployment
1. Upload all files to PythonAnywhere
2. Set environment variables in the web interface
3. Set `PROXY_URL` if needed for your region
4. Run `python main.py` in a console

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build -d
```

## 🔧 Troubleshooting

### Bot doesn't respond
```bash
# Check if bot token is correct
# Verify database connection
python setup_local.py

# Check logs for errors
tail -20 girl_club_bot.log
```

### Database connection issues
```bash
# Test database connection
python -c "
import pymysql
from dotenv import load_dotenv
load_dotenv()
import os
conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
print('Database connected successfully')
"
```

### Permission issues
- Ensure admin IDs in `ADMIN_IDS` are correct
- Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

### Memory issues on PythonAnywhere
- Use `LOG_PRESET=minimal` to reduce log file sizes
- Monitor log file sizes regularly
- Consider upgrading your PythonAnywhere plan

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💕 Acknowledgments

- Built with ❤️ for empowering girls and women
- Special thanks to the aiogram community
- Designed to create positive, supportive digital spaces

---

**Made with 💖 for our amazing GirlClub community!** 🌸✨

For questions or support, contact the bot administrators.
