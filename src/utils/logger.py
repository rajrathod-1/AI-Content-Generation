"""
Logging utility for the AI Content Generation Service
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
import colorlog

def setup_logger(log_level: str = 'INFO', log_file: str = './logs/app.log') -> logging.Logger:
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console formatter with colors
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info("=" * 50)
    logger.info("AI Content Generation Service - Logging Initialized")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Log File: {log_file}")
    logger.info("=" * 50)
    
    return logger

def get_request_logger(request_id: str = None) -> logging.Logger:
    """
    Get a logger with request context
    
    Args:
        request_id: Unique request identifier
    
    Returns:
        Logger with request context
    """
    logger = logging.getLogger('request')
    
    if request_id:
        # Add request ID to all log messages
        logger = logging.LoggerAdapter(logger, {'request_id': request_id})
    
    return logger

def log_performance(func):
    """
    Decorator to log function performance
    
    Usage:
        @log_performance
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Function {func.__name__} completed in {duration:.3f}s")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper

def log_api_request(endpoint: str, method: str, status_code: int, response_time: float, user_id: str = None):
    """
    Log API request details
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        response_time: Response time in seconds
        user_id: Optional user identifier
    """
    logger = logging.getLogger('api')
    
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time': response_time,
        'user_id': user_id or 'anonymous'
    }
    
    if status_code >= 400:
        logger.error(f"API Error: {method} {endpoint} - {status_code} - {response_time:.3f}s - User: {user_id}")
    else:
        logger.info(f"API Success: {method} {endpoint} - {status_code} - {response_time:.3f}s - User: {user_id}")

def setup_service_logger(service_name: str) -> logging.Logger:
    """
    Setup logger for a specific service
    
    Args:
        service_name: Name of the service
    
    Returns:
        Configured service logger
    """
    logger = logging.getLogger(service_name)
    
    # Add service-specific formatting if needed
    return logger

# Custom log filter for sensitive data
class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs"""
    
    SENSITIVE_PATTERNS = [
        'api_key',
        'password',
        'token',
        'secret',
        'private_key'
    ]
    
    def filter(self, record):
        # Redact sensitive information
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in msg.lower():
                    record.msg = msg.replace(record.args[0] if record.args else '', '[REDACTED]')
        
        return True

# Example usage
if __name__ == "__main__":
    # Setup logging
    logger = setup_logger('DEBUG', './logs/test.log')
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test request logger
    request_logger = get_request_logger("req_123")
    request_logger.info("Processing user request")
    
    # Test performance logging
    @log_performance
    def test_function():
        import time
        time.sleep(0.1)
        return "completed"
    
    result = test_function()
    
    # Test API logging
    log_api_request("/api/generate", "POST", 200, 0.245, "user_456")
    log_api_request("/api/search", "POST", 404, 0.050, "user_789")