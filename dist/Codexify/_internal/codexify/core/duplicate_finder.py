import os
import hashlib
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import difflib

class DuplicateFinder:
    """
    Finds duplicate code and files in a project.
    """
    
    def __init__(self):
        self.min_block_size = 3  # Minimum lines for a code block
        self.similarity_threshold = 0.8  # Similarity threshold for fuzzy matching
        
    def find_duplicates(self, file_paths: Set[str], 
                       project_path: str = "",
                       methods: List[str] = None) -> Dict:
        """
        Finds duplicates using multiple detection methods.
        
        Args:
            file_paths: Set of file paths to analyze
            project_path: Root path for relative paths
            methods: List of detection methods to use
            
        Returns:
            Dictionary containing duplicate detection results
        """
        if methods is None:
            methods = ['hash', 'content', 'similarity']
        
        if not file_paths:
            return self._empty_results()
        
        print(f"DuplicateFinder: Analyzing {len(file_paths)} files for duplicates...")
        
        results = {
            'exact_duplicates': {},
            'similar_files': {},
            'duplicate_blocks': {},
            'summary': {},
            'generated_at': None
        }
        
        # Filter to only text files
        text_files = [f for f in file_paths if self._is_text_file(f)]
        
        if 'hash' in methods:
            results['exact_duplicates'] = self._find_exact_duplicates(text_files)
        
        if 'content' in methods:
            results['duplicate_blocks'] = self._find_duplicate_blocks(text_files)
        
        if 'similarity' in methods:
            results['similar_files'] = self._find_similar_files(text_files, project_path)
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        results['generated_at'] = self._get_timestamp()
        
        print(f"DuplicateFinder: Found {results['summary']['total_duplicates']} duplicate groups")
        return results
    
    def _find_exact_duplicates(self, file_paths: List[str]) -> Dict:
        """Finds files with identical content using hash comparison."""
        file_hashes = {}
        hash_groups = defaultdict(list)
        
        for file_path in file_paths:
            try:
                file_hash = self._calculate_file_hash(file_path)
                file_hashes[file_path] = file_hash
                hash_groups[file_hash].append(file_path)
            except Exception as e:
                print(f"DuplicateFinder: Error processing {file_path}: {e}")
                continue
        
        # Filter groups with more than one file
        duplicates = {}
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                duplicates[file_hash] = {
                    'files': files,
                    'count': len(files),
                    'size': os.path.getsize(files[0]) if files else 0
                }
        
        return duplicates
    
    def _find_duplicate_blocks(self, file_paths: List[str]) -> Dict:
        """Finds duplicate code blocks across files."""
        block_hashes = defaultdict(list)
        
        for file_path in file_paths:
            try:
                blocks = self._extract_code_blocks(file_path)
                for block in blocks:
                    if len(block['lines']) >= self.min_block_size:
                        block_hash = self._calculate_block_hash(block['content'])
                        block_hashes[block_hash].append({
                            'file': file_path,
                            'start_line': block['start_line'],
                            'end_line': block['end_line'],
                            'content': block['content']
                        })
            except Exception as e:
                print(f"DuplicateFinder: Error extracting blocks from {file_path}: {e}")
                continue
        
        # Filter blocks that appear in multiple files
        duplicate_blocks = {}
        for block_hash, occurrences in block_hashes.items():
            if len(occurrences) > 1:
                duplicate_blocks[block_hash] = {
                    'occurrences': occurrences,
                    'count': len(occurrences),
                    'sample_content': occurrences[0]['content'][:200] + "..." if len(occurrences[0]['content']) > 200 else occurrences[0]['content']
                }
        
        return duplicate_blocks
    
    def _find_similar_files(self, file_paths: List[str], project_path: str) -> Dict:
        """Finds files with similar content using fuzzy matching."""
        similar_groups = []
        processed_files = set()
        
        for i, file1 in enumerate(file_paths):
            if file1 in processed_files:
                continue
                
            current_group = [file1]
            processed_files.add(file1)
            
            try:
                content1 = self._read_file_content(file1)
                if not content1:
                    continue
                    
                for file2 in file_paths[i+1:]:
                    if file2 in processed_files:
                        continue
                        
                    try:
                        content2 = self._read_file_content(file2)
                        if not content2:
                            continue
                            
                        similarity = self._calculate_similarity(content1, content2)
                        if similarity >= self.similarity_threshold:
                            current_group.append(file2)
                            processed_files.add(file2)
                            
                    except Exception as e:
                        print(f"DuplicateFinder: Error comparing {file2}: {e}")
                        continue
                
                if len(current_group) > 1:
                    similar_groups.append({
                        'files': current_group,
                        'count': len(current_group),
                        'avg_similarity': self._calculate_group_similarity(current_group)
                    })
                    
            except Exception as e:
                print(f"DuplicateFinder: Error processing {file1}: {e}")
                continue
        
        return {'groups': similar_groups}
    
    def _extract_code_blocks(self, file_path: str) -> List[Dict]:
        """Extracts code blocks from a file, ignoring comments and empty lines."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return []
        
        blocks = []
        current_block = []
        current_start = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines and comment-only lines
            if not stripped or self._is_comment_only(line):
                if current_block:
                    # End current block
                    blocks.append({
                        'start_line': current_start + 1,
                        'end_line': i,
                        'content': ''.join(current_block),
                        'lines': current_block
                    })
                    current_block = []
                continue
            
            if not current_block:
                current_start = i
            
            current_block.append(line)
        
        # Add final block if exists
        if current_block:
            blocks.append({
                'start_line': current_start + 1,
                'end_line': len(lines),
                'content': ''.join(current_block),
                'lines': current_block
            })
        
        return blocks
    
    def _is_comment_only(self, line: str) -> bool:
        """Checks if a line contains only comments."""
        stripped = line.strip()
        if not stripped:
            return True
        
        # Common comment patterns
        comment_patterns = ['#', '//', '/*', '<!--', '-->', 'REM', ';']
        return any(stripped.startswith(pattern) for pattern in comment_patterns)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculates SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _calculate_block_hash(self, content: str) -> str:
        """Calculates hash of a code block."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _read_file_content(self, file_path: str) -> str:
        """Reads file content as string."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ""
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculates similarity between two file contents using difflib."""
        if not content1 or not content2:
            return 0.0
        
        # Use difflib to calculate similarity
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
        return similarity
    
    def _calculate_group_similarity(self, file_paths: List[str]) -> float:
        """Calculates average similarity within a group of similar files."""
        if len(file_paths) < 2:
            return 1.0
        
        total_similarity = 0
        comparisons = 0
        
        for i in range(len(file_paths)):
            for j in range(i + 1, len(file_paths)):
                try:
                    content1 = self._read_file_content(file_paths[i])
                    content2 = self._read_file_content(file_paths[j])
                    similarity = self._calculate_similarity(content1, content2)
                    total_similarity += similarity
                    comparisons += 1
                except Exception:
                    continue
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _is_text_file(self, file_path: str) -> bool:
        """Determines if a file is a text file."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except Exception:
            return False
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generates summary statistics for duplicate detection results."""
        exact_count = len(results.get('exact_duplicates', {}))
        block_count = len(results.get('duplicate_blocks', {}))
        similar_count = len(results.get('similar_files', {}).get('groups', []))
        
        total_duplicates = exact_count + block_count + similar_count
        
        # Calculate total duplicate files
        duplicate_files = set()
        
        # Count files in exact duplicates
        for dup_info in results.get('exact_duplicates', {}).values():
            duplicate_files.update(dup_info['files'])
        
        # Count files in similar groups
        for group in results.get('similar_files', {}).get('groups', []):
            duplicate_files.update(group['files'])
        
        return {
            'total_duplicates': total_duplicates,
            'exact_duplicates': exact_count,
            'duplicate_blocks': block_count,
            'similar_groups': similar_count,
            'duplicate_files': len(duplicate_files),
            'duplication_ratio': len(duplicate_files) / len(results.get('summary', {}).get('total_files', 1)) if results.get('summary', {}).get('total_files', 0) > 0 else 0
        }
    
    def _get_timestamp(self) -> str:
        """Returns current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _empty_results(self) -> Dict:
        """Returns empty duplicate detection results."""
        return {
            'exact_duplicates': {},
            'similar_files': {},
            'duplicate_blocks': {},
            'summary': {
                'total_duplicates': 0,
                'exact_duplicates': 0,
                'duplicate_blocks': 0,
                'similar_groups': 0,
                'duplicate_files': 0,
                'duplication_ratio': 0
            },
            'generated_at': self._get_timestamp()
        }

# Convenience function for backward compatibility
def find_duplicates(file_paths: Set[str], project_path: str = "", methods: List[str] = None) -> Dict:
    """Finds duplicates in a set of files."""
    finder = DuplicateFinder()
    return finder.find_duplicates(file_paths, project_path, methods)
