"""
Logging configuration for GirlClub Bot
Provides memory-efficient logging with rotation for limited environments
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: str = "girl_club_bot.log",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 2,
    log_level: int = logging.INFO,
    console_level: int = logging.WARNING,
    enable_file_logging: bool = True
) -> logging.Logger:
    """
    Configure logging for the bot with memory-efficient settings

    Args:
        log_file: Path to log file
        max_bytes: Maximum bytes per log file before rotation
        backup_count: Number of backup files to keep
        log_level: Logging level for file handler
        console_level: Logging level for console handler
        enable_file_logging: Whether to enable file logging (disable for cloud environments)

    Returns:
        Configured logger instance
    """

    logger = logging.getLogger()
    logger.setLevel(log_level)

    logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add file handler only if enabled (skip for cloud environments)
    if enable_file_logging:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Always add console handler for Railway/cloud visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)


LOGGING_PRESETS = {
    'development': {
        'log_file': 'girl_club_bot_dev.log',
        'max_bytes': 10 * 1024 * 1024,
        'backup_count': 3,
        'log_level': logging.DEBUG,
        'console_level': logging.INFO,
        'enable_file_logging': True
    },

    'production': {
        'log_file': 'girl_club_bot.log',
        'max_bytes': 5 * 1024 * 1024,
        'backup_count': 2,
        'log_level': logging.INFO,
        'console_level': logging.WARNING,
        'enable_file_logging': True
    },

    'cloud': {
        'log_file': 'girl_club_bot.log',
        'max_bytes': 5 * 1024 * 1024,
        'backup_count': 2,
        'log_level': logging.INFO,
        'console_level': logging.INFO,
        'enable_file_logging': False
    },

    'minimal': {
        'log_file': 'girl_club_bot.log',
        'max_bytes': 2 * 1024 * 1024,
        'backup_count': 1,
        'log_level': logging.WARNING,
        'console_level': logging.ERROR,
        'enable_file_logging': True
    }
}


def setup_logging_from_env() -> logging.Logger:
    """
    Setup logging based on environment variables
    Defaults to cloud preset for Railway/Heroku environments, production otherwise

    Environment variables:
    - LOG_PRESET: development/production/cloud/minimal (default: auto-detect)
    - LOG_FILE: custom log file path
    - LOG_LEVEL: DEBUG/INFO/WARNING/ERROR
    - LOG_MAX_BYTES: max bytes per file
    - LOG_BACKUP_COUNT: number of backup files
    - DISABLE_FILE_LOGGING: set to 'true' to disable file logging (for cloud)
    """
    # Auto-detect cloud environment
    preset_name = os.getenv('LOG_PRESET')
    if not preset_name:
        # Auto-detect Railway/Heroku/Render environments
        if (os.getenv('RAILWAY_ENVIRONMENT') or
            os.getenv('DYNO') or  # Heroku
            os.getenv('RENDER_SERVICE_ID')):  # Render
            preset_name = 'cloud'
        else:
            preset_name = 'production'

    if preset_name not in LOGGING_PRESETS:
        preset_name = 'production'

    config = LOGGING_PRESETS[preset_name].copy()

    if os.getenv('LOG_FILE'):
        config['log_file'] = os.getenv('LOG_FILE')

    if os.getenv('LOG_LEVEL'):
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        config['log_level'] = level_map.get(os.getenv('LOG_LEVEL').upper(), logging.INFO)

    if os.getenv('LOG_MAX_BYTES'):
        try:
            config['max_bytes'] = int(os.getenv('LOG_MAX_BYTES'))
        except ValueError:
            pass

    if os.getenv('LOG_BACKUP_COUNT'):
        try:
            config['backup_count'] = int(os.getenv('LOG_BACKUP_COUNT'))
        except ValueError:
            pass

    # Allow manual override of file logging
    if os.getenv('DISABLE_FILE_LOGGING', '').lower() in ('true', '1', 'yes'):
        config['enable_file_logging'] = False

    return setup_logging(**config)


def log_user_action(logger: logging.Logger, user_id: int, username: str, action: str, details: str = None):
    """Log user actions with consistent format"""
    if details:
        logger.info(f"User {user_id} (@{username}) {action}: {details}")
    else:
        logger.info(f"User {user_id} (@{username}) {action}")


def log_admin_action(logger: logging.Logger, admin_id: int, admin_username: str, action: str, target: str = None):
    """Log admin actions with consistent format"""
    if target:
        logger.info(f"Admin {admin_id} (@{admin_username}) {action}: {target}")
    else:
        logger.info(f"Admin {admin_id} (@{admin_username}) {action}")


def log_system_event(logger: logging.Logger, event: str, details: str = None):
    """Log system events"""
    if details:
        logger.info(f"System: {event} - {details}")
    else:
        logger.info(f"System: {event}")


def log_error(logger: logging.Logger, error_msg: str, exception: Exception = None):
    """Log errors with optional exception details"""
    if exception:
        logger.error(f"{error_msg}: {str(exception)}")
    else:
        logger.error(error_msg)
