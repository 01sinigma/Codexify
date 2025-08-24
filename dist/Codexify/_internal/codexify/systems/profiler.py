"""
Performance Profiling System

This module provides comprehensive performance profiling capabilities for Codexify,
including execution time measurement, memory usage tracking, and bottleneck identification.
"""

import time
import cProfile
import pstats
import io
import psutil
import os
import threading
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime
import json
import gc

@dataclass
class PerformanceMetric:
    """Represents a single performance measurement."""
    operation: str
    duration: float
    memory_before: int
    memory_after: int
    memory_delta: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""
    session_id: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    operations: List[PerformanceMetric] = field(default_factory=list)
    memory_peak: int = 0
    memory_final: int = 0
    gc_stats: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration': self.total_duration,
            'operations': [
                {
                    'operation': op.operation,
                    'duration': op.duration,
                    'memory_before': op.memory_before,
                    'memory_after': op.memory_after,
                    'memory_delta': op.memory_delta,
                    'timestamp': op.timestamp.isoformat(),
                    'metadata': op.metadata
                }
                for op in self.operations
            ],
            'memory_peak': self.memory_peak,
            'memory_final': self.memory_final,
            'gc_stats': self.gc_stats,
            'system_info': self.system_info
        }

class PerformanceProfiler:
    """
    Main performance profiling system for Codexify.
    
    Provides decorators, context managers, and manual profiling methods
    for comprehensive performance analysis.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.current_session: Optional[PerformanceReport] = None
        self.operation_stack: List[str] = []
        self._lock = threading.Lock()
        
        # Performance tracking
        self.metrics: List[PerformanceMetric] = []
        self.start_time: Optional[datetime] = None
        self.memory_start: int = 0
        
        # System information
        self.system_info = self._gather_system_info()
    
    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for profiling context."""
        try:
            process = psutil.Process()
            return {
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'platform': os.name,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'process_id': process.pid,
                'process_name': process.name(),
                'process_memory': process.memory_info().rss
            }
        except Exception as e:
            return {'error': str(e)}
    
    def start_session(self, session_id: str = None) -> str:
        """Start a new profiling session."""
        if not self.enabled:
            return ""
            
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        with self._lock:
            self.current_session = PerformanceReport(
                session_id=session_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                total_duration=0.0,
                system_info=self.system_info
            )
            self.start_time = datetime.now()
            self.memory_start = self._get_memory_usage()
            self.operation_stack.clear()
            self.metrics.clear()
            
            print(f"Profiler: Started session '{session_id}'")
            return session_id
    
    def end_session(self) -> Optional[PerformanceReport]:
        """End the current profiling session and return the report."""
        if not self.enabled or not self.current_session:
            return None
        
        with self._lock:
            end_time = datetime.now()
            memory_final = self._get_memory_usage()
            
            self.current_session.end_time = end_time
            self.current_session.total_duration = (end_time - self.start_time).total_seconds()
            self.current_session.memory_final = memory_final
            self.current_session.operations = self.metrics.copy()
            self.current_session.memory_peak = max(
                [m.memory_after for m in self.metrics] + [memory_final]
            )
            
            # Gather garbage collection statistics
            self.current_session.gc_stats = self._get_gc_stats()
            
            report = self.current_session
            self.current_session = None
            self.start_time = None
            self.memory_start = 0
            
            print(f"Profiler: Session '{report.session_id}' completed in {report.total_duration:.2f}s")
            return report
    
    def profile_operation(self, operation_name: str):
        """Decorator to profile a function or method."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                return self._profile_callable(func, operation_name, args, kwargs)
            
            return wrapper
        return decorator
    
    def _profile_callable(self, func: Callable, operation_name: str, args: tuple, kwargs: dict) -> Any:
        """Profile a callable function."""
        memory_before = self._get_memory_usage()
        start_time = time.time()
        
        try:
            # Track operation in stack
            self.operation_stack.append(operation_name)
            
            # Execute the function
            result = func(*args, **kwargs)
            
            return result
        finally:
            # Always record metrics, even if exception occurs
            duration = time.time() - start_time
            memory_after = self._get_memory_usage()
            
            metric = PerformanceMetric(
                operation=operation_name,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - memory_before,
                metadata={
                    'args_count': len(args),
                    'kwargs_count': len(kwargs),
                    'operation_stack': self.operation_stack.copy()
                }
            )
            
            with self._lock:
                self.metrics.append(metric)
            
            # Remove from operation stack
            if self.operation_stack and self.operation_stack[-1] == operation_name:
                self.operation_stack.pop()
    
    def profile_context(self, operation_name: str):
        """Context manager for profiling code blocks."""
        return PerformanceContext(self, operation_name)
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            return 0
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Get garbage collection statistics."""
        try:
            return {
                'collections': gc.get_stats(),
                'counts': gc.get_count(),
                'thresholds': gc.get_threshold()
            }
        except Exception:
            return {}
    
    def get_current_metrics(self) -> List[PerformanceMetric]:
        """Get metrics from the current session."""
        with self._lock:
            return self.metrics.copy()
    
    def export_report(self, filepath: str, format_type: str = "json") -> bool:
        """Export the current session report to a file."""
        if not self.current_session:
            return False
        
        try:
            if format_type.lower() == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
            else:
                # Default to JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"Profiler: Report exported to {filepath}")
            return True
        except Exception as e:
            print(f"Profiler: Error exporting report: {e}")
            return False
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics."""
        if not self.metrics:
            return {}
        
        total_duration = sum(m.duration for m in self.metrics)
        total_memory_delta = sum(m.memory_delta for m in self.metrics)
        
        # Group by operation
        operation_stats = {}
        for metric in self.metrics:
            op = metric.operation
            if op not in operation_stats:
                operation_stats[op] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'avg_duration': 0.0,
                    'total_memory_delta': 0,
                    'avg_memory_delta': 0.0
                }
            
            stats = operation_stats[op]
            stats['count'] += 1
            stats['total_duration'] += metric.duration
            stats['total_memory_delta'] += metric.memory_delta
        
        # Calculate averages
        for op_stats in operation_stats.values():
            op_stats['avg_duration'] = op_stats['total_duration'] / op_stats['count']
            op_stats['avg_memory_delta'] = op_stats['total_memory_delta'] / op_stats['count']
        
        return {
            'total_operations': len(self.metrics),
            'total_duration': total_duration,
            'total_memory_delta': total_memory_delta,
            'operation_stats': operation_stats,
            'memory_usage': {
                'start': self.memory_start,
                'current': self._get_memory_usage(),
                'peak': max([m.memory_after for m in self.metrics] + [self._get_memory_usage()])
            }
        }

class PerformanceContext:
    """Context manager for profiling code blocks."""
    
    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name
        self.memory_before = 0
        self.start_time = 0
    
    def __enter__(self):
        if self.profiler.enabled:
            self.memory_before = self.profiler._get_memory_usage()
            self.start_time = time.time()
            self.profiler.operation_stack.append(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler.enabled:
            duration = time.time() - self.start_time
            memory_after = self.profiler._get_memory_usage()
            
            metric = PerformanceMetric(
                operation=self.operation_name,
                duration=duration,
                memory_before=self.memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - self.memory_before,
                metadata={
                    'context_manager': True,
                    'operation_stack': self.profiler.operation_stack.copy()
                }
            )
            
            with self.profiler._lock:
                self.profiler.metrics.append(metric)
            
            # Remove from operation stack
            if (self.profiler.operation_stack and 
                self.profiler.operation_stack[-1] == self.operation_name):
                self.profiler.operation_stack.pop()

# Global profiler instance
profiler = PerformanceProfiler()

# Convenience functions
def profile_operation(operation_name: str):
    """Decorator to profile a function using the global profiler."""
    return profiler.profile_operation(operation_name)

def profile_context(operation_name: str):
    """Context manager for profiling code blocks using the global profiler."""
    return profiler.profile_context(operation_name)

def start_profiling(session_id: str = None) -> str:
    """Start profiling session using the global profiler."""
    return profiler.start_session(session_id)

def end_profiling() -> Optional[PerformanceReport]:
    """End profiling session using the global profiler."""
    return profiler.end_session()

def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary from the global profiler."""
    return profiler.get_performance_summary()
