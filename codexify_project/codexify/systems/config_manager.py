import json
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import shutil

class ConfigManager:
    """
    Manages application configuration, user settings, presets, and themes.
    Provides a centralized way to store and retrieve application settings.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "settings.json"
        self.presets_dir = self.config_dir / "presets"
        self.themes_dir = self.config_dir / "themes"
        self.templates_dir = self.config_dir / "templates"
        self.workspaces_dir = self.config_dir / "workspaces"
        self.tags_file = self.config_dir / "tags.json"
        self.filelists_dir = self.config_dir / "filelists"
        
        # Volatile mode: keep everything in-memory unless user explicitly exports
        self.volatile_mode = True
        # Ensure directories exist (disabled in volatile mode)
        self._ensure_directories()
        
        # Default configuration
        self.default_config = {
            "app": {
                "name": "Codexify",
                "version": "0.4.0",
                "theme": "default",
                "language": "en",
                "auto_save": True,
                "auto_backup": True,
                "max_recent_projects": 10
            },
            "scanning": {
                "max_file_size": 10485760,  # 10MB
                "skip_binary": True,
                "follow_symlinks": False,
                "max_depth": 50,
                "default_formats": [".py", ".js", ".html", ".css", ".md"]
            },
            "analysis": {
                "enable_quality_metrics": True,
                "enable_complexity_analysis": True,
                "min_block_size": 3,
                "similarity_threshold": 0.8,
                "max_duplicate_groups": 100
            },
            "output": {
                "default_format": "md",
                "include_metadata": True,
                "include_timestamps": True,
                "max_line_length": 120,
                "auto_format": True
            },
            "ui": {
                "window_width": 1000,
                "window_height": 700,
                "show_toolbar": True,
                "show_statusbar": True,
                "auto_refresh": True,
                "refresh_interval": 5000
            },
            "performance": {
                "max_threads": 4,
                "chunk_size": 1024,
                "cache_size": 1000,
                "enable_caching": True
            }
        }
        
        # Load configuration
        self.config = self._load_config()
        # In-memory session overrides (do not persist on disk)
        self._session_overrides: Dict[str, Any] = {}
        
        # Load presets and themes
        self.presets = self._load_presets()
        self.themes = self._load_themes()
        self.templates = self._load_templates()
        # Format presets (extension sets)
        self.format_presets: Dict[str, List[str]] = self._load_format_presets()
        # In-memory stores for volatile mode
        self._workspaces_mem: Dict[str, Dict[str, Any]] = {}
        self._filelists_mem: Dict[str, Dict[str, Any]] = {}
        # Path presets (absolute file paths for quick include)
        self.path_presets: Dict[str, List[str]] = self._load_path_presets()
    
    def _ensure_directories(self):
        """Creates necessary configuration directories."""
        if self.volatile_mode:
            return
        for directory in [self.config_dir, self.presets_dir, self.themes_dir, self.templates_dir, self.workspaces_dir, self.filelists_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from file or creates default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.default_config, config)
            else:
                # Create default config
                self._save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"ConfigManager: Error loading config: {e}")
            return self.default_config.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merges user config with defaults."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict[str, Any]):
        """Saves configuration to file."""
        if self.volatile_mode:
            return
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Error saving config: {e}")
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Gets a setting value using dot notation (e.g., 'ui.window_width').
        
        Args:
            key_path: Dot-separated path to the setting
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        # Session overrides take precedence
        if key_path in self._session_overrides:
            return self._session_overrides.get(key_path, default)

        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    # Session override helpers (in-memory only)
    def set_session_override(self, key_path: str, value: Any):
        self._session_overrides[key_path] = value

    def clear_session_override(self, key_path: str):
        if key_path in self._session_overrides:
            del self._session_overrides[key_path]

    def clear_all_session_overrides(self):
        self._session_overrides.clear()
    
    def set_setting(self, key_path: str, value: Any):
        """
        Sets a setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save configuration
        self._save_config(self.config)
        
        # Notify about configuration change
        self.on_config_changed(key_path, value)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Returns the complete configuration."""
        return self.config.copy()
    
    def export_config(self, file_path: str):
        """Exports configuration to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Error exporting config: {e}")
    
    def import_config(self, file_path: str):
        """Imports configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self.config = self._merge_configs(self.config, imported_config)
            self._save_config(self.config)
        except Exception as e:
            print(f"ConfigManager: Error importing config: {e}")
    
    # Preset Management
    
    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        """Loads available presets."""
        presets = {}
        
        if self.presets_dir.exists():
            for preset_file in self.presets_dir.glob("*.json"):
                try:
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        preset_data = json.load(f)
                        preset_name = preset_file.stem
                        presets[preset_name] = preset_data
                except Exception as e:
                    print(f"ConfigManager: Error loading preset {preset_file}: {e}")
        
        return presets

    # -------- Format presets (extensions) --------
    def _format_presets_file(self) -> Path:
        return self.config_dir / "format_presets.json"

    def _load_format_presets(self) -> Dict[str, List[str]]:
        presets: Dict[str, List[str]] = {
            "Web": [".html", ".css", ".js", ".ts"],
            "Python": [".py", ".ipynb"],
            "Java/Kotlin": [".java", ".kt"],
            "C/C++": [".c", ".cpp", ".h", ".hpp"],
            "Docs": [".md", ".rst", ".txt"],
            "Data": [".json", ".yaml", ".yml", ".csv"]
        }
        if not self.volatile_mode:
            try:
                p = self._format_presets_file()
                if p.exists():
                    with open(p, 'r', encoding='utf-8') as f:
                        disk = json.load(f)
                        if isinstance(disk, dict):
                            presets.update(disk)
            except Exception as e:
                print(f"ConfigManager: Failed to load format presets: {e}")
        return presets

    def _save_format_presets(self):
        if self.volatile_mode:
            return
        try:
            with open(self._format_presets_file(), 'w', encoding='utf-8') as f:
                json.dump(self.format_presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Failed to save format presets: {e}")

    def get_format_preset_names(self) -> List[str]:
        return sorted(self.format_presets.keys())

    def get_format_preset(self, name: str) -> List[str]:
        return self.format_presets.get(name, [])

    def save_format_preset(self, name: str, extensions: List[str]):
        self.format_presets[name] = sorted(set(extensions))
        self._save_format_presets()

    def delete_format_preset(self, name: str):
        if name in self.format_presets:
            del self.format_presets[name]
            self._save_format_presets()

    # -------- Path presets (absolute file lists) --------
    def _path_presets_file(self) -> Path:
        return self.config_dir / "path_presets.json"

    def _load_path_presets(self) -> Dict[str, List[str]]:
        presets: Dict[str, List[str]] = {}
        try:
            p = self._path_presets_file()
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    disk = json.load(f)
                    if isinstance(disk, dict):
                        presets.update({k: list(v) for k, v in disk.items()})
        except Exception as e:
            print(f"ConfigManager: Failed to load path presets: {e}")
        return presets

    def _save_path_presets(self):
        if self.volatile_mode:
            return
        try:
            with open(self._path_presets_file(), 'w', encoding='utf-8') as f:
                json.dump(self.path_presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Failed to save path presets: {e}")

    def get_path_preset_names(self) -> List[str]:
        return sorted(self.path_presets.keys())

    def get_path_preset(self, name: str) -> List[str]:
        return list(self.path_presets.get(name, []))

    def save_path_preset(self, name: str, paths: List[str]):
        # store unique absolute paths
        uniq = []
        seen = set()
        for p in paths:
            try:
                ap = str(Path(p).resolve())
            except Exception:
                ap = str(p)
            if ap not in seen:
                seen.add(ap)
                uniq.append(ap)
        self.path_presets[name] = uniq
        self._save_path_presets()

    def delete_path_preset(self, name: str):
        if name in self.path_presets:
            del self.path_presets[name]
            self._save_path_presets()

    # -------- Bundle export/import (formats, paths, saved filters, layout, active formats) --------
    def export_bundle(self, file_path: str, layout: Dict[str, Any] = None, active_formats: List[str] = None):
        bundle = {
            "format_presets": self.format_presets,
            "path_presets": self.path_presets,
            "saved_filters": self.get_setting("ui.saved_filters", {}) or {},
            "layout": layout or {},
            "active_formats": list(active_formats or [])
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)

    def import_bundle(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        # apply into config manager
        fm = bundle.get("format_presets")
        if isinstance(fm, dict):
            self.format_presets.update(fm)
            self._save_format_presets()
        pp = bundle.get("path_presets")
        if isinstance(pp, dict):
            self.path_presets.update(pp)
            self._save_path_presets()
        sf = bundle.get("saved_filters")
        if isinstance(sf, dict):
            self.set_setting("ui.saved_filters", sf)
        # return layout and active_formats to caller to apply in UI/engine
        return {
            "layout": bundle.get("layout", {}),
            "active_formats": bundle.get("active_formats", [])
        }
    
    def create_preset(self, name: str, description: str = "", settings: Dict[str, Any] = None):
        """
        Creates a new preset with current or specified settings.
        
        Args:
            name: Preset name
            description: Preset description
            settings: Settings to save (uses current if None)
        """
        if settings is None:
            settings = self.config.copy()
        
        preset_data = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "settings": settings
        }
        
        preset_file = self.presets_dir / f"{name}.json"
        
        try:
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            # Reload presets
            self.presets = self._load_presets()
        except Exception as e:
            print(f"ConfigManager: Error creating preset: {e}")
    
    def load_preset(self, name: str):
        """Loads a preset and applies its settings."""
        if name not in self.presets:
            raise ValueError(f"Preset '{name}' not found")
        
        preset = self.presets[name]
        self.config = self._merge_configs(self.default_config, preset["settings"])
        self._save_config(self.config)
    
    def delete_preset(self, name: str):
        """Deletes a preset."""
        preset_file = self.presets_dir / f"{name}.json"
        
        if preset_file.exists():
            try:
                preset_file.unlink()
                # Reload presets
                self.presets = self._load_presets()
            except Exception as e:
                print(f"ConfigManager: Error deleting preset: {e}")
    
    def get_preset_names(self) -> List[str]:
        """Returns list of available preset names."""
        return list(self.presets.keys())
    
    def get_preset_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns information about a preset."""
        return self.presets.get(name)
    
    # Theme Management
    
    def _default_theme_data(self) -> Dict[str, Any]:
        return {
            "name": "Default",
            "description": "Default Codexify theme",
            "colors": {
                "primary": "#007acc",
                "secondary": "#6c757d",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40",
                "background": "#ffffff",
                "foreground": "#212529"
            },
            "fonts": {
                "main": "Segoe UI",
                "monospace": "Consolas",
                "size": 10
            },
            "spacing": {
                "padding": 8,
                "margin": 4,
                "border_radius": 4
            }
        }

    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """Loads available themes."""
        themes = {}
        
        if self.themes_dir.exists():
            for theme_file in self.themes_dir.glob("*.json"):
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = theme_file.stem
                        themes[theme_name] = theme_data
                except Exception as e:
                    print(f"ConfigManager: Error loading theme {theme_file}: {e}")
        
        # Add default theme if none exists
        if not themes:
            if self.volatile_mode:
                themes = {"default": self._default_theme_data()}
            else:
                self._create_default_theme()
                # After creating on disk, try to load again once
                if self.themes_dir.exists():
                    for theme_file in self.themes_dir.glob("*.json"):
                        try:
                            with open(theme_file, 'r', encoding='utf-8') as f:
                                theme_data = json.load(f)
                                theme_name = theme_file.stem
                                themes[theme_name] = theme_data
                        except Exception as e:
                            print(f"ConfigManager: Error loading theme {theme_file}: {e}")
        
        return themes
    
    def _create_default_theme(self):
        """Creates a default theme."""
        if self.volatile_mode:
            # Store in-memory only
            self.themes = {"default": self._default_theme_data()}
            return
        default_theme = self._default_theme_data()
        theme_file = self.themes_dir / "default.json"
        try:
            self.themes_dir.mkdir(parents=True, exist_ok=True)
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(default_theme, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Error creating default theme: {e}")
    
    def get_theme(self, name: str = None) -> Dict[str, Any]:
        """Gets theme data by name or current theme."""
        if name is None:
            name = self.get_setting("app.theme", "default")
        
        return self.themes.get(name, self.themes.get("default", {}))
    
    def get_theme_names(self) -> List[str]:
        """Returns list of available theme names."""
        return list(self.themes.keys())
    
    def create_theme(self, name: str, theme_data: Dict[str, Any]):
        """Creates a new theme."""
        theme_file = self.themes_dir / f"{name}.json"
        
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            # Reload themes
            self.themes = self._load_themes()
        except Exception as e:
            print(f"ConfigManager: Error creating theme: {e}")
    
    # Template Management
    
    def _default_templates_data(self) -> Dict[str, Dict[str, Any]]:
        return {
            "professional": {
                "name": "Professional",
                "description": "Clean, professional output format",
                "include_header": True,
                "include_toc": True,
                "include_metadata": True,
                "code_style": "github",
                "section_headers": True
            },
            "minimal": {
                "name": "Minimal",
                "description": "Simple, minimal output format",
                "include_header": False,
                "include_toc": False,
                "include_metadata": False,
                "code_style": "plain",
                "section_headers": False
            },
            "documentation": {
                "name": "Documentation",
                "description": "Documentation-focused output format",
                "include_header": True,
                "include_toc": True,
                "include_metadata": True,
                "code_style": "github",
                "section_headers": True,
                "include_examples": True
            }
        }

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Loads available output templates."""
        templates = {}
        
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_name = template_file.stem
                        templates[template_name] = template_data
                except Exception as e:
                    print(f"ConfigManager: Error loading template {template_file}: {e}")
        
        # Add default templates if none exist
        if not templates:
            if self.volatile_mode:
                templates = self._default_templates_data()
            else:
                self._create_default_templates()
                # reload once
                if self.templates_dir.exists():
                    for template_file in self.templates_dir.glob("*.json"):
                        try:
                            with open(template_file, 'r', encoding='utf-8') as f:
                                template_data = json.load(f)
                                template_name = template_file.stem
                                templates[template_name] = template_data
                        except Exception as e:
                            print(f"ConfigManager: Error loading template {template_file}: {e}")
        
        return templates
    
    def _create_default_templates(self):
        """Creates default output templates."""
        if self.volatile_mode:
            self.templates = self._default_templates_data()
            return
        default_templates = self._default_templates_data()
        for name, template_data in default_templates.items():
            template_file = self.templates_dir / f"{name}.json"
            try:
                self.templates_dir.mkdir(parents=True, exist_ok=True)
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"ConfigManager: Error creating template {name}: {e}")
    
    def get_template(self, name: str) -> Dict[str, Any]:
        """Gets template data by name."""
        return self.templates.get(name, self.templates.get("professional", {}))
    
    def get_template_names(self) -> List[str]:
        """Returns list of available template names."""
        return list(self.templates.keys())
    
    # Utility Methods
    
    def backup_config(self, backup_dir: str = "backups"):
        """Creates a backup of the current configuration."""
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"config_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.config_file, backup_file)
            return str(backup_file)
        except Exception as e:
            print(f"ConfigManager: Error creating backup: {e}")
            return None
    
    def restore_config(self, backup_file: str):
        """Restores configuration from a backup file."""
        try:
            shutil.copy2(backup_file, self.config_file)
            # Reload configuration
            self.config = self._load_config()
        except Exception as e:
            print(f"ConfigManager: Error restoring backup: {e}")
    
    def validate_config(self) -> List[str]:
        """Validates the current configuration and returns any errors."""
        errors = []
        
        # Check required keys
        for key, value in self.default_config.items():
            if key not in self.config:
                errors.append(f"Missing required config section: {key}")
                continue
            
            if isinstance(value, dict):
                for subkey in value:
                    if subkey not in self.config[key]:
                        errors.append(f"Missing required config key: {key}.{subkey}")
        
        # Validate specific values
        if self.get_setting("scanning.max_file_size", 0) <= 0:
            errors.append("max_file_size must be positive")
        
        if self.get_setting("analysis.similarity_threshold", 0) < 0 or self.get_setting("analysis.similarity_threshold", 0) > 1:
            errors.append("similarity_threshold must be between 0 and 1")
        
        return errors
    
    def get_recent_projects(self) -> List[str]:
        """Gets list of recently opened projects."""
        return self.get_setting("app.recent_projects", [])
    
    def add_recent_project(self, project_path: str):
        """Adds a project to recent projects list."""
        recent = self.get_recent_projects()
        
        # Remove if already exists
        if project_path in recent:
            recent.remove(project_path)
        
        # Add to beginning
        recent.insert(0, project_path)
        
        # Limit list size
        max_recent = self.get_setting("app.max_recent_projects", 10)
        recent = recent[:max_recent]
        
        self.set_setting("app.recent_projects", recent)
    
    def clear_recent_projects(self):
        """Clears the recent projects list."""
        self.set_setting("app.recent_projects", [])

    # -------- Saved filters (per list) --------
    def get_saved_filters(self, list_id: str) -> List[Dict[str, Any]]:
        all_filters = self.get_setting("ui.saved_filters", {}) or {}
        return all_filters.get(list_id, [])

    def save_filter(self, list_id: str, name: str, search: str, ext: str, min_kb: str):
        all_filters = self.get_setting("ui.saved_filters", {}) or {}
        items = all_filters.get(list_id, [])
        # update if same name exists
        updated = False
        for it in items:
            if it.get("name") == name:
                it.update({"search": search, "ext": ext, "min_kb": min_kb})
                updated = True
                break
        if not updated:
            items.append({"name": name, "search": search, "ext": ext, "min_kb": min_kb})
        all_filters[list_id] = items
        self.set_setting("ui.saved_filters", all_filters)

    # -------- Workspaces (save/restore full UI state) --------
    def save_workspace(self, name: str, data: Dict[str, Any]):
        """Save a workspace JSON under config/workspaces/{name}.json"""
        if self.volatile_mode:
            self._workspaces_mem[name] = data
            return
        path = self.workspaces_dir / f"{name}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_workspace(self, name: str) -> Optional[Dict[str, Any]]:
        if self.volatile_mode:
            return self._workspaces_mem.get(name)
        path = self.workspaces_dir / f"{name}.json"
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_workspaces(self) -> List[str]:
        if self.volatile_mode:
            return list(self._workspaces_mem.keys())
        return [p.stem for p in self.workspaces_dir.glob('*.json')]

    def delete_workspace(self, name: str):
        if self.volatile_mode:
            if name in self._workspaces_mem:
                del self._workspaces_mem[name]
            return
        path = self.workspaces_dir / f"{name}.json"
        if path.exists():
            path.unlink()

    # -------- Exact file list presets (include/other sets) --------
    def save_filelist_preset(self, name: str, include: List[str], other: List[str]):
        data = {"include": list(sorted(set(include))), "other": list(sorted(set(other)))}
        if self.volatile_mode:
            self._filelists_mem[name] = data
            return
        path = self.filelists_dir / f"{name}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_filelist_preset(self, name: str) -> Optional[Dict[str, Any]]:
        if self.volatile_mode:
            return self._filelists_mem.get(name)
        path = self.filelists_dir / f"{name}.json"
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_filelist_presets(self) -> List[str]:
        if self.volatile_mode:
            return list(self._filelists_mem.keys())
        return [p.stem for p in self.filelists_dir.glob('*.json')]

    def delete_filelist_preset(self, name: str):
        if self.volatile_mode:
            if name in self._filelists_mem:
                del self._filelists_mem[name]
            return
        path = self.filelists_dir / f"{name}.json"
        if path.exists():
            path.unlink()

    # -------- Tags/Notes per file --------
    def _load_tags(self) -> Dict[str, Dict[str, Any]]:
        if self.tags_file.exists():
            try:
                with open(self.tags_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def _save_tags(self, tags: Dict[str, Dict[str, Any]]):
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(tags, f, indent=2, ensure_ascii=False)

    def add_tag(self, path: str, tag: str):
        tags = self._load_tags()
        item = tags.get(path, {"tags": [], "note": ""})
        if tag not in item["tags"]:
            item["tags"].append(tag)
        tags[path] = item
        self._save_tags(tags)

    def remove_tag(self, path: str, tag: str):
        tags = self._load_tags()
        item = tags.get(path, {"tags": [], "note": ""})
        item["tags"] = [t for t in item["tags"] if t != tag]
        tags[path] = item
        self._save_tags(tags)

    def set_note(self, path: str, note: str):
        tags = self._load_tags()
        item = tags.get(path, {"tags": [], "note": ""})
        item["note"] = note
        tags[path] = item
        self._save_tags(tags)

    def get_item_meta(self, path: str) -> Dict[str, Any]:
        tags = self._load_tags()
        return tags.get(path, {"tags": [], "note": ""})

    def delete_filter(self, list_id: str, name: str):
        all_filters = self.get_setting("ui.saved_filters", {}) or {}
        items = [it for it in all_filters.get(list_id, []) if it.get("name") != name]
        all_filters[list_id] = items
        self.set_setting("ui.saved_filters", all_filters)
    
    # Additional methods for test compatibility
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Returns all presets with their configurations."""
        return self.presets
    
    def export_configuration(self, file_path: str):
        """Exports the current configuration to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ConfigManager: Error exporting config: {e}")
    
    def import_configuration(self, file_path: str):
        """Imports configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                # Merge with current config
                self.config = self._merge_configs(self.config, imported_config)
                self._save_config(self.config)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in configuration file: {e}", e.doc, e.pos)
        except Exception as e:
            print(f"ConfigManager: Error importing config: {e}")
    
    def validate_configuration(self) -> bool:
        """Validates the current configuration."""
        errors = self.validate_config()
        return len(errors) == 0
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Returns the configuration schema."""
        return self.default_config
    
    def get_theme_options(self) -> List[str]:
        """Returns available theme options."""
        return list(self.themes.keys())
    
    def get_language_options(self) -> List[str]:
        """Returns available language options."""
        return ["en", "es", "fr", "de", "ru", "zh", "ja"]
    
    def get_output_format_options(self) -> List[str]:
        """Returns available output format options."""
        return ["txt", "md", "html", "json", "xml"]
    
    def merge_configuration(self, partial_config: Dict[str, Any]):
        """Merges a partial configuration with the current one."""
        self.config = self._merge_configs(self.config, partial_config)
        self._save_config(self.config)
    
    def get_configuration_diff(self, other_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns differences between current and other configuration."""
        diff = {}
        
        for key, value in other_config.items():
            if key not in self.config:
                diff[key] = {"current": None, "other": value}
            elif self.config[key] != value:
                diff[key] = {"current": self.config[key], "other": value}
        
        return diff
    
    def create_backup(self, backup_path: str):
        """Creates a configuration backup."""
        return self.backup_config(backup_path)
    
    def validate_setting(self, key: str, value: Any) -> bool:
        """Validates a specific setting value."""
        try:
            # Basic validation based on key
            if key == "app.theme":
                return value in self.get_theme_options()
            elif key == "app.language":
                return value in self.get_language_options()
            elif key == "output.default_format":
                return value in self.get_output_format_options()
            elif key == "scanning.max_file_size":
                return isinstance(value, (int, float)) and value > 0
            elif key == "analysis.similarity_threshold":
                return isinstance(value, (int, float)) and 0 <= value <= 1
            elif key == "ui.window_width" or key == "ui.window_height":
                return isinstance(value, (int, float)) and value > 0
            else:
                return True  # Default to valid for unknown keys
        except Exception:
            return False
    
    def reset_to_defaults(self):
        """Resets configuration to default values."""
        self.config = self.default_config.copy()
        self._save_config(self.config)
    
    def on_config_changed(self, key: str, value: Any):
        """Callback for configuration changes."""
        # This method can be overridden by subclasses or set as a callback
        pass


# Global instance for easy access
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Returns the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
