"""
Modern Codexify GUI with enhanced UI/UX.
Uses the new widget system and modern styling.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    from tkinterdnd2 import TkinterDnD  # type: ignore
    _DND_AVAILABLE = True
except Exception:
    _DND_AVAILABLE = False
from codexify.engine import CodexifyEngine
from codexify.events import STATUS_CHANGED, FILES_UPDATED, PROJECT_LOADED, ANALYSIS_COMPLETE
from .styles import theme
from .widgets import (
    FileList, ProgressWidget, StatusBar, CodexifyToolbar, 
    SearchWidget, FormatSelector
)

BaseTk = TkinterDnD.Tk if _DND_AVAILABLE else tk.Tk

class MainWindow(BaseTk):
    """
    The main graphical user interface for the Codexify application.
    Features modern design, enhanced widgets, and better user experience.
    """
    def __init__(self):
        super().__init__()
        self.title("Codexify - Code Analysis & Documentation Tool")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        # Apply modern theme
        theme.apply_theme(self)
        
        # 1. Create and integrate the engine
        self.engine = CodexifyEngine()
        
        # 2. Subscribe to engine events
        self.engine.events.subscribe(STATUS_CHANGED, self.on_status_changed)
        self.engine.events.subscribe(FILES_UPDATED, self.on_files_updated)
        self.engine.events.subscribe(PROJECT_LOADED, self.on_project_loaded)
        self.engine.events.subscribe(ANALYSIS_COMPLETE, self.on_analysis_complete)
        
        # 3. Create UI widgets
        self._create_widgets()
        self._setup_layout()
        
        # 4. Configure callbacks
        self._configure_callbacks()
        
        # 5. Initial state
        self._update_ui_state()
    
    def _create_widgets(self):
        """Create all the UI widgets."""
        # Main container
        self.main_container = theme.create_styled_frame(self)
        
        # Toolbar
        self.toolbar = CodexifyToolbar(self.main_container)
        
        # Project info frame
        self.project_frame = theme.create_styled_labelframe(self.main_container, "Project Information")
        
        # Project path display
        self.project_path_label = theme.create_styled_label(self.project_frame, "No project loaded")
        self.project_path_label.pack(anchor=tk.W, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        # Project stats
        stats_frame = theme.create_styled_frame(self.project_frame)
        stats_frame.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        self.files_count_label = theme.create_styled_label(stats_frame, "Files: 0")
        self.files_count_label.pack(side=tk.LEFT, padx=(0, theme.SPACING['lg']))
        
        self.languages_count_label = theme.create_styled_label(stats_frame, "Languages: 0")
        self.languages_count_label.pack(side=tk.LEFT, padx=(0, theme.SPACING['lg']))
        
        self.project_size_label = theme.create_styled_label(stats_frame, "Size: 0 KB")
        self.project_size_label.pack(side=tk.LEFT)
        
        # Progress widget
        self.progress_widget = ProgressWidget(self.main_container)
        
        # Main content area
        self.content_frame = theme.create_styled_frame(self.main_container)
        
        # Left panel - Focus on file management (larger lists)
        left_panel = theme.create_styled_frame(self.content_frame)
        
        # File lists frame
        lists_frame = theme.create_styled_frame(left_panel)
        lists_frame.pack(fill=tk.BOTH, expand=True, pady=(0, theme.SPACING['md']))
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        lists_frame.grid_rowconfigure(0, weight=1)
        
        # Include files list
        self.include_list = FileList(lists_frame, "Include Files")
        self.include_list.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACING['sm']))
        
        # Other files list
        self.other_list = FileList(lists_frame, "Other Files")
        self.other_list.grid(row=0, column=1, sticky="nsew", padx=(theme.SPACING['sm'], 0))
        
        # Move buttons frame
        move_frame = theme.create_styled_frame(lists_frame)
        move_frame.grid(row=1, column=0, columnspan=2, pady=theme.SPACING['sm'])
        
        move_to_include_btn = theme.create_styled_button(move_frame, "→ Include", 
                                                       command=self.move_to_include)
        move_to_include_btn.pack(side=tk.LEFT, padx=theme.SPACING['sm'])
        
        move_to_other_btn = theme.create_styled_button(move_frame, "→ Other", 
                                                     command=self.move_to_other)
        move_to_other_btn.pack(side=tk.LEFT, padx=theme.SPACING['sm'])
        
        # Right panel - Formats, analysis and output
        right_panel = theme.create_styled_frame(self.content_frame)
        
        # Format selector moved here to free vertical space on the left
        self.format_selector = FormatSelector(right_panel, "File Formats")
        self.format_selector.pack(fill=tk.X, pady=(0, theme.SPACING['md']))
        
        # Analysis controls
        analysis_frame = theme.create_styled_labelframe(right_panel, "Analysis & Processing")
        
        analyze_btn = theme.create_styled_button(analysis_frame, "🔍 Analyze Project", 
                                               command=self.analyze_project,
                                               style='Codexify.Accent.TButton')
        analyze_btn.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        duplicates_btn = theme.create_styled_button(analysis_frame, "🔍 Find Duplicates", 
                                                  command=self.find_duplicates)
        duplicates_btn.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        # Output controls
        output_frame = theme.create_styled_labelframe(right_panel, "Output & Export")
        
        format_frame = theme.create_styled_frame(output_frame)
        format_frame.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        ttk.Label(format_frame, text="Output format:").pack(side=tk.LEFT)
        self.output_format_var = tk.StringVar(value="txt")
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format_var, 
                                   values=["txt", "md", "html"], state="readonly", width=10)
        format_combo.pack(side=tk.LEFT, padx=theme.SPACING['sm'])
        
        collect_btn = theme.create_styled_button(output_frame, "📤 Collect Code", 
                                               command=self.collect_code,
                                               style='Codexify.Accent.TButton')
        collect_btn.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        export_btn = theme.create_styled_button(output_frame, "📊 Export Report", 
                                              command=self.export_report)
        export_btn.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        # Search widget
        search_frame = theme.create_styled_labelframe(right_panel, "Search Files")
        self.search_widget = SearchWidget(search_frame, "Search in files...")
        self.search_widget.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        
        # Status bar
        self.status_bar = StatusBar(self.main_container)
    
    def _setup_layout(self):
        """Setup the widget layout."""
        # Main container
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=theme.SPACING['md'], 
                               pady=theme.SPACING['md'])
        
        # Toolbar at top
        self.toolbar.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        
        # Project info
        self.project_frame.pack(fill=tk.X, pady=(0, theme.SPACING['md']))
        
        # Content area
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, theme.SPACING['md']))
        self.content_frame.grid_columnconfigure(0, weight=3)  # Left panel wider for lists
        self.content_frame.grid_columnconfigure(1, weight=2)  # Right panel
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel
        left_panel = self.content_frame.winfo_children()[0]
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACING['md']))
        
        # Right panel
        right_panel = self.content_frame.winfo_children()[1]
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Status bar at bottom
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _configure_callbacks(self):
        """Configure all widget callbacks."""
        # Toolbar callbacks
        self.toolbar.set_project_actions(self.select_project_folder, self.refresh_project)
        self.toolbar.set_analysis_actions(self.analyze_project, self.find_duplicates)
        self.toolbar.set_output_actions(self.collect_code, self.export_report)
        self.toolbar.set_settings_actions(self.show_settings, self.show_help)
        
        # Format selector callback
        self.format_selector.set_on_formats_changed(self.on_formats_changed)
        
        # File list callbacks
        self.include_list.set_on_file_selected(self.on_include_file_selected)
        self.other_list.set_on_file_selected(self.on_other_file_selected)
        
        # Add context actions for quick move
        self.include_list.add_context_action("Move to Other", lambda: self._move_selected(self.include_list, 'other'))
        self.other_list.add_context_action("Move to Include", lambda: self._move_selected(self.other_list, 'include'))
        
        # External drops/paste to add files
        self.include_list.set_on_external_drop(lambda paths: self._add_paths(paths, 'include'))
        self.other_list.set_on_external_drop(lambda paths: self._add_paths(paths, 'other'))
        
        # Keyboard shortcuts for moving files
        self.include_list.listbox.bind('<Delete>', lambda e: self._move_selected(self.include_list, 'other'))
        self.other_list.listbox.bind('<Insert>', lambda e: self._move_selected(self.other_list, 'include'))
        self.include_list.listbox.bind('<Control-Right>', lambda e: self._move_selected(self.include_list, 'other'))
        self.other_list.listbox.bind('<Control-Left>', lambda e: self._move_selected(self.other_list, 'include'))
        
        # Simple drag-and-drop between listboxes (basic implementation)
        for src, dst, to in [
            (self.include_list, self.other_list, 'other'),
            (self.other_list, self.include_list, 'include')
        ]:
            src.listbox.bind('<ButtonPress-1>', self._dnd_start)
            src.listbox.bind('<B1-Motion>', self._dnd_drag)
            src.listbox.bind('<ButtonRelease-1>', lambda e, s=src, d=dst, t=to: self._dnd_drop(e, s, d, t))
        
        # Search widget callback
        self.search_widget.set_on_search_changed(self.on_search_changed)
        self.search_widget.set_on_result_selected(self.on_search_result_selected)
        
        # Progress widget callback
        self.progress_widget.set_cancel_callback(self.cancel_operation)

    # --- DnD helpers ---
    def _dnd_start(self, event):
        widget = event.widget
        widget._drag_start_index = widget.nearest(event.y)

    def _dnd_drag(self, event):
        # Visual feedback could be added here later
        pass

    def _dnd_drop(self, event, src_list: FileList, dst_list: FileList, to_list: str):
        try:
            start = getattr(src_list.listbox, '_drag_start_index', None)
            if start is None:
                return
            # Collect selected filenames
            selected = src_list.get_selected_files()
            if not selected:
                # If none selected, use item under drag start
                fname = src_list.listbox.get(start)
                for p in src_list.files:
                    if p.endswith(fname):
                        selected = [p]
                        break
            if selected:
                self.engine.move_files(set(selected), to_list)
        finally:
            if hasattr(src_list.listbox, '_drag_start_index'):
                delattr(src_list.listbox, '_drag_start_index')

    def _move_selected(self, list_widget: FileList, to_list: str):
        files = list_widget.get_selected_files()
        if files:
            self.engine.move_files(set(files), to_list)
            return "break"
        return None

    def _add_paths(self, paths: list, target: str):
        """Add external dropped paths (files/folders) to project lists.
        If a folder is dropped, scan it shallowly for files; absolute paths required.
        """
        import os
        collected = set()
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        collected.add(os.path.join(root, f))
            elif os.path.isfile(p):
                collected.add(p)
        if collected:
            # Merge into engine state sets directly, then notify
            if target == 'include':
                self.engine.state.include_files.update(collected)
                self.engine.state.other_files -= collected
            else:
                self.engine.state.other_files.update(collected)
                self.engine.state.include_files -= collected
            for fp in collected:
                self.engine.state.file_inclusion_modes[fp] = target
            self.engine.events.post(FILES_UPDATED)
    
    def _update_ui_state(self):
        """Update the UI state based on current engine state."""
        has_project = bool(self.engine.state.project_path)
        
        # Enable/disable actions based on project state
        if has_project:
            self.toolbar.enable_group("Analysis")
            self.toolbar.enable_group("Output")
        else:
            self.toolbar.disable_group("Analysis")
            self.toolbar.disable_group("Output")
    
    # --- UI Actions -> Engine API Calls ---
    
    def select_project_folder(self):
        """Open project folder selection dialog."""
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            self.engine.load_project(path)
    
    def refresh_project(self):
        """Refresh the current project."""
        if self.engine.state.project_path:
            self.engine.load_project(self.engine.state.project_path)
    
    def analyze_project(self):
        """Trigger project analysis."""
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning("Warning", "No project loaded. Please load a project first.")
            return
        
        self.progress_widget.show("Analyzing project...", indeterminate=True)
        self.status_bar.set_status("Analyzing project...", "info")
        self.engine.get_analytics()
    
    def find_duplicates(self):
        """Trigger duplicate detection."""
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning("Warning", "No project loaded. Please load a project first.")
            return
        
        self.progress_widget.show("Finding duplicates...", indeterminate=True)
        self.status_bar.set_status("Finding duplicates...", "info")
        self.engine.find_duplicates()
    
    def collect_code(self):
        """Collect and export code."""
        if not self.engine.state.include_files:
            messagebox.showwarning("Warning", "No files to collect. Please add files to the include list first.")
            return
        
        # Determine file extension based on format
        format_type = self.output_format_var.get()
        extensions = {"txt": ".txt", "md": ".md", "html": ".html"}
        default_ext = extensions.get(format_type, ".txt")
        
        path = filedialog.asksaveasfilename(
            title="Save Collected Code",
            defaultextension=default_ext,
            filetypes=[
                ("Text Files", "*.txt"),
                ("Markdown Files", "*.md"), 
                ("HTML Files", "*.html"),
                ("All Files", "*.*")
            ]
        )
        if path:
            self.progress_widget.show("Collecting code...", indeterminate=True)
            self.status_bar.set_status("Collecting code...", "info")
            self.engine.collect_code(path, format_type=format_type)
    
    def export_report(self):
        """Export analysis report."""
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning("Warning", "No project loaded. Please load a project first.")
            return
        
        path = filedialog.asksaveasfilename(
            title="Export Analysis Report",
            defaultextension=".html",
            filetypes=[
                ("HTML Files", "*.html"),
                ("Markdown Files", "*.md"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if path:
            self.progress_widget.show("Exporting report...", indeterminate=True)
            self.status_bar.set_status("Exporting report...", "info")
            # This would call a report export method
            self.after(2000, lambda: self.progress_widget.hide())
    
    def show_settings(self):
        """Show application settings."""
        messagebox.showinfo("Settings", "Settings dialog will be implemented in future versions.")
    
    def show_help(self):
        """Show help and documentation."""
        messagebox.showinfo("Help", "Help system will be implemented in future versions.")
    
    def cancel_operation(self):
        """Cancel the current operation."""
        self.progress_widget.hide()
        self.status_bar.set_status("Operation cancelled", "warning")
    
    # --- Event Handlers ---
    
    def on_formats_changed(self, formats):
        """Handle format selection changes."""
        self.engine.set_active_formats(set(formats))
    
    def on_include_file_selected(self, files):
        """Handle include file selection."""
        if files:
            self.status_bar.set_status(f"Selected {len(files)} file(s) in include list", "info")
    
    def on_other_file_selected(self, files):
        """Handle other file selection."""
        if files:
            self.status_bar.set_status(f"Selected {len(files)} file(s) in other list", "info")
    
    def on_search_changed(self, search_term):
        """Handle search term changes."""
        if search_term:
            self.status_bar.set_status(f"Searching for: {search_term}", "info")
    
    def on_search_result_selected(self, result):
        """Handle search result selection."""
        # Find and select the file in the appropriate list
        if result in self.engine.state.include_files:
            self.include_list.select_file(result)
        elif result in self.engine.state.other_files:
            self.other_list.select_file(result)
    
    def move_to_include(self):
        """Move selected files from other list to include list."""
        selected_files = self.other_list.get_selected_files()
        if not selected_files:
            messagebox.showinfo("Info", "Please select files to move")
            return
        
        self.engine.move_files(selected_files, 'include')
        self.status_bar.show_success(f"Moved {len(selected_files)} file(s) to include list")
    
    def move_to_other(self):
        """Move selected files from include list to other list."""
        selected_files = self.include_list.get_selected_files()
        if not selected_files:
            messagebox.showinfo("Info", "Please select files to move")
            return
        
        self.engine.move_files(selected_files, 'other')
        self.status_bar.show_success(f"Moved {len(selected_files)} file(s) to other list")
    
    # --- Engine Event Handlers -> UI Updates ---
    
    def on_status_changed(self, data=None):
        """Update status bar with engine status."""
        self.status_bar.set_status(self.engine.state.status_message)
    
    def on_project_loaded(self, data=None):
        """Handle project loaded event."""
        project_path = self.engine.state.project_path
        if project_path:
            # Update project info
            self.project_path_label.config(text=f"Project: {project_path}")
            
            # Update file counts
            total_files = len(self.engine.state.all_discovered_files)
            self.files_count_label.config(text=f"Files: {total_files}")
            
            # Update status
            self.status_bar.show_success(f"Project loaded: {total_files} files discovered")
            self.status_bar.set_project_info(project_path.split('/')[-1] if '/' in project_path else project_path.split('\\')[-1])
        else:
            self.project_path_label.config(text="No project loaded")
            self.status_bar.set_project_info("")
        
        self._update_ui_state()
        self.on_files_updated()
    
    def on_files_updated(self, data=None):
        """Handle files updated event."""
        # Update file lists
        self.include_list.set_files(list(self.engine.state.include_files))
        self.other_list.set_files(list(self.engine.state.other_files))
        
        # Update file counts
        include_count = len(self.engine.state.include_files)
        other_count = len(self.engine.state.other_files)
        total_count = include_count + other_count
        
        self.files_count_label.config(text=f"Files: {total_count}")
        self.status_bar.set_file_count(total_count)
        
        # Update search data
        all_files = list(self.engine.state.all_discovered_files)
        self.search_widget.set_search_data(all_files)
        
        # Update status
        if total_count > 0:
            self.status_bar.set_status(f"Project updated: {include_count} included, {other_count} other files", "info")
    
    def on_analysis_complete(self, data=None):
        """Handle analysis completion."""
        self.progress_widget.hide()
        
        if data and data.get('type') == 'duplicates':
            # Duplicate detection results
            results = data.get('results', {})
            summary = results.get('summary', {})
            duplicate_count = summary.get('total_duplicates', 0)
            affected_files = summary.get('duplicate_files', 0)
            
            self.status_bar.show_success(f"Found {duplicate_count} duplicate groups affecting {affected_files} files")
            messagebox.showinfo("Duplicate Detection Complete", 
                              f"Found {duplicate_count} duplicate groups\n"
                              f"Affecting {affected_files} files")
        else:
            # Regular analysis results
            if data:
                summary = data.get('summary', {})
                languages = data.get('languages', {})
                total_files = summary.get('total_files', 0)
                total_languages = languages.get('total_languages', 0)
                
                self.languages_count_label.config(text=f"Languages: {total_languages}")
                
                self.status_bar.show_success(f"Analysis complete: {total_files} files, {total_languages} languages")
                messagebox.showinfo("Analysis Complete", 
                                  f"Project analyzed successfully!\n"
                                  f"Total files: {total_files}\n"
                                  f"Programming languages: {total_languages}")
            else:
                self.status_bar.show_success("Analysis completed")
    
    def run(self):
        """Start the Tkinter event loop."""
        self.mainloop()
