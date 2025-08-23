#!/usr/bin/env python3
"""
Command Line Interface for Codexify.
Demonstrates the flexibility of the engine API.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

from ..engine import CodexifyEngine
from ..events import ANALYSIS_COMPLETE

class CodexifyCLI:
    """
    Command Line Interface for Codexify.
    """
    
    def __init__(self):
        self.engine = CodexifyEngine()
        self.analysis_results = None
        
        # Subscribe to analysis events
        self.engine.events.subscribe(ANALYSIS_COMPLETE, self.on_analysis_complete)
    
    def on_analysis_complete(self, data: Dict[str, Any]):
        """Callback for analysis completion events."""
        self.analysis_results = data
    
    def run(self, args):
        """Main CLI execution method."""
        try:
            if args.command == 'scan':
                self.cmd_scan(args.path)
            elif args.command == 'analyze':
                self.cmd_analyze()
            elif args.command == 'duplicates':
                self.cmd_duplicates(args.methods)
            elif args.command == 'collect':
                self.cmd_collect(args.output, args.format, args.metadata)
            elif args.command == 'formats':
                self.cmd_formats(args.formats)
            elif args.command == 'status':
                self.cmd_status()
            else:
                print(f"Unknown command: {args.command}")
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def cmd_scan(self, path: str):
        """Scan a project directory."""
        print(f"Scanning project: {path}")
        
        # Load the project
        self.engine.load_project(path)
        
        # Wait for completion
        while self.engine.state.is_busy:
            import time
            time.sleep(0.1)
        
        # Display results
        summary = self.engine.get_state_summary()
        print(f"\nProject loaded successfully!")
        print(f"Total files: {summary['total_files']}")
        print(f"Include files: {summary['include_files']}")
        print(f"Other files: {summary['other_files']}")
        print(f"Active formats: {', '.join(summary['active_formats']) if summary['active_formats'] else 'None'}")
    
    def cmd_analyze(self):
        """Analyze the loaded project."""
        if not self.engine.state.all_discovered_files:
            print("No project loaded. Use 'scan' command first.")
            return
        
        print("Analyzing project...")
        
        # Run analysis
        self.engine.get_analytics()
        
        # Wait for completion
        while self.engine.state.is_busy:
            import time
            time.sleep(0.1)
        
        # Display results
        if self.analysis_results:
            self._display_analysis(self.analysis_results)
        else:
            print("Analysis failed or no results available.")
    
    def cmd_duplicates(self, methods: list):
        """Find duplicates in the project."""
        if not self.engine.state.all_discovered_files:
            print("No project loaded. Use 'scan' command first.")
            return
        
        if not methods:
            methods = ['hash', 'content', 'similarity']
        
        print(f"Finding duplicates using methods: {', '.join(methods)}")
        
        # Run duplicate detection
        self.engine.find_duplicates(methods)
        
        # Wait for completion
        while self.engine.state.is_busy:
            import time
            time.sleep(0.1)
        
        # Display results
        if self.analysis_results and self.analysis_results.get('type') == 'duplicates':
            self._display_duplicates(self.analysis_results['results'])
        else:
            print("Duplicate detection failed or no results available.")
    
    def cmd_collect(self, output: str, format_type: str, include_metadata: bool):
        """Collect code from include files."""
        if not self.engine.state.include_files:
            print("No files to collect. Use 'scan' and 'formats' commands first.")
            return
        
        print(f"Collecting code to: {output}")
        print(f"Format: {format_type}")
        print(f"Metadata: {'Yes' if include_metadata else 'No'}")
        
        # Run collection
        self.engine.collect_code(output, format_type, include_metadata)
        
        # Wait for completion
        while self.engine.state.is_busy:
            import time
            time.sleep(0.1)
        
        print("Code collection completed!")
    
    def cmd_formats(self, formats: list):
        """Set active file formats."""
        if not formats:
            print("No formats specified.")
            return
        
        print(f"Setting active formats: {', '.join(formats)}")
        
        # Set formats
        self.engine.set_active_formats(set(formats))
        
        # Wait for classification
        while self.engine.state.is_busy:
            import time
            time.sleep(0.1)
        
        # Display results
        summary = self.engine.get_state_summary()
        print(f"Formats updated!")
        print(f"Include files: {summary['include_files']}")
        print(f"Other files: {summary['other_files']}")
    
    def cmd_status(self):
        """Display current engine status."""
        summary = self.engine.get_state_summary()
        
        print("=== Codexify Engine Status ===")
        print(f"Project: {summary['project_path'] or 'None'}")
        print(f"Total files: {summary['total_files']}")
        print(f"Include files: {summary['include_files']}")
        print(f"Other files: {summary['other_files']}")
        print(f"Active formats: {', '.join(summary['active_formats']) if summary['active_formats'] else 'None'}")
        print(f"Status: {summary['status_message']}")
        print(f"Busy: {'Yes' if summary['is_busy'] else 'No'}")
    
    def _display_analysis(self, analysis: Dict[str, Any]):
        """Display analysis results in a formatted way."""
        print("\n=== Project Analysis Results ===")
        
        # Summary
        summary = analysis.get('summary', {})
        print(f"Total files: {summary.get('total_files', 0)}")
        print(f"Total size: {self._format_size(summary.get('total_size', 0))}")
        print(f"Total lines: {summary.get('total_lines', 0):,}")
        
        # Languages
        languages = analysis.get('languages', {})
        if languages.get('languages'):
            print(f"\nProgramming Languages ({languages['total_languages']}):")
            for ext, lang_info in languages['languages'].items():
                print(f"  {lang_info['name']} ({ext}): {lang_info['files']} files, {lang_info['lines']:,} lines")
        
        # File types
        file_types = analysis.get('file_types', {})
        if file_types:
            print(f"\nFile Categories:")
            for category, info in file_types.items():
                print(f"  {category.title()}: {info['count']} files, {self._format_size(info['total_size'])}")
        
        # Quality metrics
        quality = analysis.get('quality_metrics', {})
        if quality:
            print(f"\nCode Quality:")
            print(f"  Comment ratio: {quality.get('comment_ratio', 0):.1%}")
            print(f"  Empty lines ratio: {quality.get('empty_lines_ratio', 0):.1%}")
            print(f"  Code lines ratio: {quality.get('code_lines_ratio', 0):.1%}")
    
    def _display_duplicates(self, duplicates: Dict[str, Any]):
        """Display duplicate detection results."""
        print("\n=== Duplicate Detection Results ===")
        
        summary = duplicates.get('summary', {})
        print(f"Total duplicate groups: {summary.get('total_duplicates', 0)}")
        print(f"Exact duplicates: {summary.get('exact_duplicates', 0)}")
        print(f"Duplicate blocks: {summary.get('duplicate_blocks', 0)}")
        print(f"Similar file groups: {summary.get('similar_groups', 0)}")
        print(f"Duplicate files: {summary.get('duplicate_files', 0)}")
        print(f"Duplication ratio: {summary.get('duplication_ratio', 0):.1%}")
        
        # Show some examples
        exact_dups = duplicates.get('exact_duplicates', {})
        if exact_dups:
            print(f"\nExact Duplicates:")
            for i, (hash_val, info) in enumerate(list(exact_dups.items())[:3]):  # Show first 3
                print(f"  Group {i+1}: {info['count']} files, {self._format_size(info['size'])}")
                for file_path in info['files']:
                    print(f"    - {file_path}")
        
        similar_groups = duplicates.get('similar_files', {}).get('groups', [])
        if similar_groups:
            print(f"\nSimilar File Groups:")
            for i, group in enumerate(similar_groups[:3]):  # Show first 3
                print(f"  Group {i+1}: {group['count']} files, {group['avg_similarity']:.1%} similarity")
                for file_path in group['files']:
                    print(f"    - {file_path}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Codexify - Code Collection and Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan /path/to/project
  %(prog)s scan /path/to/project && %(prog)s analyze
  %(prog)s scan /path/to/project && %(prog)s formats .py .js .html
  %(prog)s scan /path/to/project && %(prog)s collect output.txt
  %(prog)s scan /path/to/project && %(prog)s duplicates hash,content
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a project directory')
    scan_parser.add_argument('path', help='Path to the project directory')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze the loaded project')
    
    # Duplicates command
    dup_parser = subparsers.add_parser('duplicates', help='Find duplicates in the project')
    dup_parser.add_argument('--methods', nargs='+', 
                           choices=['hash', 'content', 'similarity'],
                           help='Duplicate detection methods to use')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect code from include files')
    collect_parser.add_argument('output', help='Output file path')
    collect_parser.add_argument('--format', choices=['txt', 'md', 'html'], 
                               default='txt', help='Output format')
    collect_parser.add_argument('--metadata', action='store_true', 
                               help='Include file metadata')
    
    # Formats command
    formats_parser = subparsers.add_parser('formats', help='Set active file formats')
    formats_parser.add_argument('formats', nargs='+', help='File extensions to include')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current engine status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run CLI
    cli = CodexifyCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
