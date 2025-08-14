import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Set up logger
def setup_logger():
    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    
    # Prevent adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler - daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(f"logs/{today}.log")
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()