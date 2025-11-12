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
    console_level: int = logging.WARNING
) -> logging.Logger:
    """
    Configure logging for the bot with memory-efficient settings

    Args:
        log_file: Path to log file
        max_bytes: Maximum bytes per log file before rotation
        backup_count: Number of backup files to keep
        log_level: Logging level for file handler
        console_level: Logging level for console handler

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

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
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
        'console_level': logging.INFO
    },

    'production': {
        'log_file': 'girl_club_bot.log',
        'max_bytes': 5 * 1024 * 1024,
        'backup_count': 2,
        'log_level': logging.INFO,
        'console_level': logging.WARNING
    },

    'minimal': {
        'log_file': 'girl_club_bot.log',
        'max_bytes': 2 * 1024 * 1024,
        'backup_count': 1,
        'log_level': logging.WARNING,
        'console_level': logging.ERROR
    }
}


def setup_logging_from_env() -> logging.Logger:
    """
    Setup logging based on environment variables
    Defaults to production preset if not specified

    Environment variables:
    - LOG_PRESET: development/production/minimal (default: production)
    - LOG_FILE: custom log file path
    - LOG_LEVEL: DEBUG/INFO/WARNING/ERROR
    - LOG_MAX_BYTES: max bytes per file
    - LOG_BACKUP_COUNT: number of backup files
    """
    preset_name = os.getenv('LOG_PRESET', 'production')

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
