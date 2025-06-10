from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import threading
import json
import queue
from .log_entry import LogEntry, LogLevel


class LogManager:
    """
    Manages log entries with thread-safe operations, filtering, and SSE support
    """
    
    def __init__(self, max_logs: int = 10000):
        """
        Initialize the LogManager
        
        Args:
            max_logs: Maximum number of logs to keep in memory
        """
        self._logs: List[LogEntry] = []
        self._max_logs = max_logs
        self._next_id = 1
        self._lock = threading.Lock()
        
        # SSE clients
        self._sse_clients: List[queue.Queue] = []
        self._sse_lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'total_logs': 0,
            'logs_by_level': {level: 0 for level in LogLevel.VALID_LEVELS},
            'logs_by_source': {}
        }

    def add_log(self, level: str, message: str, source: str = "unknown", 
                metadata: Optional[Dict[str, Any]] = None) -> LogEntry:
        """
        Add a new log entry
        
        Args:
            level: Log level
            message: Log message
            source: Source of the log
            metadata: Additional metadata
            
        Returns:
            The created LogEntry
        """
        with self._lock:
            log_entry = LogEntry(
                level=level,
                message=message,
                source=source,
                metadata=metadata,
                entry_id=self._next_id
            )
            
            self._logs.append(log_entry)
            self._next_id += 1
            
            # Update statistics
            self._update_stats(log_entry)
            
            # Trim logs if we exceed max_logs
            if len(self._logs) > self._max_logs:
                removed_log = self._logs.pop(0)
                self._decrement_stats(removed_log)
            
            # Emit SSE update
            self._emit_sse_update()
            
            return log_entry

    def add_log_from_dict(self, data: Dict[str, Any]) -> LogEntry:
        """
        Add a log entry from dictionary data
        
        Args:
            data: Dictionary containing log data
            
        Returns:
            The created LogEntry
        """
        return self.add_log(
            level=data.get("level", LogLevel.INFO),
            message=data.get("message", ""),
            source=data.get("source", "unknown"),
            metadata=data.get("metadata", {})
        )

    def get_logs(self, 
                 level_filter: Optional[str] = None,
                 source_filter: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 limit: Optional[int] = None,
                 reversed_order: bool = True) -> List[LogEntry]:
        """
        Get logs with optional filtering
        
        Args:
            level_filter: Filter by log level
            source_filter: Filter by source (partial match)
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum number of logs to return
            reversed_order: Return logs in reverse chronological order
            
        Returns:
            List of filtered LogEntry objects
        """
        with self._lock:
            filtered_logs = []
            
            for log in self._logs:
                # Level filter
                if level_filter and log.level != level_filter.upper():
                    continue
                
                # Source filter (partial match)
                if source_filter and source_filter.lower() not in log.source.lower():
                    continue
                
                # Time filters
                if start_time and log.timestamp < start_time:
                    continue
                if end_time and log.timestamp > end_time:
                    continue
                
                filtered_logs.append(log)
            
            # Sort by timestamp
            if reversed_order:
                filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            else:
                filtered_logs.sort(key=lambda x: x.timestamp)
            
            # Apply limit
            if limit:
                filtered_logs = filtered_logs[:limit]
            
            return filtered_logs

    def get_logs_as_dicts(self, **kwargs) -> List[Dict[str, Any]]:
        """Get logs as dictionaries with filtering options"""
        logs = self.get_logs(**kwargs)
        return [log.to_dict() for log in logs]

    def clear_logs(self) -> int:
        """
        Clear all logs
        
        Returns:
            Number of logs that were cleared
        """
        with self._lock:
            count = len(self._logs)
            self._logs.clear()
            self._next_id = 1
            
            # Reset statistics
            self._stats = {
                'total_logs': 0,
                'logs_by_level': {level: 0 for level in LogLevel.VALID_LEVELS},
                'logs_by_source': {}
            }
            
            # Emit SSE update
            self._emit_sse_update()
            
            return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get log statistics"""
        with self._lock:
            return {
                'current_log_count': len(self._logs),
                'total_logs_processed': self._stats['total_logs'],
                'logs_by_level': self._stats['logs_by_level'].copy(),
                'logs_by_source': self._stats['logs_by_source'].copy(),
                'oldest_log': self._logs[0].timestamp.isoformat() if self._logs else None,
                'newest_log': self._logs[-1].timestamp.isoformat() if self._logs else None
            }

    def get_recent_errors(self, hours: int = 24, limit: int = 100) -> List[LogEntry]:
        """
        Get recent error and critical logs
        
        Args:
            hours: Look back this many hours
            limit: Maximum number of errors to return
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        error_logs = []
        with self._lock:
            for log in reversed(self._logs):
                if log.timestamp < cutoff_time:
                    break
                if log.is_error():
                    error_logs.append(log)
                if len(error_logs) >= limit:
                    break
        
        return error_logs

    # SSE (Server-Sent Events) Support
    def add_sse_client(self) -> queue.Queue:
        """Add a new SSE client and return its queue"""
        client_queue = queue.Queue()
        with self._sse_lock:
            self._sse_clients.append(client_queue)
        return client_queue

    def remove_sse_client(self, client_queue: queue.Queue):
        """Remove an SSE client"""
        with self._sse_lock:
            if client_queue in self._sse_clients:
                self._sse_clients.remove(client_queue)

    def _emit_sse_update(self):
        """Emit log update to all SSE clients"""
        if not self._sse_clients:
            return
        
        data = json.dumps({
            "success": True,
            "count": len(self._logs),
            "logs": [log.to_dict() for log in reversed(self._logs)]
        })
        
        message = f"data: {data}\n\n"
        
        with self._sse_lock:
            # Remove disconnected clients
            active_clients = []
            for client in self._sse_clients:
                try:
                    client.put(message, timeout=1)
                    active_clients.append(client)
                except (queue.Full, Exception):
                    pass  # Client disconnected or queue full
            self._sse_clients[:] = active_clients

    def _update_stats(self, log_entry: LogEntry):
        """Update statistics when a log is added"""
        self._stats['total_logs'] += 1
        self._stats['logs_by_level'][log_entry.level] += 1
        
        if log_entry.source not in self._stats['logs_by_source']:
            self._stats['logs_by_source'][log_entry.source] = 0
        self._stats['logs_by_source'][log_entry.source] += 1

    def _decrement_stats(self, log_entry: LogEntry):
        """Update statistics when a log is removed"""
        self._stats['logs_by_level'][log_entry.level] = max(0, self._stats['logs_by_level'][log_entry.level] - 1)
        
        if log_entry.source in self._stats['logs_by_source']:
            self._stats['logs_by_source'][log_entry.source] = max(0, self._stats['logs_by_source'][log_entry.source] - 1)
            if self._stats['logs_by_source'][log_entry.source] == 0:
                del self._stats['logs_by_source'][log_entry.source]

    # Context manager support for batch operations
    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()

    def __len__(self) -> int:
        """Return the number of logs"""
        return len(self._logs)

    def __iter__(self):
        """Make LogManager iterable"""
        with self._lock:
            return iter(self._logs.copy())

    def search_logs(self, search_term: str, 
                    case_sensitive: bool = False,
                    search_message: bool = True,
                    search_source: bool = True,
                    search_metadata: bool = True,
                    level_filter: Optional[str] = None,
                    limit: Optional[int] = None) -> List[LogEntry]:
        """
        Search logs for text content
        
        Args:
            search_term: Text to search for
            case_sensitive: Whether search should be case sensitive
            search_message: Whether to search in log messages
            search_source: Whether to search in log sources
            search_metadata: Whether to search in log metadata
            level_filter: Filter by log level
            limit: Maximum number of results to return
            
        Returns:
            List of matching LogEntry objects
        """
        if not search_term.strip():
            return []
        
        with self._lock:
            filtered_logs = []
            search_lower = search_term.lower() if not case_sensitive else search_term
            
            for log in self._logs:
                # Level filter
                if level_filter and log.level != level_filter.upper():
                    continue
                
                found = False
                
                # Search in message
                if search_message and log.message:
                    message_text = log.message if case_sensitive else log.message.lower()
                    if search_lower in message_text:
                        found = True
                
                # Search in source
                if not found and search_source and log.source:
                    source_text = log.source if case_sensitive else log.source.lower()
                    if search_lower in source_text:
                        found = True
                
                # Search in metadata
                if not found and search_metadata and log.metadata:
                    metadata_text = str(log.metadata) if case_sensitive else str(log.metadata).lower()
                    if search_lower in metadata_text:
                        found = True
                
                if found:
                    filtered_logs.append(log)
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if limit:
                filtered_logs = filtered_logs[:limit]
            
            return filtered_logs

    def search_logs_as_dicts(self, search_term: str, **kwargs) -> List[Dict[str, Any]]:
        """Search logs and return as dictionaries"""
        logs = self.search_logs(search_term, **kwargs)
        return [log.to_dict() for log in logs] 