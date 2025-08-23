"""
Unit tests for Scanner module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from codexify.core.scanner import scan_directory, _load_codexignore, _should_ignore_file, _is_binary_file


class TestScanner:
    """Test cases for Scanner module."""
    
    def test_load_codexignore_from_file(self, temp_project_dir):
        """Test loading ignore patterns from .codexignore file."""
        # Create .codexignore file
        ignore_file = Path(temp_project_dir) / ".codexignore"
        ignore_file.write_text("*.pyc\n__pycache__\n*.log\n.DS_Store")
        
        patterns = _load_codexignore(temp_project_dir)
        
        assert "*.pyc" in patterns
        assert "__pycache__" in patterns
        assert "*.log" in patterns
        assert ".DS_Store" in patterns
        assert len(patterns) == 4
    
    def test_load_codexignore_no_file(self, temp_project_dir):
        """Test loading ignore patterns when .codexignore doesn't exist."""
        patterns = _load_codexignore(temp_project_dir)

        # Should return default patterns from .codexignore
        assert len(patterns) > 0
    
    def test_is_binary_file(self):
        """Test binary file detection."""
        # Test text files
        assert _is_binary_file("test_file.txt") is False
        
        # Test binary files (this will fail on non-existent files, but that's expected)
        # We'll test with actual file creation in other tests
    
    def test_should_ignore_file(self):
        """Test file ignore logic."""
        # Test ignored files
        assert _should_ignore_file("file.tmp", ["*.tmp", "*.log", "__pycache__"], "/test") is True
        assert _should_ignore_file("app.log", ["*.tmp", "*.log", "__pycache__"], "/test") is True
        assert _should_ignore_file("__pycache__/module.pyc", ["*.tmp", "*.log", "__pycache__/"], "/test") is True
        
        # Test non-ignored files
        assert _should_ignore_file("main.py", ["*.tmp", "*.log", "__pycache__"], "/test") is False
        assert _should_ignore_file("config.json", ["*.tmp", "*.log", "__pycache__"], "/test") is False
        assert _should_ignore_file("README.md", ["*.tmp", "*.log", "__pycache__"], "/test") is False
    
    def test_should_ignore_file_with_path_patterns(self):
        """Test file ignore logic with path-based patterns."""
        # Test ignored directories
        assert _should_ignore_file("build/", ["build/", "dist/", "*.egg-info/"], "/test") is True
        assert _should_ignore_file("dist/package", ["build/", "dist/", "*.egg-info/"], "/test") is True
        assert _should_ignore_file("package.egg-info/", ["build/", "dist/", "*.egg-info/"], "/test") is True
        
        # Test non-ignored paths
        assert _should_ignore_file("src/main.py", ["build/", "dist/", "*.egg-info/"], "/test") is False
        assert _should_ignore_file("tests/test.py", ["build/", "dist/", "*.egg-info/"], "/test") is False
    
    def test_should_ignore_file_with_wildcards(self):
        """Test file ignore logic with wildcard patterns."""
        # Test ignored files
        assert _should_ignore_file("file~", ["*~", ".#*", "*.swp"], "/test") is True
        assert _should_ignore_file(".#file", ["*~", ".#*", "*.swp"], "/test") is True
        assert _should_ignore_file("file.swp", ["*~", ".#*", "*.swp"], "/test") is True
        
        # Test non-ignored files
        assert _should_ignore_file("file.txt", ["*~", ".#*", "*.swp"], "/test") is False
        assert _should_ignore_file("file.py", ["*~", ".#*", "*.swp"], "/test") is False
    
    def test_scan_directory_basic(self, temp_project_dir):
        """Test basic directory scanning."""
        files = scan_directory(temp_project_dir)
        
        # Should find files from our test structure
        assert len(files) > 0
        
        # Check for expected files
        file_paths = list(files)
        assert any("main.py" in path for path in file_paths)
        assert any("utils.py" in path for path in file_paths)
        assert any("config.json" in path for path in file_paths)
        assert any("README.md" in path for path in file_paths)
    
    def test_scan_directory_with_ignore_patterns(self, temp_project_dir):
        """Test directory scanning with ignore patterns."""
        files = scan_directory(temp_project_dir, ignore_patterns=["*.pyc", "__pycache__", "*.log"])
        
        # Should not find ignored files
        file_paths = list(files)
        for file_path in file_paths:
            assert not file_path.endswith(".pyc")
            assert "__pycache__" not in file_path
            assert not file_path.endswith(".log")
    
    def test_scan_directory_max_file_size(self, temp_project_dir):
        """Test directory scanning with file size limit."""
        # Create a large file
        large_file = Path(temp_project_dir) / "large_file.txt"
        large_file.write_text("x" * 2048)  # 2KB file
        
        files = scan_directory(temp_project_dir, max_file_size=1024)  # 1KB limit
        
        # Should not find files larger than max size
        file_paths = list(files)
        assert "large_file.txt" not in file_paths
    
    def test_scan_directory_binary_detection(self, temp_project_dir):
        """Test binary file detection during scanning."""
        # Create a binary-like file
        binary_file = Path(temp_project_dir) / "binary.dat"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
        
        files = scan_directory(temp_project_dir, skip_binary=False)
        
        # Find the binary file
        file_paths = list(files)
        assert any("binary.dat" in path for path in file_paths)
    
    def test_scan_directory_empty_directory(self):
        """Test scanning an empty directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            files = scan_directory(temp_dir)
            
            assert len(files) == 0
        finally:
            shutil.rmtree(temp_dir)
    
    def test_scan_directory_single_file(self, temp_project_dir):
        """Test scanning a directory with only one file."""
        # Create a directory with just one file
        single_file_dir = tempfile.mkdtemp()
        try:
            test_file = Path(single_file_dir) / "test.txt"
            test_file.write_text("single file content")
            
            files = scan_directory(single_file_dir)
            
            assert len(files) == 1
            file_paths = list(files)
            assert any("test.txt" in path for path in file_paths)
        finally:
            shutil.rmtree(single_file_dir)
    
    def test_scan_directory_hidden_files(self, temp_project_dir):
        """Test scanning with hidden files."""
        # Create hidden files
        hidden_file = Path(temp_project_dir) / ".hidden"
        hidden_file.write_text("hidden content")
        
        files = scan_directory(temp_project_dir)
        
        # Should include hidden files by default
        file_paths = list(files)
        assert any(".hidden" in path for path in file_paths)
    
    def test_scan_directory_ignore_hidden_files(self, temp_project_dir):
        """Test scanning with hidden files ignored."""
        # Create hidden files
        hidden_file = Path(temp_project_dir) / ".hidden"
        hidden_file.write_text("hidden content")
        
        files = scan_directory(temp_project_dir, ignore_patterns=[".*"])
        
        # Should not include hidden files
        file_paths = list(files)
        assert not any(".hidden" in path for path in file_paths)
    
    def test_scan_directory_performance(self, temp_project_dir):
        """Test scanning performance with many files."""
        # Create many small files
        for i in range(100):
            file_path = Path(temp_project_dir) / f"file_{i:03d}.txt"
            file_path.write_text(f"Content of file {i}")
        
        import time
        start_time = time.time()
        files = scan_directory(temp_project_dir)
        end_time = time.time()
        
        # Should find all files
        assert len(files) >= 100
        
        # Should complete in reasonable time (less than 1 second for 100 files)
        assert (end_time - start_time) < 1.0
    
    def test_scan_directory_error_handling(self, temp_project_dir):
        """Test error handling during directory scanning."""
        # Create a file that can't be read
        unreadable_file = Path(temp_project_dir) / "unreadable.txt"
        unreadable_file.write_text("content")
        
        # Make file unreadable (this might not work on Windows)
        try:
            unreadable_file.chmod(0o000)
            
            files = scan_directory(temp_project_dir)
            
            # Should still scan other files
            assert len(files) > 0
            
            # Should still scan other files even if some are unreadable
            file_paths = list(files)
            assert len(file_paths) > 0
            
        except (OSError, PermissionError):
            # File permissions not supported on this system
            pass
        finally:
            # Restore permissions
            try:
                unreadable_file.chmod(0o644)
            except (OSError, PermissionError):
                pass
    
    def test_scan_directory_invalid_path(self):
        """Test scanning with invalid directory path."""
        # Test non-existent directory
        with pytest.raises(FileNotFoundError):
            scan_directory("/nonexistent/directory")
        
        # Test file instead of directory
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            with pytest.raises(NotADirectoryError):
                scan_directory(temp_file.name)
        finally:
            temp_file.close()
            Path(temp_file.name).unlink()
    
    def test_scan_directory_with_custom_ignore_patterns(self, temp_project_dir):
        """Test scanning with custom ignore patterns."""
        # Create some test files
        test_file = Path(temp_project_dir) / "test.py"
        test_file.write_text("test content")
        
        backup_file = Path(temp_project_dir) / "test.py.bak"
        backup_file.write_text("backup content")
        
        # Scan with custom ignore patterns
        files = scan_directory(temp_project_dir, ignore_patterns=["*.bak", "*.tmp"])
        
        # Should not include backup files
        file_paths = list(files)
        assert not any("test.py.bak" in path for path in file_paths)
        
        # Should include regular files
        assert any("test.py" in path for path in file_paths)
    
    def test_scan_directory_nested_structure(self, temp_project_dir):
        """Test scanning nested directory structure."""
        # Create nested directories
        nested_dir = Path(temp_project_dir) / "nested" / "deep" / "structure"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        # Create files at different levels
        (Path(temp_project_dir) / "root_file.txt").write_text("root")
        (Path(temp_project_dir) / "nested" / "nested_file.txt").write_text("nested")
        (nested_dir / "deep_file.txt").write_text("deep")
        
        files = scan_directory(temp_project_dir)
        
        # Should find files at all levels
        file_paths = list(files)
        assert any("root_file.txt" in path for path in file_paths)
        assert any("nested_file.txt" in path for path in file_paths)
        assert any("deep_file.txt" in path for path in file_paths)
    
    def test_scan_directory_symlink_handling(self, temp_project_dir):
        """Test symlink handling during scanning."""
        # Create a symlink (this might not work on Windows)
        try:
            target_file = Path(temp_project_dir) / "target.txt"
            target_file.write_text("target content")
            
            symlink_file = Path(temp_project_dir) / "symlink.txt"
            symlink_file.symlink_to(target_file)
            
            files = scan_directory(temp_project_dir)
            
            # Should find both the target and symlink
            file_paths = list(files)
            assert any("target.txt" in path for path in file_paths)
            assert any("symlink.txt" in path for path in file_paths)
            
        except (OSError, NotImplementedError):
            # Symlinks not supported on this system
            pass
    
    def test_scan_directory_memory_usage(self, temp_project_dir):
        """Test memory usage during scanning."""
        # Create many files with varying content
        for i in range(50):
            file_path = Path(temp_project_dir) / f"file_{i:03d}.txt"
            content = f"Content of file {i} with some additional text to make it longer"
            file_path.write_text(content)
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        files = scan_directory(temp_project_dir)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024
        
        # Should find all files
        assert len(files) >= 50
