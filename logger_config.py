"""
Centralized logging configuration for the PDF chatbot application.
Provides structured logging with time tracking for performance analysis.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom log formatter that adds ANSI color codes to level names for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record):
        """Apply ANSI color codes to log level names for better console readability"""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create logger with colored console output and consistent formatting for debugging"""
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format: [2024-03-24 10:30:45] INFO - module_name - Message
    formatter = ColoredFormatter(
        fmt='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


class PerformanceTimer:
    """Context manager for timing operations and logging duration with success/failure status"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def __enter__(self):
        """Start timer and log operation start"""
        self.start_time = datetime.now()
        self.logger.info(f"{'='*80}")
        self.logger.info(f"⏱️  STARTED: {self.operation}")
        self.logger.info(f"{'='*80}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer, log operation completion with duration and status"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"{'='*80}")
            self.logger.info(f"✅ COMPLETED: {self.operation}")
            self.logger.info(f"⏱️  Duration: {duration:.2f}s")
            self.logger.info(f"{'='*80}\n")
        else:
            self.logger.error(f"{'='*80}")
            self.logger.error(f"❌ FAILED: {self.operation}")
            self.logger.error(f"⏱️  Duration: {duration:.2f}s")
            self.logger.error(f"Error: {exc_val}")
            self.logger.error(f"{'='*80}\n")
        
        return False  # Don't suppress exceptions
    
    def elapsed(self) -> float:
        """Calculate elapsed time in seconds since timer start"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


def log_section(logger: logging.Logger, title: str, level: str = "INFO"):
    """Log formatted section header for organizing log output"""
    log_func = getattr(logger, level.lower())
    log_func(f"\n{'='*80}")
    log_func(f"📋 {title}")
    log_func(f"{'='*80}")


def log_step(logger: logging.Logger, step: str, details: dict = None):
    """Log operation step with optional key-value details for debugging"""
    logger.info(f"▶️  {step}")
    if details:
        for key, value in details.items():
            logger.info(f"   • {key}: {value}")
