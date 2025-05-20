#!/usr/bin/env python3
import logging
import sys
import re

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# High intensity colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

class ColoredFormatter(logging.Formatter):
    # Colors for different log levels
    LEVEL_COLORS = {
        'DEBUG': CYAN,
        'INFO': GREEN,
        'WARNING': YELLOW,
        'ERROR': RED,
        'CRITICAL': BG_RED + BOLD + WHITE
    }
    
    # Colors for different modules/components
    MODULE_COLORS = {
        'ai_gen_video': BRIGHT_BLUE,
        'api_services': BRIGHT_CYAN,
        'cache_manager': BRIGHT_GREEN,
        'video_generator': BRIGHT_MAGENTA,
        'main': BRIGHT_YELLOW
    }
    
    # Task-specific colors based on message content patterns
    TASK_PATTERNS = [
        # Data fetching and processing
        (re.compile(r'fetch|headline|news', re.I), BLUE),
        (re.compile(r'extract|article|content', re.I), CYAN),
        (re.compile(r'(generat|process).*(summary|json)', re.I), GREEN),
        
        # Media generation
        (re.compile(r'(generat|process).*(TTS|audio|speech|voice)', re.I), YELLOW),
        (re.compile(r'(generat|process).*(image|img|picture|visual)', re.I), MAGENTA),
        (re.compile(r'(generat|process|assembl).*(video|mp4|film)', re.I), BRIGHT_BLUE),
        
        # Performance and caching
        (re.compile(r'cache|cached|saving', re.I), BRIGHT_GREEN),
        (re.compile(r'load(ing)?|retriev(e|ing)|found', re.I), BRIGHT_CYAN),
        
        # Progress indicators
        (re.compile(r'start|begin|init', re.I), BRIGHT_BLUE),
        (re.compile(r'complet|finish|done|success', re.I), BRIGHT_GREEN),
        (re.compile(r'wait|pending|process(ing)?', re.I), BRIGHT_YELLOW),
        
        # Error handling
        (re.compile(r'error|fail|exception|missing|invalid', re.I), RED),
        (re.compile(r'warn(ing)?', re.I), YELLOW),
        
        # API and external services
        (re.compile(r'api|request|http|endpoint', re.I), BRIGHT_MAGENTA),
        (re.compile(r'url|link', re.I), BLUE)
    ]

    def format(self, record):
        # Save the original format
        format_orig = self._style._fmt
        original_message = record.getMessage()

        # Color based on log level
        levelname = record.levelname
        if levelname in self.LEVEL_COLORS:
            colored_levelname = f"{self.LEVEL_COLORS[levelname]}{levelname}{RESET}"
            record.levelname = colored_levelname

        # Color based on logger name/module
        module_color = self.MODULE_COLORS.get(record.name, MAGENTA)
        record.name = f"{module_color}{record.name}{RESET}"
        
        # Format the record first to get all fields
        result = super().format(record)
        
        # Apply color to timestamp
        formatted_time = self.formatTime(record, self.datefmt)
        colored_time = f"{BRIGHT_BLACK}{formatted_time}{RESET}"
        result = result.replace(formatted_time, colored_time)
        
        # Apply task-specific message coloring
        message_start = result.find(original_message)
        if message_start != -1:
            # Check if message matches any task patterns
            for pattern, color in self.TASK_PATTERNS:
                if pattern.search(original_message):
                    colored_message = f"{color}{original_message}{RESET}"
                    result = result[:message_start] + colored_message + result[message_start + len(original_message):]
                    break
        
        # Restore the original format
        self._style._fmt = format_orig
        
        return result

def setup_colored_logging(level=logging.INFO):
    """Set up colored logging for all modules."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger
