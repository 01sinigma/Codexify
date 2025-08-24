"""
Enhanced status bar with icons and animations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..styles import theme

class StatusBar(ttk.Frame):
    """Modern status bar with icons, progress, and status indicators."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.status_message = "Ready"
        self.status_type = "info"  # info, success, warning, error
        self.progress_visible = False
        self.progress_value = 0
        
        self._create_widgets()
        self._setup_animations()
    
    def _create_widgets(self):
        """Create the status bar components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        
        # Status message (left side)
        self.status_frame = theme.create_styled_frame(self)
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=theme.SPACING['sm'])
        
        # Status icon
        self.status_icon = tk.Label(self.status_frame, text="ℹ", 
                                   font=("Segoe UI", 12),
                                   bg=theme.COLORS['background'],
                                   fg=theme.COLORS['primary'])
        self.status_icon.pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        
        # Status text
        self.status_label = theme.create_styled_label(self.status_frame, self.status_message,
                                                    font=theme.FONTS['body'])
        self.status_label.pack(side=tk.LEFT)
        
        # Progress bar (center)
        self.progress_frame = theme.create_styled_frame(self)
        self.progress_frame.grid(row=0, column=1, sticky="ew", padx=theme.SPACING['sm'])
        
        self.progress_bar = theme.create_styled_progressbar(self.progress_frame, 
                                                          mode='determinate',
                                                          length=150)
        self.progress_bar.pack(pady=theme.SPACING['xs'])
        
        # Progress percentage
        self.progress_label = theme.create_styled_label(self.progress_frame, "0%",
                                                      foreground=theme.COLORS['text_secondary'],
                                                      font=theme.FONTS['small'])
        self.progress_label.pack()
        
        # Initially hide progress
        self.progress_frame.grid_remove()
        
        # Right side info (right side)
        self.info_frame = theme.create_styled_frame(self)
        self.info_frame.grid(row=0, column=2, sticky="e", padx=theme.SPACING['sm'])
        
        # File count
        self.file_count_label = theme.create_styled_label(self.info_frame, "0 files",
                                                        foreground=theme.COLORS['text_secondary'],
                                                        font=theme.FONTS['small'])
        self.file_count_label.pack(side=tk.RIGHT)
        
        # Separator
        separator = ttk.Separator(self.info_frame, orient='vertical')
        separator.pack(side=tk.RIGHT, fill=tk.Y, padx=theme.SPACING['sm'])
        
        # Project info
        self.project_label = theme.create_styled_label(self.info_frame, "No project",
                                                     foreground=theme.COLORS['text_secondary'],
                                                     font=theme.FONTS['small'])
        self.project_label.pack(side=tk.RIGHT)
        
        # Apply styling
        self.configure(relief=tk.SUNKEN, borderwidth=1)
    
    def _setup_animations(self):
        """Setup animation variables."""
        self.blink_id = None
        self.blink_state = False
    
    def _blink_icon(self):
        """Blink the status icon for attention."""
        if self.blink_state:
            self.status_icon.config(fg=theme.COLORS['background'])
        else:
            self._update_icon_color()
        
        self.blink_state = not self.blink_state
        self.blink_id = self.after(500, self._blink_icon)
    
    def _stop_blink(self):
        """Stop the blinking animation."""
        if self.blink_id:
            self.after_cancel(self.blink_id)
            self.blink_id = None
        self._update_icon_color()
    
    def _update_icon_color(self):
        """Update the icon color based on status type."""
        colors = {
            'info': theme.COLORS['primary'],
            'success': theme.COLORS['success'],
            'warning': theme.COLORS['warning'],
            'error': theme.COLORS['error']
        }
        color = colors.get(self.status_type, theme.COLORS['primary'])
        self.status_icon.config(fg=color)
    
    def set_status(self, message: str, status_type: str = "info", blink: bool = False):
        """Set the status message and type."""
        self.status_message = message
        self.status_type = status_type
        
        self.status_label.config(text=message)
        self._update_icon_color()
        
        if blink:
            self._blink_icon()
        else:
            self._stop_blink()
    
    def show_progress(self, show: bool = True):
        """Show or hide the progress bar."""
        self.progress_visible = show
        if show:
            self.progress_frame.grid()
        else:
            self.progress_frame.grid_remove()
    
    def update_progress(self, value: int):
        """Update the progress bar value."""
        self.progress_value = max(0, min(100, value))
        self.progress_bar.config(value=self.progress_value)
        self.progress_label.config(text=f"{self.progress_value:.0f}%")
        
        if not self.progress_visible:
            self.show_progress(True)
    
    def set_file_count(self, count: int):
        """Set the file count display."""
        if count == 1:
            self.file_count_label.config(text="1 file")
        else:
            self.file_count_label.config(text=f"{count} files")
    
    def set_project_info(self, project_name: str):
        """Set the project information."""
        if project_name:
            # Truncate long project names
            if len(project_name) > 30:
                project_name = "..." + project_name[-27:]
            self.project_label.config(text=project_name)
        else:
            self.project_label.config(text="No project")
    
    def clear(self):
        """Clear the status bar."""
        self.set_status("Ready", "info")
        self.show_progress(False)
        self.update_progress(0)
    
    def show_success(self, message: str):
        """Show a success message."""
        self.set_status(message, "success", blink=True)
    
    def show_warning(self, message: str):
        """Show a warning message."""
        self.set_status(message, "warning", blink=True)
    
    def show_error(self, message: str):
        """Show an error message."""
        self.set_status(message, "error", blink=True)
    
    def show_info(self, message: str):
        """Show an info message."""
        self.set_status(message, "info")
