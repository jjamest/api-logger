from datetime import datetime
from typing import Dict, Any, Optional
import json


class LogLevel:
    """Constants for log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    VALID_LEVELS = [DEBUG, INFO, WARNING, ERROR, CRITICAL]


class LogEntry:
    def __init__(self, level: str, message: str, source: str = "unknown", 
                 metadata: Optional[Dict[str, Any]] = None, 
                 timestamp: Optional[datetime] = None, entry_id: Optional[int] = None):
        """
        Initialize a log entry
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            source: Source of the log (e.g., module, function, service)
            metadata: Additional metadata as key-value pairs
            timestamp: When the log was created (defaults to now)
            entry_id: Unique identifier for the log entry
        """
        self.level = self._validate_level(level)
        self.message = str(message) if message is not None else ""
        self.source = str(source) if source is not None else "unknown"
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()
        self.entry_id = entry_id

    def _validate_level(self, level: str) -> str:
        """Validate and normalize log level"""
        level_upper = str(level).upper()
        if level_upper not in LogLevel.VALID_LEVELS:
            return LogLevel.INFO  # Default to INFO for invalid levels
        return level_upper

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            "id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict(), default=str)

    def __str__(self) -> str:
        """String representation of log entry"""
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.level} - {self.source}: {self.message}"

    def __repr__(self) -> str:
        """Developer representation of log entry"""
        return f"LogEntry(id={self.entry_id}, level='{self.level}', source='{self.source}', message='{self.message[:50]}...')"

    def is_error(self) -> bool:
        """Check if this is an error or critical log"""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]

    def is_warning_or_above(self) -> bool:
        """Check if this is warning level or above"""
        return self.level in [LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary"""
        timestamp = None
        if 'timestamp' in data:
            if isinstance(data['timestamp'], str):
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    timestamp = None
            elif isinstance(data['timestamp'], datetime):
                timestamp = data['timestamp']
        
        return cls(
            level=data.get('level', LogLevel.INFO),
            message=data.get('message', ''),
            source=data.get('source', 'unknown'),
            metadata=data.get('metadata', {}),
            timestamp=timestamp,
            entry_id=data.get('id')
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'LogEntry':
        """Create LogEntry from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)