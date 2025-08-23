#!/usr/bin/env python3
"""
Performance Testing Script for Codexify

This script runs comprehensive performance tests and benchmarks
to evaluate the performance optimization systems.
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="Run Codexify performance tests")
    parser.add_argument("--test-dir", default=".", help="Directory to test (default: current directory)")
    parser.add_argument("--profile", action="store_true", help="Enable performance profiling")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--memory", action="store_true", help="Enable memory monitoring")
    parser.add_argument("--cache", action="store_true", help="Test caching systems")
    parser.add_argument("--parallel", action="store_true", help="Test parallel processing")
    parser.add_argument("--all", action="store_true", help="Run all performance tests")
    parser.add_argument("--export", help="Export results to specified file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print("Codexify Performance Testing")
        print("=" * 40)
        print(f"Test directory: {args.test_dir}")
        print(f"Profile: {args.profile}")
        print(f"Benchmark: {args.benchmark}")
        print(f"Memory monitoring: {args.memory}")
        print(f"Cache testing: {args.cache}")
        print(f"Parallel processing: {args.parallel}")
        print(f"Run all: {args.all}")
        print()
    
    try:
        # Import performance systems
        from codexify.systems import (
            start_performance_management,
            stop_performance_management,
            run_performance_analysis,
            optimize_performance,
            get_performance_status,
            run_performance_benchmarks,
            PerformanceConfig
        )
        
        # Configure performance management
        config = PerformanceConfig(
            enable_profiling=args.profile or args.all,
            enable_caching=args.cache or args.all,
            enable_parallel_processing=args.parallel or args.all,
            enable_memory_monitoring=args.memory or args.all,
            enable_benchmarking=args.benchmark or args.all
        )
        
        print("Starting performance management systems...")
        start_performance_management(config)
        
        # Wait for systems to initialize
        time.sleep(2)
        
        # Run performance analysis
        print("\nRunning performance analysis...")
        analysis_report = run_performance_analysis()
        
        if args.verbose:
            print(f"Analysis complete: {len(analysis_report.recommendations)} recommendations")
            for rec in analysis_report.recommendations:
                print(f"  - {rec}")
        
        # Run benchmarks if requested
        if args.benchmark or args.all:
            print("\nRunning performance benchmarks...")
            benchmark_results = run_performance_benchmarks(args.test_dir)
            
            if benchmark_results:
                print(f"Benchmarks complete: {benchmark_results.get('benchmark_count', 0)} benchmarks")
                if args.verbose:
                    print(f"Results exported to: {benchmark_results.get('export_path', 'N/A')}")
        
        # Test caching if requested
        if args.cache or args.all:
            print("\nTesting caching systems...")
            test_caching_systems()
        
        # Test parallel processing if requested
        if args.parallel or args.all:
            print("\nTesting parallel processing...")
            test_parallel_processing(args.test_dir)
        
        # Run optimization
        print("\nRunning performance optimization...")
        optimization_results = optimize_performance()
        
        if args.verbose:
            print("Optimization results:")
            for key, value in optimization_results.items():
                print(f"  {key}: {value}")
        
        # Final performance analysis
        print("\nRunning final performance analysis...")
        final_report = run_performance_analysis()
        
        # Get overall status
        status = get_performance_status()
        print(f"\nPerformance Score: {status.get('performance_score', 0.0):.2f}")
        
        # Export results if requested
        if args.export:
            print(f"\nExporting results to {args.export}...")
            from codexify.systems.performance_manager import performance_manager
            performance_manager.export_performance_report(args.export)
        
        print("\nPerformance testing complete!")
        
    except ImportError as e:
        print(f"Error importing performance systems: {e}")
        print("Make sure all dependencies are installed and the codexify package is available.")
        return 1
    
    except Exception as e:
        print(f"Error during performance testing: {e}")
        return 1
    
    finally:
        # Stop performance management
        try:
            stop_performance_management()
        except Exception as e:
            print(f"Error stopping performance management: {e}")
    
    return 0

def test_caching_systems():
    """Test the caching systems."""
    try:
        from codexify.systems import (
            cache_file_content,
            get_cached_file_content,
            cache_analysis_result,
            get_cached_analysis_result,
            generate_analysis_cache_key
        )
        
        # Test file caching
        test_content = "This is a test file content for caching"
        test_file_path = "/tmp/test_cache_file.txt"
        
        # Cache content
        success = cache_file_content(test_file_path, test_content)
        print(f"  File caching test: {'PASS' if success else 'FAIL'}")
        
        # Retrieve cached content
        cached_content = get_cached_file_content(test_file_path)
        cache_hit = cached_content == test_content
        print(f"  File cache retrieval: {'PASS' if cache_hit else 'FAIL'}")
        
        # Test analysis caching
        test_files = {"/tmp/file1.txt", "/tmp/file2.txt"}
        test_analysis = {"summary": "Test analysis", "files": len(test_files)}
        
        cache_key = generate_analysis_cache_key(test_files, "test_analysis")
        success = cache_analysis_result(cache_key, test_analysis)
        print(f"  Analysis caching test: {'PASS' if success else 'FAIL'}")
        
        # Retrieve cached analysis
        cached_analysis = get_cached_analysis_result(cache_key)
        analysis_cache_hit = cached_analysis == test_analysis
        print(f"  Analysis cache retrieval: {'PASS' if analysis_cache_hit else 'FAIL'}")
        
    except Exception as e:
        print(f"  Cache testing error: {e}")

def test_parallel_processing(test_dir):
    """Test parallel processing systems."""
    try:
        from codexify.systems import (
            process_files_parallel,
            analyze_files_parallel,
            get_parallel_processing_stats
        )
        
        # Get some test files
        test_files = set()
        try:
            for root, dirs, files in os.walk(test_dir):
                for file in files[:10]:  # Limit to 10 files
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        test_files.add(file_path)
                break  # Only process root directory
        except Exception:
            # Create dummy test files if we can't scan
            test_files = {f"/tmp/test_file_{i}.txt" for i in range(5)}
        
        if test_files:
            print(f"  Testing with {len(test_files)} files")
            
            # Test file processing
            def dummy_processor(file_path):
                return f"Processed: {file_path}"
            
            results = process_files_parallel(test_files, dummy_processor)
            success_count = sum(1 for r in results if r.success)
            print(f"  Parallel file processing: {success_count}/{len(results)} successful")
            
            # Test analysis processing
            def dummy_analyzer(file_path):
                return {"file": file_path, "size": len(file_path)}
            
            analysis_results = analyze_files_parallel(test_files, dummy_analyzer)
            analysis_success_count = sum(1 for r in analysis_results if r.success)
            print(f"  Parallel analysis processing: {analysis_success_count}/{len(analysis_results)} successful")
            
            # Get stats
            stats = get_parallel_processing_stats()
            print(f"  File processor status: {stats.get('file_processor', {}).get('status', 'Unknown')}")
            print(f"  Analysis processor status: {stats.get('analysis_processor', {}).get('status', 'Unknown')}")
        
    except Exception as e:
        print(f"  Parallel processing testing error: {e}")

if __name__ == "__main__":
    sys.exit(main())
