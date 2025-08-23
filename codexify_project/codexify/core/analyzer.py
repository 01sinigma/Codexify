import os
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

class ProjectAnalyzer:
    """
    Analyzes project structure and provides comprehensive insights.
    """
    
    def __init__(self):
        # Common programming language extensions and their characteristics
        self.language_extensions = {
            '.py': {'name': 'Python', 'type': 'scripting', 'comment': '#', 'multiline_comment': '"""'},
            '.js': {'name': 'JavaScript', 'type': 'scripting', 'comment': '//', 'multiline_comment': '/*'},
            '.ts': {'name': 'TypeScript', 'type': 'scripting', 'comment': '//', 'multiline_comment': '/*'},
            '.jsx': {'name': 'React JSX', 'type': 'frontend', 'comment': '//', 'multiline_comment': '/*'},
            '.tsx': {'name': 'React TSX', 'type': 'frontend', 'comment': '//', 'multiline_comment': '/*'},
            '.html': {'name': 'HTML', 'type': 'markup', 'comment': '<!--', 'multiline_comment': '-->'},
            '.css': {'name': 'CSS', 'type': 'styling', 'comment': '/*', 'multiline_comment': '*/'},
            '.scss': {'name': 'Sass', 'type': 'styling', 'comment': '//', 'multiline_comment': '/*'},
            '.less': {'name': 'Less', 'type': 'styling', 'comment': '//', 'multiline_comment': '/*'},
            '.java': {'name': 'Java', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.cpp': {'name': 'C++', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.c': {'name': 'C', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.cs': {'name': 'C#', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.php': {'name': 'PHP', 'type': 'scripting', 'comment': '//', 'multiline_comment': '/*'},
            '.rb': {'name': 'Ruby', 'type': 'scripting', 'comment': '#', 'multiline_comment': '=begin'},
            '.go': {'name': 'Go', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.rs': {'name': 'Rust', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.swift': {'name': 'Swift', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.kt': {'name': 'Kotlin', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.scala': {'name': 'Scala', 'type': 'compiled', 'comment': '//', 'multiline_comment': '/*'},
            '.sql': {'name': 'SQL', 'type': 'query', 'comment': '--', 'multiline_comment': '/*'},
            '.sh': {'name': 'Shell Script', 'type': 'scripting', 'comment': '#', 'multiline_comment': None},
            '.bat': {'name': 'Batch', 'type': 'scripting', 'comment': 'REM', 'multiline_comment': None},
            '.ps1': {'name': 'PowerShell', 'type': 'scripting', 'comment': '#', 'multiline_comment': None},
            '.yml': {'name': 'YAML', 'type': 'config', 'comment': '#', 'multiline_comment': None},
            '.yaml': {'name': 'YAML', 'type': 'config', 'comment': '#', 'multiline_comment': None},
            '.json': {'name': 'JSON', 'type': 'config', 'comment': None, 'multiline_comment': None},
            '.xml': {'name': 'XML', 'type': 'markup', 'comment': '<!--', 'multiline_comment': '-->'},
            '.toml': {'name': 'TOML', 'type': 'config', 'comment': '#', 'multiline_comment': None},
            '.ini': {'name': 'INI', 'type': 'config', 'comment': ';', 'multiline_comment': None},
            '.md': {'name': 'Markdown', 'type': 'documentation', 'comment': None, 'multiline_comment': None},
            '.txt': {'name': 'Text', 'type': 'documentation', 'comment': None, 'multiline_comment': None},
            '.rst': {'name': 'reStructuredText', 'type': 'documentation', 'comment': None, 'multiline_comment': None}
        }
        
        # File type categories
        self.file_categories = {
            'code': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh', '.bat', '.ps1'],
            'markup': ['.html', '.xml', '.md', '.rst'],
            'styling': ['.css', '.scss', '.less'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.xml'],
            'documentation': ['.md', '.txt', '.rst', '.pdf'],
            'data': ['.csv', '.tsv', '.xlsx', '.xls', '.db', '.sqlite'],
            'media': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp4', '.mp3', '.wav'],
            'build': ['.exe', '.dll', '.so', '.dylib', '.pyc', '.pyo', '.class', '.o', '.obj']
        }

    def analyze_project(self, file_paths: Set[str], project_path: str = "") -> Dict:
        """
        Performs comprehensive analysis of the project.
        
        Args:
            file_paths: Set of file paths to analyze
            project_path: Root path of the project (for relative paths)
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        if not file_paths:
            return self._empty_analysis()
        
        print(f"Analyzer: Analyzing {len(file_paths)} files...")
        
        analysis = {
            'summary': self._get_summary_stats(file_paths),
            'languages': self._analyze_languages(file_paths),
            'file_types': self._categorize_files(file_paths),
            'structure': self._analyze_structure(file_paths, project_path),
            'complexity': self._analyze_complexity(file_paths),
            'quality_metrics': self._calculate_quality_metrics(file_paths),
            'generated_at': datetime.now().isoformat()
        }
        
        print(f"Analyzer: Analysis complete. Found {analysis['languages']['total_languages']} programming languages.")
        return analysis

    def _empty_analysis(self) -> Dict:
        """Returns empty analysis structure."""
        return {
            'summary': {'total_files': 0, 'total_size': 0, 'total_lines': 0},
            'languages': {'total_languages': 0, 'languages': {}},
            'file_types': {'categories': {}},
            'structure': {'depth': 0, 'directories': 0},
            'complexity': {'avg_file_size': 0, 'largest_files': []},
            'quality_metrics': {'comment_ratio': 0, 'empty_lines_ratio': 0},
            'generated_at': datetime.now().isoformat()
        }

    def _get_summary_stats(self, file_paths: Set[str]) -> Dict:
        """Calculates basic summary statistics."""
        total_size = 0
        total_lines = 0
        
        for file_path in file_paths:
            try:
                stat = os.stat(file_path)
                total_size += stat.st_size
                
                # Count lines for text files
                if self._is_text_file(file_path):
                    total_lines += self._count_lines(file_path)
                    
            except OSError:
                continue
        
        return {
            'total_files': len(file_paths),
            'total_size': total_size,
            'total_lines': total_lines,
            'avg_file_size': total_size / len(file_paths) if file_paths else 0
        }

    def _analyze_languages(self, file_paths: Set[str]) -> Dict:
        """Analyzes programming languages used in the project."""
        language_stats = defaultdict(lambda: {
            'files': 0,
            'size': 0,
            'lines': 0,
            'comment_lines': 0,
            'code_lines': 0,
            'empty_lines': 0
        })
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if ext in self.language_extensions:
                try:
                    stat = os.stat(file_path)
                    size = stat.st_size
                    
                    # Count lines and analyze content
                    if self._is_text_file(file_path):
                        lines, comments, code, empty = self._analyze_file_content(file_path, ext)
                        
                        language_stats[ext]['files'] += 1
                        language_stats[ext]['size'] += size
                        language_stats[ext]['lines'] += lines
                        language_stats[ext]['comment_lines'] += comments
                        language_stats[ext]['code_lines'] += code
                        language_stats[ext]['empty_lines'] += empty
                        
                except OSError:
                    continue
        
        # Convert to regular dict and add language names
        result = {}
        for ext, stats in language_stats.items():
            lang_info = self.language_extensions[ext]
            result[ext] = {
                'name': lang_info['name'],
                'type': lang_info['type'],
                **stats
            }
        
        return {
            'total_languages': len(result),
            'languages': result
        }

    def _categorize_files(self, file_paths: Set[str]) -> Dict:
        """Categorizes files by type."""
        categories = defaultdict(list)
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            categorized = False
            
            for category, extensions in self.file_categories.items():
                if ext in extensions:
                    categories[category].append(file_path)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(file_path)
        
        # Convert to regular dict and add counts
        result = {}
        for category, files in categories.items():
            result[category] = {
                'count': len(files),
                'files': files[:10],  # Limit to first 10 files for display
                'total_size': sum(os.path.getsize(f) for f in files if os.path.exists(f))
            }
        
        return result

    def _analyze_structure(self, file_paths: Set[str], project_path: str) -> Dict:
        """Analyzes project directory structure."""
        directories = set()
        max_depth = 0
        
        for file_path in file_paths:
            if project_path:
                rel_path = os.path.relpath(file_path, project_path)
            else:
                rel_path = file_path
            
            path_parts = Path(rel_path).parts
            max_depth = max(max_depth, len(path_parts) - 1)
            
            # Add all parent directories
            for i in range(len(path_parts)):
                dir_path = os.path.join(*path_parts[:i+1])
                directories.add(dir_path)
        
        return {
            'depth': max_depth,
            'directories': len(directories),
            'avg_files_per_dir': len(file_paths) / len(directories) if directories else 0
        }

    def _analyze_complexity(self, file_paths: Set[str]) -> Dict:
        """Analyzes project complexity metrics."""
        file_sizes = []
        
        for file_path in file_paths:
            try:
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size))
            except OSError:
                continue
        
        # Sort by size and get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        largest_files = file_sizes[:10]  # Top 10 largest files
        
        return {
            'avg_file_size': sum(size for _, size in file_sizes) / len(file_sizes) if file_sizes else 0,
            'largest_files': [{'path': path, 'size': size} for path, size in largest_files],
            'size_distribution': self._get_size_distribution(file_sizes)
        }

    def _calculate_quality_metrics(self, file_paths: Set[str]) -> Dict:
        """Calculates code quality metrics."""
        total_comment_lines = 0
        total_code_lines = 0
        total_empty_lines = 0
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if ext in self.language_extensions and self._is_text_file(file_path):
                try:
                    _, comments, code, empty = self._analyze_file_content(file_path, ext)
                    total_comment_lines += comments
                    total_code_lines += code
                    total_empty_lines += empty
                except OSError:
                    continue
        
        total_lines = total_code_lines + total_comment_lines + total_empty_lines
        
        return {
            'comment_ratio': total_comment_lines / total_lines if total_lines > 0 else 0,
            'empty_lines_ratio': total_empty_lines / total_lines if total_lines > 0 else 0,
            'code_lines_ratio': total_code_lines / total_lines if total_lines > 0 else 0,
            'total_comment_lines': total_comment_lines,
            'total_code_lines': total_code_lines,
            'total_empty_lines': total_empty_lines
        }

    def _is_text_file(self, file_path: str) -> bool:
        """Determines if a file is a text file."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except Exception:
            return False

    def _count_lines(self, file_path: str) -> int:
        """Counts lines in a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _analyze_file_content(self, file_path: str, extension: str) -> Tuple[int, int, int, int]:
        """
        Analyzes file content to count different types of lines.
        Returns: (total_lines, comment_lines, code_lines, empty_lines)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return 0, 0, 0, 0
        
        total_lines = len(lines)
        comment_lines = 0
        code_lines = 0
        empty_lines = 0
        
        lang_info = self.language_extensions.get(extension, {})
        comment_char = lang_info.get('comment')
        multiline_start = lang_info.get('multiline_comment')
        multiline_end = lang_info.get('multiline_comment')
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Empty line
            if not stripped:
                empty_lines += 1
                continue
            
            # Check for multiline comments
            if multiline_start and multiline_start in stripped:
                if multiline_end and multiline_end in stripped:
                    # Single line multiline comment
                    comment_lines += 1
                    continue
                else:
                    in_multiline_comment = True
                    comment_lines += 1
                    continue
            
            if in_multiline_comment:
                comment_lines += 1
                if multiline_end and multiline_end in stripped:
                    in_multiline_comment = False
                continue
            
            # Single line comment
            if comment_char and stripped.startswith(comment_char):
                comment_lines += 1
                continue
            
            # Code line
            code_lines += 1
        
        return total_lines, comment_lines, code_lines, empty_lines

    def _get_size_distribution(self, file_sizes: List[Tuple[str, int]]) -> Dict:
        """Gets distribution of file sizes."""
        if not file_sizes:
            return {}
        
        sizes = [size for _, size in file_sizes]
        total_files = len(sizes)
        
        # Define size categories
        size_categories = {
            'tiny': 0,      # < 1KB
            'small': 0,     # 1KB - 10KB
            'medium': 0,    # 10KB - 100KB
            'large': 0,     # 100KB - 1MB
            'huge': 0       # > 1MB
        }
        
        for size in sizes:
            if size < 1024:
                size_categories['tiny'] += 1
            elif size < 10 * 1024:
                size_categories['small'] += 1
            elif size < 100 * 1024:
                size_categories['medium'] += 1
            elif size < 1024 * 1024:
                size_categories['large'] += 1
            else:
                size_categories['huge'] += 1
        
        # Convert to percentages
        return {k: (v / total_files) * 100 for k, v in size_categories.items()}

# Convenience function for backward compatibility
def analyze_project(file_paths: Set[str], project_path: str = "") -> Dict:
    """Analyzes a project and returns comprehensive statistics."""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project(file_paths, project_path)
