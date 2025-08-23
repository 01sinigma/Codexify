"""
Unit tests for CodexifyState class.
"""

import pytest
from datetime import datetime
from pathlib import Path

from codexify.state import CodexifyState


class TestCodexifyState:
    """Test cases for CodexifyState class."""
    
    def test_initialization(self):
        """Test state initialization with default values."""
        state = CodexifyState()
        
        assert state.project_path == ""
        assert state.all_discovered_files == set()
        assert state.include_files == set()
        assert state.other_files == set()
        assert state.ignored_files == set()
        assert state.file_inclusion_modes == {}
        assert state.active_formats == set()
        assert state.is_busy is False
        assert state.status_message == "Ready"
    
    def test_set_project_path(self):
        """Test setting project path."""
        state = CodexifyState()
        test_path = "/test/project"
        
        state.project_path = test_path
        
        assert state.project_path == test_path
    
    def test_add_files(self):
        """Test adding files to the state."""
        state = CodexifyState()
        test_files = {"file1.py", "file2.py"}
        
        state.all_discovered_files = test_files
        
        assert len(state.all_discovered_files) == 2
        assert "file1.py" in state.all_discovered_files
        assert "file2.py" in state.all_discovered_files
    
    def test_set_include_files(self):
        """Test setting include files."""
        state = CodexifyState()
        include_files = {"file1.py", "file2.py"}
        
        state.include_files = include_files
        
        assert state.include_files == include_files
    
    def test_set_other_files(self):
        """Test setting other files."""
        state = CodexifyState()
        other_files = {"file3.txt", "file4.log"}
        
        state.other_files = other_files
        
        assert state.other_files == other_files
    
    def test_set_ignored_files(self):
        """Test setting ignored files."""
        state = CodexifyState()
        ignored_files = {"*.tmp", "*.log"}
        
        state.ignored_files = ignored_files
        
        assert state.ignored_files == ignored_files
    
    def test_file_inclusion_modes(self):
        """Test file inclusion modes."""
        state = CodexifyState()
        
        # Set inclusion modes
        state.file_inclusion_modes = {
            "file1.py": "include",
            "file2.py": "include",
            "file3.txt": "other"
        }
        
        assert state.file_inclusion_modes["file1.py"] == "include"
        assert state.file_inclusion_modes["file2.py"] == "include"
        assert state.file_inclusion_modes["file3.txt"] == "other"
    
    def test_active_formats_management(self):
        """Test active formats set operations."""
        state = CodexifyState()
        
        # Add formats
        state.active_formats.add(".py")
        state.active_formats.add(".js")
        
        assert ".py" in state.active_formats
        assert ".js" in state.active_formats
        assert len(state.active_formats) == 2
        
        # Remove format
        state.active_formats.remove(".py")
        assert ".py" not in state.active_formats
        assert ".js" in state.active_formats
    
    def test_busy_status(self):
        """Test busy status flag."""
        state = CodexifyState()
        
        # Test busy flag
        state.is_busy = True
        assert state.is_busy is True
        
        # Test not busy
        state.is_busy = False
        assert state.is_busy is False
    
    def test_status_message(self):
        """Test status message management."""
        state = CodexifyState()
        
        # Test default status
        assert state.status_message == "Ready"
        
        # Test setting status
        state.status_message = "Processing files..."
        assert state.status_message == "Processing files..."
        
        # Test updating status
        state.status_message = "Analysis complete"
        assert state.status_message == "Analysis complete"
    
    def test_state_validation(self):
        """Test state validation methods."""
        state = CodexifyState()
        
        # Test empty state validation
        assert state.project_path == ""
        assert len(state.all_discovered_files) == 0
        
        # Test project loaded validation
        state.project_path = "/test/project"
        assert state.project_path == "/test/project"
        assert state.project_path != ""
    
    def test_file_count_methods(self):
        """Test file counting methods."""
        state = CodexifyState()
        
        # Test with no files
        assert len(state.all_discovered_files) == 0
        assert len(state.include_files) == 0
        assert len(state.other_files) == 0
        assert len(state.ignored_files) == 0
        
        # Test with files
        state.all_discovered_files = {"file1.py", "file2.py", "file3.txt"}
        state.include_files = {"file1.py", "file2.py"}
        state.other_files = {"file3.txt"}
        state.ignored_files = {"*.tmp", "*.log"}
        
        assert len(state.all_discovered_files) == 3
        assert len(state.include_files) == 2
        assert len(state.other_files) == 1
        assert len(state.ignored_files) == 2
    
    def test_format_validation(self):
        """Test format validation methods."""
        state = CodexifyState()
        
        # Test with no formats
        assert len(state.active_formats) == 0
        
        # Test with formats
        state.active_formats.add(".py")
        state.active_formats.add(".js")
        
        assert len(state.active_formats) == 2
        assert ".py" in state.active_formats
        assert ".js" in state.active_formats
    
    def test_operation_status(self):
        """Test operation status checking."""
        state = CodexifyState()
        
        # Test no operations running
        assert state.is_busy is False
        
        # Test with operation running
        state.is_busy = True
        assert state.is_busy is True
        
        # Test operation completion
        state.is_busy = False
        assert state.is_busy is False
    
    def test_state_representation(self):
        """Test string representation of state."""
        state = CodexifyState()
        
        # Test empty state
        str_repr = str(state)
        assert "CodexifyState" in str_repr
        assert "project_path=''" in str_repr
        
        # Test populated state
        state.project_path = "/test/project"
        state.all_discovered_files = {"test.py"}
        
        str_repr = str(state)
        assert "/test/project" in str_repr
        assert "test.py" in str_repr
    
    def test_state_equality(self):
        """Test state equality comparison."""
        state1 = CodexifyState()
        state2 = CodexifyState()
        
        # Test equal empty states
        assert state1 == state2
        
        # Test different states
        state1.project_path = "/test1"
        state2.project_path = "/test2"
        assert state1 != state2
        
        # Test same values
        state2.project_path = "/test1"
        assert state1 == state2
    
    def test_state_copy(self):
        """Test state copying functionality."""
        state = CodexifyState()
        state.project_path = "/test/project"
        state.all_discovered_files = {"test.py"}
        state.active_formats.add(".py")
        
        # Create copy
        copied_state = CodexifyState(
            project_path=state.project_path,
            all_discovered_files=state.all_discovered_files.copy(),
            active_formats=state.active_formats.copy()
        )
        
        # Verify copy
        assert copied_state.project_path == state.project_path
        assert copied_state.all_discovered_files == state.all_discovered_files
        assert copied_state.active_formats == state.active_formats
        
        # Verify independence
        copied_state.project_path = "/different/project"
        assert copied_state.project_path != state.project_path
    
    def test_file_operations(self):
        """Test file operations on state."""
        state = CodexifyState()
        
        # Add files to different categories
        state.all_discovered_files.add("main.py")
        state.all_discovered_files.add("utils.py")
        state.all_discovered_files.add("config.json")
        
        state.include_files.add("main.py")
        state.include_files.add("utils.py")
        state.other_files.add("config.json")
        
        # Verify file categorization
        assert "main.py" in state.include_files
        assert "utils.py" in state.include_files
        assert "config.json" in state.other_files
        
        # Test file inclusion modes
        state.file_inclusion_modes["main.py"] = "include"
        state.file_inclusion_modes["utils.py"] = "include"
        state.file_inclusion_modes["config.json"] = "other"
        
        assert state.file_inclusion_modes["main.py"] == "include"
        assert state.file_inclusion_modes["config.json"] == "other"
    
    def test_format_operations(self):
        """Test format operations on state."""
        state = CodexifyState()
        
        # Add formats
        state.active_formats.add(".py")
        state.active_formats.add(".js")
        state.active_formats.add(".html")
        
        # Verify formats
        assert ".py" in state.active_formats
        assert ".js" in state.active_formats
        assert ".html" in state.active_formats
        
        # Remove format
        state.active_formats.remove(".js")
        assert ".js" not in state.active_formats
        assert ".py" in state.active_formats
        assert ".html" in state.active_formats
        
        # Clear formats
        state.active_formats.clear()
        assert len(state.active_formats) == 0
    
    def test_ignored_files_operations(self):
        """Test ignored files operations."""
        state = CodexifyState()
        
        # Add ignore patterns
        state.ignored_files.add("*.pyc")
        state.ignored_files.add("__pycache__")
        state.ignored_files.add("*.log")
        
        # Verify ignore patterns
        assert "*.pyc" in state.ignored_files
        assert "__pycache__" in state.ignored_files
        assert "*.log" in state.ignored_files
        
        # Remove ignore pattern
        state.ignored_files.remove("*.log")
        assert "*.log" not in state.ignored_files
        assert "*.pyc" in state.ignored_files
        assert "__pycache__" in state.ignored_files
    
    def test_status_message_operations(self):
        """Test status message operations."""
        state = CodexifyState()
        
        # Test default status
        assert state.status_message == "Ready"
        
        # Test various status messages
        statuses = [
            "Scanning files...",
            "Analyzing project...",
            "Finding duplicates...",
            "Collecting code...",
            "Operation complete"
        ]
        
        for status in statuses:
            state.status_message = status
            assert state.status_message == status
    
    def test_busy_status_operations(self):
        """Test busy status operations."""
        state = CodexifyState()
        
        # Test default busy status
        assert state.is_busy is False
        
        # Test setting busy
        state.is_busy = True
        assert state.is_busy is True
        
        # Test toggling busy status
        state.is_busy = not state.is_busy
        assert state.is_busy is False
        
        state.is_busy = not state.is_busy
        assert state.is_busy is True
    
    def test_project_path_operations(self):
        """Test project path operations."""
        state = CodexifyState()
        
        # Test default project path
        assert state.project_path == ""
        
        # Test setting project path
        test_paths = [
            "/home/user/project",
            "C:\\Users\\user\\project",
            "project",
            "/very/long/path/to/project/with/many/levels"
        ]
        
        for path in test_paths:
            state.project_path = path
            assert state.project_path == path
        
        # Test clearing project path
        state.project_path = ""
        assert state.project_path == ""
    
    def test_complex_state_scenario(self):
        """Test complex state scenario with multiple operations."""
        state = CodexifyState()
        
        # Simulate a complete workflow
        # 1. Set project path
        state.project_path = "/test/project"
        assert state.project_path == "/test/project"
        
        # 2. Discover files
        state.all_discovered_files = {
            "src/main.py", "src/utils.py", "src/config.py",
            "tests/test_main.py", "tests/test_utils.py",
            "docs/README.md", "docs/API.md",
            "config.json", "requirements.txt"
        }
        assert len(state.all_discovered_files) == 9
        
        # 3. Set active formats
        state.active_formats = {".py", ".md", ".json", ".txt"}
        assert len(state.active_formats) == 4
        
        # 4. Categorize files
        state.include_files = {"src/main.py", "src/utils.py", "src/config.py", "tests/test_main.py", "tests/test_utils.py"}
        state.other_files = {"docs/README.md", "docs/API.md", "config.json", "requirements.txt"}
        assert len(state.include_files) == 5
        assert len(state.other_files) == 4
        
        # 5. Set file inclusion modes
        for file_path in state.include_files:
            state.file_inclusion_modes[file_path] = "include"
        for file_path in state.other_files:
            state.file_inclusion_modes[file_path] = "other"
        
        assert len(state.file_inclusion_modes) == 9
        
        # 6. Set ignore patterns
        state.ignored_files = {"*.pyc", "__pycache__", "*.log", ".git"}
        assert len(state.ignored_files) == 4
        
        # 7. Set status
        state.is_busy = True
        state.status_message = "Processing complete project"
        assert state.is_busy is True
        assert state.status_message == "Processing complete project"
        
        # 8. Verify final state
        assert state.project_path == "/test/project"
        assert len(state.all_discovered_files) == 9
        assert len(state.include_files) == 5
        assert len(state.other_files) == 4
        assert len(state.active_formats) == 4
        assert len(state.ignored_files) == 4
        assert len(state.file_inclusion_modes) == 9
        assert state.is_busy is True
        assert state.status_message == "Processing complete project"
