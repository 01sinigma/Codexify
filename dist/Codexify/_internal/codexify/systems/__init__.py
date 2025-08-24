"""
Codexify Performance Systems

This package contains all performance-related systems for Codexify,
including profiling, caching, parallel processing, benchmarking, and optimization.
"""

from .profiler import (
    PerformanceProfiler,
    PerformanceMetric,
    PerformanceReport,
    profile_operation,
    profile_context,
    start_profiling,
    end_profiling,
    get_performance_summary
)

from .cache import (
    FileContentCache,
    AnalysisResultCache,
    PersistentCache,
    CachePolicy,
    CacheEntry,
    file_cache,
    analysis_cache,
    persistent_cache,
    cache_file_content,
    get_cached_file_content,
    cache_analysis_result,
    get_cached_analysis_result,
    generate_analysis_cache_key
)

from .parallel import (
    ParallelProcessor,
    FileProcessor,
    AnalysisProcessor,
    ProcessingTask,
    ProcessingResult,
    file_processor,
    analysis_processor,
    process_files_parallel,
    analyze_files_parallel,
    start_parallel_processors,
    stop_parallel_processors,
    get_parallel_processing_stats
)

from .benchmark import (
    BenchmarkRunner,
    BenchmarkResult,
    BenchmarkSuite,
    CodexifyBenchmarks,
    benchmark_runner,
    start_benchmark_suite,
    end_benchmark_suite,
    run_benchmark,
    run_codexify_benchmarks
)

from .memory_optimizer import (
    MemoryMonitor,
    MemoryOptimizer,
    WeakReferenceManager,
    MemorySnapshot,
    MemoryLeak,
    memory_monitor,
    memory_optimizer,
    weak_ref_manager,
    start_memory_monitoring,
    stop_memory_monitoring,
    take_memory_snapshot,
    optimize_memory,
    get_memory_status
)

from .performance_manager import (
    PerformanceManager,
    PerformanceConfig,
    PerformanceReport as PerfReport,
    performance_manager,
    start_performance_management,
    stop_performance_management,
    run_performance_analysis,
    optimize_performance,
    get_performance_status,
    run_performance_benchmarks
)

__version__ = "0.6.0"
__author__ = "Codexify Team"

__all__ = [
    # Profiler
    'PerformanceProfiler',
    'PerformanceMetric', 
    'PerformanceReport',
    'profile_operation',
    'profile_context',
    'start_profiling',
    'end_profiling',
    'get_performance_summary',
    
    # Cache
    'FileContentCache',
    'AnalysisResultCache',
    'PersistentCache',
    'CachePolicy',
    'CacheEntry',
    'file_cache',
    'analysis_cache',
    'persistent_cache',
    'cache_file_content',
    'get_cached_file_content',
    'cache_analysis_result',
    'get_cached_analysis_result',
    'generate_analysis_cache_key',
    
    # Parallel Processing
    'ParallelProcessor',
    'FileProcessor',
    'AnalysisProcessor',
    'ProcessingTask',
    'ProcessingResult',
    'file_processor',
    'analysis_processor',
    'process_files_parallel',
    'analyze_files_parallel',
    'start_parallel_processors',
    'stop_parallel_processors',
    'get_parallel_processing_stats',
    
    # Benchmarking
    'BenchmarkRunner',
    'BenchmarkResult',
    'BenchmarkSuite',
    'CodexifyBenchmarks',
    'benchmark_runner',
    'start_benchmark_suite',
    'end_benchmark_suite',
    'run_benchmark',
    'run_codexify_benchmarks',
    
    # Memory Optimization
    'MemoryMonitor',
    'MemoryOptimizer',
    'WeakReferenceManager',
    'MemorySnapshot',
    'MemoryLeak',
    'memory_monitor',
    'memory_optimizer',
    'weak_ref_manager',
    'start_memory_monitoring',
    'stop_memory_monitoring',
    'take_memory_snapshot',
    'optimize_memory',
    'get_memory_status',
    
    # Performance Management
    'PerformanceManager',
    'PerformanceConfig',
    'PerfReport',
    'performance_manager',
    'start_performance_management',
    'stop_performance_management',
    'run_performance_analysis',
    'optimize_performance',
    'get_performance_status',
    'run_performance_benchmarks'
]
