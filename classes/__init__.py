"""
Log management classes for the API Logger

This package provides:
- LogEntry: Individual log entry with validation and utility methods
- LogLevel: Constants for log levels
- LogManager: Thread-safe log management with filtering and SSE support
"""

from .log_entry import LogEntry, LogLevel
from .log_manager import LogManager

__all__ = ['LogEntry', 'LogLevel', 'LogManager']
__version__ = '1.0.0' 