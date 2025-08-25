import json
import os
from typing import Dict, List, Set, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import tkinter as tk

class KeyModifier(Enum):
    """Keyboard modifiers for hotkeys."""
    CTRL = "Ctrl"
    SHIFT = "Shift"
    ALT = "Alt"
    SUPER = "Super"  # Windows key, Command key, etc.

@dataclass
class Hotkey:
    """Represents a single hotkey binding."""
    id: str
    name: str
    description: str
    action: str
    key: str
    modifiers: List[KeyModifier]
    enabled: bool = True
    category: str = "general"
    
    def __post_init__(self):
        if isinstance(self.modifiers, list) and self.modifiers:
            if isinstance(self.modifiers[0], str):
                self.modifiers = [KeyModifier(mod) for mod in self.modifiers]

class HotkeyManager:
    """
    Manages keyboard shortcuts and hotkey bindings.
    Provides a flexible system for binding keys to application actions.
    """
    
    def __init__(self, data_dir: str = "hotkeys"):
        self.data_dir = Path(data_dir)
        self.hotkeys_file = self.data_dir / "hotkeys.json"
        self.profiles_dir = self.data_dir / "profiles"
        # volatile mode: do not write to disk unless explicit export
        self.volatile_mode = True
        
        # Ensure directory exists (disabled in volatile mode)
        if not self.volatile_mode:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize hotkeys
        self.hotkeys = self._load_hotkeys()
        self.profiles = self._load_profiles()
        self.current_profile = "default"
        
        # Action handlers (will be set by the application)
        self.action_handlers: Dict[str, Callable] = {}
        
        # Tkinter binding state
        self.root_widget = None
        self.bound_widgets = set()
    
    def _load_hotkeys(self) -> Dict[str, Hotkey]:
        """Loads or creates default hotkeys."""
        if (not self.volatile_mode) and self.hotkeys_file.exists():
            try:
                with open(self.hotkeys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    hotkeys = {}
                    for hotkey_id, hotkey_data in data.items():
                        hotkey_data['modifiers'] = [KeyModifier(mod) for mod in hotkey_data.get('modifiers', [])]
                        hotkeys[hotkey_id] = Hotkey(**hotkey_data)
                    return hotkeys
            except Exception as e:
                print(f"HotkeyManager: Error loading hotkeys: {e}")
        
        # Create default hotkeys
        return self._create_default_hotkeys()
    
    def _create_default_hotkeys(self) -> Dict[str, Hotkey]:
        """Creates the default set of hotkeys."""
        hotkeys = {
            # File operations
            "open_project": Hotkey(
                id="open_project",
                name="Open Project",
                description="Open a project directory",
                action="open_project",
                key="O",
                modifiers=[KeyModifier.CTRL],
                category="file"
            ),
            "save_collection": Hotkey(
                id="save_collection",
                name="Save Collection",
                description="Save current code collection",
                action="save_collection",
                key="S",
                modifiers=[KeyModifier.CTRL],
                category="file"
            ),
            "export_project": Hotkey(
                id="export_project",
                name="Export Project",
                description="Export project analysis",
                action="export_project",
                key="E",
                modifiers=[KeyModifier.CTRL, KeyModifier.SHIFT],
                category="file"
            ),
            
            # Analysis operations
            "run_analysis": Hotkey(
                id="run_analysis",
                name="Run Analysis",
                description="Run project analysis",
                action="run_analysis",
                key="A",
                modifiers=[KeyModifier.CTRL],
                category="analysis"
            ),
            "find_duplicates": Hotkey(
                id="find_duplicates",
                name="Find Duplicates",
                description="Search for duplicate code",
                action="find_duplicates",
                key="D",
                modifiers=[KeyModifier.CTRL],
                category="analysis"
            ),
            "quick_scan": Hotkey(
                id="quick_scan",
                name="Quick Scan",
                description="Quick project scan",
                action="quick_scan",
                key="Q",
                modifiers=[KeyModifier.CTRL],
                category="analysis"
            ),
            
            # Navigation
            "next_file": Hotkey(
                id="next_file",
                name="Next File",
                description="Select next file in list",
                action="next_file",
                key="Tab",
                modifiers=[],
                category="navigation"
            ),
            "previous_file": Hotkey(
                id="previous_file",
                name="Previous File",
                description="Select previous file in list",
                action="previous_file",
                key="Tab",
                modifiers=[KeyModifier.SHIFT],
                category="navigation"
            ),
            "toggle_include": Hotkey(
                id="toggle_include",
                name="Toggle Include",
                description="Toggle file inclusion status",
                action="toggle_include",
                key="Space",
                modifiers=[],
                category="navigation"
            ),
            
            # View operations
            "toggle_sidebar": Hotkey(
                id="toggle_sidebar",
                name="Toggle Sidebar",
                description="Show/hide sidebar",
                action="toggle_sidebar",
                key="B",
                modifiers=[KeyModifier.CTRL],
                category="view"
            ),
            "toggle_toolbar": Hotkey(
                id="toggle_toolbar",
                name="Toggle Toolbar",
                description="Show/hide toolbar",
                action="toggle_toolbar",
                key="T",
                modifiers=[KeyModifier.CTRL],
                category="view"
            ),
            "fullscreen": Hotkey(
                id="fullscreen",
                name="Fullscreen",
                description="Toggle fullscreen mode",
                action="fullscreen",
                key="F11",
                modifiers=[],
                category="view"
            ),
            
            # Application
            "preferences": Hotkey(
                id="preferences",
                name="Preferences",
                description="Open preferences dialog",
                action="preferences",
                key=",",
                modifiers=[KeyModifier.CTRL],
                category="application"
            ),
            "help": Hotkey(
                id="help",
                name="Help",
                description="Show help information",
                action="help",
                key="F1",
                modifiers=[],
                category="application"
            ),
            "about": Hotkey(
                id="about",
                name="About",
                description="Show about dialog",
                action="about",
                key="F1",
                modifiers=[KeyModifier.CTRL],
                category="application"
            ),
            
            # Development
            "refresh": Hotkey(
                id="refresh",
                name="Refresh",
                description="Refresh current view",
                action="refresh",
                key="F5",
                modifiers=[],
                category="development"
            ),
            "debug_mode": Hotkey(
                id="debug_mode",
                name="Debug Mode",
                description="Toggle debug mode",
                action="debug_mode",
                key="F12",
                modifiers=[],
                category="development"
            ),
            "console": Hotkey(
                id="console",
                name="Console",
                description="Toggle console/terminal",
                action="console",
                key="`",
                modifiers=[KeyModifier.CTRL],
                category="development"
            )
        }
        
        # Save default hotkeys
        self._save_hotkeys(hotkeys)
        return hotkeys
    
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Loads available hotkey profiles."""
        profiles: Dict[str, Dict[str, Any]] = {}
        # Load from disk if not volatile
        if (not self.volatile_mode) and self.profiles_dir.exists():
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        profile_name = profile_file.stem
                        profiles[profile_name] = profile_data
                except Exception as e:
                    print(f"HotkeyManager: Error loading profile {profile_file}: {e}")
        # Ensure default exists
        if not profiles:
            if self.volatile_mode:
                profiles["default"] = {
                    "name": "Default",
                    "description": "Default Codexify hotkey profile",
                    "created_at": "2024-01-01T00:00:00",
                    "hotkeys": {}
                }
            else:
                self._create_default_profile()
                # Try load again from disk
                try:
                    for profile_file in self.profiles_dir.glob("*.json"):
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile_data = json.load(f)
                            profiles[profile_file.stem] = profile_data
                except Exception as e:
                    print(f"HotkeyManager: Error loading default profile: {e}")
        return profiles
    
    def _create_default_profile(self):
        """Creates a default hotkey profile."""
        default_profile = {
            "name": "Default",
            "description": "Default Codexify hotkey profile",
            "created_at": "2024-01-01T00:00:00",
            "hotkeys": {}
        }
        if self.volatile_mode:
            # Store in-memory
            self.profiles = {"default": default_profile}
            self.current_profile = "default"
        else:
            profile_file = self.profiles_dir / "default.json"
            try:
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(default_profile, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"HotkeyManager: Error creating default profile: {e}")
    
    def _save_hotkeys(self, hotkeys: Dict[str, Hotkey]):
        """Saves hotkeys to file."""
        if self.volatile_mode:
            return
        try:
            data = {}
            for hotkey_id, hotkey in hotkeys.items():
                hotkey_dict = asdict(hotkey)
                hotkey_dict['modifiers'] = [mod.value for mod in hotkey.modifiers]
                data[hotkey_id] = hotkey_dict
            with open(self.hotkeys_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"HotkeyManager: Error saving hotkeys: {e}")
    
    def _save_profiles(self):
        """Saves profiles to files."""
        if self.volatile_mode:
            return
        for profile_name, profile_data in self.profiles.items():
            profile_file = self.profiles_dir / f"{profile_name}.json"
            try:
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"HotkeyManager: Error saving profile {profile_name}: {e}")
    
    def set_root_widget(self, root: tk.Tk):
        """Sets the root widget for hotkey binding."""
        self.root_widget = root
        self._bind_all_hotkeys()
    
    def _bind_all_hotkeys(self):
        """Binds all enabled hotkeys to the root widget."""
        if not self.root_widget:
            return
        
        # Unbind existing hotkeys
        self._unbind_all_hotkeys()
        
        # Bind enabled hotkeys
        for hotkey in self.hotkeys.values():
            if hotkey.enabled:
                self._bind_hotkey(hotkey)
    
    def _bind_hotkey(self, hotkey: Hotkey):
        """Binds a single hotkey to the root widget."""
        if not self.root_widget:
            return
        
        # Convert hotkey to Tkinter format
        key_sequence = self._hotkey_to_sequence(hotkey)
        
        try:
            # Bind the hotkey
            self.root_widget.bind(key_sequence, lambda e: self._handle_hotkey(hotkey))
            self.bound_widgets.add(hotkey.id)
        except Exception as e:
            print(f"HotkeyManager: Error binding hotkey {hotkey.id}: {e}")
    
    def _hotkey_to_sequence(self, hotkey: Hotkey) -> str:
        """Converts a hotkey to Tkinter key sequence format."""
        sequence_parts = []
        
        # Add modifiers
        for modifier in hotkey.modifiers:
            if modifier == KeyModifier.CTRL:
                sequence_parts.append("Control")
            elif modifier == KeyModifier.SHIFT:
                sequence_parts.append("Shift")
            elif modifier == KeyModifier.ALT:
                sequence_parts.append("Alt")
            elif modifier == KeyModifier.SUPER:
                sequence_parts.append("Super")
        
        # Add key
        sequence_parts.append(hotkey.key)
        
        return "-".join(sequence_parts)
    
    def _handle_hotkey(self, hotkey: Hotkey):
        """Handles a hotkey press event."""
        print(f"HotkeyManager: Hotkey pressed: {hotkey.name} ({hotkey.action})")
        
        # Execute the action if handler exists
        if hotkey.action in self.action_handlers:
            try:
                self.action_handlers[hotkey.action]()
            except Exception as e:
                print(f"HotkeyManager: Error executing action {hotkey.action}: {e}")
        else:
            print(f"HotkeyManager: No handler for action {hotkey.action}")
    
    def _unbind_all_hotkeys(self):
        """Unbinds all hotkeys from the root widget."""
        if not self.root_widget:
            return
        
        for hotkey_id in self.bound_widgets:
            try:
                # Note: Tkinter doesn't have a direct way to unbind specific sequences
                # This is a limitation, but in practice it's rarely needed
                pass
            except Exception as e:
                print(f"HotkeyManager: Error unbinding hotkey {hotkey_id}: {e}")
        
        self.bound_widgets.clear()
    
    def register_action_handler(self, action: str, handler: Callable):
        """Registers a handler function for a specific action."""
        self.action_handlers[action] = handler
    
    def unregister_action_handler(self, action: str):
        """Unregisters a handler function for a specific action."""
        if action in self.action_handlers:
            del self.action_handlers[action]
    
    def get_hotkey(self, hotkey_id: str) -> Optional[Hotkey]:
        """Gets a hotkey by ID."""
        return self.hotkeys.get(hotkey_id)
    
    def get_all_hotkeys(self) -> List[Hotkey]:
        """Gets all hotkeys."""
        return list(self.hotkeys.values())
    
    def get_hotkeys_by_category(self, category: str) -> List[Hotkey]:
        """Gets hotkeys by category."""
        return [h for h in self.hotkeys.values() if h.category == category]
    
    def get_enabled_hotkeys(self) -> List[Hotkey]:
        """Gets all enabled hotkeys."""
        return [h for h in self.hotkeys.values() if h.enabled]
    
    def set_hotkey_enabled(self, hotkey_id: str, enabled: bool):
        """Enables or disables a hotkey."""
        hotkey = self.hotkeys.get(hotkey_id)
        if hotkey:
            hotkey.enabled = enabled
            if enabled:
                self._bind_hotkey(hotkey)
            # Note: Disabling requires rebinding all hotkeys
            self._save_hotkeys(self.hotkeys)
    
    def update_hotkey(self, hotkey_id: str, key: str = None, modifiers: List[KeyModifier] = None):
        """Updates a hotkey's key or modifiers."""
        hotkey = self.hotkeys.get(hotkey_id)
        if hotkey:
            if key is not None:
                hotkey.key = key
            if modifiers is not None:
                hotkey.modifiers = modifiers
            
            # Rebind if enabled
            if hotkey.enabled:
                self._bind_hotkey(hotkey)
            
            self._save_hotkeys(self.hotkeys)
    
    def create_hotkey(self, hotkey_id: str, name: str, description: str, action: str, 
                      key: str, modifiers: List[KeyModifier], category: str = "custom"):
        """Creates a new custom hotkey."""
        hotkey = Hotkey(
            id=hotkey_id,
            name=name,
            description=description,
            action=action,
            key=key,
            modifiers=modifiers,
            category=category
        )
        
        self.hotkeys[hotkey_id] = hotkey
        
        # Bind if enabled
        if hotkey.enabled:
            self._bind_hotkey(hotkey)
        
        self._save_hotkeys(self.hotkeys)
        return hotkey
    
    def delete_hotkey(self, hotkey_id: str):
        """Deletes a hotkey."""
        if hotkey_id in self.hotkeys:
            del self.hotkeys[hotkey_id]
            self._save_hotkeys(self.hotkeys)
    
    def get_profile_names(self) -> List[str]:
        """Returns list of available profile names."""
        return list(self.profiles.keys())
    
    def load_profile(self, profile_name: str):
        """Loads a hotkey profile."""
        if profile_name not in self.profiles:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        profile = self.profiles[profile_name]
        self.current_profile = profile_name
        
        # Apply profile hotkeys
        if "hotkeys" in profile:
            for hotkey_id, hotkey_data in profile["hotkeys"].items():
                if hotkey_id in self.hotkeys:
                    hotkey = self.hotkeys[hotkey_id]
                    hotkey.key = hotkey_data.get("key", hotkey.key)
                    hotkey.modifiers = [KeyModifier(mod) for mod in hotkey_data.get("modifiers", [])]
                    hotkey.enabled = hotkey_data.get("enabled", hotkey.enabled)
        
        # Rebind all hotkeys
        self._bind_all_hotkeys()
        self._save_hotkeys(self.hotkeys)
    
    def save_profile(self, profile_name: str, description: str = ""):
        """Saves current hotkey configuration as a profile."""
        profile_data = {
            "name": profile_name,
            "description": description,
            "created_at": "2024-01-01T00:00:00",  # Would use actual timestamp
            "hotkeys": {}
        }
        
        # Save current hotkey configuration
        for hotkey_id, hotkey in self.hotkeys.items():
            profile_data["hotkeys"][hotkey_id] = {
                "key": hotkey.key,
                "modifiers": [mod.value for mod in hotkey.modifiers],
                "enabled": hotkey.enabled
            }
        
        self.profiles[profile_name] = profile_data
        self._save_profiles()
    
    def delete_profile(self, profile_name: str):
        """Deletes a hotkey profile."""
        if profile_name in self.profiles:
            if not self.volatile_mode:
                profile_file = self.profiles_dir / f"{profile_name}.json"
                if profile_file.exists():
                    try:
                        profile_file.unlink()
                    except Exception as e:
                        print(f"HotkeyManager: Error deleting profile file: {e}")
            
            del self.profiles[profile_name]
    
    def export_hotkeys(self, file_path: str):
        """Exports hotkey configuration to a file."""
        try:
            data = {}
            for hotkey_id, hotkey in self.hotkeys.items():
                hotkey_dict = asdict(hotkey)
                hotkey_dict['modifiers'] = [mod.value for mod in hotkey.modifiers]
                data[hotkey_id] = hotkey_dict
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"HotkeyManager: Error exporting hotkeys: {e}")
    
    def import_hotkeys(self, file_path: str):
        """Imports hotkey configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Update existing hotkeys
            for hotkey_id, hotkey_data in imported_data.items():
                if hotkey_id in self.hotkeys:
                    hotkey = self.hotkeys[hotkey_id]
                    if "key" in hotkey_data:
                        hotkey.key = hotkey_data["key"]
                    if "modifiers" in hotkey_data:
                        hotkey.modifiers = [KeyModifier(mod) for mod in hotkey_data["modifiers"]]
                    if "enabled" in hotkey_data:
                        hotkey.enabled = hotkey_data["enabled"]
            
            # Rebind all hotkeys
            self._bind_all_hotkeys()
            self._save_hotkeys(self.hotkeys)
        except Exception as e:
            print(f"HotkeyManager: Error importing hotkeys: {e}")
    
    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Checks for hotkey conflicts and returns them."""
        conflicts = []
        key_combinations = {}
        
        for hotkey in self.hotkeys.values():
            if not hotkey.enabled:
                continue
            
            sequence = self._hotkey_to_sequence(hotkey)
            if sequence in key_combinations:
                conflicts.append({
                    "sequence": sequence,
                    "hotkey1": key_combinations[sequence],
                    "hotkey2": hotkey
                })
            else:
                key_combinations[sequence] = hotkey
        
        return conflicts
    
    def validate_hotkey(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """Validates if a hotkey combination is valid."""
        # Check if key is valid
        if not key or len(key) == 0:
            return False
        
        # Check for reserved combinations
        reserved_combinations = [
            ("Ctrl", "Alt", "Delete"),
            ("Ctrl", "Shift", "Esc"),
            ("Alt", "F4"),
            ("F1", "Ctrl"),  # Help
        ]
        
        current_modifiers = [mod.value for mod in modifiers]
        current_modifiers.sort()
        
        for reserved in reserved_combinations:
            reserved_list = list(reserved)
            reserved_list.sort()
            if current_modifiers == reserved_list:
                return False
        
        return True


# Global instance for easy access
_hotkey_manager = None

def get_hotkey_manager() -> HotkeyManager:
    """Returns the global hotkey manager instance."""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager()
    return _hotkey_manager
