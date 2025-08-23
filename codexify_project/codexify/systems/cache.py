"""
Intelligent Caching System

This module provides intelligent caching capabilities for Codexify,
including file content caching, analysis result caching, and duplicate detection caching.
"""

import os
import hashlib
import json
import pickle
import time
import threading
from typing import Dict, Any, Optional, Set, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import tempfile
import shutil

@dataclass
class CacheEntry:
    """Represents a single cache entry."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if the cache entry has expired."""
        return (datetime.now() - self.created_at).total_seconds() > ttl_seconds
    
    def update_access(self):
        """Update access statistics."""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def get_age_seconds(self) -> float:
        """Get the age of the cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

class CachePolicy:
    """Defines caching policies and strategies."""
    
    def __init__(self, 
                 max_size_mb: int = 100,
                 max_entries: int = 1000,
                 default_ttl_seconds: int = 3600,
                 cleanup_interval_seconds: int = 300):
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds

class FileContentCache:
    """Caches file content to avoid repeated file I/O operations."""
    
    def __init__(self, policy: CachePolicy = None):
        self.policy = policy or CachePolicy()
        self.cache: Dict[str, CacheEntry] = {}
        self.total_size_bytes = 0
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        
        # File modification time tracking
        self.file_mtimes: Dict[str, float] = {}
    
    def get(self, file_path: str) -> Optional[str]:
        """Get cached file content if valid."""
        if not os.path.exists(file_path):
            return None
        
        cache_key = self._get_cache_key(file_path)
        
        with self._lock:
            # Check if file has been modified
            current_mtime = os.path.getmtime(file_path)
            if (cache_key in self.file_mtimes and 
                self.file_mtimes[cache_key] != current_mtime):
                # File modified, invalidate cache
                self._remove_entry(cache_key)
                return None
            
            entry = self.cache.get(cache_key)
            if entry is None:
                return None
            
            # Check expiration
            if entry.is_expired(self.policy.default_ttl_seconds):
                self._remove_entry(cache_key)
                return None
            
            # Update access statistics
            entry.update_access()
            return entry.value
    
    def put(self, file_path: str, content: str) -> bool:
        """Cache file content."""
        cache_key = self._get_cache_key(file_path)
        content_size = len(content.encode('utf-8'))
        
        with self._lock:
            # Check if we need to make space
            if (self.total_size_bytes + content_size > self.policy.max_size_bytes or
                len(self.cache) >= self.policy.max_entries):
                self._cleanup()
            
            # Still no space after cleanup
            if (self.total_size_bytes + content_size > self.policy.max_size_bytes or
                len(self.cache) >= self.policy.max_entries):
                return False
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=content,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                size_bytes=content_size,
                metadata={'file_path': file_path}
            )
            
            # Store entry
            self.cache[cache_key] = entry
            self.total_size_bytes += content_size
            
            # Track file modification time
            try:
                self.file_mtimes[cache_key] = os.path.getmtime(file_path)
            except OSError:
                pass
            
            return True
    
    def invalidate(self, file_path: str) -> bool:
        """Invalidate cache for a specific file."""
        cache_key = self._get_cache_key(file_path)
        with self._lock:
            return self._remove_entry(cache_key)
    
    def clear(self):
        """Clear all cached content."""
        with self._lock:
            self.cache.clear()
            self.file_mtimes.clear()
            self.total_size_bytes = 0
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for file path."""
        return hashlib.md5(file_path.encode('utf-8')).hexdigest()
    
    def _remove_entry(self, cache_key: str) -> bool:
        """Remove a cache entry."""
        if cache_key not in self.cache:
            return False
        
        entry = self.cache[cache_key]
        self.total_size_bytes -= entry.size_bytes
        del self.cache[cache_key]
        
        if cache_key in self.file_mtimes:
            del self.file_mtimes[cache_key]
        
        return True
    
    def _cleanup(self):
        """Clean up expired and least used entries."""
        current_time = time.time()
        
        # Remove expired entries first
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired(self.policy.default_ttl_seconds)
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        # If still over limit, remove least recently used
        if (self.total_size_bytes > self.policy.max_size_bytes or
            len(self.cache) > self.policy.max_entries):
            
            # Sort by access time and remove oldest
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].accessed_at
            )
            
            while (self.total_size_bytes > self.policy.max_size_bytes or
                   len(self.cache) > self.policy.max_entries):
                if not sorted_entries:
                    break
                
                key, _ = sorted_entries.pop(0)
                self._remove_entry(key)
        
        self._last_cleanup = current_time

class AnalysisResultCache:
    """Caches analysis results to avoid re-computation."""
    
    def __init__(self, policy: CachePolicy = None):
        self.policy = policy or CachePolicy()
        self.cache: Dict[str, CacheEntry] = {}
        self.total_size_bytes = 0
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        with self._lock:
            entry = self.cache.get(cache_key)
            if entry is None:
                return None
            
            # Check expiration
            if entry.is_expired(self.policy.default_ttl_seconds):
                self._remove_entry(cache_key)
                return None
            
            # Update access statistics
            entry.update_access()
            return entry.value
    
    def put(self, cache_key: str, result: Dict[str, Any]) -> bool:
        """Cache analysis result."""
        # Estimate size (rough approximation)
        result_size = len(json.dumps(result, default=str).encode('utf-8'))
        
        with self._lock:
            # Check if we need to make space
            if (self.total_size_bytes + result_size > self.policy.max_size_bytes or
                len(self.cache) >= self.policy.max_entries):
                self._cleanup()
            
            # Still no space after cleanup
            if (self.total_size_bytes + result_size > self.policy.max_size_bytes or
                len(self.cache) >= self.policy.max_entries):
                return False
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=result,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                size_bytes=result_size,
                metadata={'type': 'analysis_result'}
            )
            
            # Store entry
            self.cache[cache_key] = entry
            self.total_size_bytes += result_size
            return True
    
    def generate_key(self, file_paths: Set[str], analysis_type: str, 
                    parameters: Dict[str, Any] = None) -> str:
        """Generate cache key for analysis parameters."""
        # Sort file paths for consistent key generation
        sorted_paths = sorted(file_paths)
        
        # Create parameter string
        param_str = ""
        if parameters:
            sorted_params = sorted(parameters.items())
            param_str = json.dumps(sorted_params, sort_keys=True)
        
        # Combine all components
        key_data = f"{analysis_type}:{len(sorted_paths)}:{param_str}:{sorted_paths}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
    
    def invalidate(self, cache_key: str) -> bool:
        """Invalidate specific cache entry."""
        with self._lock:
            return self._remove_entry(cache_key)
    
    def clear(self):
        """Clear all cached results."""
        with self._lock:
            self.cache.clear()
            self.total_size_bytes = 0
    
    def _remove_entry(self, cache_key: str) -> bool:
        """Remove a cache entry."""
        if cache_key not in self.cache:
            return False
        
        entry = self.cache[cache_key]
        self.total_size_bytes -= entry.size_bytes
        del self.cache[cache_key]
        return True
    
    def _cleanup(self):
        """Clean up expired and least used entries."""
        current_time = time.time()
        
        # Remove expired entries first
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired(self.policy.default_ttl_seconds)
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        # If still over limit, remove least recently used
        if (self.total_size_bytes > self.policy.max_size_bytes or
            len(self.cache) > self.policy.max_entries):
            
            # Sort by access time and remove oldest
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].accessed_at
            )
            
            while (self.total_size_bytes > self.policy.max_size_bytes or
                   len(self.cache) > self.policy.max_entries):
                if not sorted_entries:
                    break
                
                key, _ = sorted_entries.pop(0)
                self._remove_entry(key)
        
        self._last_cleanup = current_time

class PersistentCache:
    """Persistent cache that survives application restarts."""
    
    def __init__(self, cache_dir: str = None, policy: CachePolicy = None):
        self.policy = policy or CachePolicy()
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self._ensure_cache_dir()
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Load existing cache data
        self._load_cache()
    
    def _get_default_cache_dir(self) -> str:
        """Get default cache directory."""
        cache_dir = os.path.join(tempfile.gettempdir(), 'codexify_cache')
        return cache_dir
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get file path for cache entry."""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Get cached value."""
        # Check memory cache first
        with self._lock:
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired(self.policy.default_ttl_seconds):
                    entry.update_access()
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
        
        # Check persistent cache
        cache_file = self._get_cache_file_path(cache_key)
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                entry_data = pickle.load(f)
            
            # Check expiration
            if entry_data.is_expired(self.policy.default_ttl_seconds):
                os.remove(cache_file)
                return None
            
            # Update access and add to memory cache
            entry_data.update_access()
            
            with self._lock:
                self.memory_cache[cache_key] = entry_data
                
                # Limit memory cache size
                if len(self.memory_cache) > self.policy.max_entries // 10:
                    self._cleanup_memory_cache()
            
            return entry_data.value
            
        except Exception as e:
            print(f"Cache: Error loading cache entry {cache_key}: {e}")
            return None
    
    def put(self, cache_key: str, value: Any, metadata: Dict[str, Any] = None) -> bool:
        """Cache a value."""
        try:
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # Save to persistent storage
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
            
            # Add to memory cache
            with self._lock:
                self.memory_cache[cache_key] = entry
                
                # Limit memory cache size
                if len(self.memory_cache) > self.policy.max_entries // 10:
                    self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            print(f"Cache: Error saving cache entry {cache_key}: {e}")
            return False
    
    def clear(self):
        """Clear all cached data."""
        with self._lock:
            self.memory_cache.clear()
        
        # Remove all cache files
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            print(f"Cache: Error clearing cache files: {e}")
    
    def _load_cache(self):
        """Load existing cache data into memory."""
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.cache'):
                    continue
                
                cache_file = os.path.join(self.cache_dir, filename)
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    # Only load non-expired entries
                    if not entry.is_expired(self.policy.default_ttl_seconds):
                        cache_key = filename[:-6]  # Remove .cache extension
                        self.memory_cache[cache_key] = entry
                        
                        # Limit memory cache size
                        if len(self.memory_cache) > self.policy.max_entries // 10:
                            break
                            
                except Exception:
                    # Remove corrupted cache file
                    try:
                        os.remove(cache_file)
                    except OSError:
                        pass
                        
        except Exception as e:
            print(f"Cache: Error loading cache: {e}")
    
    def _cleanup_memory_cache(self):
        """Clean up memory cache."""
        if len(self.memory_cache) <= self.policy.max_entries // 20:
            return
        
        # Remove least recently used entries
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].accessed_at
        )
        
        entries_to_remove = len(sorted_entries) - (self.policy.max_entries // 20)
        for i in range(entries_to_remove):
            if i < len(sorted_entries):
                key, _ = sorted_entries[i]
                del self.memory_cache[key]

# Global cache instances
file_cache = FileContentCache()
analysis_cache = AnalysisResultCache()
persistent_cache = PersistentCache()

# Convenience functions
def cache_file_content(file_path: str, content: str) -> bool:
    """Cache file content using the global file cache."""
    return file_cache.put(file_path, content)

def get_cached_file_content(file_path: str) -> Optional[str]:
    """Get cached file content using the global file cache."""
    return file_cache.get(file_path)

def cache_analysis_result(cache_key: str, result: Dict[str, Any]) -> bool:
    """Cache analysis result using the global analysis cache."""
    return analysis_cache.put(cache_key, result)

def get_cached_analysis_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached analysis result using the global analysis cache."""
    return analysis_cache.get(cache_key)

def generate_analysis_cache_key(file_paths: Set[str], analysis_type: str, 
                              parameters: Dict[str, Any] = None) -> str:
    """Generate cache key for analysis parameters."""
    return analysis_cache.generate_key(file_paths, analysis_type, parameters)
