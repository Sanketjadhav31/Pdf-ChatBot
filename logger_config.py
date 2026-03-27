"""
Centralized logging configuration for the PDF chatbot application.
Provides structured logging with time tracking for performance analysis.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
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
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
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
    """Context manager for timing operations"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"{'='*80}")
        self.logger.info(f"⏱️  STARTED: {self.operation}")
        self.logger.info(f"{'='*80}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
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
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


def log_section(logger: logging.Logger, title: str, level: str = "INFO"):
    """Log a section header"""
    log_func = getattr(logger, level.lower())
    log_func(f"\n{'='*80}")
    log_func(f"📋 {title}")
    log_func(f"{'='*80}")


def log_step(logger: logging.Logger, step: str, details: dict = None):
    """Log a step with optional details"""
    logger.info(f"▶️  {step}")
    if details:
        for key, value in details.items():
            logger.info(f"   • {key}: {value}")
