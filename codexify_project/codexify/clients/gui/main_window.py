"""
Modern Codexify GUI with an enhanced and user-friendly layout.
Uses a paned window for a resizable two-panel interface.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from codexify.engine import CodexifyEngine
from codexify.events import STATUS_CHANGED, FILES_UPDATED, PROJECT_LOADED, ANALYSIS_COMPLETE
from .styles import theme
from .widgets import (
    FileList, ProgressWidget, StatusBar, CodexifyToolbar, 
    FormatSelector
)
from pathlib import Path

class MainWindow(tk.Tk):
    """
    The main graphical user interface for the Codexify application.
    Features a modern, resizable two-panel layout for better workflow.
    """
    def __init__(self):
        super().__init__()
        self.title("Codexify - Code Analysis & Documentation Tool")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        theme.apply_theme(self)
        
        self.engine = CodexifyEngine()
        self._subscribe_to_events()
        
        self._create_widgets()
        self._setup_layout()
        self._configure_callbacks()
        self._update_ui_state()

    def _subscribe_to_events(self):
        """Subscribes UI methods to engine events."""
        self.engine.events.subscribe(STATUS_CHANGED, self.on_status_changed)
        self.engine.events.subscribe(FILES_UPDATED, self.on_files_updated)
        self.engine.events.subscribe(PROJECT_LOADED, self.on_project_loaded)
        self.engine.events.subscribe(ANALYSIS_COMPLETE, self.on_analysis_complete)

    def _create_widgets(self):
        """Creates all UI components."""
        # --- Main Container ---
        self.main_container = theme.create_styled_frame(self, padding=theme.SPACING['md'])
        
        # --- Toolbar ---
        self.toolbar = CodexifyToolbar(self.main_container)
        
        # --- Project Info Header ---
        self.project_frame = theme.create_styled_labelframe(self.main_container, "Project Information")
        self.project_path_label = theme.create_styled_label(self.project_frame, "No project loaded.", padding=(theme.SPACING['sm'], theme.SPACING['xs']))
        
        # --- Main Paned Window (Left/Right Panels) ---
        self.main_paned_window = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, style='Codexify.Sash')

        # --- LEFT PANEL: File Selection & Filtering ---
        self.left_panel = theme.create_styled_frame(self.main_paned_window, padding=theme.SPACING['sm'])
        self.format_selector = FormatSelector(self.left_panel)
        
        # --- RIGHT PANEL: File Lists & Actions ---
        self.right_panel = theme.create_styled_frame(self.main_paned_window, padding=theme.SPACING['sm'])
        
        # --- File Lists inside a sub-paned window ---
        self.file_paned_window = ttk.PanedWindow(self.right_panel, orient=tk.VERTICAL, style='Codexify.Sash')
        self.include_list = FileList(self.file_paned_window, "Included Files")
        self.other_list = FileList(self.file_paned_window, "Other Project Files")

        # --- Move Buttons ---
        self.move_frame = theme.create_styled_frame(self.right_panel)
        self.move_to_include_btn = theme.create_styled_button(self.move_frame, text="< Include", command=self.move_to_include)
        self.move_to_other_btn = theme.create_styled_button(self.move_frame, text="Exclude >", command=self.move_to_other)

        # --- Progress Widget ---
        self.progress_widget = ProgressWidget(self.main_container)
        
        # --- Status Bar ---
        self.status_bar = StatusBar(self)

    def _setup_layout(self):
        """Arranges widgets in the main window."""
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.toolbar.pack(fill=tk.X, pady=(0, theme.SPACING['md']))
        self.project_frame.pack(fill=tk.X, pady=(0, theme.SPACING['md']))
        self.project_path_label.pack(fill=tk.X)
        
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)
        self.main_paned_window.add(self.left_panel, weight=1)
        self.main_paned_window.add(self.right_panel, weight=3)

        # Left panel layout
        self.format_selector.pack(fill=tk.BOTH, expand=True)

        # Right panel layout
        self.move_frame.pack(fill=tk.X, pady=theme.SPACING['sm'])
        self.move_to_include_btn.pack(side=tk.LEFT, padx=(0, theme.SPACING['sm']))
        self.move_to_other_btn.pack(side=tk.LEFT)
        
        self.file_paned_window.pack(fill=tk.BOTH, expand=True)
        self.file_paned_window.add(self.include_list, weight=1)
        self.file_paned_window.add(self.other_list, weight=1)

        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _configure_callbacks(self):
        """Configures all widget callbacks."""
        self.toolbar.set_project_actions(self.select_project_folder, self.refresh_project)
        self.toolbar.set_analysis_actions(self.analyze_project, self.find_duplicates)
        self.toolbar.set_output_actions(self.collect_code, self.export_report)
        self.toolbar.set_settings_actions(self.show_settings, self.show_help)
        
        self.format_selector.set_on_formats_changed(self.on_formats_changed)
        
        self.progress_widget.set_cancel_callback(self.cancel_operation)

    def _update_ui_state(self):
        """Updates UI element states based on the application state."""
        has_project = bool(self.engine.state.project_path)
        actions_to_toggle = ["Analysis", "Output"]
        for group in actions_to_toggle:
            if has_project:
                self.toolbar.enable_group(group)
            else:
                self.toolbar.disable_group(group)

    # --- UI Actions -> Engine API Calls ---

    def select_project_folder(self):
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            self.engine.load_project(path)
            self.status_bar.show_info(f"Loading project: {path}")
    
    def refresh_project(self):
        if self.engine.state.project_path:
            self.engine.load_project(self.engine.state.project_path)

    def analyze_project(self):
        if not self.engine.state.project_path:
            messagebox.showwarning("No Project", "Please load a project first.")
            return
        self.progress_widget.pack(fill=tk.X, pady=theme.SPACING['sm'], before=self.main_paned_window)
        self.progress_widget.show("Analyzing project...", indeterminate=True)
        self.engine.get_analytics()

    def find_duplicates(self):
        if not self.engine.state.project_path:
            messagebox.showwarning("No Project", "Please load a project first.")
            return
        self.progress_widget.pack(fill=tk.X, pady=theme.SPACING['sm'], before=self.main_paned_window)
        self.progress_widget.show("Finding duplicates...", indeterminate=True)
        self.engine.find_duplicates()

    def collect_code(self):
        if not self.engine.state.include_files:
            messagebox.showwarning("No Files", "There are no files in the 'Included' list to collect.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Collected Code",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")]
        )
        if file_path:
            format_type = Path(file_path).suffix[1:] or 'txt'
            self.engine.collect_code(file_path, format_type)

    def export_report(self):
        messagebox.showinfo("Not Implemented", "Exporting reports will be available in a future version.")

    def show_settings(self):
        messagebox.showinfo("Not Implemented", "A settings dialog will be available in a future version.")

    def show_help(self):
        messagebox.showinfo("Help", "For assistance, please visit the Codexify documentation.")

    def cancel_operation(self):
        # In a real app, this would signal the engine to stop the current task.
        self.progress_widget.hide()
        self.progress_widget.pack_forget()
        self.status_bar.show_warning("Operation cancelled.")

    # --- Event Handlers & UI Updaters ---

    def on_formats_changed(self, formats):
        self.engine.set_active_formats(set(formats))

    def move_to_include(self):
        selected_files = self.other_list.get_selected_files()
        if not selected_files:
            messagebox.showinfo("No Selection", "Select files from the 'Other' list to include them.")
            return
        self.engine.move_files(selected_files, 'include')

    def move_to_other(self):
        selected_files = self.include_list.get_selected_files()
        if not selected_files:
            messagebox.showinfo("No Selection", "Select files from the 'Included' list to exclude them.")
            return
        self.engine.move_files(selected_files, 'other')

    def on_status_changed(self, data=None):
        self.status_bar.show_info(self.engine.state.status_message)
    
    def on_project_loaded(self, data=None):
        path = self.engine.state.project_path
        self.project_path_label.config(text=f"Project: {path}")
        self.status_bar.set_project_info(Path(path).name)
        self._update_ui_state()
        self.on_files_updated()
    
    def on_files_updated(self, data=None):
        self.include_list.set_files(sorted(list(self.engine.state.include_files)))
        self.other_list.set_files(sorted(list(self.engine.state.other_files)))
        self.status_bar.set_file_count(len(self.engine.state.all_discovered_files))

    def on_analysis_complete(self, data=None):
        self.progress_widget.hide()
        self.progress_widget.pack_forget()
        if data and data.get('type') == 'duplicates':
            summary = data.get('results', {}).get('summary', {})
            msg = f"Found {summary.get('total_duplicates', 0)} duplicate groups."
            self.status_bar.show_success("Duplicate scan complete.")
        else:
            msg = "Project analysis complete."
            self.status_bar.show_success(msg)
        
        messagebox.showinfo("Analysis Complete", msg)

    def run(self):
        self.mainloop()
