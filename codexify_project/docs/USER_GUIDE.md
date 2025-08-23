# Codexify User Guide

Welcome to Codexify! This comprehensive guide will help you get started with using Codexify to collect, analyze, and manage code from your projects.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Configuration](#configuration)
5. [Achievements](#achievements)
6. [Hotkeys](#hotkeys)
7. [Troubleshooting](#troubleshooting)
8. [Tips and Tricks](#tips-and-tricks)

## Getting Started

### What is Codexify?

Codexify is a powerful tool designed for developers to:
- **Collect Code**: Gather code from various file types in your projects
- **Analyze Projects**: Get insights into code structure, quality, and metrics
- **Find Duplicates**: Identify duplicate code and similar files
- **Generate Reports**: Create formatted output in multiple formats
- **Track Progress**: Monitor your development activities with achievements

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Python**: Python 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 100MB free space for the application

### Installation

1. **Download Codexify**
   ```bash
   git clone <repository-url>
   cd codexify_project
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python -m run_gui
   ```

## Basic Usage

### Starting Codexify

#### GUI Mode
```bash
python -m run_gui
```

#### CLI Mode
```bash
python -m run_cli --help
```

### Your First Project

1. **Launch Codexify GUI**
   - Start the application using `python -m run_gui`
   - You'll see the main window with file lists and controls

2. **Load a Project**
   - Click the "Load Project" button
   - Navigate to your project directory
   - Select the folder and click "Open"

3. **View Project Files**
   - Files are automatically scanned and categorized
   - "Include" list shows files that match active formats
   - "Other" list shows files that don't match active formats

4. **Select File Formats**
   - Use the format checkboxes to select file types
   - Common formats are pre-selected
   - Files are automatically reclassified when formats change

5. **Collect Code**
   - Choose output format (TXT, MD, HTML)
   - Select save location
   - Click "Collect Code" to generate output

### Understanding the Interface

#### Main Window Components

- **Project Path**: Shows current project location
- **Format Selection**: Checkboxes for different file types
- **Include Files**: Files that will be included in output
- **Other Files**: Files that won't be included
- **Status Bar**: Shows current operation and progress
- **Action Buttons**: Load, Analyze, Find Duplicates, Collect

#### File Lists

- **File Name**: Name and extension of the file
- **Size**: File size in bytes/KB/MB
- **Path**: Relative path from project root
- **Status**: Whether file is included or excluded

## Advanced Features

### Project Analysis

Codexify provides comprehensive project analysis:

1. **Click "Analyze Project"**
   - Analysis runs in the background
   - Progress is shown in the status bar
   - Results are displayed in a new window

2. **Analysis Results Include**:
   - **Language Statistics**: Count of files by programming language
   - **File Categories**: Code, configuration, documentation, etc.
   - **Quality Metrics**: Comment ratios, code density, complexity
   - **Size Distribution**: File sizes and project structure

3. **Example Analysis Output**:
   ```
   Project Analysis Results
   ========================
   
   Total Files: 45
   Total Size: 2.3 MB
   
   Languages:
   - Python: 15 files (1.2 MB)
   - JavaScript: 8 files (0.8 MB)
   - HTML: 5 files (0.2 MB)
   - CSS: 3 files (0.1 MB)
   
   Categories:
   - Code: 23 files (2.0 MB)
   - Configuration: 12 files (0.2 MB)
   - Documentation: 10 files (0.1 MB)
   ```

### Duplicate Detection

Find duplicate code and similar files:

1. **Click "Find Duplicates"**
   - Duplicate detection runs in background
   - Progress is shown in status bar
   - Results are displayed in a new window

2. **Duplicate Types**:
   - **Exact Duplicates**: Identical file content
   - **Similar Files**: Files with high similarity (80%+)
   - **Code Blocks**: Duplicate code segments

3. **Example Duplicate Results**:
   ```
   Duplicate Detection Results
   ==========================
   
   Exact Duplicates: 2 groups
   - Group 1: 3 files (config.json, config.backup.json, config.old.json)
   - Group 2: 2 files (utils.py, helpers.py)
   
   Similar Files: 1 group
   - Group 1: 2 files (main.py, main_backup.py) - 85% similarity
   
   Total Size Saved: 15.2 KB
   ```

### Output Formats

Codexify supports multiple output formats:

#### Plain Text (TXT)
- Simple text format with file separators
- Includes file metadata (size, modification date)
- Easy to read and process

#### Markdown (MD)
- Structured format with code blocks
- File headers and metadata
- Suitable for documentation

#### HTML
- Web-ready format with CSS styling
- Interactive elements and navigation
- Professional appearance

## Configuration

### Accessing Configuration

1. **GUI Mode**: Use the configuration menu
2. **CLI Mode**: Use configuration commands
3. **Direct API**: Access through the engine

### Configuration Categories

#### App Settings
- **Theme**: Light, Dark, or Auto
- **Language**: English, Spanish, French, German
- **Auto-save**: Automatically save settings

#### Scanning Settings
- **Max File Size**: Maximum file size to process
- **Max Depth**: Maximum directory depth to scan
- **Follow Symlinks**: Whether to follow symbolic links

#### Analysis Settings
- **Quality Metrics**: Enable/disable code quality analysis
- **Similarity Threshold**: Minimum similarity for duplicate detection

#### Output Settings
- **Default Format**: Default output format
- **Include Metadata**: Whether to include file metadata
- **Encoding**: Output file encoding

### Managing Presets

#### Creating Presets
```python
# Create a preset for web development
engine.create_preset("web_dev", "Web development settings")

# Create a preset with custom configuration
custom_config = {
    "scanning": {"max_file_size": 5242880},
    "output": {"default_format": "html"}
}
engine.create_preset("custom", "Custom settings", custom_config)
```

#### Loading Presets
```python
# Load a preset
engine.load_preset("web_dev")

# List available presets
presets = engine.get_presets()
```

#### Exporting/Importing
```python
# Export current configuration
engine.export_configuration("my_config.json")

# Import configuration
engine.import_configuration("my_config.json")
```

## Achievements

### Understanding Achievements

Codexify includes a gamification system to track your progress:

#### Achievement Categories
- **Projects**: Loading and managing projects
- **Files**: Processing files and working with formats
- **Analysis**: Running project analysis
- **Duplicates**: Finding duplicate code
- **Collection**: Creating code collections
- **Efficiency**: Performance and optimization
- **Exploration**: Discovering advanced features

#### Achievement Levels
- **Bronze**: Basic achievements (10 points)
- **Silver**: Intermediate achievements (25 points)
- **Gold**: Advanced achievements (50 points)
- **Platinum**: Expert achievements (100 points)

### Viewing Achievements

#### GUI Mode
- Access through the achievements menu
- View progress and unlocked achievements
- See statistics and rankings

#### CLI Mode
```bash
# View all achievements
python -m run_cli achievements

# View unlocked achievements
python -m run_cli achievements --unlocked

# View progress
python -m run_cli achievements --progress
```

### Example Achievements

```
🏆 First Project (10 points)
   Load your first project
   Status: ✅ Unlocked

📁 File Explorer (25 points)
   Process 100 files
   Status: 🔄 45/100 files processed

🔍 Code Analyzer (50 points)
   Analyze 10 projects
   Status: 🔄 3/10 projects analyzed

🎯 Duplicate Hunter (25 points)
   Find duplicates in 5 projects
   Status: 🔄 2/5 projects completed
```

## Hotkeys

### Default Hotkeys

Codexify includes pre-configured keyboard shortcuts:

#### File Operations
- **Ctrl+O**: Open Project
- **Ctrl+S**: Save Collection
- **Ctrl+E**: Export Configuration

#### Analysis Operations
- **Ctrl+A**: Analyze Project
- **Ctrl+D**: Find Duplicates
- **Ctrl+Q**: Quick Scan

#### Navigation
- **Tab**: Switch between file lists
- **Ctrl+F**: Focus search/filter
- **F5**: Refresh project

#### View Controls
- **Ctrl+T**: Toggle theme
- **Ctrl+L**: Toggle line numbers
- **F11**: Toggle fullscreen

### Customizing Hotkeys

#### GUI Mode
- Access through the hotkeys menu
- Modify existing shortcuts
- Create new shortcuts

#### CLI Mode
```bash
# View all hotkeys
python -m run_cli hotkeys

# Update a hotkey
python -m run_cli hotkeys --update "open_project" "Ctrl+Shift+O"

# Enable/disable hotkeys
python -m run_cli hotkeys --disable "open_project"
```

#### Hotkey Profiles
```python
# Create a profile
engine.create_hotkey_profile("gaming", "Gaming profile")

# Load a profile
engine.load_hotkey_profile("gaming")

# List profiles
profiles = engine.get_hotkey_profiles()
```

### Hotkey Categories

- **File**: Open, save, export operations
- **Analysis**: Run analysis, find duplicates
- **Navigation**: File navigation and selection
- **View**: Interface controls and display
- **Application**: Preferences, help, about
- **Development**: Debug mode, console, refresh
- **Custom**: User-defined shortcuts

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep codexify

# Check for errors
python -m run_gui --debug
```

#### File Scanning Issues
```bash
# Check file permissions
ls -la /path/to/project

# Verify .codexignore file
cat .codexignore

# Test scanner directly
python -c "from codexify.core.scanner import Scanner; s = Scanner(); print(s.scan_directory('/path/to/project'))"
```

#### Performance Issues
```bash
# Check system resources
top
htop

# Monitor memory usage
python -c "import psutil; print(psutil.virtual_memory())"

# Profile specific operations
python -m cProfile -o profile.stats run_gui.py
```

#### Output Generation Issues
```bash
# Check file permissions
ls -la /output/directory

# Verify encoding
file -i output_file.txt

# Test builder directly
python -c "from codexify.core.builder import Builder; b = Builder(); print(b.build_output(files, 'output.txt', 'txt'))"
```

### Getting Help

1. **Check Documentation**: Review this guide and code comments
2. **Search Issues**: Look for similar problems in the issue tracker
3. **Create Issue**: Provide detailed information about the problem
4. **Ask Questions**: Use the discussion forum for questions

### Debug Mode

Enable debug mode for detailed information:

```bash
# GUI with debug output
python -m run_gui --debug

# CLI with debug output
python -m run_cli --debug

# Set logging level
export CODEXIFY_LOG_LEVEL=DEBUG
python -m run_gui
```

## Tips and Tricks

### Efficient Workflow

1. **Use Presets**: Create presets for different project types
2. **Batch Operations**: Use CLI for automated processing
3. **Regular Analysis**: Run analysis regularly to track progress
4. **Backup Configurations**: Export your settings regularly

### Performance Optimization

1. **Limit File Sizes**: Set appropriate max file size limits
2. **Use .codexignore**: Exclude unnecessary files and directories
3. **Batch Processing**: Process multiple projects in sequence
4. **Monitor Resources**: Watch memory and CPU usage

### Best Practices

1. **Organize Projects**: Keep projects in dedicated directories
2. **Use Version Control**: Track changes with Git
3. **Regular Backups**: Backup your configurations and presets
4. **Document Workflows**: Document your analysis processes

### Advanced Usage

#### Custom File Types
```python
# Add custom file format
engine.add_file_format(".xyz", "Custom Format")

# Remove file format
engine.remove_file_format(".xyz")

# List all formats
formats = engine.get_file_formats()
```

#### Automated Processing
```bash
# Process multiple projects
for project in projects/*; do
    python -m run_cli scan "$project"
    python -m run_cli analyze
    python -m run_cli collect --output "outputs/$(basename $project).md"
done
```

#### Integration with Other Tools
```python
# Use with Jupyter notebooks
from codexify.engine import CodexifyEngine
engine = CodexifyEngine()
results = engine.analyze_project("/path/to/project")

# Use with CI/CD pipelines
python -m run_cli scan /path/to/project
python -m run_cli analyze --output analysis.json
python -m run_cli collect --output code_collection.md
```

## Conclusion

Codexify is a powerful tool that can significantly improve your code analysis and documentation workflow. By following this guide and exploring the advanced features, you'll be able to:

- Efficiently collect and organize code from your projects
- Gain insights into code quality and structure
- Identify and resolve code duplication
- Generate professional documentation
- Track your development progress
- Customize the tool to your specific needs

Remember to:
- Start with simple projects to learn the interface
- Experiment with different output formats
- Use presets to save time on common tasks
- Explore the achievement system for motivation
- Customize hotkeys for your workflow
- Report issues and contribute to improvements

Happy coding with Codexify! 🚀
