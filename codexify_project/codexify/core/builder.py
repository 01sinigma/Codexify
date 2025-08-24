import os
import time
from typing import Set, Dict, Optional
from pathlib import Path
from datetime import datetime

class CodeBuilder:
    """
    Handles the collection and formatting of source code files.
    """
    
    def __init__(self):
        self.supported_formats = {
            'txt': self._write_text_format,
            'md': self._write_markdown_format,
            'html': self._write_html_format
        }
    
    def write_collected_sources(self, 
                              output_path: str, 
                              files_to_include: Set[str],
                              project_path: str = "",
                              format_type: str = "txt",
                              include_metadata: bool = True,
                              other_files: Optional[Set[str]] = None) -> bool:
        """
        Writes the content of all specified files into a single output file.
        
        Args:
            output_path: Path to the output file
            files_to_include: Set of file paths to include
            project_path: Root path of the project (for relative paths)
            format_type: Output format ('txt', 'md', 'html')
            include_metadata: Whether to include file metadata
        
        Returns:
            True if successful, False otherwise
        """
        if not files_to_include:
            print("Builder: No files to include")
            return False
        
        # Determine output format
        if format_type not in self.supported_formats:
            print(f"Builder: Unsupported format '{format_type}', using 'txt'")
            format_type = "txt"
        
        print(f"Builder: Writing {len(files_to_include)} files to {output_path} in {format_type} format...")
        
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get file statistics
            file_stats = self._get_files_info(files_to_include, project_path)
            
            # Write the file using the appropriate formatter
            formatter = self.supported_formats[format_type]
            success = formatter(output_path, files_to_include, file_stats, project_path, include_metadata, other_files or set())
            
            if success:
                print(f"Builder: Successfully wrote collected sources to {output_path}")
                print(f"Builder: Total size: {file_stats['total_size']} bytes")
                return True
            else:
                print("Builder: Failed to write output file")
                return False
                
        except Exception as e:
            print(f"Builder: Error writing to output file: {e}")
            return False
    
    def _get_files_info(self, files: Set[str], project_path: str) -> Dict:
        """Gets information about all files to be included."""
        total_size = 0
        file_info = {}
        
        for file_path in sorted(files):
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                total_size += size
                
                # Get relative path if project_path is provided
                rel_path = os.path.relpath(file_path, project_path) if project_path else file_path
                
                file_info[file_path] = {
                    'relative_path': rel_path,
                    'size': size,
                    'modified': stat.st_mtime,
                    'encoding': self._detect_encoding(file_path)
                }
                
            except OSError as e:
                print(f"Builder: Warning: Could not get info for {file_path}: {e}")
                file_info[file_path] = {
                    'relative_path': file_path,
                    'size': 0,
                    'modified': 0,
                    'encoding': 'unknown'
                }
        
        return {
            'total_files': len(files),
            'total_size': total_size,
            'file_info': file_info,
            'generated_at': datetime.now().isoformat()
        }
    
    def _detect_encoding(self, file_path: str) -> str:
        """Attempts to detect the encoding of a text file."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # Read a small sample
                    return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'unknown'
    
    def _write_text_format(self, output_path: str, files: Set[str], 
                          file_stats: Dict, project_path: str, include_metadata: bool, other_files: Set[str]) -> bool:
        """Writes output in plain text format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                if include_metadata:
                    outfile.write(f"Codexify - Collected Sources\n")
                    outfile.write(f"Generated: {file_stats['generated_at']}\n")
                    outfile.write(f"Total files: {file_stats['total_files']}\n")
                    outfile.write(f"Total size: {file_stats['total_size']} bytes\n")
                # Always write full path lists at the beginning
                outfile.write("== Include files (full paths) ==\n")
                for p in sorted(files):
                    outfile.write(p + "\n")
                outfile.write("\n== Other files (full paths) ==\n")
                for p in sorted(other_files or set()):
                    outfile.write(p + "\n")
                outfile.write("\n" + ("=" * 50) + "\n\n")
                
                for file_path in sorted(files):
                    file_info = file_stats['file_info'][file_path]
                    
                    # Always show full path before content
                    outfile.write(f"=== {file_path} ===\n")
                    
                    if include_metadata:
                        outfile.write(f"Size: {file_info['size']} bytes\n")
                        outfile.write(f"Modified: {datetime.fromtimestamp(file_info['modified']).isoformat()}\n")
                        outfile.write(f"Encoding: {file_info['encoding']}\n")
                        outfile.write("-" * 30 + "\n\n")
                    
                    try:
                        encoding = file_info['encoding']
                        if encoding == 'unknown':
                            encoding = 'utf-8'
                        
                        with open(file_path, 'r', encoding=encoding, errors='replace') as infile:
                            content = infile.read()
                            outfile.write(content)
                            
                        if not content.endswith('\n'):
                            outfile.write('\n')
                            
                    except Exception as e:
                        outfile.write(f"!!! Could not read file: {e} !!!\n")
                    
                    if include_metadata:
                        outfile.write(f"\n--- End of {file_path} ---\n\n")
                
                return True
                
        except Exception as e:
            print(f"Builder: Error in text formatter: {e}")
            return False
    
    def _write_markdown_format(self, output_path: str, files: Set[str], 
                             file_stats: Dict, project_path: str, include_metadata: bool, other_files: Set[str]) -> bool:
        """Writes output in Markdown format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                if include_metadata:
                    outfile.write(f"# Codexify - Collected Sources\n\n")
                    outfile.write(f"**Generated:** {file_stats['generated_at']}  \n")
                    outfile.write(f"**Total files:** {file_stats['total_files']}  \n")
                    outfile.write(f"**Total size:** {file_stats['total_size']} bytes\n\n")
                    outfile.write("---\n\n")
                # Always write full path lists at the beginning
                outfile.write("## Include files (full paths)\n\n")
                for p in sorted(files):
                    outfile.write(f"- {p}\n")
                outfile.write("\n## Other files (full paths)\n\n")
                for p in sorted(other_files or set()):
                    outfile.write(f"- {p}\n")
                outfile.write("\n---\n\n")
                
                for file_path in sorted(files):
                    file_info = file_stats['file_info'][file_path]
                    
                    # Always show full path before content
                    outfile.write(f"## {file_path}\n\n")
                    if include_metadata:
                        outfile.write(f"**Size:** {file_info['size']} bytes  \n")
                        outfile.write(f"**Modified:** {datetime.fromtimestamp(file_info['modified']).isoformat()}  \n")
                        outfile.write(f"**Encoding:** {file_info['encoding']}\n\n")
                    
                    outfile.write("```\n")
                    
                    try:
                        encoding = file_info['encoding']
                        if encoding == 'unknown':
                            encoding = 'utf-8'
                        
                        with open(file_path, 'r', encoding=encoding, errors='replace') as infile:
                            content = infile.read()
                            outfile.write(content)
                            
                    except Exception as e:
                        outfile.write(f"!!! Could not read file: {e} !!!")
                    
                    outfile.write("\n```\n\n")
                
                return True
                
        except Exception as e:
            print(f"Builder: Error in markdown formatter: {e}")
            return False
    
    def _write_html_format(self, output_path: str, files: Set[str], 
                          file_stats: Dict, project_path: str, include_metadata: bool, other_files: Set[str]) -> bool:
        """Writes output in HTML format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codexify - Collected Sources</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 20px; }
        .file-header { background: #f0f0f0; padding: 10px; margin: 20px 0; border-radius: 5px; }
        .file-content { background: #f8f8f8; padding: 15px; border-left: 4px solid #007acc; }
        .metadata { color: #666; font-size: 0.9em; }
        .file-path { font-weight: bold; color: #333; }
    </style>
</head>
<body>
""")
                
                if include_metadata:
                    outfile.write(f"<h1>Codexify - Collected Sources</h1>")
                    outfile.write(f"<div class='metadata'>")
                    outfile.write(f"<p><strong>Generated:</strong> {file_stats['generated_at']}</p>")
                    outfile.write(f"<p><strong>Total files:</strong> {file_stats['total_files']}</p>")
                    outfile.write(f"<p><strong>Total size:</strong> {file_stats['total_size']} bytes</p>")
                    outfile.write(f"</div><hr>")
                # Always write full path lists at the beginning
                outfile.write("<h2>Include files (full paths)</h2><ul>")
                for p in sorted(files):
                    outfile.write(f"<li>{p}</li>")
                outfile.write("</ul>")
                outfile.write("<h2>Other files (full paths)</h2><ul>")
                for p in sorted(other_files or set()):
                    outfile.write(f"<li>{p}</li>")
                outfile.write("</ul><hr>")
                
                for file_path in sorted(files):
                    file_info = file_stats['file_info'][file_path]
                    
                    # Always show header with full path
                    outfile.write(f"<div class='file-header'>")
                    outfile.write(f"<div class='file-path'>{file_path}</div>")
                    if include_metadata:
                        outfile.write(f"<div class='metadata'>")
                        outfile.write(f"Size: {file_info['size']} bytes | ")
                        outfile.write(f"Modified: {datetime.fromtimestamp(file_info['modified']).isoformat()} | ")
                        outfile.write(f"Encoding: {file_info['encoding']}")
                        outfile.write(f"</div>")
                    outfile.write(f"</div>")
                    
                    outfile.write(f"<div class='file-content'><pre>")
                    
                    try:
                        encoding = file_info['encoding']
                        if encoding == 'unknown':
                            encoding = 'utf-8'
                        
                        with open(file_path, 'r', encoding=encoding, errors='replace') as infile:
                            content = infile.read()
                            # Escape HTML characters
                            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            outfile.write(content)
                            
                    except Exception as e:
                        outfile.write(f"!!! Could not read file: {e} !!!")
                    
                    outfile.write("</pre></div>")
                
                outfile.write("</body></html>")
                return True
                
        except Exception as e:
            print(f"Builder: Error in HTML formatter: {e}")
            return False

# Backward compatibility function
def write_collected_sources(output_path: str, files_to_include: Set[str]):
    """
    Legacy function for backward compatibility.
    """
    builder = CodeBuilder()
    return builder.write_collected_sources(output_path, files_to_include)
