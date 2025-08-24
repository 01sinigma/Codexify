import threading
from typing import Set, Optional, Any
from pathlib import Path

from .state import CodexifyState
from .events import EventManager, STATUS_CHANGED, PROJECT_LOADED, FILES_UPDATED, COLLECTION_COMPLETE, ANALYSIS_COMPLETE
from .core.scanner import scan_directory, get_file_stats
from .core.builder import CodeBuilder
from .core.analyzer import ProjectAnalyzer
from .core.duplicate_finder import DuplicateFinder
from .systems.config_manager import get_config_manager
from .systems.achievement_system import get_achievement_system
from .systems.hotkey_manager import get_hotkey_manager
from .utils.logger import get_logger

class CodexifyEngine:
    """
    The central coordinator of the Codexify application.
    It holds the state, manages business logic, and notifies clients of changes.
    """
    def __init__(self):
        self.log = get_logger("engine")
        self.state = CodexifyState()
        self.events = EventManager()
        self.builder = CodeBuilder()
        self.analyzer = ProjectAnalyzer()
        self.duplicate_finder = DuplicateFinder()
        # history for undo/redo
        self._undo_stack = []
        self._redo_stack = []
        
        # Initialize systems
        self.config_manager = get_config_manager()
        self.achievement_system = get_achievement_system()
        self.hotkey_manager = get_hotkey_manager()
        
        # Connect systems to engine
        self._connect_systems()

    def _connect_systems(self):
        """Connects all systems to the engine and event manager."""
        # Connect achievement system
        self.achievement_system.set_engine(self, self.events)
        
        # Connect hotkey manager (will be set when GUI is created)
        # self.hotkey_manager.set_root_widget(root_widget) - called from GUI
        
        # Register hotkey action handlers
        self._register_hotkey_handlers()
        
        # Apply configuration settings
        self._apply_configuration()

    def _register_hotkey_handlers(self):
        """Registers action handlers for hotkeys."""
        self.hotkey_manager.register_action_handler("open_project", self._hotkey_open_project)
        self.hotkey_manager.register_action_handler("save_collection", self._hotkey_save_collection)
        self.hotkey_manager.register_action_handler("export_project", self._hotkey_export_project)
        self.hotkey_manager.register_action_handler("run_analysis", self._hotkey_run_analysis)
        self.hotkey_manager.register_action_handler("find_duplicates", self._hotkey_find_duplicates)
        self.hotkey_manager.register_action_handler("quick_scan", self._hotkey_quick_scan)
        self.hotkey_manager.register_action_handler("next_file", self._hotkey_next_file)
        self.hotkey_manager.register_action_handler("previous_file", self._hotkey_previous_file)
        self.hotkey_manager.register_action_handler("toggle_include", self._hotkey_toggle_include)
        self.hotkey_manager.register_action_handler("preferences", self._hotkey_preferences)
        self.hotkey_manager.register_action_handler("help", self._hotkey_help)
        self.hotkey_manager.register_action_handler("refresh", self._hotkey_refresh)

    def _apply_configuration(self):
        """Applies configuration settings to the engine."""
        # Apply scanning settings
        max_file_size = self.config_manager.get_setting("scanning.max_file_size", 10485760)
        skip_binary = self.config_manager.get_setting("scanning.skip_binary", True)
        
        # Apply analysis settings
        min_block_size = self.config_manager.get_setting("analysis.min_block_size", 3)
        similarity_threshold = self.config_manager.get_setting("analysis.similarity_threshold", 0.8)
        
        # Apply performance settings
        max_threads = self.config_manager.get_setting("performance.max_threads", 4)
        
        # Update duplicate finder settings
        self.duplicate_finder.min_block_size = min_block_size
        self.duplicate_finder.similarity_threshold = similarity_threshold
        
        self.log.info("config applied | max_file_size=%s skip_binary=%s", max_file_size, skip_binary)

    def _run_in_background(self, func, *args, **kwargs):
        """Helper to run a function in a separate thread."""
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()

    def load_project(self, path: str):
        """
        Loads and scans a project directory.
        This is a long-running operation and should be run in the background.
        """
        self.state.is_busy = True
        self.state.status_message = f"Scanning {path}..."
        self.events.post(STATUS_CHANGED)
        self.log.info("load_project: %s", path)

        # Run scanning in background
        self._run_in_background(self._scan_project, path)

    def _scan_project(self, path: str):
        """
        Internal method to scan project directory.
        This runs in a background thread.
        """
        try:
            # Get configuration settings
            max_file_size = self.config_manager.get_setting("scanning.max_file_size", 10485760)
            skip_binary = self.config_manager.get_setting("scanning.skip_binary", True)
            max_depth = self.config_manager.get_setting("scanning.max_depth", 50)
            
            # Scan the directory with configuration
            found_files = scan_directory(path, max_file_size=max_file_size, skip_binary=skip_binary)
            
            # Update state with discovered files
            self.state.all_discovered_files = found_files
            self.state.project_path = path
            
            # Classify files based on current active formats
            self._classify_files()
            
            # Get file statistics
            stats = get_file_stats(found_files)
            self.state.status_message = f"Project loaded. Found {stats['total_files']} files ({stats['total_size']} bytes)"
            
            # Add to recent projects
            self.config_manager.add_recent_project(path)
            
        except Exception as e:
            self.state.status_message = f"Error loading project: {e}"
            self.log.exception("Error scanning project")
        finally:
            self.state.is_busy = False
            self.events.post(PROJECT_LOADED)

    def set_active_formats(self, formats: Set[str]):
        """
        Updates the active file formats and re-classifies files.
        """
        self.state.active_formats = formats
        self.log.info("active formats set: %s", formats)
        # Re-classify files immediately (considering union of known files)
        self._classify_files()
        self.events.post(FILES_UPDATED)
        self.log.debug("post FILES_UPDATED after format change")

    def move_files(self, files: Set[str], to_list: str):
        """
        Moves files between include/other lists.
        'to_list' can be 'include' or 'other'.
        """
        if to_list not in ['include', 'other']:
            self.log.warning("invalid destination: %s", to_list)
            return
        
        self.log.debug("move_files | count=%d dest=%s", len(files), to_list)
        
        # Remove files from both lists first
        self.state.include_files -= files
        self.state.other_files -= files
        
        # Add to the specified list
        if to_list == 'include':
            self.state.include_files.update(files)
        else:
            self.state.other_files.update(files)
        
        # Update inclusion modes
        for file_path in files:
            self.state.file_inclusion_modes[file_path] = to_list
        
        # record history
        self._undo_stack.append({
            'type': 'move',
            'files': set(files),
            'to': to_list,
        })
        self._redo_stack.clear()
        self.events.post(FILES_UPDATED)
        self.log.debug("post FILES_UPDATED after move")

    def apply_path_preset(self, name: str, destination: str = 'include', mode: str = 'merge'):
        """Loads a saved path preset and adds files to include/other.
        destination: 'include' or 'other'
        mode: 'merge' (default) or 'replace' — replace clears destination list first
        """
        try:
            paths = set(self.config_manager.get_path_preset(name))
            if not paths:
                return False
            dest = 'include' if destination == 'include' else 'other'
            if mode == 'replace':
                if dest == 'include':
                    # move all current include to other to keep modes consistent
                    self.state.file_inclusion_modes = {k: v for k, v in self.state.file_inclusion_modes.items() if k not in self.state.include_files}
                    self.state.include_files.clear()
                else:
                    self.state.file_inclusion_modes = {k: v for k, v in self.state.file_inclusion_modes.items() if k not in self.state.other_files}
                    self.state.other_files.clear()
            self.move_files(paths, dest)
            return True
        except Exception:
            return False

    def save_path_preset(self, name: str, from_selection: Optional[Set[str]] = None):
        """Saves a path preset from current selection or include list if selection is None."""
        paths = list(from_selection or self.state.include_files)
        self.config_manager.save_path_preset(name, paths)
        return True

    def delete_path_preset(self, name: str):
        self.config_manager.delete_path_preset(name)
        return True

    def remove_files(self, files: Set[str]):
        """Removes files from include/other lists (moves to ignored)."""
        if not files:
            return
        self.log.debug("remove_files | count=%d", len(files))
        self.state.include_files -= files
        self.state.other_files -= files
        self.state.ignored_files.update(files)
        for fp in files:
            if fp in self.state.file_inclusion_modes:
                del self.state.file_inclusion_modes[fp]
        # record history
        self._undo_stack.append({
            'type': 'remove',
            'files': set(files),
            'from_include': set(files) & self.state.include_files,
            'from_other': set(files) & self.state.other_files,
        })
        self._redo_stack.clear()
        self.events.post(FILES_UPDATED)
        self.log.debug("post FILES_UPDATED after removal")

    # --- Undo/Redo ---
    def undo(self):
        if not self._undo_stack:
            return False
        action = self._undo_stack.pop()
        self.log.debug("undo: %s", action.get('type'))
        if action['type'] == 'move':
            files = action['files']
            dest = action['to']
            back = 'include' if dest == 'other' else 'other'
            # apply inverse
            self.move_files(files, back)
            # push redo info
            self._redo_stack.append(action)
            # don't double-record in history for inverse
            if self._undo_stack and self._undo_stack[-1] == action:
                pass
        elif action['type'] == 'remove':
            files = action['files']
            # restore to previous lists
            if action['from_include']:
                self.state.include_files.update(action['from_include'])
            if action['from_other']:
                self.state.other_files.update(action['from_other'])
            self.state.ignored_files -= files
            for fp in files:
                if fp in action.get('from_include', set()):
                    self.state.file_inclusion_modes[fp] = 'include'
                elif fp in action.get('from_other', set()):
                    self.state.file_inclusion_modes[fp] = 'other'
            self._redo_stack.append(action)
            self.events.post(FILES_UPDATED)
        return True

    def redo(self):
        if not self._redo_stack:
            return False
        action = self._redo_stack.pop()
        self.log.debug("redo: %s", action.get('type'))
        if action['type'] == 'move':
            self.move_files(action['files'], action['to'])
        elif action['type'] == 'remove':
            self.remove_files(action['files'])
        return True

    def collect_code(self, output_path: str, format_type: str = "txt", include_metadata: bool = True):
        """
        Collects all 'included' files into a single output file.
        """
        if not self.state.include_files:
            self.state.status_message = "No files to collect. Please add files to the include list first."
            self.events.post(STATUS_CHANGED)
            return
        
        # Get configuration settings
        if format_type == "default":
            format_type = self.config_manager.get_setting("output.default_format", "md")
        
        if include_metadata is None:
            include_metadata = self.config_manager.get_setting("output.include_metadata", True)
        
        self.state.is_busy = True
        self.state.status_message = "Collecting code..."
        self.events.post(STATUS_CHANGED)

        # Run collection in background
        self._run_in_background(self._collect_code_background, output_path, format_type, include_metadata)

    def _collect_code_background(self, output_path: str, format_type: str, include_metadata: bool):
        """
        Internal method to collect code in background thread.
        """
        try:
            self.log.info("collect to: %s", output_path)
            
            # Use the builder to write the output
            success = self.builder.write_collected_sources(
                output_path=output_path,
                files_to_include=self.state.include_files,
                project_path=self.state.project_path,
                format_type=format_type,
                include_metadata=include_metadata,
                other_files=self.state.other_files
            )
            
            if success:
                self.state.status_message = f"Code collected to {output_path}"
                self.events.post(COLLECTION_COMPLETE, data=output_path)
                self.log.info("collection complete")
            else:
                self.state.status_message = "Failed to collect code"
                self.log.warning("collection failed")
                
        except Exception as e:
            self.state.status_message = f"Error collecting code: {e}"
            self.log.exception("Error collecting code")
        finally:
            self.state.is_busy = False
            self.events.post(STATUS_CHANGED)

    def get_analytics(self):
        """
        Triggers comprehensive project analysis.
        """
        if not self.state.all_discovered_files:
            self.state.status_message = "No project loaded for analysis"
            self.events.post(STATUS_CHANGED)
            return
        
        # Check if analysis is enabled
        if not self.config_manager.get_setting("analysis.enable_quality_metrics", True):
            self.state.status_message = "Analysis disabled in configuration"
            self.events.post(STATUS_CHANGED)
            return
        
        self.state.is_busy = True
        self.state.status_message = "Analyzing project..."
        self.events.post(STATUS_CHANGED)

        # Run analysis in background
        self._run_in_background(self._analyze_project_background)

    def _analyze_project_background(self):
        """
        Internal method to analyze project in background thread.
        """
        try:
            self.log.info("analysis start")
            
            # Use the analyzer to get comprehensive project analysis
            analysis_results = self.analyzer.analyze_project(
                self.state.all_discovered_files,
                self.state.project_path
            )
            
            # Add engine-specific information
            analysis_results['engine_state'] = {
                'include_files': len(self.state.include_files),
                'other_files': len(self.state.other_files),
                'ignored_files': len(self.state.ignored_files),
                'active_formats': list(self.state.active_formats),
                'project_path': self.state.project_path
            }
            
            self.state.status_message = "Analysis complete."
            self.events.post(ANALYSIS_COMPLETE, data=analysis_results)
            self.log.info("analysis complete")
            
        except Exception as e:
            self.state.status_message = f"Error during analysis: {e}"
            self.log.exception("Error during analysis")
        finally:
            self.state.is_busy = False
            self.events.post(STATUS_CHANGED)

    def find_duplicates(self, methods: list = None):
        """
        Triggers duplicate detection analysis.
        """
        if not self.state.all_discovered_files:
            self.state.status_message = "No project loaded for duplicate detection"
            self.events.post(STATUS_CHANGED)
            return
        
        # Check if duplicate detection is enabled
        if not self.config_manager.get_setting("analysis.enable_complexity_analysis", True):
            self.state.status_message = "Duplicate detection disabled in configuration"
            self.events.post(STATUS_CHANGED)
            return
        
        # Use configured methods if none specified
        if methods is None:
            methods = ["hash", "content", "similarity"]
        
        self.state.is_busy = True
        self.state.status_message = "Finding duplicates..."
        self.events.post(STATUS_CHANGED)

        # Run duplicate detection in background
        self._run_in_background(self._find_duplicates_background, methods)

    def _find_duplicates_background(self, methods: list = None):
        """
        Internal method to find duplicates in background thread.
        """
        try:
            self.log.info("duplicates start")
            
            # Use the duplicate finder to detect duplicates
            duplicate_results = self.duplicate_finder.find_duplicates(
                self.state.all_discovered_files,
                self.state.project_path,
                methods
            )
            
            # Add engine-specific information
            duplicate_results['engine_state'] = {
                'include_files': len(self.state.include_files),
                'other_files': len(self.state.other_files),
                'ignored_files': len(self.state.ignored_files),
                'active_formats': list(self.state.active_formats),
                'project_path': self.state.project_path
            }
            
            self.state.status_message = "Duplicate detection complete."
            self.events.post(ANALYSIS_COMPLETE, data={'type': 'duplicates', 'results': duplicate_results})
            self.log.info("duplicates complete")
            
        except Exception as e:
            self.state.status_message = f"Error during duplicate detection: {e}"
            self.log.exception("Error during duplicates")
        finally:
            self.state.is_busy = False
            self.events.post(STATUS_CHANGED)

    def _classify_files(self):
        """
        Internal method to classify all_discovered_files into
        include_files, other_files, and ignored_files based on active_formats.
        """
        if not self.state.all_discovered_files:
            return
        
        self.log.debug("classify | discovered=%d", len(self.state.all_discovered_files))
        
        # Build source as union of discovered and currently listed files (supports DnD/manual adds)
        source_files = set(self.state.all_discovered_files or set()) \
            | set(self.state.include_files or set()) \
            | set(self.state.other_files or set())

        # Reset classifications
        self.state.include_files = set()
        self.state.other_files = set()
        self.state.ignored_files = set()
        self.state.file_inclusion_modes = {}

        # If нет выбранных форматов, ничего не включаем: все попадут в Other
        active_exts = set(self.state.active_formats or [])

        # Classify files based on extensions
        for file_path in source_files:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in active_exts:
                self.state.include_files.add(file_path)
                self.state.file_inclusion_modes[file_path] = 'include'
            else:
                self.state.other_files.add(file_path)
                self.state.file_inclusion_modes[file_path] = 'other'

        self.log.info("classified | include=%d other=%d", len(self.state.include_files), len(self.state.other_files))

    # Configuration Management Methods
    
    def get_setting(self, key_path: str, default: Any = None):
        """Gets a configuration setting."""
        return self.config_manager.get_setting(key_path, default)
    
    def set_setting(self, key_path: str, value: Any):
        """Sets a configuration setting."""
        self.config_manager.set_setting(key_path, value)
        
        # Apply configuration changes if needed
        if key_path.startswith("scanning.") or key_path.startswith("analysis."):
            self._apply_configuration()
    
    def get_all_settings(self):
        """Gets all configuration settings."""
        return self.config_manager.get_all_settings()
    
    def reset_configuration(self):
        """Resets configuration to defaults."""
        self.config_manager.reset_to_defaults()
        self._apply_configuration()
    
    def export_configuration(self, file_path: str):
        """Exports configuration to a file."""
        self.config_manager.export_config(file_path)
    
    def import_configuration(self, file_path: str):
        """Imports configuration from a file."""
        self.config_manager.import_config(file_path)
        self._apply_configuration()
    
    # Preset Management Methods
    
    def create_preset(self, name: str, description: str = ""):
        """Creates a new configuration preset."""
        self.config_manager.create_preset(name, description)
    
    def load_preset(self, name: str):
        """Loads a configuration preset."""
        self.config_manager.load_preset(name)
        self._apply_configuration()
    
    def get_preset_names(self):
        """Gets list of available preset names."""
        return self.config_manager.get_preset_names()
    
    def delete_preset(self, name: str):
        """Deletes a configuration preset."""
        self.config_manager.delete_preset(name)
    
    # Theme Management Methods
    
    def get_theme(self, name: str = None):
        """Gets theme data."""
        return self.config_manager.get_theme(name)
    
    def get_theme_names(self):
        """Gets list of available theme names."""
        return self.config_manager.get_theme_names()
    
    def create_theme(self, name: str, theme_data: dict):
        """Creates a new theme."""
        self.config_manager.create_theme(name, theme_data)
    
    # Achievement System Methods
    
    def get_achievements(self):
        """Gets all achievements."""
        return self.achievement_system.get_all_achievements()
    
    def get_unlocked_achievements(self):
        """Gets unlocked achievements."""
        return self.achievement_system.get_unlocked_achievements()
    
    def get_achievement_progress(self):
        """Gets achievement progress summary."""
        return self.achievement_system.get_progress_summary()
    
    def reset_achievements(self):
        """Resets all achievement progress."""
        self.achievement_system.reset_progress()
    
    # Hotkey Management Methods
    
    def set_root_widget(self, root_widget):
        """Sets the root widget for hotkey binding."""
        self.hotkey_manager.set_root_widget(root_widget)
    
    def get_hotkeys(self):
        """Gets all hotkeys."""
        return self.hotkey_manager.get_all_hotkeys()
    
    def get_hotkeys_by_category(self, category: str):
        """Gets hotkeys by category."""
        return self.hotkey_manager.get_hotkeys_by_category(category)
    
    def set_hotkey_enabled(self, hotkey_id: str, enabled: bool):
        """Enables or disables a hotkey."""
        self.hotkey_manager.set_hotkey_enabled(hotkey_id, enabled)
    
    def update_hotkey(self, hotkey_id: str, key: str = None, modifiers: list = None):
        """Updates a hotkey's key or modifiers."""
        self.hotkey_manager.update_hotkey(hotkey_id, key, modifiers)
    
    def get_hotkey_conflicts(self):
        """Gets hotkey conflicts."""
        return self.hotkey_manager.get_conflicts()
    
    # Hotkey Action Handlers
    
    def _hotkey_open_project(self):
        """Hotkey handler for opening project."""
        print("Engine: Hotkey - Open project")
        # This would typically trigger a file dialog in the GUI
    
    def _hotkey_save_collection(self):
        """Hotkey handler for saving collection."""
        print("Engine: Hotkey - Save collection")
        # This would typically trigger a save dialog in the GUI
    
    def _hotkey_export_project(self):
        """Hotkey handler for exporting project."""
        print("Engine: Hotkey - Export project")
        # This would typically trigger an export dialog in the GUI
    
    def _hotkey_run_analysis(self):
        """Hotkey handler for running analysis."""
        print("Engine: Hotkey - Run analysis")
        self.get_analytics()
    
    def _hotkey_find_duplicates(self):
        """Hotkey handler for finding duplicates."""
        print("Engine: Hotkey - Find duplicates")
        self.find_duplicates()
    
    def _hotkey_quick_scan(self):
        """Hotkey handler for quick scan."""
        print("Engine: Hotkey - Quick scan")
        # This would implement a quick scan without full analysis
    
    def _hotkey_next_file(self):
        """Hotkey handler for next file."""
        print("Engine: Hotkey - Next file")
        # This would navigate to next file in GUI
    
    def _hotkey_previous_file(self):
        """Hotkey handler for previous file."""
        print("Engine: Hotkey - Previous file")
        # This would navigate to previous file in GUI
    
    def _hotkey_toggle_include(self):
        """Hotkey handler for toggling include."""
        print("Engine: Hotkey - Toggle include")
        # This would toggle file inclusion in GUI
    
    def _hotkey_preferences(self):
        """Hotkey handler for preferences."""
        print("Engine: Hotkey - Preferences")
        # This would open preferences dialog
    
    def _hotkey_help(self):
        """Hotkey handler for help."""
        print("Engine: Hotkey - Help")
        # This would show help information
    
    def _hotkey_refresh(self):
        """Hotkey handler for refresh."""
        print("Engine: Hotkey - Refresh")
        # This would refresh the current view
    
    # Utility Methods
    
    def get_recent_projects(self):
        """Gets list of recently opened projects."""
        return self.config_manager.get_recent_projects()
    
    def clear_recent_projects(self):
        """Clears the recent projects list."""
        self.config_manager.clear_recent_projects()
    
    def backup_configuration(self, backup_dir: str = "backups"):
        """Creates a backup of the current configuration."""
        return self.config_manager.backup_config(backup_dir)
    
    def restore_configuration(self, backup_file: str):
        """Restores configuration from a backup file."""
        self.config_manager.restore_config(backup_file)
        self._apply_configuration()
    
    def validate_configuration(self):
        """Validates the current configuration."""
        return self.config_manager.validate_config()
    
    def get_state_summary(self) -> dict:
        """
        Returns a summary of the current engine state.
        Useful for debugging and monitoring.
        """
        return {
            "project_path": self.state.project_path,
            "total_files": len(self.state.all_discovered_files),
            "include_files": len(self.state.include_files),
            "other_files": len(self.state.other_files),
            "ignored_files": len(self.state.ignored_files),
            "active_formats": list(self.state.active_formats),
            "is_busy": self.state.is_busy,
            "status_message": self.state.status_message,
            "config_errors": self.validate_configuration(),
            "achievement_progress": self.achievement_system.get_progress_summary(),
            "hotkey_conflicts": self.get_hotkey_conflicts()
        }
