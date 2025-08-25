"""
Modern toolbar with grouped actions and icons.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
from ..styles import theme, modern_widgets

class Toolbar(ttk.Frame):
    """Modern toolbar with grouped actions and visual enhancements."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.action_groups: Dict[str, List[Dict]] = {}
        self.buttons: Dict[str, ttk.Button] = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the toolbar components."""
        # Main toolbar frame
        self.toolbar_frame = theme.create_styled_frame(self)
        self.toolbar_frame.pack(fill=tk.X, pady=theme.SPACING['sm'])
        
        # Configure grid for groups
        self.toolbar_frame.grid_columnconfigure(0, weight=1)
        
        # Groups will be added here dynamically
        self.groups_frame = theme.create_styled_frame(self.toolbar_frame)
        self.groups_frame.grid(row=0, column=0, sticky="ew")
    
    def add_action_group(self, group_name: str, actions: List[Dict]):
        """Add a group of actions to the toolbar.
        
        Args:
            group_name: Name of the action group
            actions: List of action dictionaries with keys:
                - name: Action name
                - text: Button text
                - command: Callback function
                - style: Button style (optional)
                - tooltip: Tooltip text (optional)
                - icon: Icon text (optional)
        """
        self.action_groups[group_name] = actions
        
        # Create group frame
        group_frame = theme.create_styled_frame(self.groups_frame)
        group_frame.pack(side=tk.LEFT, padx=(0, theme.SPACING['lg']))
        
        # Group label
        if group_name:
            group_label = theme.create_styled_label(group_frame, group_name,
                                                 font=theme.FONTS['small'],
                                                 foreground=theme.COLORS['text_secondary'])
            group_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        # Buttons frame
        buttons_frame = theme.create_styled_frame(group_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Create buttons for this group
        for action in actions:
            button = self._create_action_button(buttons_frame, action)
            if button:
                button.pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
                self.buttons[action['name']] = button
    
    def _create_action_button(self, parent, action: Dict) -> ttk.Button:
        """Create a button for an action."""
        # Determine button style
        style = action.get('style', 'Codexify.TButton')
        
        # Create button
        button = theme.create_styled_button(
            parent,
            text=action['text'],
            command=action['command'],
            style=style
        )
        
        # Add tooltip if specified
        if 'tooltip' in action:
            modern_widgets.create_tooltip(button, action['tooltip'])
        
        return button
    
    def add_separator(self):
        """Add a visual separator between groups."""
        separator = ttk.Separator(self.groups_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=theme.SPACING['md'])
    
    def enable_action(self, action_name: str):
        """Enable a specific action."""
        if action_name in self.buttons:
            self.buttons[action_name].configure(state='normal')
    
    def disable_action(self, action_name: str):
        """Disable a specific action."""
        if action_name in self.buttons:
            self.buttons[action_name].configure(state='disabled')
    
    def enable_group(self, group_name: str):
        """Enable all actions in a group."""
        if group_name in self.action_groups:
            for action in self.action_groups[group_name]:
                if action['name'] in self.buttons:
                    self.buttons[action['name']].configure(state='normal')
    
    def disable_group(self, group_name: str):
        """Disable all actions in a group."""
        if group_name in self.action_groups:
            for action in self.action_groups[group_name]:
                if action['name'] in self.buttons:
                    self.buttons[action['name']].configure(state='disabled')
    
    def get_button(self, action_name: str) -> Optional[ttk.Button]:
        """Get a button by action name."""
        return self.buttons.get(action_name)
    
    def clear(self):
        """Clear all action groups."""
        for widget in self.groups_frame.winfo_children():
            widget.destroy()
        self.action_groups.clear()
        self.buttons.clear()


class CodexifyToolbar(Toolbar):
    """Pre-configured toolbar for Codexify application."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_default_groups()
    
    def _setup_default_groups(self):
        """Setup the default action groups for Codexify."""
        
        # Project group
        project_actions = [
            {
                'name': 'load_project',
                'text': '📁 Load Project',
                'command': None,  # Will be set by parent
                'tooltip': 'Load a project folder for analysis'
            },
            {
                'name': 'refresh',
                'text': '🔄 Refresh',
                'command': None,
                'tooltip': 'Refresh the current project'
            }
        ]
        
        # Analysis group
        analysis_actions = [
            {
                'name': 'analyze',
                'text': '🔍 Analyze',
                'command': None,
                'tooltip': 'Analyze project structure and content'
            },
            {
                'name': 'find_duplicates',
                'text': '🔍 Find Duplicates',
                'command': None,
                'tooltip': 'Find duplicate files in the project'
            }
        ]
        
        # Output group
        output_actions = [
            {
                'name': 'collect_code',
                'text': '📤 Collect Code',
                'command': None,
                'tooltip': 'Collect and export code from selected files'
            },
            {
                'name': 'export_report',
                'text': '📊 Export Report',
                'command': None,
                'tooltip': 'Export analysis report'
            }
        ]
        
        # AI group
        ai_actions = [
            {
                'name': 'ai_explain',
                'text': '🧠 Explain (AI)',
                'command': None,
                'tooltip': 'Explain project using configured LLM'
            },
            {
                'name': 'ai_map',
                'text': '🗺️ Code Map',
                'command': None,
                'tooltip': 'Generate full Mermaid code map'
            },
            {
                'name': 'ai_settings',
                'text': '🔑 AI Settings',
                'command': None,
                'tooltip': 'Configure LLM provider and API key'
            }
        ]
        
        # Settings group
        settings_actions = [
            {
                'name': 'settings',
                'text': '⚙️ Settings',
                'command': None,
                'tooltip': 'Open application settings'
            },
            {
                'name': 'help',
                'text': '❓ Help',
                'command': None,
                'tooltip': 'Show help and documentation'
            }
        ]
        
        # Add groups
        self.add_action_group("Project", project_actions)
        self.add_separator()
        self.add_action_group("Analysis", analysis_actions)
        self.add_separator()
        self.add_action_group("AI", ai_actions)
        self.add_separator()
        self.add_action_group("Output", output_actions)
        self.add_separator()
        self.add_action_group("Settings", settings_actions)
    
    def set_project_actions(self, load_callback, refresh_callback):
        """Set callbacks for project actions."""
        if 'load_project' in self.buttons:
            self.buttons['load_project'].configure(command=load_callback)
        if 'refresh' in self.buttons:
            self.buttons['refresh'].configure(command=refresh_callback)
    
    def set_analysis_actions(self, analyze_callback, duplicates_callback):
        """Set callbacks for analysis actions."""
        if 'analyze' in self.buttons:
            self.buttons['analyze'].configure(command=analyze_callback)
        if 'find_duplicates' in self.buttons:
            self.buttons['find_duplicates'].configure(command=duplicates_callback)
    
    def set_output_actions(self, collect_callback, export_callback):
        """Set callbacks for output actions."""
        if 'collect_code' in self.buttons:
            self.buttons['collect_code'].configure(command=collect_callback)
        if 'export_report' in self.buttons:
            self.buttons['export_report'].configure(command=export_callback)
    
    def set_ai_actions(self, explain_callback, map_callback, settings_callback):
        """Set callbacks for AI actions."""
        if 'ai_explain' in self.buttons:
            self.buttons['ai_explain'].configure(command=explain_callback)
        if 'ai_map' in self.buttons:
            self.buttons['ai_map'].configure(command=map_callback)
        if 'ai_settings' in self.buttons:
            self.buttons['ai_settings'].configure(command=settings_callback)
    
    def set_settings_actions(self, settings_callback, help_callback):
        """Set callbacks for settings actions."""
        if 'settings' in self.buttons:
            self.buttons['settings'].configure(command=settings_callback)
        if 'help' in self.buttons:
            self.buttons['help'].configure(command=help_callback)
