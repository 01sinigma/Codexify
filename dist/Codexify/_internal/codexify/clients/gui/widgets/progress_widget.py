"""
Modern progress widget with detailed information and animations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from ..styles import theme

class ProgressWidget(ttk.Frame):
    """Enhanced progress widget with detailed status and animations."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_task = ""
        self.progress_value = 0
        self.is_indeterminate = False
        self.on_cancel: Optional[Callable] = None
        
        self._create_widgets()
        self._setup_animations()
    
    def _create_widgets(self):
        """Create the widget components."""
        # Main progress frame
        self.progress_frame = theme.create_styled_frame(self)
        self.progress_frame.pack(fill=tk.X, pady=theme.SPACING['sm'])
        
        # Task label
        self.task_label = theme.create_styled_label(self.progress_frame, "Ready", 
                                                  font=theme.FONTS['body'])
        self.task_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        # Progress bar frame
        bar_frame = theme.create_styled_frame(self.progress_frame)
        bar_frame.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        bar_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = theme.create_styled_progressbar(bar_frame, 
                                                          mode='determinate',
                                                          length=200)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, theme.SPACING['sm']))
        
        # Progress percentage
        self.percentage_label = theme.create_styled_label(bar_frame, "0%", 
                                                        foreground=theme.COLORS['text_secondary'])
        self.percentage_label.grid(row=0, column=1)
        
        # Cancel button (initially hidden)
        self.cancel_button = theme.create_styled_button(bar_frame, "Cancel", 
                                                      command=self._cancel_operation,
                                                      style='Codexify.Accent.TButton')
        self.cancel_button.grid(row=0, column=2, padx=(theme.SPACING['sm'], 0))
        self.cancel_button.grid_remove()  # Hidden by default
        
        # Status details frame
        self.details_frame = theme.create_styled_frame(self)
        self.details_frame.pack(fill=tk.X, pady=(theme.SPACING['xs'], 0))
        
        # Status text
        self.status_label = theme.create_styled_label(self.details_frame, "", 
                                                    foreground=theme.COLORS['text_secondary'],
                                                    font=theme.FONTS['small'])
        self.status_label.pack(anchor=tk.W)
        
        # Initially hidden
        self.pack_forget()
    
    def _setup_animations(self):
        """Setup animation variables."""
        self.animation_id = None
        self.dots_count = 0
    
    def _animate_dots(self):
        """Animate the dots for indeterminate progress."""
        if self.is_indeterminate:
            dots = "." * (self.dots_count % 4)
            self.task_label.config(text=f"{self.current_task}{dots}")
            self.dots_count += 1
            self.animation_id = self.after(500, self._animate_dots)
    
    def _cancel_operation(self):
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()
        self.hide()
    
    def show(self, task: str = "", indeterminate: bool = False):
        """Show the progress widget."""
        self.current_task = task
        self.is_indeterminate = indeterminate
        
        if task:
            self.task_label.config(text=task)
        
        if indeterminate:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self._animate_dots()
        else:
            self.progress_bar.config(mode='determinate')
            self.progress_bar.stop()
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None
        
        self.pack(fill=tk.X, pady=theme.SPACING['sm'])
        self.update_idletasks()
    
    def hide(self):
        """Hide the progress widget."""
        self.pack_forget()
        self.progress_bar.stop()
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
    
    def update_progress(self, value: int, status: str = ""):
        """Update the progress value and status."""
        self.progress_value = max(0, min(100, value))
        self.progress_bar.config(value=self.progress_value)
        
        # Update percentage
        self.percentage_label.config(text=f"{self.progress_value:.0f}%")
        
        # Update status
        if status:
            self.status_label.config(text=status)
        
        # Show cancel button if progress is active
        if self.progress_value > 0 and self.progress_value < 100:
            self.cancel_button.grid()
        else:
            self.cancel_button.grid_remove()
        
        self.update_idletasks()
    
    def set_task(self, task: str):
        """Set the current task description."""
        self.current_task = task
        self.task_label.config(text=task)
    
    def set_status(self, status: str):
        """Set the status message."""
        self.status_label.config(text=status)
    
    def set_cancel_callback(self, callback: Callable):
        """Set the callback for when cancel is clicked."""
        self.on_cancel = callback
    
    def set_indeterminate(self, indeterminate: bool):
        """Set whether the progress is indeterminate."""
        self.is_indeterminate = indeterminate
        if indeterminate:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self._animate_dots()
        else:
            self.progress_bar.config(mode='determinate')
            self.progress_bar.stop()
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None
