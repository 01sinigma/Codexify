"""
Parallel Processing System

This module provides parallel processing capabilities for Codexify,
including file processing, analysis, and duplicate detection using multiple threads/processes.
"""

import os
import threading
import multiprocessing
import queue
import time
from typing import Dict, List, Set, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import psutil

@dataclass
class ProcessingTask:
    """Represents a processing task."""
    task_id: str
    file_path: str
    task_type: str
    priority: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingResult:
    """Represents the result of a processing task."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TaskQueue:
    """Thread-safe task queue with priority support."""
    
    def __init__(self, maxsize: int = 1000):
        self.queue = queue.PriorityQueue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._task_count = 0
    
    def put(self, task: ProcessingTask) -> bool:
        """Add a task to the queue."""
        try:
            # Priority is negative so higher priority tasks come first
            priority = (-task.priority, self._task_count)
            self.queue.put((priority, task), timeout=1.0)
            self._task_count += 1
            return True
        except queue.Full:
            return False
    
    def get(self, timeout: float = None) -> Optional[ProcessingTask]:
        """Get the next task from the queue."""
        try:
            priority, task = self.queue.get(timeout=timeout)
            return task
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()

class ParallelProcessor:
    """
    Main parallel processing system for Codexify.
    
    Provides both thread-based and process-based parallel processing
    with configurable worker pools and task management.
    """
    
    def __init__(self, 
                 max_workers: int = None,
                 use_processes: bool = False,
                 chunk_size: int = 1):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        
        # Task management
        self.task_queue = TaskQueue()
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_results: List[ProcessingResult] = []
        
        # Worker management
        self.executor = None
        self.workers = []
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'start_time': None
        }
    
    def start(self):
        """Start the parallel processor."""
        if self.executor is not None:
            return
        
        self._shutdown_event.clear()
        self.stats['start_time'] = time.time()
        
        if self.use_processes:
            self.executor = ProcessPoolExecutor(
                max_workers=self.max_workers,
                mp_context=multiprocessing.get_context('spawn')
            )
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        print(f"ParallelProcessor: Started with {self.max_workers} {'processes' if self.use_processes else 'threads'}")
    
    def stop(self):
        """Stop the parallel processor."""
        if self.executor is None:
            return
        
        self._shutdown_event.set()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        self.executor = None
        
        # Clear active tasks
        with self._lock:
            self.active_tasks.clear()
        
        print("ParallelProcessor: Stopped")
    
    def submit_task(self, task: ProcessingTask) -> bool:
        """Submit a task for processing."""
        if self.executor is None:
            return False
        
        with self._lock:
            self.active_tasks[task.task_id] = task
            self.stats['tasks_submitted'] += 1
        
        # Submit to executor
        future = self.executor.submit(self._process_task, task)
        future.add_done_callback(lambda f: self._task_completed(task.task_id, f))
        
        return True
    
    def submit_batch(self, tasks: List[ProcessingTask]) -> int:
        """Submit multiple tasks for processing."""
        submitted_count = 0
        for task in tasks:
            if self.submit_task(task):
                submitted_count += 1
        return submitted_count
    
    def process_files_parallel(self, 
                             file_paths: Set[str],
                             processor_func: Callable[[str], Any],
                             task_type: str = "file_processing",
                             priority: int = 0) -> List[ProcessingResult]:
        """
        Process multiple files in parallel.
        
        Args:
            file_paths: Set of file paths to process
            processor_func: Function to process each file
            task_type: Type of processing task
            priority: Task priority (higher = more important)
            
        Returns:
            List of processing results
        """
        if not file_paths:
            return []
        
        # Create tasks
        tasks = []
        for file_path in file_paths:
            task = ProcessingTask(
                task_id=f"{task_type}_{hash(file_path)}",
                file_path=file_path,
                task_type=task_type,
                priority=priority
            )
            tasks.append(task)
        
        # Submit tasks
        submitted_count = self.submit_batch(tasks)
        print(f"ParallelProcessor: Submitted {submitted_count} {task_type} tasks")
        
        # Wait for completion
        self._wait_for_completion()
        
        # Return results
        with self._lock:
            results = self.completed_results.copy()
            self.completed_results.clear()
        
        return results
    
    def _process_task(self, task: ProcessingTask) -> ProcessingResult:
        """Process a single task."""
        start_time = time.time()
        
        try:
            # Import the processor function if using processes
            if self.use_processes:
                # For process-based execution, we need to handle imports differently
                # This is a simplified approach - in practice, you might want to use
                # a more sophisticated method for process-based function execution
                result = self._execute_processor_function(task)
            else:
                # For thread-based execution, we can call the function directly
                result = self._execute_processor_function(task)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                task_id=task.task_id,
                success=True,
                result=result,
                processing_time=processing_time,
                metadata=task.metadata
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                task_id=task.task_id,
                success=False,
                result=None,
                error=str(e),
                processing_time=processing_time,
                metadata=task.metadata
            )
    
    def _execute_processor_function(self, task: ProcessingTask) -> Any:
        """Execute the processor function for a task."""
        # This is a placeholder - in practice, you would implement
        # the actual function execution logic here
        # For now, we'll just return a simple result
        return f"Processed: {task.file_path}"
    
    def _task_completed(self, task_id: str, future):
        """Handle task completion."""
        try:
            result = future.result()
        except Exception as e:
            result = ProcessingResult(
                task_id=task_id,
                success=False,
                result=None,
                error=str(e),
                metadata={}
            )
        
        with self._lock:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Add to completed results
            self.completed_results.append(result)
            
            # Update statistics
            self.stats['tasks_completed'] += 1
            if not result.success:
                self.stats['tasks_failed'] += 1
            
            self.stats['total_processing_time'] += result.processing_time
    
    def _wait_for_completion(self, timeout: float = None):
        """Wait for all active tasks to complete."""
        start_time = time.time()
        
        while True:
            with self._lock:
                if not self.active_tasks:
                    break
            
            if timeout and (time.time() - start_time) > timeout:
                break
            
            time.sleep(0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        with self._lock:
            stats = self.stats.copy()
            stats['active_tasks'] = len(self.active_tasks)
            stats['queue_size'] = self.task_queue.size()
            
            if stats['start_time']:
                uptime = time.time() - stats['start_time']
                stats['uptime_seconds'] = uptime
                if stats['tasks_completed'] > 0:
                    stats['avg_task_time'] = stats['total_processing_time'] / stats['tasks_completed']
        
        return stats
    
    def get_status(self) -> str:
        """Get current processor status."""
        stats = self.get_stats()
        
        if self.executor is None:
            return "Stopped"
        
        return (f"Running - Workers: {self.max_workers}, "
                f"Active: {stats['active_tasks']}, "
                f"Completed: {stats['tasks_completed']}, "
                f"Failed: {stats['tasks_failed']}")

class FileProcessor:
    """Specialized file processor for parallel file operations."""
    
    def __init__(self, max_workers: int = None):
        self.processor = ParallelProcessor(
            max_workers=max_workers,
            use_processes=False,  # Use threads for I/O operations
            chunk_size=1
        )
    
    def process_files(self, 
                     file_paths: Set[str],
                     processor_func: Callable[[str], Any],
                     **kwargs) -> List[ProcessingResult]:
        """Process files using the parallel processor."""
        return self.processor.process_files_parallel(
            file_paths, processor_func, **kwargs
        )
    
    def start(self):
        """Start the file processor."""
        self.processor.start()
    
    def stop(self):
        """Stop the file processor."""
        self.processor.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return self.processor.get_stats()

class AnalysisProcessor:
    """Specialized processor for parallel analysis operations."""
    
    def __init__(self, max_workers: int = None):
        self.processor = ParallelProcessor(
            max_workers=max_workers,
            use_processes=True,  # Use processes for CPU-intensive analysis
            chunk_size=1
        )
    
    def analyze_files(self, 
                     file_paths: Set[str],
                     analyzer_func: Callable[[str], Any],
                     **kwargs) -> List[ProcessingResult]:
        """Analyze files using the parallel processor."""
        return self.processor.process_files_parallel(
            file_paths, analyzer_func, **kwargs
        )
    
    def start(self):
        """Start the analysis processor."""
        self.processor.start()
    
    def stop(self):
        """Stop the analysis processor."""
        self.processor.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return self.processor.get_stats()

# Global processor instances
file_processor = FileProcessor()
analysis_processor = AnalysisProcessor()

# Convenience functions
def process_files_parallel(file_paths: Set[str], 
                          processor_func: Callable[[str], Any],
                          **kwargs) -> List[ProcessingResult]:
    """Process files in parallel using the global file processor."""
    return file_processor.process_files(file_paths, processor_func, **kwargs)

def analyze_files_parallel(file_paths: Set[str],
                          analyzer_func: Callable[[str], Any],
                          **kwargs) -> List[ProcessingResult]:
    """Analyze files in parallel using the global analysis processor."""
    return analysis_processor.analyze_files(file_paths, analyzer_func, **kwargs)

def start_parallel_processors():
    """Start all parallel processors."""
    file_processor.start()
    analysis_processor.start()

def stop_parallel_processors():
    """Stop all parallel processors."""
    file_processor.stop()
    analysis_processor.stop()

def get_parallel_processing_stats() -> Dict[str, Any]:
    """Get statistics from all parallel processors."""
    return {
        'file_processor': file_processor.get_stats(),
        'analysis_processor': analysis_processor.get_stats()
    }
