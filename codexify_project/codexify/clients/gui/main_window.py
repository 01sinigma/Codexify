"""
Modern Codexify GUI with enhanced UI/UX.
Uses the new widget system and modern styling.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser, tempfile, os
import json
import re
from codexify.utils.logger import get_logger
try:
    from tkinterdnd2 import TkinterDnD  # type: ignore
    _DND_AVAILABLE = True
except Exception:
    _DND_AVAILABLE = False
from codexify.engine import CodexifyEngine
from codexify.utils.llm import LLMProvider
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
        # Localization (basic RU/EN)
        try:
            self.lang = (self.engine.get_setting('app.language', 'en') or 'en')
        except Exception:
            self.lang = 'en'
        self._i18n = {
            'en': {
                'Copy': 'Copy',
                'Open HTML': 'Open HTML',
                'Nodes': 'Nodes',
                'Legend': 'Legend',
                'Select in list': 'Select in list',
                'Map Settings': 'Map Settings',
                'Apply': 'Apply',
                'Include classes': 'Include classes',
                'Include functions': 'Include functions',
                'Include imports': 'Include imports',
                'Min hot score (0..1):': 'Min hot score (0..1):'
            },
            'ru': {
                'Copy': 'Копировать',
                'Open HTML': 'Открыть HTML',
                'Nodes': 'Узлы',
                'Legend': 'Легенда',
                'Select in list': 'Выбрать в списке',
                'Map Settings': 'Настройки карты',
                'Apply': 'Применить',
                'Include classes': 'Включать классы',
                'Include functions': 'Включать функции',
                'Include imports': 'Включать импорты',
                'Min hot score (0..1):': 'Мин. hot‑оценка (0..1):'
            }
        }
        self._ = lambda k: self._i18n.get(self.lang, {}).get(k, k)
        # Bind hotkeys to this root
        try:
            self.engine.set_root_widget(self)
        except Exception:
            pass
        
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
        
        self.log = get_logger('gui')
    
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
        theme.create_styled_button(analysis_frame, "Analysis Settings", command=self._open_analysis_settings).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        theme.create_styled_button(analysis_frame, "View Analysis", command=self._show_analysis_results).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        theme.create_styled_button(analysis_frame, "View Hot Files", command=self._show_hot_files).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        theme.create_styled_button(analysis_frame, "Analysis Filters", command=self._open_analysis_filters).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        
        duplicates_btn = theme.create_styled_button(analysis_frame, "🔍 Find Duplicates", 
                                                  command=self.find_duplicates)
        duplicates_btn.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        theme.create_styled_button(analysis_frame, "Duplicates Settings", command=self._open_duplicates_settings).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        theme.create_styled_button(analysis_frame, "View Duplicates", command=self._show_duplicates_results).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        theme.create_styled_button(analysis_frame, "AI Refactor Plan", command=self._ai_refactor_plan).pack(fill=tk.X, padx=theme.SPACING['sm'], pady=(0, theme.SPACING['xs']))
        
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

        # AI Tools
        ai_frame = theme.create_styled_labelframe(right_panel, "AI Tools")
        ai_btns = theme.create_styled_frame(ai_frame)
        ai_btns.pack(fill=tk.X, padx=theme.SPACING['sm'], pady=theme.SPACING['xs'])
        # Controls row (detail + include modules)
        ctrl = theme.create_styled_frame(ai_btns)
        ctrl.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        ttk.Label(ctrl, text='Detail:').pack(side=tk.LEFT)
        self.ai_detail_var = tk.StringVar(value='normal')
        ttk.Combobox(ctrl, textvariable=self.ai_detail_var, values=['short','normal','deep'], width=8, state='readonly').pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['sm']))
        self.ai_include_modules_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text='Include modules list', variable=self.ai_include_modules_var).pack(side=tk.LEFT)
        # Action buttons
        theme.create_styled_button(ai_btns, 'Explain Project (AI)', command=self._ai_explain_project).pack(fill=tk.X)
        theme.create_styled_button(ai_btns, 'Generate Import Map (Mermaid)', command=self._ai_generate_map).pack(fill=tk.X, pady=(6,0))
        theme.create_styled_button(ai_btns, 'Generate Full Code Map (Mermaid)', command=self._generate_full_code_map).pack(fill=tk.X, pady=(6,0))
        theme.create_styled_button(ai_btns, 'Map Settings', command=self._open_map_settings).pack(fill=tk.X, pady=(6,0))
        theme.create_styled_button(ai_btns, 'Annotate Map (AI)', command=self._ai_annotate_map).pack(fill=tk.X, pady=(6,0))
        theme.create_styled_button(ai_btns, 'Open LLM Settings', command=self.show_llm_settings).pack(fill=tk.X, pady=(6,0))
        ai_frame.pack(fill=tk.X)
        
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
        if not messagebox.askyesno('Reset layout', 'Reset the layout to defaults?'):
            return
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
        # AI toolbar actions
        try:
            self.toolbar.set_ai_actions(self._ai_explain_project, self._generate_full_code_map, self.show_llm_settings)
        except Exception:
            pass
        
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
        self._toast(f"Moved {len(files)} file(s) → {to_list}", kind='success')
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
            if not messagebox.askyesno('Remove', f'Remove {len(files)} file(s) from lists?'):
                return None
            self.engine.remove_files(set(files))
            self._toast(f"Removed {len(files)} file(s)", kind='warning')
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

    def _toast(self, text: str, kind: str = 'info'):
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        x = self.winfo_rootx() + self.winfo_width() - 220
        y = self.winfo_rooty() + self.winfo_height() - 80
        top.geometry(f"200x40+{x}+{y}")
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True)
        # Color by kind
        colors = {
            'info': '#e3f2fd',
            'success': '#e8f5e9',
            'warning': '#fffde7',
            'error': '#ffebee'
        }
        try:
            bg = colors.get(kind, colors['info'])
            frm.configure(background=bg)
        except Exception:
            pass
        lbl = ttk.Label(frm, text=text)
        lbl.pack(expand=True)
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
            ('AI: Explain Project', self._ai_explain_project),
            ('AI: Generate Import Map', self._ai_generate_map),
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
        try:
            self.log.info('UI: select_project_folder')
        except Exception:
            pass
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            self.engine.load_project(path)
    
    def refresh_project(self):
        """Refresh the current project."""
        try:
            self.log.info('UI: refresh_project')
        except Exception:
            pass
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

    # --- AI Tools ---
    def _ai_explain_project(self):
        try:
            self.log.info('UI: AI explain project')
        except Exception:
            pass
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning('AI', 'No project loaded.')
            return
        # Safe mode: send only metadata
        files = list(self.engine.state.include_files or self.engine.state.all_discovered_files)
        # Build brief metadata
        from pathlib import Path
        exts = {}
        for p in files[:500]:  # cap
            e = Path(p).suffix.lower()
            exts[e] = exts.get(e, 0) + 1
        detail = self.ai_detail_var.get() if hasattr(self, 'ai_detail_var') else 'normal'
        include_mods = self.ai_include_modules_var.get() if hasattr(self, 'ai_include_modules_var') else False
        prompt = (
            'You are a senior software architect. Given project metadata (file extensions and counts), '
            f'explain the likely architecture with {"5-7" if detail=="short" else ("8-12" if detail=="normal" else "12-16")} bullet points.\n'
            f'{"Also list prominent modules." if include_mods else ""}\n\n'
            f'Extensions: {json.dumps(exts, ensure_ascii=False)}\n'
            f'Top files: {json.dumps(files[:20], ensure_ascii=False)}'
        )
        self._run_ai_task(prompt, 'Be concise and technical.', 'AI Project Explanation')

    def _ai_generate_map(self):
        self.log.info('Generate simple import map (AI)')
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning('AI', 'No project loaded.')
            return
        # Build simple import map (Python only as heuristic)
        graph = []
        try:
            import ast, os
            for p in list(self.engine.state.all_discovered_files)[:800]:
                if p.endswith('.py') and os.path.exists(p):
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            tree = ast.parse(f.read(), filename=p)
                        mod = os.path.splitext(os.path.basename(p))[0]
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for a in node.names:
                                    graph.append((mod, a.name.split('.')[0]))
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    graph.append((mod, node.module.split('.')[0]))
                    except Exception:
                        continue
        except Exception:
            pass
        # Also build simple per-module function call graph (Python)
        try:
            import ast, os
            func_graph = []
            for p in list(self.engine.state.all_discovered_files)[:400]:
                if p.endswith('.py') and os.path.exists(p):
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            tree = ast.parse(f.read(), filename=p)
                        mod = os.path.splitext(os.path.basename(p))[0]
                        # collect local function names
                        funcs = set()
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                funcs.add(node.name)
                        # find calls to local functions
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                fn = None
                                if isinstance(node.func, ast.Name):
                                    fn = node.func.id
                                elif isinstance(node.func, ast.Attribute):
                                    fn = node.func.attr
                                if fn and fn in funcs:
                                    func_graph.append((f'{mod}', f'{mod}_{fn}'))
                    except Exception:
                        continue
        except Exception:
            func_graph = []
        # Render Mermaid (modules + calls)
        def _sid(s: str) -> str:
            return re.sub(r'[^a-zA-Z0-9_]', '_', s)
        lines = ['graph TD']
        for a,b in graph[:2000]:
            lines.append(f'	{_sid(a)} --> {_sid(b)}')
        for a,b in func_graph[:2000]:
            lines.append(f'	{_sid(a)} --> {_sid(b)}')
        if len(lines) == 1:
            lines.append('	Empty[No graph data]')
        mermaid = "\n".join(lines)
        self._last_mermaid = mermaid
        self._show_text_modal('Import Map (Mermaid)', mermaid, mermaid=True)

    def _ai_annotate_map(self):
        try:
            self.log.info('UI: AI annotate map')
        except Exception:
            pass
        if not hasattr(self, '_last_mermaid'):
            messagebox.showinfo('AI', 'Generate the map first.')
            return
        prompt = (
            'You will receive a Mermaid graph (graph TD). Add short annotations (<=10 words) per important node '
            'and a concise legend (5-7 bullets) explaining subsystems. Return only plain text: first a list of '
            '"node: note" lines, then a blank line, then "Legend:" with bullets.\n\n'
            f'{self._last_mermaid[:12000]}'
        )
        self._run_ai_task(prompt, 'Be concise and technical.', 'AI Map Annotations')

    def _show_text_modal(self, title: str, text: str, mermaid: bool = False, nodes_map: dict = None, legend_text: str = None):
        top = tk.Toplevel(self)
        top.title(title)
        # square geometry near the main window
        try:
            side = min(int(self.winfo_screenheight()*0.8), int(self.winfo_screenwidth()*0.8))
            x = self.winfo_rootx()+80
            y = self.winfo_rooty()+80
            top.geometry(f"{side}x{side}+{x}+{y}")
        except Exception:
            top.geometry(f"900x900+{self.winfo_rootx()+80}+{self.winfo_rooty()+80}")
        frm = theme.create_styled_frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        # toolbar
        tbar = theme.create_styled_frame(frm)
        tbar.pack(fill=tk.X)
        def do_copy():
            try:
                self.clipboard_clear()
                self.clipboard_append(text)
                self._toast('Copied')
            except Exception:
                pass
        theme.create_styled_button(tbar, self._('Copy'), command=do_copy).pack(side=tk.RIGHT)
        if mermaid:
            theme.create_styled_button(tbar, self._('Open HTML'), command=lambda: self._open_mermaid_html(text, nodes_map or {})).pack(side=tk.RIGHT, padx=(6,0))
        body = theme.create_styled_frame(frm)
        body.pack(fill=tk.BOTH, expand=True)
        # Left text
        txt = tk.Text(body, wrap='word')
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert('1.0', text)
        txt.configure(state='disabled')
        # Optional nodes list for navigation
        if nodes_map:
            side = theme.create_styled_frame(body)
            side.pack(side=tk.RIGHT, fill=tk.Y, padx=(8,0))
            ttk.Label(side, text=self._('Nodes')).pack(anchor=tk.W)
            # search
            search_var = tk.StringVar()
            ent = ttk.Entry(side, textvariable=search_var, width=18)
            ent.pack(fill=tk.X, pady=(0,4))
            lb = tk.Listbox(side, height=12)
            items = sorted(nodes_map.keys())
            def refresh_list(*_):
                q = (search_var.get() or '').lower()
                lb.delete(0, tk.END)
                for k in items:
                    if not q or q in k.lower():
                        lb.insert(tk.END, k)
            refresh_list()
            search_var.trace_add('write', refresh_list)
            lb.pack(fill=tk.Y)
            def select_node():
                sel = lb.curselection()
                if not sel:
                    return
                key = lb.get(sel[0])
                path = nodes_map.get(key)
                if path:
                    if path in self.engine.state.include_files:
                        self.include_list.select_file(path)
                    elif path in self.engine.state.other_files:
                        self.other_list.select_file(path)
            theme.create_styled_button(side, self._('Select in list'), command=select_node).pack(fill=tk.X, pady=(6,0))
            if legend_text:
                ttk.Label(side, text=self._('Legend')).pack(anchor=tk.W, pady=(8,0))
                leg = tk.Text(side, height=6, wrap='word')
                leg.pack(fill=tk.X)
                leg.insert('1.0', legend_text)
                leg.configure(state='disabled')

    def _open_mermaid_html(self, mermaid_text: str, node_to_path: dict | None = None):
        # Create temporary HTML with Mermaid CDN
        try:
            mapping_json = json.dumps(node_to_path or {}, ensure_ascii=False)
        except Exception:
            mapping_json = '{}'
        html = ("<!DOCTYPE html>\n"
"<html>\n"
"<head>\n"
"  <meta charset='utf-8'/>\n"
"  <meta name='viewport' content='width=device-width, initial-scale=1'/>\n"
"  <title>Codexify Mermaid Preview</title>\n"
"  <script src='https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js'></script>\n"
"  <style>\n"
"    body{margin:0;padding:12px;font-family:Segoe UI,Arial,sans-serif;background:#fafafa;}\n"
"    .toolbar{display:flex;gap:8px;justify-content:flex-end;margin-bottom:8px;}\n"
"    #view{position:relative; width:100%; height:calc(100vh - 60px); background:#fff; border:1px solid #ddd; overflow:hidden;}\n"
"    #view svg{user-select:none; cursor:grab;}\n"
"    .hint{position:fixed;left:16px;bottom:16px;background:#fff;border:1px solid #ccc;border-radius:6px;padding:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);max-width:70%;display:none;}\n"
"    .hint strong{display:block;margin-bottom:6px;}\n"
"    .hint button{margin-right:8px;}\n"
"  </style>\n"
"  <script>\n"
"    const NODE_TO_PATH = " + (mapping_json) + ";\n"
"    mermaid.initialize({startOnLoad:true, securityLevel:'loose'});\n"
"    let vb0 = null;\n"
"    function getSvg(){ return document.querySelector('#view svg'); }\n"
"    function ensureViewBox(svg){\n"
"      if(!svg) return;\n"
"      if(!svg.getAttribute('viewBox')){\n"
"        const bb = svg.getBBox();\n"
"        svg.setAttribute('viewBox', bb.x + ' ' + bb.y + ' ' + bb.width + ' ' + bb.height);\n"
"      }\n"
"      if(!vb0){ vb0 = (svg.getAttribute('viewBox')||'0 0 100 100').split(' ').map(Number); }\n"
"    }\n"
"    function setViewBox(svg, x,y,w,h){ svg.setAttribute('viewBox', x+' '+y+' '+w+' '+h); }\n"
"    function currentVB(svg){ return (svg.getAttribute('viewBox')||'0 0 100 100').split(' ').map(Number); }\n"
"    function zoomAt(svg, factor, cx, cy){\n"
"      ensureViewBox(svg);\n"
"      let vb = currentVB(svg); let x=vb[0], y=vb[1], w=vb[2], h=vb[3];\n"
"      const mx = x + w * cx/svg.clientWidth;\n"
"      const my = y + h * cy/svg.clientHeight;\n"
"      const nw = w * factor; const nh = h * factor;\n"
"      const nx = mx - (mx - x) * (nw/w);\n"
"      const ny = my - (my - y) * (nh/h);\n"
"      setViewBox(svg, nx, ny, nw, nh);\n"
"    }\n"
"    function zoomIn(){ const s=getSvg(); if(s) zoomAt(s, 0.8, s.clientWidth/2, s.clientHeight/2); }\n"
"    function zoomOut(){ const s=getSvg(); if(s) zoomAt(s, 1.25, s.clientWidth/2, s.clientHeight/2); }\n"
"    function fitToContent(){ const s=getSvg(); if(!s) return; const bb=s.getBBox(); setViewBox(s, bb.x-10, bb.y-10, bb.width+20, bb.height+20); }\n"
"    function resetView(){ const s=getSvg(); if(!s||!vb0) return; setViewBox(s, vb0[0], vb0[1], vb0[2], vb0[3]); }\n"
"    function attachHandlers(){\n"
"      const svg = getSvg(); if(!svg) return; ensureViewBox(svg);\n"
"      svg.addEventListener('click', (e)=>{\n"
"        let g = e.target; while(g && g.tagName !== 'g') g = g.parentElement; if(!g) return;\n"
"        const id = g.id || (g.querySelector('[id]') && g.querySelector('[id]').id) || '';\n"
"        if(!id) return; const p = NODE_TO_PATH[id] || ''; const hint = document.getElementById('hint');\n"
"        if(p){ document.getElementById('hintPath').textContent = p; document.getElementById('openLink').href = 'file:///' + p.replace(/\\\\/g,'/'); hint.style.display = 'block'; }\n"
"        else { document.getElementById('hintPath').textContent = id; document.getElementById('openLink').removeAttribute('href'); hint.style.display = 'block'; }\n"
"      });\n"
"      svg.addEventListener('wheel', (e)=>{ e.preventDefault(); const k = e.deltaY < 0 ? 0.9 : 1.1; zoomAt(svg, k, e.offsetX, e.offsetY); }, {passive:false});\n"
"      let dragging=false, px=0, py=0; svg.addEventListener('mousedown',(e)=>{ dragging=true; px=e.clientX; py=e.clientY; svg.style.cursor='grabbing'; });\n"
"      window.addEventListener('mouseup',()=>{ dragging=false; if(svg) svg.style.cursor='grab'; });\n"
"      window.addEventListener('mousemove',(e)=>{ if(!dragging) return; const vb=currentVB(svg); const x=vb[0], y=vb[1], w=vb[2], h=vb[3]; const dx = (e.clientX-px)*w/svg.clientWidth; const dy=(e.clientY-py)*h/svg.clientHeight; setViewBox(svg, x-dx, y-dy, w, h); px=e.clientX; py=e.clientY; });\n"
"    }\n"
"    function exportPng(){\n"
"      const svg = getSvg(); if(!svg) return alert('SVG not ready');\n"
"      const serializer = new XMLSerializer(); const svgStr = serializer.serializeToString(svg);\n"
"      const blob = new Blob([svgStr], {type: 'image/svg+xml;charset=utf-8'});\n"
"      const url = URL.createObjectURL(blob); const img = new Image();\n"
"      img.onload = function(){ const canvas = document.createElement('canvas'); const bb = svg.getBBox();\n"
"        canvas.width = Math.ceil(bb.width+40); canvas.height = Math.ceil(bb.height+40);\n"
"        const ctx = canvas.getContext('2d'); ctx.fillStyle='#ffffff'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.drawImage(img, 20, 20);\n"
"        const a = document.createElement('a'); a.download='code_map.png'; a.href=canvas.toDataURL('image/png'); a.click(); URL.revokeObjectURL(url); };\n"
"      img.onerror = function(){ URL.revokeObjectURL(url); alert('Export failed'); };\n"
"      img.src = url;\n"
"    }\n"
"    function copyPath(){ const t = document.getElementById('hintPath').textContent; if(!t) return; if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(t); } else { const ta=document.createElement('textarea'); ta.value=t; document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta);} }\n"
"    document.addEventListener('DOMContentLoaded', ()=>{ setTimeout(()=>{ attachHandlers(); }, 400); });\n"
"  </script>\n"
"  </head>\n"
"<body>\n"
"<div class='toolbar'>\n"
"  <button onclick='zoomIn()'>Zoom In</button>\n"
"  <button onclick='zoomOut()'>Zoom Out</button>\n"
"  <button onclick='fitToContent()'>Fit</button>\n"
"  <button onclick='resetView()'>Reset</button>\n"
"  <button onclick='exportPng()'>Export PNG</button>\n"
"</div>\n"
"<div id='view'>\n"
"  <div class='mermaid'>\n" + mermaid_text + "\n"
"  </div>\n"
"</div>\n"
"<div class='hint' id='hint'>\n"
"  <strong>Node</strong>\n"
"  <div id='hintPath' style='word-wrap:anywhere'></div>\n"
"  <div style='margin-top:8px;'>\n"
"    <button onclick='copyPath()'>Copy Path</button>\n"
"    <a id='openLink' href='#' target='_blank'><button>Open</button></a>\n"
"  </div>\n"
"</div>\n"
"</body>\n"
"</html>")
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html)
                path = f.name
            self.log.info('Opening Mermaid HTML preview')
            webbrowser.open('file://' + os.path.abspath(path))
        except Exception as e:
            messagebox.showerror('Mermaid', f'Failed to open HTML: {e}')

    def _generate_full_code_map(self):
        if not hasattr(self, '_last_analysis'):
            # trigger analysis if not present
            if not self.engine.state.all_discovered_files:
                messagebox.showwarning('Map', 'No project loaded.')
                return
            self.analyze_project()
            return
        data = self._last_analysis
        symbols = data.get('symbols', {}).get('python', {}).get('modules', {})
        import_edges = (data.get('import_graph') or {}).get('edges', [])
        hot_list = (data.get('hot_files') or [])
        hot = {os.path.splitext(os.path.basename(h.get('path','')))[0] for h in hot_list}
        # Fallback: if no Python symbols/imports, build a simple file-based map (handles JS too)
        if not symbols and not import_edges:
            try:
                proj = self.engine.state.project_path or ''
                files = list(self.engine.state.include_files or self.engine.state.all_discovered_files)
                files = [p for p in files if os.path.exists(p)]
                def _sid(s: str) -> str:
                    return re.sub(r'[^a-zA-Z0-9_]', '_', s)
                lines = [
                    'graph TD',
                    'classDef module fill:#e3f2fd,stroke:#1e88e5,stroke-width:1px;',
                    'classDef file fill:#eef7ff,stroke:#64b5f6,stroke-width:1px;'
                ]
                node_to_path = {}
                # Directory nodes (top-level under project)
                dir_ids = {}
                for p in files[:2000]:
                    rel = os.path.relpath(p, proj) if proj and os.path.commonprefix([proj, p]) else os.path.basename(os.path.dirname(p)) + '/' + os.path.basename(p)
                    parts = rel.split(os.sep)
                    top = parts[0] if parts else os.path.basename(os.path.dirname(p))
                    dir_id = dir_ids.get(top)
                    if not dir_id:
                        dir_id = _sid(f'dir_{top}')
                        dir_ids[top] = dir_id
                        node_to_path[dir_id] = os.path.join(proj, top) if proj else os.path.dirname(p)
                        lines.append(f'{dir_id}[{top}]')
                        lines.append(f'class {dir_id} module')
                    file_id = _sid(f'file_{rel.replace(os.sep,"_")}')
                    node_to_path[file_id] = p
                    lines.append(f'{file_id}[{os.path.basename(p)}]')
                    lines.append(f'{dir_id} --> {file_id}')
                # JS imports edges (best-effort)
                for p in [f for f in files if f.lower().endswith(('.js','.ts','.jsx','.tsx'))][:800]:
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            txt = f.read()
                        src_id = _sid(f'file_{os.path.relpath(p, proj).replace(os.sep,"_")}') if proj else _sid(f'file_{os.path.basename(p)}')
                        for m in re.findall(r"import\s+[^;]*?from\s+['\"](.+?)['\"]", txt):
                            if m.startswith('.'):
                                tgt = os.path.normpath(os.path.join(os.path.dirname(p), m))
                                for ext in ('','.js','.ts','.jsx','.tsx'):
                                    cand = tgt + ext
                                    if os.path.exists(cand):
                                        tgt = cand; break
                                tgt_id = _sid(f'file_{os.path.relpath(tgt, proj).replace(os.sep,"_")}') if proj and os.path.exists(tgt) else _sid(f'mod_{m}')
                            else:
                                tgt_id = _sid(f'mod_{m.split('/')[-1]}')
                            if tgt_id not in node_to_path:
                                node_to_path[tgt_id] = tgt if 'tgt' in locals() and os.path.exists(tgt) else ''
                                lines.append(f'{tgt_id}[{m}]')
                            lines.append(f'{src_id} -.-> {tgt_id}')
                        for m in re.findall(r"require\(\s*['\"](.+?)['\"]\s*\)", txt):
                            if m.startswith('.'):
                                tgt = os.path.normpath(os.path.join(os.path.dirname(p), m))
                                for ext in ('','.js','.ts','.jsx','.tsx'):
                                    cand = tgt + ext
                                    if os.path.exists(cand):
                                        tgt = cand; break
                                tgt_id = _sid(f'file_{os.path.relpath(tgt, proj).replace(os.sep,"_")}') if proj and os.path.exists(tgt) else _sid(f'mod_{m}')
                            else:
                                tgt_id = _sid(f'mod_{m.split('/')[-1]}')
                            if tgt_id not in node_to_path:
                                node_to_path[tgt_id] = tgt if 'tgt' in locals() and os.path.exists(tgt) else ''
                                lines.append(f'{tgt_id}[{m}]')
                            lines.append(f'{src_id} -.-> {tgt_id}')
                    except Exception:
                        continue
                if len(lines) <= 3:
                    lines.append('Empty[No code map data]')
                mermaid = "\n".join(lines)
                self._last_mermaid = mermaid
                self._show_text_modal('Full Code Map (Mermaid)', mermaid, mermaid=True, nodes_map=node_to_path, legend_text='Files and directories map')
                return
            except Exception as e:
                self.log.error(f'Map fallback failed: {e}')
        # Map options from session overrides
        include_classes = bool(self.engine.get_setting('map.include_classes', True))
        include_functions = bool(self.engine.get_setting('map.include_functions', True))
        include_imports = bool(self.engine.get_setting('map.include_imports', True))
        min_hot = float(self.engine.get_setting('map.min_hot_score', 0.0) or 0.0)
        # build legend text
        legend = (
            'Classes:\n'
            '  module: blue\n  class: purple\n  function: green\n  hot: red overlay\n\n'
            'Edges:\n  solid: contains\n  dotted: import\n  solid module→fn: local call\n'
        )
        lines = [
            'graph TD',
            'classDef module fill:#e3f2fd,stroke:#1e88e5,stroke-width:1px;',
            'classDef class fill:#ede7f6,stroke:#6a1b9a,stroke-width:1px;',
            'classDef func fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;',
            'classDef hot fill:#ffebee,stroke:#c62828,stroke-width:1px;'
        ]
        node_to_path = {}
        # Modules and members
        for mod, meta in symbols.items():
            mod_id = _sid(f'mod_{mod}')
            node_to_path[mod_id] = meta.get('path','')
            lines.append(f'{mod_id}[{mod}]')
            lines.append(f'class {mod_id} module')
            # apply hot overlay if module exceeds threshold
            base = os.path.splitext(os.path.basename(meta.get('path','')))[0]
            # find score by path
            try:
                pth = meta.get('path','')
                score = 0.0
                for hf in hot_list:
                    if hf.get('path') == pth:
                        score = float(hf.get('score', 0.0))
                        break
            except Exception:
                score = 0.0
            if base in hot and score >= min_hot:
                lines.append(f'class {mod_id} hot')
            if include_classes:
                for cls in meta.get('classes', []):
                    cls_id = _sid(f'cls_{mod}_{cls}')
                    node_to_path[cls_id] = meta.get('path','')
                    lines.append(f'{cls_id}[{cls}]')
                    lines.append(f'class {cls_id} class')
                    lines.append(f'{mod_id} --> {cls_id}')
            if include_functions:
                for fn in meta.get('functions', []):
                    fn_id = _sid(f'fn_{mod}_{fn}')
                    node_to_path[fn_id] = meta.get('path','')
                    lines.append(f'{fn_id}[{fn}()]')
                    lines.append(f'class {fn_id} func')
                    lines.append(f'{mod_id} --> {fn_id}')
        # Import edges
        if include_imports:
            for a,b in import_edges[:2000]:
                lines.append(f'{_sid("mod_"+a)} -.-> {_sid("mod_"+b)}')
        # Local function calls (quick pass)
        try:
            import ast
            for mod, meta in symbols.items():
                p = meta.get('path')
                if not p or not os.path.exists(p):
                    continue
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        tree = ast.parse(f.read(), filename=p)
                    funcs = set(meta.get('functions') or []) if include_functions else set()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            fn = None
                            if isinstance(node.func, ast.Name):
                                fn = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                fn = node.func.attr
                            if fn and fn in funcs:
                                lines.append(f'{_sid("mod_"+mod)} --> {_sid("fn_"+mod+"_"+fn)}')
                except Exception:
                    continue
        except Exception:
            pass
        mermaid = "\n".join(lines)
        self._last_mermaid = mermaid
        self._show_text_modal('Full Code Map (Mermaid)', mermaid, mermaid=True, nodes_map=node_to_path, legend_text=legend)
        if len(lines) == 5:
            lines.append('Empty[No code map data]')

    def _open_map_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title(self._('Map Settings'))
        dlg.transient(self)
        dlg.geometry(f"380x200+{self.winfo_rootx()+130}+{self.winfo_rooty()+130}")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        inc_cls = tk.BooleanVar(value=bool(self.engine.get_setting('map.include_classes', True)))
        inc_fn = tk.BooleanVar(value=bool(self.engine.get_setting('map.include_functions', True)))
        inc_imp = tk.BooleanVar(value=bool(self.engine.get_setting('map.include_imports', True)))
        min_hot = tk.StringVar(value=str(self.engine.get_setting('map.min_hot_score', 0.0)))
        ttk.Checkbutton(frm, text=self._('Include classes'), variable=inc_cls).pack(anchor=tk.W)
        ttk.Checkbutton(frm, text=self._('Include functions'), variable=inc_fn).pack(anchor=tk.W)
        ttk.Checkbutton(frm, text=self._('Include imports'), variable=inc_imp).pack(anchor=tk.W)
        ttk.Label(frm, text=self._('Min hot score (0..1):')).pack(anchor=tk.W, pady=(6,0))
        ttk.Entry(frm, textvariable=min_hot, width=10).pack(anchor=tk.W)
        def apply():
            self.engine.config_manager.set_session_override('map.include_classes', bool(inc_cls.get()))
            self.engine.config_manager.set_session_override('map.include_functions', bool(inc_fn.get()))
            self.engine.config_manager.set_session_override('map.include_imports', bool(inc_imp.get()))
            try:
                self.engine.config_manager.set_session_override('map.min_hot_score', float(min_hot.get()))
            except Exception:
                pass
            self._toast('Map settings applied')
            dlg.destroy()
        theme.create_styled_button(frm, self._('Apply'), command=apply).pack(anchor=tk.E, pady=(8,0))
    
    def analyze_project(self):
        """Trigger project analysis."""
        try:
            self.log.info('UI: analyze_project')
        except Exception:
            pass
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning("Warning", "No project loaded. Please load a project first.")
            return
        
        # re-apply analysis settings from in-memory overrides
        try:
            self.engine._apply_configuration()
        except Exception:
            pass
        self.progress_widget.show("Analyzing project...", indeterminate=True)
        self.status_bar.set_status("Analyzing project...", "info")
        self.engine.get_analytics()
    
    def find_duplicates(self):
        """Trigger duplicate detection."""
        try:
            self.log.info('UI: find_duplicates')
        except Exception:
            pass
        if not self.engine.state.all_discovered_files:
            messagebox.showwarning("Warning", "No project loaded. Please load a project first.")
            return
        
        self.progress_widget.show("Finding duplicates...", indeterminate=True)
        self.status_bar.set_status("Finding duplicates...", "info")
        # read methods from overrides (comma-separated or list)
        methods = self.engine.get_setting('analysis.methods', None)
        if isinstance(methods, str):
            methods = [m.strip() for m in methods.split(',') if m.strip()]
        self.engine.find_duplicates(methods)

    # --- Analysis/Duplicates settings dialogs ---
    def _open_analysis_settings(self):
        try:
            self.log.info('UI: open_analysis_settings')
        except Exception:
            pass
        dlg = tk.Toplevel(self)
        dlg.title('Analysis Settings')
        dlg.transient(self)
        dlg.geometry(f"420x260+{self.winfo_rootx()+100}+{self.winfo_rooty()+100}")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text='Min block size:').pack(anchor=tk.W)
        min_var = tk.StringVar(value=str(self.engine.get_setting('analysis.min_block_size', 3)))
        ttk.Entry(frm, textvariable=min_var, width=10).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(frm, text='Similarity threshold (0..1):').pack(anchor=tk.W)
        thr_var = tk.StringVar(value=str(self.engine.get_setting('analysis.similarity_threshold', 0.8)))
        ttk.Entry(frm, textvariable=thr_var, width=10).pack(anchor=tk.W, pady=(0,6))
        def apply():
            try:
                self.engine.config_manager.set_session_override('analysis.min_block_size', int(min_var.get()))
            except Exception:
                pass
            try:
                self.engine.config_manager.set_session_override('analysis.similarity_threshold', float(thr_var.get()))
            except Exception:
                pass
            try:
                self.engine._apply_configuration()
            except Exception:
                pass
            self._toast('Analysis settings applied')
            dlg.destroy()
        theme.create_styled_button(frm, 'Apply', command=apply).pack(anchor=tk.E, pady=(8,0))

    def _open_duplicates_settings(self):
        try:
            self.log.info('UI: open_duplicates_settings')
        except Exception:
            pass
        dlg = tk.Toplevel(self)
        dlg.title('Duplicates Settings')
        dlg.transient(self)
        dlg.geometry(f"420x260+{self.winfo_rootx()+110}+{self.winfo_rooty()+110}")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text='Methods:').pack(anchor=tk.W)
        m_hash = tk.BooleanVar(value=True)
        m_content = tk.BooleanVar(value=True)
        m_similarity = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text='hash', variable=m_hash).pack(anchor=tk.W)
        ttk.Checkbutton(frm, text='content', variable=m_content).pack(anchor=tk.W)
        ttk.Checkbutton(frm, text='similarity', variable=m_similarity).pack(anchor=tk.W)
        ttk.Label(frm, text='Min block size:').pack(anchor=tk.W, pady=(6,0))
        blk_var = tk.StringVar(value=str(self.engine.get_setting('duplicates.min_block_size', 3)))
        ttk.Entry(frm, textvariable=blk_var, width=10).pack(anchor=tk.W)
        ttk.Label(frm, text='Similarity threshold (0..1):').pack(anchor=tk.W, pady=(6,0))
        thr_var = tk.StringVar(value=str(self.engine.get_setting('duplicates.similarity_threshold', 0.8)))
        ttk.Entry(frm, textvariable=thr_var, width=10).pack(anchor=tk.W)
        skip_bin = tk.BooleanVar(value=bool(self.engine.get_setting('duplicates.skip_binary', True)))
        ttk.Checkbutton(frm, text='Skip binary/generated files', variable=skip_bin).pack(anchor=tk.W, pady=(6,0))
        def apply():
            methods = []
            if m_hash.get(): methods.append('hash')
            if m_content.get(): methods.append('content')
            if m_similarity.get(): methods.append('similarity')
            self.engine.config_manager.set_session_override('analysis.methods', ','.join(methods))
            try:
                self.engine.config_manager.set_session_override('duplicates.min_block_size', int(blk_var.get()))
            except Exception:
                pass
            try:
                self.engine.config_manager.set_session_override('duplicates.similarity_threshold', float(thr_var.get()))
            except Exception:
                pass
            self.engine.config_manager.set_session_override('duplicates.skip_binary', bool(skip_bin.get()))
            self._toast('Duplicates settings applied')
            dlg.destroy()
        theme.create_styled_button(frm, 'Apply', command=apply).pack(anchor=tk.E, pady=(8,0))

    def _ai_refactor_plan(self):
        if not hasattr(self, '_last_duplicates'):
            messagebox.showinfo('AI', 'Find Duplicates first.')
            return
        groups = self._last_duplicates.get('groups', []) or self._last_duplicates.get('duplicate_groups', [])
        if not groups:
            messagebox.showinfo('AI', 'No duplicate groups found.')
            return
        # Build compact description of top-N groups
        top = groups[:10]
        compact = []
        for g in top:
            files = g.get('files') if isinstance(g, dict) else g
            compact.append({'count': len(files), 'files': files[:5]})
        import json as _json
        prompt = (
            'You are a senior engineer. Given duplicate groups (file samples), propose a short refactor plan: '
            '1) shared modules to extract, 2) common utilities, 3) steps. 8-12 bullets.\n\n'
            f'{_json.dumps(compact, ensure_ascii=False)}'
        )
        self._run_ai_task(prompt, 'Be concise and actionable.', 'AI Refactor Plan')

    # Generic AI runner (background thread with cancel & progress)
    def _run_ai_task(self, prompt: str, system: str, title: str):
        if getattr(self, '_ai_task_active', False):
            self._toast('AI task already running')
            return
        self._ai_task_active = True
        self._ai_cancelled = False
        self.status_bar.set_status('AI: working...', 'info')
        # wire cancel to cancel flag
        def _cancel():
            self._ai_cancelled = True
            self.progress_widget.hide()
            self.status_bar.set_status('AI: cancelled', 'warning')
        self.progress_widget.set_cancel_callback(_cancel)
        self.progress_widget.show('AI is working...', indeterminate=True)

        import threading
        result_box = {'text': ''}
        def worker():
            try:
                llm = LLMProvider()
                out = llm.summarize(prompt, system)
                result_box['text'] = out
            except Exception as e:
                result_box['text'] = f'[AI error: {e}]'
            finally:
                self.after(0, finish)

        def finish():
            self._ai_task_active = False
            self.progress_widget.hide()
            if not self._ai_cancelled:
                self._show_text_modal(title, result_box.get('text',''))
                self.status_bar.set_status('AI: done', 'success')
        threading.Thread(target=worker, daemon=True).start()
    
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
    
    def show_settings(self, initial_tab: str = 'general'):
        """Show application settings dialog (in-memory).
        initial_tab: 'general' | 'llm' | 'hotkeys'
        """
        try:
            self.log.info(f'UI: show_settings tab={initial_tab}')
        except Exception:
            pass
        dlg = tk.Toplevel(self)
        dlg.title('Settings')
        dlg.transient(self)
        dlg.geometry(f"520x420+{self.winfo_rootx()+80}+{self.winfo_rooty()+80}")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        nb = ttk.Notebook(frm)
        nb.pack(fill=tk.BOTH, expand=True)
        # General tab
        tab_general = theme.create_styled_frame(nb)
        nb.add(tab_general, text='General')
        ttk.Label(tab_general, text='Language (RU/EN):').pack(anchor=tk.W)
        lang_var = tk.StringVar(value=self.engine.get_setting('app.language', 'en'))
        ttk.Combobox(tab_general, textvariable=lang_var, values=['en','ru'], state='readonly', width=10).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(tab_general, text='Default output format:').pack(anchor=tk.W)
        out_var = tk.StringVar(value=self.engine.get_setting('output.default_format', 'md'))
        ttk.Combobox(tab_general, textvariable=out_var, values=['txt','md','html'], state='readonly', width=10).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(tab_general, text='Watch interval (ms):').pack(anchor=tk.W)
        watch_var = tk.StringVar(value=str(self.engine.get_setting('ui.refresh_interval', 5000)))
        ttk.Entry(tab_general, textvariable=watch_var, width=12).pack(anchor=tk.W, pady=(0,6))
        # LLM tab
        tab_llm = theme.create_styled_frame(nb)
        nb.add(tab_llm, text='LLM')
        ttk.Label(tab_llm, text='Provider:').pack(anchor=tk.W)
        prov_var = tk.StringVar(value=self.engine.get_setting('llm.provider', 'none'))
        ttk.Combobox(tab_llm, textvariable=prov_var, values=['none','openai','gemini','custom'], state='readonly', width=12).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(tab_llm, text='API Key (kept in-memory):').pack(anchor=tk.W)
        key_var = tk.StringVar(value=self.engine.get_setting('llm.api_key', ''))
        key_entry = ttk.Entry(tab_llm, textvariable=key_var, show='*')
        key_entry.pack(fill=tk.X, pady=(0,6))
        # Key helpers (paste + show)
        key_tools = theme.create_styled_frame(tab_llm)
        key_tools.pack(fill=tk.X, pady=(0,6))
        def paste_key():
            try:
                val = self.clipboard_get()
                if val:
                    key_var.set(val)
                    key_entry.icursor('end')
            except Exception:
                pass
        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            try:
                key_entry.configure(show='' if show_var.get() else '*')
            except Exception:
                pass
        theme.create_styled_button(key_tools, 'Paste', command=paste_key).pack(side=tk.LEFT)
        ttk.Checkbutton(key_tools, text='Show key', variable=show_var, command=toggle_show).pack(side=tk.LEFT, padx=(8,0))
        ttk.Label(tab_llm, text='Model:').pack(anchor=tk.W)
        model_var = tk.StringVar(value=self.engine.get_setting('llm.model', 'gpt-4o-mini'))
        # Preset models per provider (editable combobox)
        model_presets = {
            'openai': [
                'gpt-4o-mini','gpt-4o','gpt-4.1','gpt-4.1-mini','o3-mini','o4-mini','o4','gpt-4-turbo',
                'gpt-4','gpt-3.5-turbo','gpt-4o-realtime-preview'
            ],
            'gemini': [
                'gemini-1.5-flash','gemini-1.5-flash-8b','gemini-1.5-flash-001','gemini-1.5-pro',
                'gemini-1.5-pro-exp','gemini-1.0-pro','gemini-2.0-flash-exp','gemini-2.5-flash','gemini-2.5-pro'
            ],
            'custom': [],
            'none': []
        }
        model_combo = ttk.Combobox(tab_llm, textvariable=model_var, values=model_presets.get(prov_var.get(), []), state='normal')
        model_combo.pack(fill=tk.X, pady=(0,6))
        def _refresh_models(*_):
            prov = (prov_var.get() or 'none').lower()
            opts = model_presets.get(prov, [])
            try:
                model_combo['values'] = opts
            except Exception:
                pass
            # Set a sensible default if current not in options
            cur = model_var.get() or ''
            if opts and (not cur or cur not in opts):
                model_var.set(opts[0])
            # Try dynamic discovery from provider APIs (if key present)
            try:
                from codexify.utils.llm import LLMProvider
                self.engine.config_manager.set_session_override('llm.provider', prov)
                if key_var.get():
                    self.engine.config_manager.set_session_override('llm.api_key', key_var.get())
                llm = LLMProvider()
                discovered = llm.list_models(prov)
                if discovered:
                    # merge
                    merged = opts + [m for m in discovered if m not in opts]
                    model_combo['values'] = merged
            except Exception:
                pass
        try:
            prov_var.trace_add('write', _refresh_models)
        except Exception:
            pass
        _refresh_models()

        # Optional: models catalog with notes
        catalog = [
            ('openai','gpt-4o-mini','~128k','pricing: see OpenAI pricing page'),
            ('openai','gpt-4o','~128k','pricing: see OpenAI pricing page'),
            ('openai','o3-mini','~200k','pricing: see OpenAI pricing page'),
            ('gemini','gemini-1.5-flash','~1M','pricing: see Google AI pricing'),
            ('gemini','gemini-1.5-flash-8b','~1M','pricing: see Google AI pricing'),
            ('gemini','gemini-1.5-pro','~2M','pricing: see Google AI pricing'),
        ]
        cat_frame = theme.create_styled_frame(tab_llm)
        cat_frame.pack(fill=tk.BOTH, expand=False, pady=(4,6))
        ttk.Label(cat_frame, text='Models catalog (context/pricing)').pack(anchor=tk.W)
        tv = ttk.Treeview(cat_frame, columns=('prov','model','ctx','price'), show='headings', height=6)
        tv.heading('prov', text='Provider'); tv.column('prov', width=80)
        tv.heading('model', text='Model'); tv.column('model', width=160)
        tv.heading('ctx', text='Context'); tv.column('ctx', width=80, anchor='e')
        tv.heading('price', text='Pricing'); tv.column('price', width=220)
        for row in catalog:
            tv.insert('', 'end', values=row)
        tv.pack(fill=tk.X)
        ttk.Label(tab_llm, text='Temperature:').pack(anchor=tk.W)
        temp_var = tk.StringVar(value=str(self.engine.get_setting('llm.temperature', 0.2)))
        ttk.Entry(tab_llm, textvariable=temp_var, width=8).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(tab_llm, text='Max tokens:').pack(anchor=tk.W)
        max_var = tk.StringVar(value=str(self.engine.get_setting('llm.max_tokens', 2000)))
        ttk.Entry(tab_llm, textvariable=max_var, width=10).pack(anchor=tk.W, pady=(0,6))
        safe_var = tk.BooleanVar(value=bool(self.engine.get_setting('llm.safe_mode', True)))
        ttk.Checkbutton(tab_llm, text='Do not send source code (metadata only)', variable=safe_var).pack(anchor=tk.W, pady=(0,6))
        # Footer buttons
        btns = theme.create_styled_frame(frm)
        btns.pack(fill=tk.X, pady=(10,0))
        def apply_and_close():
            # Apply in-memory overrides
            self.engine.config_manager.set_session_override('app.language', lang_var.get())
            self.engine.config_manager.set_session_override('output.default_format', out_var.get())
            try:
                self.engine.config_manager.set_session_override('ui.refresh_interval', int(watch_var.get()))
            except Exception:
                pass
            self.engine.config_manager.set_session_override('llm.provider', prov_var.get())
            self.engine.config_manager.set_session_override('llm.api_key', key_var.get())
            self.engine.config_manager.set_session_override('llm.model', model_var.get())
            try:
                self.engine.config_manager.set_session_override('llm.temperature', float(temp_var.get()))
                self.engine.config_manager.set_session_override('llm.max_tokens', int(max_var.get()))
            except Exception:
                pass
            self.engine.config_manager.set_session_override('llm.safe_mode', bool(safe_var.get()))
            self._toast('Settings applied')
            dlg.destroy()
        def save_api():
            # Persist provider, model and api key into config (still portable, but saved in memory/session or user opts to export later)
            try:
                self.log.info('UI: Save API settings')
            except Exception:
                pass
            # ... existing code ...
            self.engine.set_setting('llm.provider', prov_var.get())
            self.engine.set_setting('llm.model', model_var.get())
            # Note: storing API key per запросу пользователя
            self.engine.set_setting('llm.api_key', key_var.get())
            # Also reflect in current session overrides for immediate use
            self.engine.config_manager.set_session_override('llm.provider', prov_var.get())
            self.engine.config_manager.set_session_override('llm.model', model_var.get())
            self.engine.config_manager.set_session_override('llm.api_key', key_var.get())
            self._toast('API settings saved')
        def test_api():
            # Temporarily apply overrides and make a lightweight request
            try:
                self.log.info('UI: LLM Test API')
            except Exception:
                pass
            # ... existing code ...
            self.engine.config_manager.set_session_override('llm.provider', prov_var.get())
            self.engine.config_manager.set_session_override('llm.api_key', key_var.get())
            self.engine.config_manager.set_session_override('llm.model', model_var.get())
            try:
                from codexify.utils.llm import LLMProvider
                llm = LLMProvider()
                resp = llm.summarize('ping')
                self._show_text_modal('LLM Test Result', str(resp))
            except Exception as e:
                self._show_text_modal('LLM Test Result', f'Error: {e}')
        # Logging controls
        def clear_logs():
            try:
                from codexify.utils.logger import clear_in_memory_logs
                clear_in_memory_logs()
                self._toast('Logs cleared')
            except Exception:
                pass
        def toggle_debug():
            try:
                from codexify.utils.logger import set_log_level
                curr = self.engine.get_setting('app.log_level', 'INFO')
                new = 'DEBUG' if curr != 'DEBUG' else 'INFO'
                self.engine.config_manager.set_session_override('app.log_level', new)
                set_log_level(new)
                self._toast(f'Log level: {new}')
            except Exception:
                pass
        left_btns = theme.create_styled_frame(btns)
        left_btns.pack(side=tk.LEFT)
        theme.create_styled_button(left_btns, 'Clear Logs', command=clear_logs).pack(side=tk.LEFT, padx=(0,6))
        theme.create_styled_button(left_btns, 'Toggle Debug', command=toggle_debug).pack(side=tk.LEFT)
        theme.create_styled_button(btns, 'Apply', command=apply_and_close).pack(side=tk.RIGHT)
        theme.create_styled_button(btns, 'Save API', command=save_api).pack(side=tk.RIGHT, padx=(0,6))
        theme.create_styled_button(btns, 'Test API', command=test_api).pack(side=tk.RIGHT, padx=(0,6))

        # Preselect requested tab and focus
        try:
            if initial_tab.lower() == 'llm':
                nb.select(tab_llm)
                key_entry.focus_set()
            elif initial_tab.lower() == 'hotkeys':
                nb.select(tab_hk)
            else:
                nb.select(tab_general)
        except Exception:
            pass

    def show_llm_settings(self):
        """Open Settings dialog focused on the LLM tab for API key setup."""
        self.show_settings(initial_tab='llm')
        return

        # Hotkeys tab
        tab_hk = theme.create_styled_frame(nb)
        nb.add(tab_hk, text='Hotkeys')
        hk_frame = theme.create_styled_frame(tab_hk)
        hk_frame.pack(fill=tk.BOTH, expand=True)
        left = theme.create_styled_frame(hk_frame)
        right = theme.create_styled_frame(hk_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,8))
        right.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(left, text='Hotkeys').pack(anchor=tk.W)
        hk_list = tk.Listbox(left, height=12)
        hk_list.pack(fill=tk.BOTH, expand=True)
        # load hotkeys
        try:
            hk_objs = self.engine.hotkey_manager.get_all_hotkeys()
        except Exception:
            hk_objs = []
        id_to_obj = {h.id: h for h in hk_objs}
        for h in hk_objs:
            hk_list.insert(tk.END, f"{h.id} — {h.name}")
        # editors
        ttk.Label(right, text='Key:').pack(anchor=tk.W)
        key_var = tk.StringVar()
        ttk.Entry(right, textvariable=key_var, width=12).pack(anchor=tk.W)
        ttk.Label(right, text='Modifiers:').pack(anchor=tk.W, pady=(6,0))
        m_ctrl = tk.BooleanVar(); m_shift = tk.BooleanVar(); m_alt = tk.BooleanVar()
        ttk.Checkbutton(right, text='Ctrl', variable=m_ctrl).pack(anchor=tk.W)
        ttk.Checkbutton(right, text='Shift', variable=m_shift).pack(anchor=tk.W)
        ttk.Checkbutton(right, text='Alt', variable=m_alt).pack(anchor=tk.W)
        enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text='Enabled', variable=enabled_var).pack(anchor=tk.W, pady=(6,0))
        sel_id = {'id': None}
        def on_select(*_):
            sel = hk_list.curselection()
            if not sel:
                return
            idx = sel[0]
            # recover id from display line
            line = hk_list.get(idx)
            hk_id = line.split(' — ',1)[0]
            sel_id['id'] = hk_id
            h = id_to_obj.get(hk_id)
            if not h:
                return
            key_var.set(h.key)
            mods = {m.value for m in (h.modifiers or [])}
            m_ctrl.set('Ctrl' in mods); m_shift.set('Shift' in mods); m_alt.set('Alt' in mods)
            enabled_var.set(bool(h.enabled))
        hk_list.bind('<<ListboxSelect>>', on_select)
        def apply_hotkey():
            hk_id = sel_id.get('id')
            if not hk_id:
                return
            from codexify.systems.hotkey_manager import KeyModifier
            mods = []
            if m_ctrl.get(): mods.append(KeyModifier.CTRL)
            if m_shift.get(): mods.append(KeyModifier.SHIFT)
            if m_alt.get(): mods.append(KeyModifier.ALT)
            try:
                self.engine.hotkey_manager.update_hotkey(hk_id, key=key_var.get().strip(), modifiers=mods)
                self.engine.hotkey_manager.set_hotkey_enabled(hk_id, bool(enabled_var.get()))
                self._toast('Hotkey updated', kind='success')
            except Exception as e:
                messagebox.showerror('Hotkeys', f'Failed to update: {e}')
        theme.create_styled_button(right, 'Apply', command=apply_hotkey).pack(anchor=tk.E, pady=(8,0))
        # Profiles/export-import
        prof_bar = theme.create_styled_frame(tab_hk)
        prof_bar.pack(fill=tk.X, pady=(8,0))
        ttk.Label(prof_bar, text='Profile:').pack(side=tk.LEFT)
        prof_var = tk.StringVar()
        try:
            prof_names = self.engine.hotkey_manager.get_profile_names()
        except Exception:
            prof_names = []
        prof_combo = ttk.Combobox(prof_bar, textvariable=prof_var, values=prof_names, state='readonly', width=18)
        prof_combo.pack(side=tk.LEFT, padx=(6,6))
        def load_profile():
            name = prof_var.get().strip()
            if not name:
                return
            try:
                self.engine.hotkey_manager.load_profile(name)
                self._toast('Profile loaded', kind='success')
            except Exception as e:
                messagebox.showerror('Hotkeys', f'Failed to load: {e}')
        def save_profile():
            name = simpledialog.askstring('Save Profile', 'Profile name:')
            if not name:
                return
            try:
                self.engine.hotkey_manager.save_profile(name, '')
                self._toast('Profile saved', kind='success')
            except Exception as e:
                messagebox.showerror('Hotkeys', f'Failed to save: {e}')
        def export_hotkeys():
            path = filedialog.asksaveasfilename(title='Export Hotkeys', defaultextension='.json', filetypes=[('JSON','*.json')])
            if not path:
                return
            try:
                self.engine.hotkey_manager.export_hotkeys(path)
                self._toast('Hotkeys exported', kind='success')
            except Exception as e:
                messagebox.showerror('Hotkeys', f'Failed to export: {e}')
        def import_hotkeys():
            path = filedialog.askopenfilename(title='Import Hotkeys', filetypes=[('JSON','*.json'), ('All','*.*')])
            if not path:
                return
            try:
                self.engine.hotkey_manager.import_hotkeys(path)
                self._toast('Hotkeys imported', kind='success')
            except Exception as e:
                messagebox.showerror('Hotkeys', f'Failed to import: {e}')
        theme.create_styled_button(prof_bar, 'Load Profile', command=load_profile).pack(side=tk.LEFT)
        theme.create_styled_button(prof_bar, 'Save Profile', command=save_profile).pack(side=tk.LEFT, padx=(6,0))
        theme.create_styled_button(prof_bar, 'Export', command=export_hotkeys).pack(side=tk.LEFT, padx=(12,0))
        theme.create_styled_button(prof_bar, 'Import', command=import_hotkeys).pack(side=tk.LEFT, padx=(6,0))
    
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
            self._last_duplicates = results
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
                # Store last analysis in memory for viewing
                self._last_analysis = data
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

    def _show_duplicates_results(self):
        if not hasattr(self, '_last_duplicates'):
            messagebox.showinfo('Duplicates', 'No duplicates data. Run Find Duplicates first.')
            return
        res = self._last_duplicates
        groups = res.get('groups', []) or res.get('duplicate_groups', [])
        parts = []
        parts.append(f"Groups: {len(groups)}\n")
        for i, g in enumerate(groups[:50], 1):
            files = g.get('files') if isinstance(g, dict) else g
            parts.append(f"[{i}] {len(files)} files:")
            for p in list(files)[:10]:
                parts.append(f"  - {p}")
            parts.append("")
        text = "\n".join(parts)
        self._show_text_modal('Duplicate Results', text)

    def _show_analysis_results(self):
        if not hasattr(self, '_last_analysis'):
            messagebox.showinfo('Analysis', 'No analysis data. Run Analyze first.')
            return
        data = self._last_analysis
        # Build readable text
        parts = []
        s = data.get('summary', {})
        parts.append(f"Summary:\n  files: {s.get('total_files',0)}\n  size: {s.get('total_size',0)} bytes\n  lines: {s.get('total_lines',0)}\n")
        langs = data.get('languages', {}).get('languages', {})
        if langs:
            parts.append('Languages:')
            for ext, info in sorted(langs.items(), key=lambda kv: kv[1].get('files',0), reverse=True)[:20]:
                parts.append(f"  {info.get('name','?')} ({ext}): files={info.get('files',0)}, lines={info.get('lines',0)}")
            parts.append('')
        ft = data.get('file_types', {}).get('categories', {})
        if ft:
            parts.append('Categories:')
            for cat, meta in ft.items():
                parts.append(f"  {cat}: count={meta.get('count',0)}, total_size={meta.get('total_size',0)}")
            parts.append('')
        text = "\n".join(parts) or '[no data]'
        self._show_text_modal('Analysis Results', text)

    def _show_hot_files(self):
        if not hasattr(self, '_last_analysis'):
            messagebox.showinfo('Analysis', 'No analysis data.')
            return
        hot = list(self._last_analysis.get('hot_files') or [])
        # Apply filters
        min_score = float(self.engine.get_setting('analysis.filter.min_hot_score', 0.0) or 0.0)
        min_size_kb = float(self.engine.get_setting('analysis.filter.min_size_kb', 0.0) or 0.0)
        top_n = int(self.engine.get_setting('analysis.filter.top_n', 50) or 50)
        min_size_bytes = int(min_size_kb * 1024)
        hot = [h for h in hot if h.get('score', 0.0) >= min_score and h.get('size', 0) >= min_size_bytes]
        hot = hot[:top_n]
        parts = ['Hot Files (top by score):']
        for i, item in enumerate(hot[:50], 1):
            parts.append(f"[{i}] score={item.get('score',0)} size={item.get('size',0)} lines={item.get('lines',0)}\n  {item.get('path','')}")
        self._show_text_modal('Hot Files', "\n".join(parts) if parts else '[no data]')

    def _open_analysis_filters(self):
        dlg = tk.Toplevel(self)
        dlg.title('Analysis Filters')
        dlg.transient(self)
        dlg.geometry(f"420x220+{self.winfo_rootx()+120}+{self.winfo_rooty()+120}")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text='Min hot score (0..1):').pack(anchor=tk.W)
        score_var = tk.StringVar(value=str(self.engine.get_setting('analysis.filter.min_hot_score', 0.0)))
        ttk.Entry(frm, textvariable=score_var, width=10).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(frm, text='Min size (KB):').pack(anchor=tk.W)
        size_var = tk.StringVar(value=str(self.engine.get_setting('analysis.filter.min_size_kb', 0.0)))
        ttk.Entry(frm, textvariable=size_var, width=10).pack(anchor=tk.W, pady=(0,6))
        ttk.Label(frm, text='Top N:').pack(anchor=tk.W)
        top_var = tk.StringVar(value=str(self.engine.get_setting('analysis.filter.top_n', 50)))
        ttk.Entry(frm, textvariable=top_var, width=10).pack(anchor=tk.W, pady=(0,6))
        def apply():
            try:
                self.engine.config_manager.set_session_override('analysis.filter.min_hot_score', float(score_var.get()))
            except Exception:
                pass
            try:
                self.engine.config_manager.set_session_override('analysis.filter.min_size_kb', float(size_var.get()))
            except Exception:
                pass
            try:
                self.engine.config_manager.set_session_override('analysis.filter.top_n', int(top_var.get()))
            except Exception:
                pass
            self._toast('Filters applied')
            dlg.destroy()
        theme.create_styled_button(frm, 'Apply', command=apply).pack(anchor=tk.E, pady=(8,0))
    
    def run(self):
        """Start the Tkinter event loop."""
        self.mainloop()
