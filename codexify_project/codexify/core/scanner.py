import os
import fnmatch
from typing import Set, List, Optional
from pathlib import Path

def _load_codexignore(project_path: str) -> List[str]:
    """
    Loads and parses .codexignore file from the project directory.
    Returns a list of ignore patterns.
    """
    ignore_file = Path(project_path) / ".codexignore"
    if not ignore_file.exists():
        return []
    
    patterns = []
    try:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    except Exception as e:
        print(f"Warning: Could not read .codexignore: {e}")
    
    return patterns

def _should_ignore_file(file_path: str, ignore_patterns: List[str], project_path: str) -> bool:
    """
    Checks if a file should be ignored based on .codexignore patterns.
    """
    # Convert to relative path for pattern matching
    rel_path = os.path.relpath(file_path, project_path)
    
    for pattern in ignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            if rel_path.startswith(pattern[:-1]) or '/' + pattern[:-1] in rel_path:
                return True
        # Handle file patterns
        elif fnmatch.fnmatch(rel_path, pattern):
            return True
        # Handle special patterns that fnmatch might not handle well
        elif pattern == ".#*" and rel_path.startswith(".#"):
            return True
        # Handle absolute patterns
        elif pattern.startswith('/') and fnmatch.fnmatch('/' + rel_path, pattern):
            return True
        # Handle patterns without slashes (like __pycache__)
        elif '/' not in pattern and pattern in rel_path.split('/'):
            return True
    
    return False

def _is_binary_file(file_path: str) -> bool:
    """
    Checks if a file is binary by reading the first few bytes.
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return False

def scan_directory(path: str, 
                  ignore_patterns: Optional[List[str]] = None,
                  max_file_size: int = 10 * 1024 * 1024,  # 10MB
                  skip_binary: bool = True) -> Set[str]:
    """
    Scans a directory and returns a set of all file paths.
    
    Args:
        path: Directory path to scan
        ignore_patterns: List of ignore patterns (if None, loads from .codexignore)
        max_file_size: Maximum file size to include (in bytes)
        skip_binary: Whether to skip binary files
    
    Returns:
        Set of file paths that should be included
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    print(f"Scanner: Scanning directory {path}...")
    
    # Load ignore patterns if not provided
    if ignore_patterns is None:
        ignore_patterns = _load_codexignore(path)
        if ignore_patterns:
            print(f"Scanner: Loaded {len(ignore_patterns)} ignore patterns from .codexignore")
    
    found_files: Set[str] = set()
    ignored_count = 0
    binary_count = 0
    size_ignored_count = 0
    
    try:
        for root, dirs, files in os.walk(path):
            # Remove ignored directories from dirs list to prevent walking into them
            dirs[:] = [d for d in dirs if not _should_ignore_file(
                os.path.join(root, d), ignore_patterns, path)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file should be ignored
                if _should_ignore_file(file_path, ignore_patterns, path):
                    ignored_count += 1
                    continue
                
                # Check file size (record, but do not exclude from listing)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size:
                        size_ignored_count += 1
                except OSError:
                    # Skip files we can't access
                    continue
                
                # Check if binary file (record, but do not exclude from listing)
                if skip_binary and _is_binary_file(file_path):
                    binary_count += 1
                
                found_files.add(file_path)
                
    except PermissionError as e:
        print(f"Scanner: Permission denied accessing {e.filename}")
    except Exception as e:
        print(f"Scanner: Error during scanning: {e}")
    
    print(f"Scanner: Found {len(found_files)} files")
    print(f"Scanner: Ignored {ignored_count} files (patterns)")
    if binary_count or size_ignored_count:
        print(f"Scanner: Also detected {binary_count} binary and {size_ignored_count} large files (listed anyway)")
    
    return found_files

def get_file_stats(file_paths: Set[str]) -> dict:
    """
    Returns statistics about the scanned files.
    """
    if not file_paths:
        return {"total_files": 0, "total_size": 0, "extensions": {}}
    
    total_size = 0
    extensions = {}
    
    for file_path in file_paths:
        try:
            size = os.path.getsize(file_path)
            total_size += size
            
            ext = Path(file_path).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
            
        except OSError:
            continue
    
    return {
        "total_files": len(file_paths),
        "total_size": total_size,
        "extensions": extensions
    }
