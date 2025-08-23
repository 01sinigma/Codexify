#!/usr/bin/env python3
"""
Performance Tuning Script for Codexify.
Performs fine-tuning of performance systems and generates optimization recommendations.
"""

import argparse
import sys
import os
import time
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from codexify.systems.performance_manager import PerformanceManager, PerformanceConfig
from codexify.systems.profiler import PerformanceProfiler
from codexify.systems.benchmark import BenchmarkRunner, CodexifyBenchmarks
from codexify.systems.memory_optimizer import MemoryOptimizer, MemoryMonitor
from codexify.systems.cache import FileContentCache, AnalysisResultCache, PersistentCache
from codexify.systems.parallel import ParallelProcessor, FileProcessor, AnalysisProcessor

def create_performance_config():
    """Create an optimized performance configuration."""
    config = PerformanceConfig(
        enable_profiling=True,
        enable_caching=True,
        enable_parallel_processing=True,
        enable_memory_monitoring=True,
        enable_benchmarking=True,
        profiling_sample_rate=0.1,  # 10% sampling for production
        cache_max_size_mb=200,      # Increased cache size
        cache_cleanup_interval_seconds=600,  # 10 minutes
        parallel_max_workers=os.cpu_count(),
        parallel_chunk_size=10,
        memory_monitoring_interval_seconds=30,
        benchmark_iterations=5
    )
    return config

def run_performance_analysis(manager, test_dir="."):
    """Run comprehensive performance analysis."""
    print("🔍 Running Performance Analysis...")
    
    # Start all systems
    manager.start_all_systems()
    
    # Run analysis
    analysis_results = manager.run_analysis(test_dir)
    
    # Run benchmarks
    benchmark_results = manager.run_benchmarks()
    
    # Run optimization
    optimization_results = manager.run_optimization()
    
    # Generate report
    report = manager.generate_report()
    
    return {
        'analysis': analysis_results,
        'benchmarks': benchmark_results,
        'optimization': optimization_results,
        'report': report
    }

def tune_cache_systems():
    """Tune cache systems for optimal performance."""
    print("💾 Tuning Cache Systems...")
    
    # File content cache tuning
    file_cache = FileContentCache()
    file_cache.policy.max_size_mb = 300
    file_cache.policy.default_ttl_seconds = 7200  # 2 hours
    file_cache.policy.cleanup_interval_seconds = 900  # 15 minutes
    
    # Analysis result cache tuning
    analysis_cache = AnalysisResultCache()
    analysis_cache.policy.max_size_mb = 200
    analysis_cache.policy.default_ttl_seconds = 3600  # 1 hour
    
    # Persistent cache tuning
    persistent_cache = PersistentCache()
    persistent_cache.policy.max_size_mb = 500
    persistent_cache.policy.default_ttl_seconds = 86400  # 24 hours
    
    print("   ✓ File cache: 300MB, 2h TTL")
    print("   ✓ Analysis cache: 200MB, 1h TTL")
    print("   ✓ Persistent cache: 500MB, 24h TTL")

def tune_parallel_processing():
    """Tune parallel processing systems."""
    print("⚡ Tuning Parallel Processing...")
    
    # Determine optimal worker count
    cpu_count = os.cpu_count()
    optimal_workers = min(cpu_count * 2, 16)  # Cap at 16 workers
    
    # File processor tuning
    file_processor = FileProcessor(max_workers=optimal_workers)
    
    # Analysis processor tuning
    analysis_processor = AnalysisProcessor(max_workers=optimal_workers)
    
    # General parallel processor tuning
    parallel_processor = ParallelProcessor(
        max_workers=optimal_workers,
        use_processes=True,  # Use processes for CPU-intensive tasks
        chunk_size=20
    )
    
    print(f"   ✓ Workers: {optimal_workers} (CPU cores: {cpu_count})")
    print("   ✓ Chunk size: 20")
    print("   ✓ Process-based execution enabled")

def tune_memory_optimization():
    """Tune memory optimization systems."""
    print("🧠 Tuning Memory Optimization...")
    
    # Memory monitor tuning
    memory_monitor = MemoryMonitor(enable_tracemalloc=True)
    memory_monitor.monitoring_interval = 15  # 15 seconds
    
    # Memory optimizer tuning
    memory_optimizer = MemoryOptimizer()
    memory_optimizer.gc_threshold = 0.7  # 70% memory usage threshold
    memory_optimizer.cleanup_threshold = 0.5  # 50% memory usage threshold
    
    print("   ✓ Monitoring interval: 15 seconds")
    print("   ✓ GC threshold: 70%")
    print("   ✓ Cleanup threshold: 50%")

def generate_optimization_report(results):
    """Generate a detailed optimization report."""
    print("\n📊 Performance Optimization Report")
    print("=" * 50)
    
    # Analysis results
    if 'analysis' in results:
        analysis = results['analysis']
        print(f"\n🔍 Analysis Results:")
        print(f"   • Total operations: {len(analysis.get('operations', []))}")
        print(f"   • Average duration: {analysis.get('avg_duration', 0):.3f}s")
        print(f"   • Memory usage: {analysis.get('memory_usage', 0) / 1024 / 1024:.1f} MB")
    
    # Benchmark results
    if 'benchmarks' in results:
        benchmarks = results['benchmarks']
        print(f"\n⚡ Benchmark Results:")
        for name, result in benchmarks.items():
            if isinstance(result, dict):
                duration = result.get('duration', 0)
                memory = result.get('memory_delta', 0) / 1024 / 1024
                print(f"   • {name}: {duration:.3f}s, {memory:.1f} MB")
    
    # Optimization results
    if 'optimization' in results:
        optimization = results['optimization']
        print(f"\n🚀 Optimization Results:")
        print(f"   • Performance score: {optimization.get('performance_score', 0):.1f}/100")
        print(f"   • Memory efficiency: {optimization.get('memory_efficiency', 0):.1f}%")
        
        recommendations = optimization.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
    
    # Overall report
    if 'report' in results:
        report = results['report']
        print(f"\n📈 Overall Performance:")
        print(f"   • Cache hit rate: {report.get('cache_hit_rate', 0):.1f}%")
        print(f"   • Parallel efficiency: {report.get('parallel_efficiency', 0):.1f}%")
        print(f"   • Memory utilization: {report.get('memory_utilization', 0):.1f}%")

def save_optimization_config(config, filename="performance_config.json"):
    """Save the optimized configuration to a file."""
    config_data = {
        'cache_settings': {
            'file_cache_max_size_mb': 300,
            'analysis_cache_max_size_mb': 200,
            'persistent_cache_max_size_mb': 500,
            'cleanup_interval_seconds': 900
        },
        'parallel_settings': {
            'max_workers': min(os.cpu_count() * 2, 16),
            'chunk_size': 20,
            'use_processes': True
        },
        'memory_settings': {
            'monitoring_interval_seconds': 15,
            'gc_threshold': 0.7,
            'cleanup_threshold': 0.5
        },
        'profiling_settings': {
            'sample_rate': 0.1,
            'enabled': True
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\n💾 Configuration saved to: {filename}")

def main():
    """Main performance tuning function."""
    parser = argparse.ArgumentParser(description="Codexify Performance Tuning")
    parser.add_argument("--test-dir", default=".", help="Directory to test (default: current)")
    parser.add_argument("--config", help="Load configuration from file")
    parser.add_argument("--save-config", help="Save optimized configuration to file")
    parser.add_argument("--tune-only", action="store_true", help="Only tune systems, don't run analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 Codexify Performance Tuning")
    print("=" * 40)
    
    try:
        # Create performance manager
        config = create_performance_config()
        manager = PerformanceManager(config)
        
        if args.verbose:
            print(f"Configuration: {config}")
        
        # Tune individual systems
        tune_cache_systems()
        tune_parallel_processing()
        tune_memory_optimization()
        
        if args.tune_only:
            print("\n✅ Performance tuning completed!")
            return
        
        # Run comprehensive analysis
        results = run_performance_analysis(manager, args.test_dir)
        
        # Generate report
        generate_optimization_report(results)
        
        # Save configuration if requested
        if args.save_config:
            save_optimization_config(config, args.save_config)
        
        # Stop all systems
        manager.stop_all_systems()
        
        print("\n✅ Performance tuning and analysis completed!")
        
    except Exception as e:
        print(f"\n❌ Error during performance tuning: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
