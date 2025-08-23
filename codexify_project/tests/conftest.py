"""
Pytest configuration and common fixtures for Codexify tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from codexify.engine import CodexifyEngine
from codexify.state import CodexifyState
from codexify.events import EventManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample project files for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample project structure
    project_structure = {
        'src': {
            'main.py': 'print("Hello, World!")\n# This is a comment',
            'utils.py': 'def helper():\n    return "helper"',
            'config.json': '{"debug": true}',
            'styles.css': 'body { margin: 0; }',
            'README.md': '# Sample Project\n\nThis is a test project.'
        },
        'tests': {
            'test_main.py': 'import unittest\n\nclass TestMain(unittest.TestCase):\n    pass',
            'test_utils.py': 'import unittest\n\nclass TestUtils(unittest.TestCase):\n    pass'
        },
        'docs': {
            'api.md': '# API Documentation\n\n## Overview\n\nThis is the API docs.',
            'setup.md': '# Setup Guide\n\n## Installation\n\nFollow these steps...'
        },
        '.codexignore': '*.pyc\n__pycache__\n*.log\n.DS_Store',
        'requirements.txt': 'pytest>=7.0.0\nrequests>=2.28.0'
    }
    
    def create_files(base_path, structure):
        for name, content in structure.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir(exist_ok=True)
                create_files(path, content)
            else:
                path.write_text(content, encoding='utf-8')
    
    create_files(Path(temp_dir), project_structure)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_event_manager():
    """Create a mock event manager for testing."""
    return Mock(spec=EventManager)


@pytest.fixture
def engine_instance(temp_project_dir):
    """Create a CodexifyEngine instance for testing."""
    engine = CodexifyEngine()
    # Don't start the engine to avoid background threads in tests
    return engine


@pytest.fixture
def state_instance():
    """Create a CodexifyState instance for testing."""
    return CodexifyState()


@pytest.fixture
def sample_files():
    """Sample file data for testing."""
    return [
        {
            'path': 'src/main.py',
            'size': 1024,
            'modified': 1640995200.0,
            'is_binary': False,
            'encoding': 'utf-8'
        },
        {
            'path': 'src/utils.py',
            'size': 512,
            'modified': 1640995200.0,
            'is_binary': False,
            'encoding': 'utf-8'
        },
        {
            'path': 'src/config.json',
            'size': 256,
            'modified': 1640995200.0,
            'is_binary': False,
            'encoding': 'utf-8'
        }
    ]


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        'total_files': 10,
        'total_size': 2048,
        'languages': {
            'Python': {'count': 3, 'size': 1024, 'lines': 50},
            'JSON': {'count': 1, 'size': 256, 'lines': 10},
            'Markdown': {'count': 2, 'size': 512, 'lines': 30}
        },
        'categories': {
            'code': {'count': 4, 'size': 1280},
            'config': {'count': 2, 'size': 512},
            'documentation': {'count': 2, 'size': 512}
        },
        'quality_metrics': {
            'avg_comment_ratio': 0.15,
            'avg_code_density': 0.85,
            'total_lines': 90
        }
    }


@pytest.fixture
def sample_duplicates_result():
    """Sample duplicates result for testing."""
    return {
        'exact_duplicates': [
            {
                'files': ['src/file1.py', 'src/file2.py'],
                'size': 1024,
                'hash': 'abc123'
            }
        ],
        'similar_files': [
            {
                'files': ['src/utils.py', 'src/helpers.py'],
                'similarity': 0.85,
                'size': 512
            }
        ],
        'total_duplicates': 2,
        'total_size_saved': 1536
    }


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'app': {
            'theme': 'dark',
            'language': 'en',
            'auto_save': True
        },
        'scanning': {
            'max_file_size': 1048576,
            'max_depth': 10,
            'follow_symlinks': False
        },
        'analysis': {
            'enable_quality_metrics': True,
            'similarity_threshold': 0.8
        },
        'output': {
            'default_format': 'md',
            'include_metadata': True,
            'encoding': 'utf-8'
        },
        'ui': {
            'window_width': 1200,
            'window_height': 800,
            'show_line_numbers': True
        }
    }


@pytest.fixture
def sample_achievements():
    """Sample achievements for testing."""
    return {
        'first_project': {
            'id': 'first_project',
            'name': 'First Project',
            'description': 'Load your first project',
            'category': 'projects',
            'points': 10,
            'unlocked': True,
            'unlocked_at': '2024-01-01T00:00:00Z'
        },
        'file_explorer': {
            'id': 'file_explorer',
            'name': 'File Explorer',
            'description': 'Process 100 files',
            'category': 'files',
            'points': 25,
            'unlocked': False,
            'progress': 50,
            'target': 100
        }
    }


@pytest.fixture
def sample_hotkeys():
    """Sample hotkeys for testing."""
    return {
        'open_project': {
            'id': 'open_project',
            'name': 'Open Project',
            'category': 'file',
            'key': 'O',
            'modifiers': ['Ctrl'],
            'enabled': True,
            'description': 'Open a new project'
        },
        'save_collection': {
            'id': 'save_collection',
            'name': 'Save Collection',
            'category': 'file',
            'key': 'S',
            'modifiers': ['Ctrl'],
            'enabled': True,
            'description': 'Save the current collection'
        }
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def assert_file_exists(file_path):
        """Assert that a file exists."""
        assert Path(file_path).exists(), f"File {file_path} does not exist"
    
    @staticmethod
    def assert_file_content(file_path, expected_content):
        """Assert that a file contains expected content."""
        content = Path(file_path).read_text(encoding='utf-8')
        assert expected_content in content, f"Expected content not found in {file_path}"
    
    @staticmethod
    def assert_directory_structure(base_path, expected_structure):
        """Assert that a directory has the expected structure."""
        for name, is_dir in expected_structure.items():
            path = base_path / name
            if is_dir:
                assert path.is_dir(), f"Expected directory {name} not found"
            else:
                assert path.is_file(), f"Expected file {name} not found"
    
    @staticmethod
    def create_test_file(file_path, content):
        """Create a test file with given content."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI"
    )
    config.addinivalue_line(
        "markers", "engine: mark test as testing engine functionality"
    )
    config.addinivalue_line(
        "markers", "systems: mark test as testing system modules"
    )
