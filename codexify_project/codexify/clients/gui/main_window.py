"""
Modern Codexify GUI with enhanced UI/UX.
Uses the new widget system and modern styling.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
        
        # Main content area with resizable panes
        self.content_frame = theme.create_styled_frame(self.main_container)
        self.main_panes = ttk.Panedwindow(self.content_frame, orient=tk.HORIZONTAL)
        self.main_panes.pack(fill=tk.BOTH, expand=True)
        
        left_container = theme.create_styled_frame(self.main_panes)
        right_container = theme.create_styled_frame(self.main_panes)
        # set reasonable minimums so справа File Formats не сплющивался
        self.main_panes.add(left_container, weight=3)
        self.main_panes.add(right_container, weight=2)
        
        # Left panel - Focus on file management (larger lists)
        left_panel = theme.create_styled_frame(left_container)
        left_panel.pack(fill=tk.BOTH, expand=True)
        
        # Resizable split between Include and Other
        left_split = ttk.Panedwindow(left_panel, orient=tk.HORIZONTAL)
        left_split.pack(fill=tk.BOTH, expand=True, pady=(0, theme.SPACING['md']))
        inc_frame = theme.create_styled_frame(left_split)
        oth_frame = theme.create_styled_frame(left_split)
        left_split.add(inc_frame, weight=1)
        left_split.add(oth_frame, weight=1)
        
        # Include files list
        self.include_list = FileList(inc_frame, "Include Files")
        self.include_list.pack(fill=tk.BOTH, expand=True, padx=(0, theme.SPACING['sm']))
        
        # Other files list
        self.other_list = FileList(oth_frame, "Other Files")
        self.other_list.pack(fill=tk.BOTH, expand=True, padx=(theme.SPACING['sm'], 0))
        
        # Move buttons frame
        move_frame = theme.create_styled_frame(left_panel)
        move_frame.pack(fill=tk.X, pady=theme.SPACING['sm'])
        
        move_to_include_btn = theme.create_styled_button(move_frame, "→ Include", 
                                                       command=self.move_to_include)
        move_to_include_btn.pack(side=tk.LEFT, padx=theme.SPACING['sm'])
        
        move_to_other_btn = theme.create_styled_button(move_frame, "→ Other", 
                                                     command=self.move_to_other)
        move_to_other_btn.pack(side=tk.LEFT, padx=theme.SPACING['sm'])

        # File List Presets (save/restore exact Include/Other sets)
        lists_preset_frame = theme.create_styled_labelframe(left_panel, "File List Presets")
        lists_preset_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        inner_lp = theme.create_styled_frame(lists_preset_frame)
        inner_lp.pack(fill=tk.X)
        ttk.Label(inner_lp, text="Preset:").pack(side=tk.LEFT)
        self.filelist_preset_var = tk.StringVar()
        self.filelist_preset_combo = ttk.Combobox(inner_lp, textvariable=self.filelist_preset_var, state='readonly', width=24)
        self.filelist_preset_combo.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['xs']))
        theme.create_styled_button(inner_lp, "Save Current", command=self._filelist_preset_save).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(inner_lp, "Load", command=self._filelist_preset_load).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(inner_lp, "Delete", command=self._filelist_preset_delete).pack(side=tk.LEFT)
        
        # Right panel - Formats, preview, analysis and output
        right_panel = theme.create_styled_frame(right_container)
        right_panel.pack(fill=tk.BOTH, expand=True)
        
        # Format selector moved here to free vertical space on the left
        self.format_selector = FormatSelector(right_panel, "File Formats")
        self.format_selector.pack(fill=tk.X, pady=(0, theme.SPACING['md']))
        
        # Inline preview
        preview_frame = theme.create_styled_labelframe(right_panel, "Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, theme.SPACING['md']))
        self.preview_text = tk.Text(preview_frame, height=12, wrap='none')
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        self.preview_text.configure(state='disabled')

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
        
        # Restore layout if saved
        self.after(150, self._restore_layout)
    
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
        # Set initial sash positions after geometry is ready
        self.after(100, self._init_sash_positions)
        
        # Bottom bar with Logs (left) and StatusBar (expand) — grid to ensure visibility
        self.bottom_bar = theme.create_styled_frame(self.main_container)
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        try:
            # clear any prior packing of status bar
            self.status_bar.destroy()
        except Exception:
            pass
        # Grid columns: 0 fixed for Logs button, 1 stretchy for StatusBar
        try:
            self.bottom_bar.grid_columnconfigure(0, weight=0)
            self.bottom_bar.grid_columnconfigure(1, weight=1)
        except Exception:
            pass
        logs_btn = theme.create_styled_button(self.bottom_bar, 'Logs', command=self._open_logs_viewer)
        logs_btn.grid(row=0, column=0, sticky='w', padx=(theme.SPACING['sm'], theme.SPACING['sm']), pady=(0, theme.SPACING['xs']))
        self.status_bar = StatusBar(self.bottom_bar)
        self.status_bar.grid(row=0, column=1, sticky='ew', padx=(0, theme.SPACING['sm']), pady=(0, theme.SPACING['xs']))

    def _init_sash_positions(self):
        try:
            total = self.main_panes.winfo_width()
            if total <= 0:
                total = self.winfo_width()
            # 60% for left, 40% for right
            self.main_panes.sashpos(0, int(total * 0.60))
        except Exception:
            pass
        # inner split 50/50
        try:
            # left_panel is inside left_container: find the Panedwindow
            left_split = None
            for w in self.content_frame.winfo_children():
                if isinstance(w, ttk.Panedwindow):
                    # this is main_panes; find the first child frame (left_container)
                    left_container = w.panes()[0] if hasattr(w, 'panes') else None
            # fallback: search recursively
            for child in self.main_panes.winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Panedwindow):
                        left_split = sub
                        break
                if left_split:
                    break
            if left_split:
                width = left_split.winfo_width()
                if width <= 0:
                    width = int(self.main_panes.winfo_width() * 0.6)
                left_split.sashpos(0, int(width * 0.5))
        except Exception:
            pass

    # --- Layout persistence ---
    def _restore_layout(self):
        try:
            cfg = self.engine.get_setting('ui.layout', {}) or {}
            main_pos = cfg.get('main_sash')
            if isinstance(main_pos, int):
                self.main_panes.sashpos(0, main_pos)
            # set columns widths if saved
            inc_cols = cfg.get('include_cols')
            oth_cols = cfg.get('other_cols')
            if isinstance(inc_cols, dict):
                self.include_list.set_column_widths(inc_cols)
            if isinstance(oth_cols, dict):
                self.other_list.set_column_widths(oth_cols)
        except Exception:
            pass

    def _save_layout(self):
        try:
            cfg = {
                'main_sash': self.main_panes.sashpos(0),
                'include_cols': self.include_list.get_column_widths(),
                'other_cols': self.other_list.get_column_widths()
            }
            self.engine.set_setting('ui.layout', cfg)
        except Exception:
            pass
    
    def reset_layout(self):
        self.engine.set_setting('ui.layout', {})
        self._init_sash_positions()

    def destroy(self):
        # save layout before close
        self._save_layout()
        super().destroy()

    def _configure_callbacks(self):
        """Configure all widget callbacks."""
        # Toolbar callbacks
        self.toolbar.set_project_actions(self.select_project_folder, self.refresh_project)
        self.toolbar.set_analysis_actions(self.analyze_project, self.find_duplicates)
        self.toolbar.set_output_actions(self.collect_code, self.export_report)
        self.toolbar.set_settings_actions(self.show_settings, self.show_help)
        
        # Format selector callback
        self.format_selector.set_on_formats_changed(self.on_formats_changed)
        # Preset wiring
        try:
            preset_names = self.engine.config_manager.get_format_preset_names()
            self.format_selector.set_preset_names(preset_names)
        except Exception:
            pass
        self.format_selector.set_on_apply_preset(self._apply_preset)
        self.format_selector.set_on_save_preset(self._save_preset)
        self.format_selector.set_on_delete_preset(self._delete_preset)
        self.format_selector.set_on_suggest_preset(self._suggest_preset)
        
        # Undo/Redo shortcuts
        self.bind_all('<Control-z>', lambda e: self._do_undo())
        self.bind_all('<Control-y>', lambda e: self._do_redo())
        # Command palette
        self.bind_all('<Control-k>', lambda e: self._open_command_palette())
        # Watch mode timer holder
        self._watch_job = None
        
        # File list callbacks (status + preview)
        self.include_list.set_on_file_selected(lambda files: self._on_list_selection('include', files))
        self.other_list.set_on_file_selected(lambda files: self._on_list_selection('other', files))
        
        # Add context actions for quick move
        self.include_list.add_context_action("Move to Other", lambda: self._move_selected(self.include_list, 'other'))
        self.other_list.add_context_action("Move to Include", lambda: self._move_selected(self.other_list, 'include'))
        self.include_list.add_context_action("Remove from list", lambda: self._remove_selected(self.include_list))
        self.other_list.add_context_action("Remove from list", lambda: self._remove_selected(self.other_list))
        self.include_list.add_context_action("Move all of same type → Other", lambda: self._move_all_by_type(self.include_list, 'other'))
        self.other_list.add_context_action("Move all of same type → Include", lambda: self._move_all_by_type(self.other_list, 'include'))
        
        # External drops/paste to add files
        self.include_list.set_on_external_drop(lambda paths: self._add_paths(paths, 'include'))
        self.other_list.set_on_external_drop(lambda paths: self._add_paths(paths, 'other'))
        # Saved filters wiring
        self._refresh_saved_filters_ui()
        self.include_list.set_on_filters_save(lambda n,s,e,k: self._save_filter('include', n, s, e, k))
        self.include_list.set_on_filters_delete(lambda n: self._delete_filter('include', n))
        self.include_list.set_on_filters_apply(lambda n: self._apply_filter('include', n))
        self.other_list.set_on_filters_save(lambda n,s,e,k: self._save_filter('other', n, s, e, k))
        self.other_list.set_on_filters_delete(lambda n: self._delete_filter('other', n))
        self.other_list.set_on_filters_apply(lambda n: self._apply_filter('other', n))
        # File list preset names
        try:
            names = self.engine.config_manager.list_filelist_presets()
            self.filelist_preset_combo['values'] = names
            if names:
                self.filelist_preset_combo.current(0)
        except Exception:
            pass
        
        # Keyboard shortcuts for moving files
        self.include_list.listbox.bind('<Delete>', lambda e: self._remove_selected(self.include_list))
        self.other_list.listbox.bind('<Delete>', lambda e: self._remove_selected(self.other_list))
        self.include_list.listbox.bind('<Insert>', lambda e: self._move_selected(self.include_list, 'include'))
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
        
        # Listen column width changes to persist
        self.include_list.bind('<<ColumnsChanged>>', lambda e: self._save_layout())
        self.other_list.bind('<<ColumnsChanged>>', lambda e: self._save_layout())

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
        from pathlib import Path
        files = list_widget.get_selected_files()
        if not files:
            return None
        if to_list == 'include':
            # check formats
            active = set(self.engine.state.active_formats or [])
            new_exts = {Path(fp).suffix.lower() for fp in files if Path(fp).suffix}
            missing = sorted([e for e in new_exts if e not in active])
            if missing:
                ans = messagebox.askyesno("Add formats?", 
                    f"Selected files contain new types: {', '.join(missing)}.\nAdd these formats and include ALL files of these types?")
                if ans:
                    # add formats
                    active.update(missing)
                    self.engine.set_active_formats(active)
                    # include all files of those types
                    from_set = self.engine.state.other_files | self.engine.state.include_files
                    all_of_types = {p for p in from_set if Path(p).suffix.lower() in missing}
                    files = list(set(files) | all_of_types)
                else:
                    # include only selected
                    pass
        self.engine.move_files(set(files), to_list)
        self._toast(f"Moved {len(files)} file(s) → {to_list}")
        return "break"

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
            if target == 'include':
                # apply same policy as manual move
                self._move_selected(self.include_list, 'include')  # reuse path
                # fallback include only collected if selection not present
                self.engine.move_files(collected, 'include')
            else:
                # add to Other и расширения в набор форматов для будущего
                from pathlib import Path
                self.engine.state.other_files.update(collected)
                self.engine.state.include_files -= collected
                for fp in collected:
                    self.engine.state.file_inclusion_modes[fp] = 'other'
                # расширить пресеты активных форматов для будущего
                active = set(self.engine.state.active_formats or [])
                exts = {Path(p).suffix.lower() for p in collected if Path(p).suffix}
                if exts - active:
                    self.engine.set_active_formats(active | exts)
                self.engine.events.post(FILES_UPDATED)

    def _remove_selected(self, list_widget: FileList):
        files = list_widget.get_selected_files()
        if files:
            self.engine.remove_files(set(files))
            self._toast(f"Removed {len(files)} file(s)")
            return "break"
        return None

    # --- Preset handlers ---
    def _apply_preset(self, name: str):
        exts = self.engine.config_manager.get_format_preset(name)
        self.engine.set_active_formats(set(exts))
        self.status_bar.show_success(f"Preset applied: {name}")
        self._toast(f"Preset: {name}")
        # Refresh file lists
        self.on_files_updated()

    def _save_preset(self, name: str, exts: list):
        self.engine.config_manager.save_format_preset(name, exts)
        self.format_selector.set_preset_names(self.engine.config_manager.get_format_preset_names())
        self.status_bar.show_success(f"Preset saved: {name}")

    def _delete_preset(self, name: str):
        self.engine.config_manager.delete_format_preset(name)
        self.format_selector.set_preset_names(self.engine.config_manager.get_format_preset_names())
        self.status_bar.show_success(f"Preset deleted: {name}")

    # --- Helpers ---
    def _move_all_by_type(self, list_widget: FileList, to_list: str):
        from pathlib import Path
        files = list_widget.get_selected_files()
        if not files:
            return None
        exts = {Path(fp).suffix.lower() for fp in files}
        source = self.engine.state.include_files if list_widget is self.include_list else self.engine.state.other_files
        candidates = {fp for fp in source if Path(fp).suffix.lower() in exts}
        if candidates:
            self.engine.move_files(candidates, to_list)
            return "break"
        return None

    def _suggest_preset(self):
        # Heuristic: pick preset with most overlap of discovered extensions
        from pathlib import Path
        discovered_exts = {Path(p).suffix.lower() for p in self.engine.state.all_discovered_files}
        best_name = None
        best_score = -1
        for name in self.engine.config_manager.get_format_preset_names():
            exts = set(self.engine.config_manager.get_format_preset(name))
            score = len(discovered_exts & exts)
            if score > best_score:
                best_score = score
                best_name = name
        if best_name:
            self._apply_preset(best_name)
            self.status_bar.show_success(f"Suggested preset applied: {best_name}")
        else:
            messagebox.showinfo("Suggest preset", "No suitable preset found for current project.")

    # --- Undo/Redo and toasts ---
    def _do_undo(self):
        if self.engine.undo():
            self._toast("Undo")

    def _do_redo(self):
        if self.engine.redo():
            self._toast("Redo")

    def _toast(self, text: str):
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        x = self.winfo_rootx() + self.winfo_width() - 220
        y = self.winfo_rooty() + self.winfo_height() - 80
        top.geometry(f"200x40+{x}+{y}")
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text=text).pack(expand=True)
        top.after(1500, top.destroy)

    # --- Command palette ---
    def _open_command_palette(self):
        palette = tk.Toplevel(self)
        palette.title('Command palette')
        palette.transient(self)
        palette.geometry(f"360x300+{self.winfo_rootx()+40}+{self.winfo_rooty()+80}")
        frm = theme.create_styled_frame(palette)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        query = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=query)
        ent.pack(fill=tk.X)
        lst = tk.Listbox(frm, height=10)
        lst.pack(fill=tk.BOTH, expand=True, pady=(6,0))
        # Context-aware actions
        focus_widget = self.focus_get()
        list_actions = []
        if focus_widget and (hasattr(self.include_list, 'tree') and focus_widget in (self.include_list.tree,)):
            list_actions = [
                ('List: Select same extension', self.include_list.select_same_extension),
                ('List: Select by pattern…', self.include_list.select_by_pattern),
            ]
        elif focus_widget and (hasattr(self.other_list, 'tree') and focus_widget in (self.other_list.tree,)):
            list_actions = [
                ('List: Select same extension', self.other_list.select_same_extension),
                ('List: Select by pattern…', self.other_list.select_by_pattern),
            ]

        actions = [
            ('Load Project', self.select_project_folder),
            ('Refresh Project', self.refresh_project),
            ('Analyze', self.analyze_project),
            ('Find Duplicates', self.find_duplicates),
            ('Collect Code', self.collect_code),
            ('Path Preset: Save from Include', self._cmd_save_path_preset),
            ('Path Preset: Apply to Include', self._cmd_apply_path_preset_include),
            ('Path Preset: Apply to Other', self._cmd_apply_path_preset_other),
            ('Path Preset: Delete', self._cmd_delete_path_preset),
            ('Workspace: Save…', self._cmd_workspace_save),
            ('Workspace: Load…', self._cmd_workspace_load),
            ('Workspace: Delete…', self._cmd_workspace_delete),
            ('Watch: Toggle', self._cmd_watch_toggle),
            ('Bundle: Export…', self._cmd_bundle_export),
            ('Bundle: Import…', self._cmd_bundle_import),
            ('Open Logs', lambda: self.show_help()),
            ('Reset Layout', self.reset_layout)
        ] + list_actions
        def refresh_list(*_):
            q = query.get().lower()
            lst.delete(0, tk.END)
            for name, _cb in actions:
                if q in name.lower():
                    lst.insert(tk.END, name)
        refresh_list()
        query.trace_add('write', refresh_list)
        def run():
            sel = lst.curselection()
            if not sel:
                return
            name = lst.get(sel[0])
            for n, cb in actions:
                if n == name:
                    cb()
                    break
            palette.destroy()
        lst.bind('<Return>', lambda e: run())
        lst.bind('<Double-Button-1>', lambda e: run())
        ent.bind('<Return>', lambda e: run())
        ent.focus()

    # --- Path preset commands (simple prompts) ---
    def _cmd_save_path_preset(self):
        name = tk.simpledialog.askstring("Save Path Preset", "Preset name:")
        if not name:
            return
        # save current Include selection if any, else all Include
        sel = set(self.include_list.get_selected_files())
        if not sel:
            sel = set(self.engine.state.include_files)
        self.engine.save_path_preset(name, sel)
        self._toast(f"Path preset saved: {name}")

    def _cmd_apply_path_preset_include(self):
        self._apply_path_preset_to('include')

    def _cmd_apply_path_preset_other(self):
        self._apply_path_preset_to('other')

    def _apply_path_preset_to(self, destination: str):
        names = self.engine.config_manager.get_path_preset_names()
        if not names:
            messagebox.showinfo('Path Presets', 'No path presets found')
            return
        # quick selection dialog
        top = tk.Toplevel(self)
        top.title('Select Path Preset')
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        lb = tk.Listbox(frm, height=min(10, max(3, len(names))))
        for n in names:
            lb.insert(tk.END, n)
        lb.pack(fill=tk.BOTH, expand=True)
        def ok():
            sel = lb.curselection()
            if not sel:
                top.destroy()
                return
            name = lb.get(sel[0])
            if self.engine.apply_path_preset(name, destination):
                self._toast(f"Applied: {name} → {destination}")
                self.on_files_updated()
            top.destroy()
        theme.create_styled_button(frm, 'Apply', command=ok).pack(pady=6)

    def _cmd_delete_path_preset(self):
        names = self.engine.config_manager.get_path_preset_names()
        if not names:
            messagebox.showinfo('Path Presets', 'No path presets found')
            return
        name = tk.simpledialog.askstring('Delete Path Preset', 'Preset name to delete:', initialvalue=names[0])
        if name and name in names:
            self.engine.delete_path_preset(name)
            self._toast(f"Deleted preset: {name}")

    # --- Workspace commands ---
    def _collect_workspace_state(self) -> dict:
        return {
            'active_formats': list(self.engine.state.active_formats),
            'layout': self.engine.get_setting('ui.layout', {}),
            'include': list(self.engine.state.include_files),
            'other': list(self.engine.state.other_files),
            'project_path': self.engine.state.project_path,
        }

    def _apply_workspace_state(self, data: dict):
        try:
            from pathlib import Path
            if data.get('project_path'):
                self.engine.load_project(data['project_path'])
            if data.get('active_formats') is not None:
                self.engine.set_active_formats(set(data['active_formats']))
            if data.get('layout') is not None:
                self.engine.set_setting('ui.layout', data['layout'])
                self._restore_layout()
            # apply lists
            inc = set(data.get('include') or [])
            oth = set(data.get('other') or [])
            if inc:
                self.engine.move_files(inc, 'include')
            if oth:
                self.engine.move_files(oth, 'other')
            self.on_files_updated()
        except Exception as e:
            messagebox.showerror('Workspace', f'Failed to apply workspace: {e}')

    def _cmd_workspace_save(self):
        name = tk.simpledialog.askstring('Save Workspace', 'Workspace name:')
        if not name:
            return
        data = self._collect_workspace_state()
        self.engine.config_manager.save_workspace(name, data)
        self._toast(f"Workspace saved: {name}")

    def _cmd_workspace_load(self):
        names = self.engine.config_manager.list_workspaces()
        if not names:
            messagebox.showinfo('Workspaces', 'No workspaces found')
            return
        top = tk.Toplevel(self)
        top.title('Load Workspace')
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        lb = tk.Listbox(frm, height=min(10, max(3, len(names))))
        for n in names:
            lb.insert(tk.END, n)
        lb.pack(fill=tk.BOTH, expand=True)
        def ok():
            sel = lb.curselection()
            if not sel:
                top.destroy(); return
            name = lb.get(sel[0])
            data = self.engine.config_manager.load_workspace(name)
            if data:
                self._apply_workspace_state(data)
                self._toast(f"Workspace loaded: {name}")
            top.destroy()
        theme.create_styled_button(frm, 'Load', command=ok).pack(pady=6)

    def _cmd_workspace_delete(self):
        names = self.engine.config_manager.list_workspaces()
        if not names:
            messagebox.showinfo('Workspaces', 'No workspaces found')
            return
        name = tk.simpledialog.askstring('Delete Workspace', 'Workspace name to delete:', initialvalue=names[0])
        if name and name in names:
            self.engine.config_manager.delete_workspace(name)
            self._toast(f"Workspace deleted: {name}")

    # --- File list preset commands ---
    def _filelist_preset_save(self):
        name = simpledialog.askstring('Save File List Preset', 'Preset name:')
        if not name:
            return
        include = list(self.engine.state.include_files)
        other = list(self.engine.state.other_files)
        self.engine.config_manager.save_filelist_preset(name, include, other)
        names = self.engine.config_manager.list_filelist_presets()
        self.filelist_preset_combo['values'] = names
        self._toast(f"File list preset saved: {name}")

    def _filelist_preset_load(self):
        name = self.filelist_preset_var.get().strip()
        if not name:
            return
        data = self.engine.config_manager.load_filelist_preset(name)
        if not data:
            return
        inc = set(data.get('include') or [])
        oth = set(data.get('other') or [])
        # Replace mode: clear then apply
        self.engine.state.include_files.clear()
        self.engine.state.other_files.clear()
        if inc:
            self.engine.move_files(inc, 'include')
        if oth:
            self.engine.move_files(oth, 'other')
        self.on_files_updated()
        self._toast(f"File list preset loaded: {name}")

    def _filelist_preset_delete(self):
        name = self.filelist_preset_var.get().strip()
        if not name:
            return
        self.engine.config_manager.delete_filelist_preset(name)
        names = self.engine.config_manager.list_filelist_presets()
        self.filelist_preset_combo['values'] = names
        self._toast(f"File list preset deleted: {name}")

    # --- Bundle commands ---
    def _cmd_bundle_export(self):
        path = filedialog.asksaveasfilename(title='Export Bundle', defaultextension='.json', filetypes=[('JSON','*.json')])
        if not path:
            return
        layout = self.engine.get_setting('ui.layout', {}) or {}
        active = list(self.engine.state.active_formats or [])
        self.engine.config_manager.export_bundle(path, layout, active)
        self._toast('Bundle exported')

    def _cmd_bundle_import(self):
        path = filedialog.askopenfilename(title='Import Bundle', filetypes=[('JSON','*.json'), ('All','*.*')])
        if not path:
            return
        data = self.engine.config_manager.import_bundle(path)
        if data.get('active_formats'):
            self.engine.set_active_formats(set(data['active_formats']))
        if data.get('layout'):
            self.engine.set_setting('ui.layout', data['layout'])
            self._restore_layout()
        # refresh preset names after import
        try:
            self.format_selector.set_preset_names(self.engine.config_manager.get_format_preset_names())
        except Exception:
            pass
        self.on_files_updated()
        self._toast('Bundle imported')
    
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

    # --- Watch mode ---
    def _cmd_watch_toggle(self):
        if self._watch_job:
            try:
                self.after_cancel(self._watch_job)
            except Exception:
                pass
            self._watch_job = None
            self._toast('Watch: off')
        else:
            self._schedule_watch()
            self._toast('Watch: on')

    def _schedule_watch(self):
        try:
            interval_ms = int(self.engine.get_setting('ui.refresh_interval', 5000))
        except Exception:
            interval_ms = 5000
        def tick():
            try:
                if self.engine.state.project_path:
                    self.engine.load_project(self.engine.state.project_path)
            finally:
                self._watch_job = self.after(interval_ms, tick)
        self._watch_job = self.after(interval_ms, tick)
    
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
        def open_logs():
            import os, subprocess
            log_path = os.path.abspath('logs/app.log')
            os.makedirs('logs', exist_ok=True)
            if not os.path.exists(log_path):
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write('')
            if os.name == 'nt':
                subprocess.Popen(['notepad.exe', log_path])
            else:
                subprocess.Popen(['xdg-open', log_path])
        top = tk.Toplevel(self)
        top.title('Help')
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text='Documentation: docs/USER_GUIDE.md').pack(anchor=tk.W)
        btns = theme.create_styled_frame(frm)
        btns.pack(fill=tk.X, pady=(8,0))
        theme.create_styled_button(btns, 'Open Logs', command=open_logs).pack(side=tk.RIGHT)
        theme.create_styled_button(btns, 'Reset layout', command=self.reset_layout).pack(side=tk.RIGHT, padx=(0,8))

    def _open_logs_viewer(self):
        top = tk.Toplevel(self)
        top.title('Application Logs')
        top.geometry(f"800x500+{self.winfo_rootx()+60}+{self.winfo_rooty()+100}")
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        # Toolbar
        tbar = theme.create_styled_frame(frm)
        tbar.pack(fill=tk.X)
        search_var = tk.StringVar()
        ttk.Entry(tbar, textvariable=search_var, width=30).pack(side=tk.LEFT)
        def do_copy():
            txt.event_generate('<<Copy>>')
        def do_refresh():
            from codexify.utils.logger import get_in_memory_logs
            content = get_in_memory_logs()
            txt.configure(state='normal')
            txt.delete('1.0', tk.END)
            if search_var.get().strip():
                needle = search_var.get().lower()
                for line in content.splitlines(True):
                    if needle in line.lower():
                        txt.insert(tk.END, line, 'match')
                    else:
                        txt.insert(tk.END, line)
            else:
                txt.insert(tk.END, content)
            txt.configure(state='disabled')
        theme.create_styled_button(tbar, 'Refresh', command=do_refresh).pack(side=tk.LEFT, padx=(6,0))
        theme.create_styled_button(tbar, 'Copy', command=do_copy).pack(side=tk.LEFT, padx=(6,0))
        # Text area
        txt = tk.Text(frm, wrap='none')
        txt.pack(fill=tk.BOTH, expand=True, pady=(6,0))
        txt.tag_configure('match', background='#fff59d')
        # Scrollers
        xscroll = ttk.Scrollbar(frm, orient='horizontal', command=txt.xview)
        xscroll.pack(fill=tk.X)
        txt.configure(xscrollcommand=xscroll.set)
        # initial load
        do_refresh()

    # Saved filters handlers
    def _refresh_saved_filters_ui(self):
        inc_names = [it.get('name') for it in self.engine.config_manager.get_saved_filters('include')]
        oth_names = [it.get('name') for it in self.engine.config_manager.get_saved_filters('other')]
        self.include_list.set_saved_filters(inc_names)
        self.other_list.set_saved_filters(oth_names)

    def _save_filter(self, list_id: str, name: str, search: str, ext: str, min_kb: str):
        self.engine.config_manager.save_filter(list_id, name, search, ext, min_kb)
        self._refresh_saved_filters_ui()

    def _delete_filter(self, list_id: str, name: str):
        self.engine.config_manager.delete_filter(list_id, name)
        self._refresh_saved_filters_ui()

    def _apply_filter(self, list_id: str, name: str):
        items = self.engine.config_manager.get_saved_filters(list_id)
        for it in items:
            if it.get('name') == name:
                target = self.include_list if list_id=='include' else self.other_list
                target.search_var.set(it.get('search',''))
                target.type_filter_var.set(it.get('ext',''))
                target.size_min_var.set(it.get('min_kb',''))
                target._apply_filters()
                break
    
    def cancel_operation(self):
        """Cancel the current operation."""
        self.progress_widget.hide()
        self.status_bar.set_status("Operation cancelled", "warning")
    
    # --- Event Handlers ---
    
    def on_formats_changed(self, formats):
        """Handle format selection changes."""
        # Normalize to lowercase extensions
        norm = {f.lower() for f in formats if f}
        self.engine.set_active_formats(norm)
        # Mirror back to selector to keep Active list in sync (if external changes)
        try:
            self.format_selector.set_formats(sorted(list(norm)))
        except Exception:
            pass
    
    def on_include_file_selected(self, files):
        """Handle include file selection."""
        if files:
            self.status_bar.set_status(f"Selected {len(files)} file(s) in include list", "info")
    
    def on_other_file_selected(self, files):
        """Handle other file selection."""
        if files:
            self.status_bar.set_status(f"Selected {len(files)} file(s) in other list", "info")

    def _on_list_selection(self, list_id: str, files):
        if list_id == 'include':
            self.on_include_file_selected(files)
        else:
            self.on_other_file_selected(files)
        self._update_preview(files)

    def _update_preview(self, files):
        try:
            path = files[0] if files else None
            self.preview_text.configure(state='normal')
            self.preview_text.delete('1.0', tk.END)
            if not path:
                self.preview_text.configure(state='disabled')
                return
            import os
            header = f"{path}\n" + ("-"*40) + "\n"
            self.preview_text.insert('1.0', header)
            # Try to show small snippet
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        snippet = f.read(20000)
                        self.preview_text.insert(tk.END, snippet)
                except Exception as e:
                    self.preview_text.insert(tk.END, f"[Preview error: {e}]")
            self.preview_text.configure(state='disabled')
        except Exception:
            try:
                self.preview_text.configure(state='disabled')
            except Exception:
                pass
    
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
