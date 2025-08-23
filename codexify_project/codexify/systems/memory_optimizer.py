"""
Memory Optimization System

This module provides memory optimization capabilities for Codexify,
including memory monitoring, garbage collection optimization, and memory-efficient data structures.
"""

import gc
import sys
import psutil
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import weakref
import tracemalloc

@dataclass
class MemorySnapshot:
    """Represents a memory usage snapshot."""
    timestamp: datetime
    memory_usage: int
    memory_percent: float
    gc_stats: Dict[str, Any]
    tracemalloc_stats: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tracemalloc_stats is None:
            self.tracemalloc_stats = {}

@dataclass
class MemoryLeak:
    """Represents a potential memory leak."""
    location: str
    size_increase: int
    time_period: float
    severity: str  # 'low', 'medium', 'high'
    description: str
    recommendations: List[str] = field(default_factory=list)

class MemoryMonitor:
    """Monitors memory usage and provides insights."""
    
    def __init__(self, enable_tracemalloc: bool = False):
        self.enable_tracemalloc = enable_tracemalloc
        self.snapshots: List[MemorySnapshot] = []
        self.monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Memory thresholds
        self.warning_threshold_mb = 100  # 100MB
        self.critical_threshold_mb = 500  # 500MB
        
        if self.enable_tracemalloc:
            tracemalloc.start()
    
    def start_monitoring(self, interval_seconds: float = 5.0):
        """Start continuous memory monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        print("MemoryMonitor: Started monitoring")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        
        print("MemoryMonitor: Stopped monitoring")
    
    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory usage snapshot."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get GC statistics
        gc_stats = {
            'collections': gc.get_stats(),
            'counts': gc.get_count(),
            'thresholds': gc.get_threshold()
        }
        
        # Get tracemalloc statistics if enabled
        tracemalloc_stats = {}
        if self.enable_tracemalloc and tracemalloc.is_tracing():
            try:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc_stats = {
                    'current': current,
                    'peak': peak,
                    'limit': tracemalloc.get_traceback_limit()
                }
            except Exception:
                pass
        
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            memory_usage=memory_info.rss,
            memory_percent=process.memory_percent(),
            gc_stats=gc_stats,
            tracemalloc_stats=tracemalloc_stats
        )
        
        with self._lock:
            self.snapshots.append(snapshot)
        
        return snapshot
    
    def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                snapshot = self.take_snapshot()
                
                # Check thresholds
                memory_mb = snapshot.memory_usage / (1024 * 1024)
                if memory_mb > self.critical_threshold_mb:
                    print(f"MemoryMonitor: CRITICAL - Memory usage: {memory_mb:.1f}MB")
                elif memory_mb > self.warning_threshold_mb:
                    print(f"MemoryMonitor: WARNING - Memory usage: {memory_mb:.1f}MB")
                
                # Wait for next interval
                self._stop_event.wait(interval_seconds)
                
            except Exception as e:
                print(f"MemoryMonitor: Error in monitoring loop: {e}")
                time.sleep(1.0)
    
    def get_memory_trend(self, minutes: int = 10) -> Dict[str, Any]:
        """Get memory usage trend over the specified time period."""
        if not self.snapshots:
            return {}
        
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        recent_snapshots = [
            s for s in self.snapshots
            if s.timestamp.timestamp() > cutoff_time
        ]
        
        if not recent_snapshots:
            return {}
        
        memory_values = [s.memory_usage for s in recent_snapshots]
        timestamps = [s.timestamp.timestamp() for s in recent_snapshots]
        
        # Calculate trend
        if len(memory_values) > 1:
            # Simple linear regression
            n = len(memory_values)
            sum_x = sum(timestamps)
            sum_y = sum(memory_values)
            sum_xy = sum(timestamps[i] * memory_values[i] for i in range(n))
            sum_x2 = sum(timestamps[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        else:
            trend = "stable"
            slope = 0
        
        return {
            'trend': trend,
            'slope': slope,
            'min_memory': min(memory_values),
            'max_memory': max(memory_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'snapshot_count': len(recent_snapshots),
            'time_period_minutes': minutes
        }
    
    def detect_memory_leaks(self) -> List[MemoryLeak]:
        """Detect potential memory leaks based on snapshots."""
        if len(self.snapshots) < 2:
            return []
        
        leaks = []
        
        # Analyze memory growth patterns
        for i in range(1, len(self.snapshots)):
            prev_snapshot = self.snapshots[i - 1]
            curr_snapshot = self.snapshots[i]
            
            memory_increase = curr_snapshot.memory_usage - prev_snapshot.memory_usage
            time_diff = (curr_snapshot.timestamp - prev_snapshot.timestamp).total_seconds()
            
            # Check for significant memory increase
            if memory_increase > 10 * 1024 * 1024:  # 10MB threshold
                severity = "high" if memory_increase > 50 * 1024 * 1024 else "medium"
                
                leak = MemoryLeak(
                    location=f"Snapshot {i-1} to {i}",
                    size_increase=memory_increase,
                    time_period=time_diff,
                    severity=severity,
                    description=f"Memory increased by {memory_increase / (1024*1024):.1f}MB in {time_diff:.1f}s",
                    recommendations=[
                        "Check for unclosed file handles",
                        "Review object lifecycle management",
                        "Consider using weak references for large objects"
                    ]
                )
                leaks.append(leak)
        
        return leaks
    
    def get_recommendations(self) -> List[str]:
        """Get memory optimization recommendations."""
        recommendations = []
        
        if not self.snapshots:
            return recommendations
        
        current_memory = self.snapshots[-1].memory_usage
        memory_mb = current_memory / (1024 * 1024)
        
        # Memory usage recommendations
        if memory_mb > self.critical_threshold_mb:
            recommendations.append("CRITICAL: Memory usage is very high. Consider restarting the application.")
        
        if memory_mb > self.warning_threshold_mb:
            recommendations.append("WARNING: Memory usage is high. Review memory-intensive operations.")
        
        # GC recommendations
        gc_stats = self.snapshots[-1].gc_stats
        if gc_stats.get('collections'):
            collections = gc_stats['collections']
            if collections:
                last_collection = collections[-1]
                if last_collection.get('collections', 0) > 100:
                    recommendations.append("High garbage collection activity. Consider manual GC calls.")
        
        # Trend-based recommendations
        trend = self.get_memory_trend()
        if trend.get('trend') == 'increasing':
            recommendations.append("Memory usage is increasing over time. Check for memory leaks.")
        
        return recommendations

class MemoryOptimizer:
    """Provides memory optimization utilities."""
    
    def __init__(self):
        self.monitor = MemoryMonitor()
        self.optimization_history: List[Dict[str, Any]] = []
    
    def optimize_garbage_collection(self):
        """Optimize garbage collection settings."""
        # Get current GC thresholds
        old_thresholds = gc.get_threshold()
        
        # Set more aggressive thresholds for memory optimization
        new_thresholds = (700, 10, 10)  # (threshold0, threshold1, threshold2)
        gc.set_threshold(*new_thresholds)
        
        # Force garbage collection
        collected = gc.collect()
        
        optimization_record = {
            'timestamp': datetime.now(),
            'type': 'gc_optimization',
            'old_thresholds': old_thresholds,
            'new_thresholds': new_thresholds,
            'objects_collected': collected
        }
        
        self.optimization_history.append(optimization_record)
        
        print(f"MemoryOptimizer: GC optimized, collected {collected} objects")
        return collected
    
    def clear_memory_caches(self):
        """Clear various memory caches."""
        from codexify.systems.cache import file_cache, analysis_cache
        
        # Clear caches
        file_cache.clear()
        analysis_cache.clear()
        
        # Force garbage collection
        collected = gc.collect()
        
        optimization_record = {
            'timestamp': datetime.now(),
            'type': 'cache_clear',
            'objects_collected': collected
        }
        
        self.optimization_history.append(optimization_record)
        
        print(f"MemoryOptimizer: Caches cleared, collected {collected} objects")
        return collected
    
    def optimize_data_structures(self, data: Any) -> Any:
        """Optimize data structures for memory efficiency."""
        if isinstance(data, list):
            # Convert to tuple if list is not modified
            return tuple(data)
        elif isinstance(data, dict):
            # Use dict() constructor for better memory layout
            return dict(data)
        elif isinstance(data, set):
            # Use frozenset if set is not modified
            return frozenset(data)
        else:
            return data
    
    def create_memory_efficient_list(self, items: List[Any]) -> List[Any]:
        """Create a memory-efficient list."""
        # Pre-allocate list size if known
        if hasattr(items, '__len__'):
            result = [None] * len(items)
            for i, item in enumerate(items):
                result[i] = item
            return result
        else:
            return list(items)
    
    def create_memory_efficient_dict(self, items: Dict[str, Any]) -> Dict[str, Any]:
        """Create a memory-efficient dictionary."""
        # Use dict() constructor for better memory layout
        return dict(items)
    
    def monitor_memory_usage(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Monitor memory usage during function execution."""
        # Take snapshot before
        snapshot_before = self.monitor.take_snapshot()
        
        # Execute function
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Take snapshot after
        snapshot_after = self.monitor.take_snapshot()
        
        # Calculate memory impact
        memory_delta = snapshot_after.memory_usage - snapshot_before.memory_usage
        
        return {
            'result': result,
            'execution_time': execution_time,
            'memory_before': snapshot_before.memory_usage,
            'memory_after': snapshot_after.memory_usage,
            'memory_delta': memory_delta,
            'memory_efficient': memory_delta < 1024 * 1024  # 1MB threshold
        }
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization activities."""
        if not self.optimization_history:
            return {}
        
        summary = {
            'total_optimizations': len(self.optimization_history),
            'gc_optimizations': len([o for o in self.optimization_history if o['type'] == 'gc_optimization']),
            'cache_clears': len([o for o in self.optimization_history if o['type'] == 'cache_clear']),
            'total_objects_collected': sum(o.get('objects_collected', 0) for o in self.optimization_history),
            'last_optimization': self.optimization_history[-1]['timestamp'] if self.optimization_history else None
        }
        
        return summary

class WeakReferenceManager:
    """Manages weak references to prevent memory leaks."""
    
    def __init__(self):
        self._weak_refs: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()
    
    def add_reference(self, key: str, obj: Any):
        """Add a weak reference to an object."""
        with self._lock:
            self._weak_refs[key] = weakref.ref(obj, lambda ref: self._on_object_finalized(key))
    
    def get_reference(self, key: str) -> Optional[Any]:
        """Get the referenced object if it still exists."""
        with self._lock:
            weak_ref = self._weak_refs.get(key)
            if weak_ref:
                obj = weak_ref()
                if obj is None:
                    # Object has been garbage collected
                    del self._weak_refs[key]
                return obj
        return None
    
    def remove_reference(self, key: str):
        """Remove a weak reference."""
        with self._lock:
            if key in self._weak_refs:
                del self._weak_refs[key]
    
    def _on_object_finalized(self, key: str):
        """Called when a referenced object is finalized."""
        with self._lock:
            if key in self._weak_refs:
                del self._weak_refs[key]
    
    def cleanup_dead_references(self):
        """Remove references to dead objects."""
        with self._lock:
            dead_keys = []
            for key, weak_ref in self._weak_refs.items():
                if weak_ref() is None:
                    dead_keys.append(key)
            
            for key in dead_keys:
                del self._weak_refs[key]
        
        return len(dead_keys)

# Global instances
memory_monitor = MemoryMonitor()
memory_optimizer = MemoryOptimizer()
weak_ref_manager = WeakReferenceManager()

# Convenience functions
def start_memory_monitoring(interval_seconds: float = 5.0):
    """Start memory monitoring using the global monitor."""
    memory_monitor.start_monitoring(interval_seconds)

def stop_memory_monitoring():
    """Stop memory monitoring using the global monitor."""
    memory_monitor.stop_monitoring()

def take_memory_snapshot() -> MemorySnapshot:
    """Take a memory snapshot using the global monitor."""
    return memory_monitor.take_snapshot()

def optimize_memory():
    """Run memory optimization using the global optimizer."""
    memory_optimizer.optimize_garbage_collection()
    memory_optimizer.clear_memory_caches()

def get_memory_status() -> Dict[str, Any]:
    """Get current memory status."""
    snapshot = memory_monitor.take_snapshot()
    trend = memory_monitor.get_memory_trend()
    recommendations = memory_monitor.get_recommendations()
    optimization_summary = memory_optimizer.get_optimization_summary()
    
    return {
        'current_memory_mb': snapshot.memory_usage / (1024 * 1024),
        'memory_percent': snapshot.memory_percent,
        'trend': trend,
        'recommendations': recommendations,
        'optimization_summary': optimization_summary
    }
