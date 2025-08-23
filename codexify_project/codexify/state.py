from dataclasses import dataclass, field
from typing import Set, Dict

@dataclass
class CodexifyState:
    """
    A dataclass to hold the entire state of the Codexify application.
    This is the single source of truth.
    """
    project_path: str = ""
    all_discovered_files: Set[str] = field(default_factory=set)
    include_files: Set[str] = field(default_factory=set)
    other_files: Set[str] = field(default_factory=set)
    ignored_files: Set[str] = field(default_factory=set)
    file_inclusion_modes: Dict[str, str] = field(default_factory=dict)  # e.g., {'path/to/file.py': 'include'}
    active_formats: Set[str] = field(default_factory=set)
    is_busy: bool = False
    status_message: str = "Ready"
