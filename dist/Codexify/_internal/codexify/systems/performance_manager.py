"""
Performance Management System

This module provides a unified interface for managing all performance-related
systems in Codexify, including profiling, caching, parallel processing, and optimization.
"""

import os
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .profiler import PerformanceProfiler, start_profiling, end_profiling, get_performance_summary
from .cache import file_cache, analysis_cache, persistent_cache
from .parallel import start_parallel_processors, stop_parallel_processors, get_parallel_processing_stats
from .benchmark import BenchmarkRunner, start_benchmark_suite, end_benchmark_suite
from .memory_optimizer import start_memory_monitoring, stop_memory_monitoring, get_memory_status, optimize_memory

@dataclass
class PerformanceConfig:
    """Configuration for performance management."""
    enable_profiling: bool = True
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    enable_memory_monitoring: bool = True
    enable_benchmarking: bool = True
    
    # Profiling settings
    profiling_interval: float = 5.0
    
    # Caching settings
    cache_max_size_mb: int = 100
    cache_ttl_seconds: int = 3600
    
    # Parallel processing settings
    max_workers: int = None
    
    # Memory monitoring settings
    memory_monitoring_interval: float = 5.0
    memory_warning_threshold_mb: int = 100
    memory_critical_threshold_mb: int = 500

@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    timestamp: datetime
    profiling_summary: Dict[str, Any]
    cache_stats: Dict[str, Any]
    parallel_processing_stats: Dict[str, Any]
    memory_status: Dict[str, Any]
    benchmark_results: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)

class PerformanceManager:
    """
    Main performance management system for Codexify.
    
    Provides a unified interface for all performance-related operations
    and coordinates between different performance systems.
    """
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.is_running = False
        self._lock = threading.Lock()
        
        # Performance systems
        self.profiler = PerformanceProfiler(enabled=self.config.enable_profiling)
        self.benchmark_runner = BenchmarkRunner()
        
        # Performance history
        self.performance_history: List[PerformanceReport] = []
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Auto-optimization settings
        self.auto_optimize = True
        self.optimization_threshold = 0.8  # 80% of warning threshold
    
    def start(self):
        """Start all performance management systems."""
        if self.is_running:
            return
        
        with self._lock:
            try:
                # Start profiling
                if self.config.enable_profiling:
                    start_profiling("performance_session")
                    print("PerformanceManager: Profiling started")
                
                # Start parallel processors
                if self.config.enable_parallel_processing:
                    start_parallel_processors()
                    print("PerformanceManager: Parallel processors started")
                
                # Start memory monitoring
                if self.config.enable_memory_monitoring:
                    start_memory_monitoring(self.config.memory_monitoring_interval)
                    print("PerformanceManager: Memory monitoring started")
                
                self.is_running = True
                print("PerformanceManager: All systems started successfully")
                
            except Exception as e:
                print(f"PerformanceManager: Error starting systems: {e}")
                self.stop()
                raise
    
    def stop(self):
        """Stop all performance management systems."""
        if not self.is_running:
            return
        
        with self._lock:
            try:
                # Stop profiling
                if self.config.enable_profiling:
                    end_profiling()
                
                # Stop parallel processors
                if self.config.enable_parallel_processing:
                    stop_parallel_processors()
                
                # Stop memory monitoring
                if self.config.enable_memory_monitoring:
                    stop_memory_monitoring()
                
                self.is_running = False
                print("PerformanceManager: All systems stopped")
                
            except Exception as e:
                print(f"PerformanceManager: Error stopping systems: {e}")
    
    def run_performance_analysis(self) -> PerformanceReport:
        """Run comprehensive performance analysis."""
        if not self.is_running:
            raise RuntimeError("PerformanceManager is not running")
        
        print("PerformanceManager: Running performance analysis...")
        
        # Collect data from all systems
        profiling_summary = get_performance_summary()
        
        cache_stats = {
            'file_cache_size': len(file_cache.cache),
            'file_cache_memory_mb': file_cache.total_size_bytes / (1024 * 1024),
            'analysis_cache_size': len(analysis_cache.cache),
            'analysis_cache_memory_mb': analysis_cache.total_size_bytes / (1024 * 1024)
        }
        
        parallel_processing_stats = get_parallel_processing_stats()
        memory_status = get_memory_status()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            profiling_summary, cache_stats, parallel_processing_stats, memory_status
        )
        
        # Create performance report
        report = PerformanceReport(
            timestamp=datetime.now(),
            profiling_summary=profiling_summary,
            cache_stats=cache_stats,
            parallel_processing_stats=parallel_processing_stats,
            memory_status=memory_status,
            recommendations=recommendations
        )
        
        # Store in history
        with self._lock:
            self.performance_history.append(report)
            
            # Keep only last 100 reports
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
        
        print(f"PerformanceManager: Analysis complete. Generated {len(recommendations)} recommendations.")
        return report
    
    def run_benchmarks(self, test_directory: str, suite_name: str = "performance_benchmarks") -> Dict[str, Any]:
        """Run performance benchmarks."""
        if not self.config.enable_benchmarking:
            print("PerformanceManager: Benchmarking is disabled")
            return {}
        
        print(f"PerformanceManager: Starting benchmarks for {test_directory}")
        
        try:
            # Start benchmark suite
            start_benchmark_suite(suite_name, f"Performance benchmarks for {test_directory}")
            
            # Run Codexify benchmarks
            from .benchmark import run_codexify_benchmarks
            run_codexify_benchmarks(test_directory)
            
            # End benchmark suite
            suite = end_benchmark_suite()
            
            if suite:
                # Export results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"benchmarks_{suite_name}_{timestamp}.json"
                suite.export_json(export_path)
                
                return {
                    'suite_name': suite.name,
                    'benchmark_count': len(suite.results),
                    'export_path': export_path,
                    'summary': suite.get_summary()
                }
            else:
                return {}
                
        except Exception as e:
            print(f"PerformanceManager: Error running benchmarks: {e}")
            return {}
    
    def optimize_performance(self, force: bool = False) -> Dict[str, Any]:
        """Run performance optimization."""
        if not self.is_running:
            print("PerformanceManager: Cannot optimize - not running")
            return {}
        
        print("PerformanceManager: Running performance optimization...")
        
        optimization_results = {}
        
        try:
            # Memory optimization
            if self.config.enable_memory_monitoring:
                memory_before = get_memory_status()
                optimize_memory()
                memory_after = get_memory_status()
                
                optimization_results['memory'] = {
                    'before_mb': memory_before['current_memory_mb'],
                    'after_mb': memory_after['current_memory_mb'],
                    'improvement_mb': memory_before['current_memory_mb'] - memory_after['current_memory_mb']
                }
            
            # Cache optimization
            if self.config.enable_caching:
                # Clear expired entries
                file_cache._cleanup()
                analysis_cache._cleanup()
                
                optimization_results['cache'] = {
                    'file_cache_entries': len(file_cache.cache),
                    'analysis_cache_entries': len(analysis_cache.cache)
                }
            
            # Force garbage collection
            import gc
            collected = gc.collect()
            optimization_results['garbage_collection'] = {
                'objects_collected': collected
            }
            
            # Record optimization
            optimization_record = {
                'timestamp': datetime.now(),
                'type': 'performance_optimization',
                'results': optimization_results
            }
            
            with self._lock:
                self.optimization_history.append(optimization_record)
            
            print("PerformanceManager: Optimization complete")
            return optimization_results
            
        except Exception as e:
            print(f"PerformanceManager: Error during optimization: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance status."""
        if not self.is_running:
            return {'status': 'not_running'}
        
        try:
            # Get current data
            profiling_summary = get_performance_summary()
            cache_stats = {
                'file_cache_size': len(file_cache.cache),
                'file_cache_memory_mb': file_cache.total_size_bytes / (1024 * 1024),
                'analysis_cache_size': len(analysis_cache.cache),
                'analysis_cache_memory_mb': analysis_cache.total_size_bytes / (1024 * 1024)
            }
            parallel_processing_stats = get_parallel_processing_stats()
            memory_status = get_memory_status()
            
            # Calculate overall performance score
            performance_score = self._calculate_performance_score(
                profiling_summary, cache_stats, parallel_processing_stats, memory_status
            )
            
            return {
                'status': 'running',
                'performance_score': performance_score,
                'profiling': profiling_summary,
                'caching': cache_stats,
                'parallel_processing': parallel_processing_stats,
                'memory': memory_status,
                'last_optimization': self._get_last_optimization_time(),
                'recommendations': self._generate_recommendations(
                    profiling_summary, cache_stats, parallel_processing_stats, memory_status
                )
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def export_performance_report(self, filepath: str) -> bool:
        """Export comprehensive performance report to JSON."""
        try:
            # Get current performance data
            performance_data = self.get_performance_summary()
            
            # Add historical data
            performance_data['history'] = {
                'performance_reports': len(self.performance_history),
                'optimization_history': len(self.optimization_history),
                'last_10_reports': [
                    {
                        'timestamp': report.timestamp.isoformat(),
                        'recommendations_count': len(report.recommendations)
                    }
                    for report in self.performance_history[-10:]
                ]
            }
            
            # Export to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False)
            
            print(f"PerformanceManager: Report exported to {filepath}")
            return True
            
        except Exception as e:
            print(f"PerformanceManager: Error exporting report: {e}")
            return False
    
    def _generate_recommendations(self, profiling_summary: Dict[str, Any],
                                cache_stats: Dict[str, Any],
                                parallel_processing_stats: Dict[str, Any],
                                memory_status: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Memory recommendations
        if memory_status.get('current_memory_mb', 0) > self.config.memory_warning_threshold_mb:
            recommendations.append("High memory usage detected. Consider running memory optimization.")
        
        # Cache recommendations
        if cache_stats.get('file_cache_memory_mb', 0) > self.config.cache_max_size_mb * 0.8:
            recommendations.append("File cache is approaching size limit. Consider clearing old entries.")
        
        if cache_stats.get('analysis_cache_memory_mb', 0) > self.config.cache_max_size_mb * 0.8:
            recommendations.append("Analysis cache is approaching size limit. Consider clearing old entries.")
        
        # Profiling recommendations
        if profiling_summary.get('total_operations', 0) > 1000:
            recommendations.append("High number of profiled operations. Consider reducing profiling granularity.")
        
        # Parallel processing recommendations
        if parallel_processing_stats.get('file_processor', {}).get('active_tasks', 0) > 0:
            recommendations.append("File processing tasks are active. Monitor for completion.")
        
        return recommendations
    
    def _calculate_performance_score(self, profiling_summary: Dict[str, Any],
                                   cache_stats: Dict[str, Any],
                                   parallel_processing_stats: Dict[str, Any],
                                   memory_status: Dict[str, Any]) -> float:
        """Calculate overall performance score (0.0 to 1.0)."""
        score = 1.0
        
        # Memory score (lower is better)
        memory_mb = memory_status.get('current_memory_mb', 0)
        if memory_mb > self.config.memory_critical_threshold_mb:
            score *= 0.3
        elif memory_mb > self.config.memory_warning_threshold_mb:
            score *= 0.7
        
        # Cache efficiency score
        cache_efficiency = min(
            cache_stats.get('file_cache_memory_mb', 0) / self.config.cache_max_size_mb,
            cache_stats.get('analysis_cache_memory_mb', 0) / self.config.cache_max_size_mb
        )
        if cache_efficiency > 0.8:
            score *= 0.8
        
        # Profiling overhead score
        if profiling_summary.get('total_operations', 0) > 1000:
            score *= 0.9
        
        return max(0.0, min(1.0, score))
    
    def _get_last_optimization_time(self) -> Optional[str]:
        """Get the timestamp of the last optimization."""
        if not self.optimization_history:
            return None
        
        last_optimization = self.optimization_history[-1]
        return last_optimization['timestamp'].isoformat()
    
    def auto_optimize_if_needed(self):
        """Automatically optimize performance if thresholds are exceeded."""
        if not self.auto_optimize or not self.is_running:
            return
        
        try:
            memory_status = get_memory_status()
            current_memory_mb = memory_status.get('current_memory_mb', 0)
            
            # Check if memory usage is approaching warning threshold
            if current_memory_mb > (self.config.memory_warning_threshold_mb * self.optimization_threshold):
                print("PerformanceManager: Auto-optimization triggered due to high memory usage")
                self.optimize_performance()
                
        except Exception as e:
            print(f"PerformanceManager: Error in auto-optimization: {e}")

# Global performance manager instance
performance_manager = PerformanceManager()

# Convenience functions
def start_performance_management(config: PerformanceConfig = None):
    """Start performance management using the global manager."""
    if config:
        performance_manager.config = config
    performance_manager.start()

def stop_performance_management():
    """Stop performance management using the global manager."""
    performance_manager.stop()

def run_performance_analysis() -> PerformanceReport:
    """Run performance analysis using the global manager."""
    return performance_manager.run_performance_analysis()

def optimize_performance(force: bool = False) -> Dict[str, Any]:
    """Optimize performance using the global manager."""
    return performance_manager.optimize_performance(force)

def get_performance_status() -> Dict[str, Any]:
    """Get performance status using the global manager."""
    return performance_manager.get_performance_summary()

def run_performance_benchmarks(test_directory: str, suite_name: str = "performance_benchmarks") -> Dict[str, Any]:
    """Run performance benchmarks using the global manager."""
    return performance_manager.run_benchmarks(test_directory, suite_name)
