import logging
import colorlog
from contextlib import contextmanager

from almanac.config import config

def get_formatter():
    return colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def get_logger():
    handler = colorlog.StreamHandler()
    logger = logging.getLogger()
    logger.setLevel(int(config.logging_level))
    logger.addHandler(handler)
    handler.setFormatter(get_formatter())
    return logger

logger = get_logger()

@contextmanager
def buffered_logging():
    """Context manager that buffers logging during Live display"""
    # Store original handlers
    logger = logging.getLogger(__name__.split(".", 1)[0])

    original_handlers = logger.handlers[:]
    
    # Create buffer
    log_buffer = []
    
    class BufferHandler(logging.Handler):
        def emit(self, record):
            log_buffer.append(self.format(record))
    
    # Replace handlers with buffer
    logger.handlers.clear()
    buffer_handler = BufferHandler()
    buffer_handler.setFormatter(get_formatter())
    logger.addHandler(buffer_handler)
    
    try:
        yield log_buffer
    finally:
        # Restore original handlers
        logger.handlers.clear()
        logger.handlers.extend(original_handlers)
        print("HSDFSD")
        
        # Print buffered logs
        if log_buffer:
            print("HSDFSD")
            for log_line in log_buffer:
                print(log_line)
