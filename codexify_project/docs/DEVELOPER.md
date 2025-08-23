# Codexify Developer Documentation

This document provides comprehensive information for developers working on the Codexify project, including architecture overview, development setup, testing guidelines, and contribution guidelines.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Development Setup](#development-setup)
4. [Code Structure](#code-structure)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Documentation](#documentation)
8. [Contributing](#contributing)
9. [Release Process](#release-process)
10. [Troubleshooting](#troubleshooting)

## Project Overview

Codexify is a tool for developers to collect, analyze, and manage code from various sources within a project. It follows a clean architecture pattern with clear separation of concerns:

- **Engine Core**: Business logic and state management
- **Systems**: Auxiliary functionality (config, achievements, hotkeys)
- **Clients**: User interfaces (GUI, CLI)
- **Core Modules**: Core functionality (scanner, builder, analyzer)

## Architecture

### Core Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Event-Driven**: Components communicate through events
4. **API-First**: Clear interfaces between components
5. **Testable**: All components are designed for easy testing

### Component Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Clients     │    │      Engine     │    │     Systems     │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │    GUI    │  │◄──►│   State    │  │    │  │   Config  │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │    CLI    │  │    │   Events   │  │    │  │Achievements│  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    │  ┌───────────┐  │    │  ┌───────────┐  │
                       │   Scanner   │  │    │  │ Hotkeys   │  │
                       │  └───────────┘  │    │  └───────────┘  │
                       │  ┌───────────┐  │    └─────────────────┘
                       │   Builder    │  │
                       │  └───────────┘  │
                       │  ┌───────────┐  │
                       │  Analyzer    │  │
                       │  └───────────┘  │
                       └─────────────────┘
```

### Data Flow

1. **Client Request**: GUI/CLI makes request to Engine
2. **Engine Processing**: Engine coordinates with appropriate systems
3. **Event Emission**: Progress and completion events are emitted
4. **Client Update**: Clients receive events and update UI/state
5. **Result Return**: Final result returned to client

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd codexify_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. **Verify installation**
   ```bash
   python -m run_gui
   python -m run_cli --help
   ```

### Development Dependencies

The following tools are used for development:

- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **isort**: Import sorting
- **coverage**: Code coverage

## Code Structure

### Directory Layout

```
codexify_project/
├── codexify/                 # Main package
│   ├── __init__.py
│   ├── engine.py            # Main engine
│   ├── state.py             # State management
│   ├── events.py            # Event system
│   ├── core/                # Core modules
│   │   ├── scanner.py       # File scanning
│   │   ├── builder.py       # Output building
│   │   ├── analyzer.py      # Code analysis
│   │   └── duplicate_finder.py
│   ├── systems/             # System modules
│   │   ├── config_manager.py
│   │   ├── achievement_system.py
│   │   └── hotkey_manager.py
│   └── clients/             # Client modules
│       ├── gui/             # GUI client
│       └── cli.py           # CLI client
├── tests/                   # Test suite
├── docs/                    # Documentation
├── requirements.txt         # Runtime dependencies
├── requirements-test.txt    # Test dependencies
├── run_gui.py              # GUI entry point
├── run_cli.py              # CLI entry point
├── run_tests.py            # Test runner
└── pytest.ini             # Pytest configuration
```

### Module Responsibilities

#### Engine (`codexify/engine.py`)
- Coordinates all operations
- Manages state and events
- Provides public API for clients
- Handles background processing

#### State (`codexify/state.py`)
- Single source of truth for application state
- Immutable data structures
- State validation and transitions

#### Events (`codexify/events.py`)
- Observer pattern implementation
- Event emission and subscription
- Decoupled component communication

#### Core Modules
- **Scanner**: File discovery and filtering
- **Builder**: Output generation in various formats
- **Analyzer**: Code analysis and metrics
- **Duplicate Finder**: Duplicate code detection

#### Systems
- **Config Manager**: Settings and presets
- **Achievement System**: Gamification and progress tracking
- **Hotkey Manager**: Keyboard shortcuts and profiles

## Testing

### Test Structure

Tests are organized to mirror the main code structure:

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_state.py            # State management tests
├── test_events.py           # Event system tests
├── test_scanner.py          # Scanner tests
├── test_config_manager.py   # Config manager tests
└── integration/             # Integration tests
    ├── test_engine_gui.py   # Engine-GUI integration
    └── test_engine_cli.py   # Engine-CLI integration
```

### Running Tests

#### All Tests
```bash
python run_tests.py
```

#### Specific Test Categories
```bash
# Unit tests only
python run_tests.py --unit-only

# Integration tests only
python run_tests.py --integration-only

# Linting only
python run_tests.py --lint-only

# Specific test file
python run_tests.py --test tests/test_state.py
```

#### With Coverage
```bash
python run_tests.py --coverage
```

#### Parallel Execution
```bash
python run_tests.py --parallel
```

### Test Guidelines

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Structure**: Follow AAA pattern (Arrange, Act, Assert)
3. **Test Isolation**: Each test should be independent
4. **Mocking**: Use mocks for external dependencies
5. **Coverage**: Aim for >80% code coverage
6. **Performance**: Tests should complete quickly (<1 second for unit tests)

### Example Test

```python
def test_scanner_ignores_binary_files():
    """Test that scanner correctly identifies and ignores binary files."""
    # Arrange
    scanner = Scanner()
    binary_content = b"\x00\x01\x02\x03\xff\xfe"
    
    # Act
    is_binary = scanner._is_binary_file(binary_content)
    
    # Assert
    assert is_binary is True
```

## Code Quality

### Code Style

We use the following tools to maintain code quality:

- **Black**: Automatic code formatting
- **isort**: Import sorting
- **flake8**: Style and error checking
- **mypy**: Type checking

### Pre-commit Checks

Before committing code, ensure:

1. **Tests pass**: `python run_tests.py --unit-only`
2. **Linting passes**: `python run_tests.py --lint-only`
3. **Type checking passes**: `python run_tests.py --type-check`
4. **Code is formatted**: `black codexify/ tests/`

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No debugging code remains
- [ ] Error handling is appropriate
- [ ] Performance considerations addressed

## Documentation

### Documentation Standards

1. **Docstrings**: Use Google-style docstrings
2. **Type Hints**: Include type hints for all functions
3. **Examples**: Provide usage examples in docstrings
4. **API Documentation**: Document all public APIs

### Example Documentation

```python
def scan_directory(self, directory_path: str) -> List[Dict[str, Any]]:
    """Scan a directory for files and return file information.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        List of dictionaries containing file information
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        PermissionError: If directory access is denied
        
    Example:
        >>> scanner = Scanner()
        >>> files = scanner.scan_directory("/path/to/project")
        >>> len(files)
        10
    """
```

### Documentation Generation

Generate documentation using:

```bash
# Install documentation tools
pip install sphinx sphinx-rtd-theme

# Generate documentation
cd docs
make html
```

## Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow coding standards
   - Write tests for new functionality
   - Update documentation

3. **Test Changes**
   ```bash
   python run_tests.py
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Commit Message Format

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

### Pull Request Guidelines

1. **Description**: Clear description of changes
2. **Testing**: Evidence that tests pass
3. **Documentation**: Updated documentation
4. **Review**: Address review comments
5. **Squash**: Squash commits before merging

## Release Process

### Version Management

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Steps

1. **Update Version**
   - Update version in `__init__.py` files
   - Update version in documentation

2. **Create Release Branch**
   ```bash
   git checkout -b release/v1.0.0
   ```

3. **Final Testing**
   ```bash
   python run_tests.py --coverage
   python -m run_gui
   python -m run_cli --help
   ```

4. **Create Tag**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

5. **Merge to Main**
   ```bash
   git checkout main
   git merge release/v1.0.0
   git push origin main
   ```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the right directory
cd codexify_project

# Check Python path
python -c "import sys; print(sys.path)"

# Install dependencies
pip install -r requirements.txt
```

#### Test Failures
```bash
# Run specific failing test
python run_tests.py --test tests/test_failing.py -v

# Check test dependencies
pip install -r requirements-test.txt

# Run with debug output
python -m pytest tests/ -v -s
```

#### GUI Issues
```bash
# Check Tkinter installation
python -c "import tkinter; print('Tkinter OK')"

# Run with debug output
python -m run_gui --debug
```

#### Performance Issues
```bash
# Profile specific operations
python -m cProfile -o profile.stats run_gui.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### Getting Help

1. **Check Documentation**: Review this document and code comments
2. **Search Issues**: Look for similar issues in GitHub
3. **Create Issue**: Provide detailed information about the problem
4. **Ask Questions**: Use GitHub Discussions for questions

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set specific logger
logging.getLogger('codexify').setLevel(logging.DEBUG)
```

## Conclusion

This developer documentation provides a comprehensive guide for contributing to the Codexify project. Follow the established patterns and guidelines to ensure code quality and maintainability.

For additional questions or clarifications, please refer to the project issues or create a new discussion topic.
