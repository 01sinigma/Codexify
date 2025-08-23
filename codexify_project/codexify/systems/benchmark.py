"""
Performance Benchmarking System

This module provides comprehensive benchmarking capabilities for Codexify,
including performance tests, comparison tools, and optimization recommendations.
"""

import time
import statistics
import json
import os
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import psutil
import gc

@dataclass
class BenchmarkResult:
    """Represents the result of a single benchmark run."""
    name: str
    duration: float
    memory_before: int
    memory_after: int
    memory_delta: int
    iterations: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_per_iteration(self) -> float:
        """Get average duration per iteration."""
        return self.duration / self.iterations if self.iterations > 0 else 0.0
    
    @property
    def memory_per_iteration(self) -> float:
        """Get average memory usage per iteration."""
        return self.memory_delta / self.iterations if self.iterations > 0 else 0.0

@dataclass
class BenchmarkSuite:
    """Represents a collection of benchmark results."""
    name: str
    description: str
    results: List[BenchmarkResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: BenchmarkResult):
        """Add a benchmark result to the suite."""
        self.results.append(result)
    
    def get_result(self, name: str) -> Optional[BenchmarkResult]:
        """Get a specific benchmark result by name."""
        for result in self.results:
            if result.name == name:
                return result
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all benchmark results."""
        if not self.results:
            return {}
        
        summary = {
            'total_benchmarks': len(self.results),
            'total_duration': sum(r.duration for r in self.results),
            'total_memory_delta': sum(r.memory_delta for r in self.results),
            'benchmarks': {}
        }
        
        for result in self.results:
            summary['benchmarks'][result.name] = {
                'duration': result.duration,
                'duration_per_iteration': result.duration_per_iteration,
                'memory_delta': result.memory_delta,
                'memory_per_iteration': result.memory_per_iteration,
                'iterations': result.iterations
            }
        
        return summary
    
    def export_json(self, filepath: str) -> bool:
        """Export benchmark suite to JSON file."""
        try:
            data = {
                'name': self.name,
                'description': self.description,
                'created_at': self.created_at.isoformat(),
                'system_info': self.system_info,
                'results': [
                    {
                        'name': r.name,
                        'duration': r.duration,
                        'memory_before': r.memory_before,
                        'memory_after': r.memory_after,
                        'memory_delta': r.memory_delta,
                        'iterations': r.iterations,
                        'timestamp': r.timestamp.isoformat(),
                        'metadata': r.metadata
                    }
                    for r in self.results
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Benchmark: Error exporting to {filepath}: {e}")
            return False

class BenchmarkRunner:
    """
    Main benchmark runner for Codexify.
    
    Provides methods to run benchmarks, compare results, and generate reports.
    """
    
    def __init__(self):
        self.current_suite: Optional[BenchmarkSuite] = None
        self._lock = threading.Lock()
        
        # System information
        self.system_info = self._gather_system_info()
    
    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for benchmarking context."""
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
    
    def start_suite(self, name: str, description: str = "") -> str:
        """Start a new benchmark suite."""
        with self._lock:
            self.current_suite = BenchmarkSuite(
                name=name,
                description=description,
                system_info=self.system_info
            )
            print(f"Benchmark: Started suite '{name}'")
            return name
    
    def end_suite(self) -> Optional[BenchmarkSuite]:
        """End the current benchmark suite and return it."""
        with self._lock:
            if not self.current_suite:
                return None
            
            suite = self.current_suite
            self.current_suite = None
            
            print(f"Benchmark: Completed suite '{suite.name}' with {len(suite.results)} benchmarks")
            return suite
    
    def run_benchmark(self, 
                     name: str,
                     func: Callable,
                     iterations: int = 1,
                     args: tuple = (),
                     kwargs: dict = None,
                     warmup_iterations: int = 0,
                     metadata: Dict[str, Any] = None) -> Optional[BenchmarkResult]:
        """
        Run a benchmark for a function.
        
        Args:
            name: Name of the benchmark
            func: Function to benchmark
            iterations: Number of iterations to run
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            warmup_iterations: Number of warmup iterations
            metadata: Additional metadata for the benchmark
            
        Returns:
            BenchmarkResult if successful, None otherwise
        """
        if kwargs is None:
            kwargs = {}
        
        if metadata is None:
            metadata = {}
        
        if not self.current_suite:
            print("Benchmark: No active suite. Call start_suite() first.")
            return None
        
        print(f"Benchmark: Running '{name}' ({iterations} iterations)")
        
        try:
            # Warmup runs
            if warmup_iterations > 0:
                for _ in range(warmup_iterations):
                    func(*args, **kwargs)
            
            # Force garbage collection before measurement
            gc.collect()
            
            # Measure memory before
            memory_before = self._get_memory_usage()
            
            # Run benchmark
            start_time = time.time()
            
            for _ in range(iterations):
                result = func(*args, **kwargs)
            
            end_time = time.time()
            
            # Measure memory after
            memory_after = self._get_memory_usage()
            
            # Create benchmark result
            benchmark_result = BenchmarkResult(
                name=name,
                duration=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - memory_before,
                iterations=iterations,
                metadata=metadata
            )
            
            # Add to current suite
            with self._lock:
                if self.current_suite:
                    self.current_suite.add_result(benchmark_result)
            
            print(f"Benchmark: '{name}' completed in {benchmark_result.duration:.4f}s "
                  f"({benchmark_result.duration_per_iteration:.6f}s per iteration)")
            
            return benchmark_result
            
        except Exception as e:
            print(f"Benchmark: Error running '{name}': {e}")
            return None
    
    def run_benchmark_multiple(self, 
                              name: str,
                              func: Callable,
                              iterations: int = 1,
                              runs: int = 5,
                              args: tuple = (),
                              kwargs: dict = None,
                              warmup_iterations: int = 0,
                              metadata: Dict[str, Any] = None) -> List[BenchmarkResult]:
        """
        Run a benchmark multiple times and return all results.
        
        Args:
            name: Name of the benchmark
            func: Function to benchmark
            iterations: Number of iterations per run
            runs: Number of runs to perform
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            warmup_iterations: Number of warmup iterations
            metadata: Additional metadata for the benchmark
            
        Returns:
            List of BenchmarkResult objects
        """
        results = []
        
        for run_num in range(runs):
            run_name = f"{name}_run_{run_num + 1}"
            run_metadata = metadata.copy() if metadata else {}
            run_metadata['run_number'] = run_num + 1
            
            result = self.run_benchmark(
                name=run_name,
                func=func,
                iterations=iterations,
                args=args,
                kwargs=kwargs,
                warmup_iterations=warmup_iterations,
                metadata=run_metadata
            )
            
            if result:
                results.append(result)
        
        return results
    
    def compare_benchmarks(self, 
                          benchmark_names: List[str],
                          metric: str = "duration") -> Dict[str, Any]:
        """
        Compare multiple benchmarks by a specific metric.
        
        Args:
            benchmark_names: List of benchmark names to compare
            metric: Metric to compare ('duration', 'memory_delta', 'duration_per_iteration')
            
        Returns:
            Comparison results
        """
        if not self.current_suite:
            return {}
        
        comparison = {
            'metric': metric,
            'benchmarks': {},
            'statistics': {}
        }
        
        # Collect benchmark data
        for name in benchmark_names:
            result = self.current_suite.get_result(name)
            if result:
                if metric == "duration":
                    value = result.duration
                elif metric == "memory_delta":
                    value = result.memory_delta
                elif metric == "duration_per_iteration":
                    value = result.duration_per_iteration
                else:
                    value = result.duration
                
                comparison['benchmarks'][name] = {
                    'value': value,
                    'iterations': result.iterations,
                    'timestamp': result.timestamp.isoformat()
                }
        
        # Calculate statistics
        values = [b['value'] for b in comparison['benchmarks'].values()]
        if values:
            comparison['statistics'] = {
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0.0
            }
        
        return comparison
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on benchmark results."""
        if not self.current_suite or not self.current_suite.results:
            return []
        
        recommendations = []
        
        # Analyze memory usage
        high_memory_benchmarks = [
            r for r in self.current_suite.results
            if r.memory_delta > 10 * 1024 * 1024  # 10MB threshold
        ]
        
        if high_memory_benchmarks:
            recommendations.append(
                f"Consider optimizing memory usage for {len(high_memory_benchmarks)} benchmarks "
                f"that use more than 10MB of memory"
            )
        
        # Analyze duration
        slow_benchmarks = [
            r for r in self.current_suite.results
            if r.duration_per_iteration > 1.0  # 1 second threshold
        ]
        
        if slow_benchmarks:
            recommendations.append(
                f"Consider optimizing performance for {len(slow_benchmarks)} benchmarks "
                f"that take more than 1 second per iteration"
            )
        
        # Analyze iterations
        low_iteration_benchmarks = [
            r for r in self.current_suite.results
            if r.iterations < 10
        ]
        
        if low_iteration_benchmarks:
            recommendations.append(
                f"Consider increasing iterations for {len(low_iteration_benchmarks)} benchmarks "
                f"to get more accurate measurements"
            )
        
        return recommendations
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            return 0

class CodexifyBenchmarks:
    """Predefined benchmarks for Codexify operations."""
    
    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
    
    def benchmark_file_scanning(self, test_directory: str, iterations: int = 5):
        """Benchmark file scanning operations."""
        from codexify.core.scanner import scan_directory
        
        self.runner.run_benchmark(
            name="file_scanning",
            func=scan_directory,
            iterations=iterations,
            args=(test_directory,),
            metadata={'operation': 'file_scanning', 'test_directory': test_directory}
        )
    
    def benchmark_file_analysis(self, test_files: List[str], iterations: int = 3):
        """Benchmark file analysis operations."""
        from codexify.core.analyzer import ProjectAnalyzer
        
        analyzer = ProjectAnalyzer()
        
        self.runner.run_benchmark(
            name="file_analysis",
            func=analyzer.analyze_project,
            iterations=iterations,
            args=(set(test_files),),
            metadata={'operation': 'file_analysis', 'file_count': len(test_files)}
        )
    
    def benchmark_duplicate_finding(self, test_files: List[str], iterations: int = 3):
        """Benchmark duplicate finding operations."""
        from codexify.core.duplicate_finder import DuplicateFinder
        
        finder = DuplicateFinder()
        
        self.runner.run_benchmark(
            name="duplicate_finding",
            func=finder.find_duplicates,
            iterations=iterations,
            args=(set(test_files),),
            metadata={'operation': 'duplicate_finding', 'file_count': len(test_files)}
        )
    
    def benchmark_file_building(self, test_files: List[str], iterations: int = 3):
        """Benchmark file building operations."""
        from codexify.core.builder import CodeBuilder
        
        builder = CodeBuilder()
        
        # Create temporary output file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_output = f.name
        
        try:
            self.runner.run_benchmark(
                name="file_building",
                func=builder.write_collected_sources,
                iterations=iterations,
                args=(temp_output, set(test_files), "", "txt", True),
                metadata={'operation': 'file_building', 'file_count': len(test_files)}
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_output)
            except OSError:
                pass
    
    def run_all_benchmarks(self, test_directory: str):
        """Run all predefined benchmarks."""
        print("Benchmark: Running all Codexify benchmarks...")
        
        # Get test files
        from codexify.core.scanner import scan_directory
        test_files = list(scan_directory(test_directory, max_file_size=1024*1024))  # 1MB limit
        
        if not test_files:
            print("Benchmark: No test files found")
            return
        
        # Run benchmarks
        self.benchmark_file_scanning(test_directory)
        self.benchmark_file_analysis(test_files[:10])  # Limit to 10 files for analysis
        self.benchmark_duplicate_finding(test_files[:10])
        self.benchmark_file_building(test_files[:10])
        
        print("Benchmark: All benchmarks completed")

# Global benchmark runner
benchmark_runner = BenchmarkRunner()

# Convenience functions
def start_benchmark_suite(name: str, description: str = "") -> str:
    """Start a benchmark suite using the global runner."""
    return benchmark_runner.start_suite(name, description)

def end_benchmark_suite() -> Optional[BenchmarkSuite]:
    """End the current benchmark suite using the global runner."""
    return benchmark_runner.end_suite()

def run_benchmark(name: str, func: Callable, **kwargs) -> Optional[BenchmarkResult]:
    """Run a benchmark using the global runner."""
    return benchmark_runner.run_benchmark(name, func, **kwargs)

def run_codexify_benchmarks(test_directory: str):
    """Run all Codexify benchmarks using the global runner."""
    benchmarks = CodexifyBenchmarks(benchmark_runner)
    benchmarks.run_all_benchmarks(test_directory)
