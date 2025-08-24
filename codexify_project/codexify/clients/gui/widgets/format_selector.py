"""
Enhanced format selector widget with better UX.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Set, Optional
from ..styles import theme, modern_widgets

class FormatSelector(ttk.Frame):
    """Enhanced format selector with search, categories, presets, and better organization."""
    
    def __init__(self, parent, title: str = "File Formats", **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.selected_formats: Set[str] = set()
        self.on_formats_changed: Optional[Callable] = None
        self.on_apply_preset: Optional[Callable[[str], None]] = None
        self.on_save_preset: Optional[Callable[[str, List[str]], None]] = None
        self.on_delete_preset: Optional[Callable[[str], None]] = None
        self.on_suggest_preset: Optional[Callable[[], None]] = None
        
        # Predefined format categories
        self.format_categories = {
            'Programming': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift'],
            'Web': ['.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.svg', '.jsx', '.tsx'],
            'Data': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.csv', '.tsv'],
            'Documentation': ['.md', '.rst', '.txt', '.adoc', '.tex', '.doc', '.docx'],
            'Configuration': ['.env', '.properties', '.config', '.ini', '.cfg', '.conf', '.xml'],
            'Build': ['.py', '.js', '.ts', '.java', '.gradle', '.maven', '.pom', '.sbt', '.cargo', '.go.mod']
        }
        
        self._create_widgets()
        self._setup_bindings()
    
    def _create_widgets(self):
        """Create the format selector components."""
        main_frame = theme.create_styled_frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = theme.create_styled_frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        title_label = theme.create_styled_label(header_frame, self.title,
                                              font=theme.FONTS['subheading'])
        title_label.pack(side=tk.LEFT)
        
        self.count_label = theme.create_styled_label(header_frame, "0 formats selected",
                                                   foreground=theme.COLORS['text_secondary'],
                                                   font=theme.FONTS['small'])
        self.count_label.pack(side=tk.RIGHT)
        
        # Presets row
        presets_row = theme.create_styled_frame(main_frame)
        presets_row.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        ttk.Label(presets_row, text="Presets:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(presets_row, textvariable=self.preset_var, state='readonly', width=18)
        self.preset_combo.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['xs']))
        theme.create_styled_button(presets_row, "Apply", command=self._apply_selected_preset).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(presets_row, "Suggest", command=self._suggest_preset).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(presets_row, "Save As…", command=self._save_as_preset).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(presets_row, "Delete", command=self._delete_preset).pack(side=tk.LEFT)

        # Quick tags row
        quick_row = theme.create_styled_frame(main_frame)
        quick_row.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        ttk.Label(quick_row, text="Quick:").pack(side=tk.LEFT)
        theme.create_styled_button(quick_row, "Code", command=lambda: self._apply_quick('Code')).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        theme.create_styled_button(quick_row, "Docs", command=lambda: self._apply_quick('Docs')).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        theme.create_styled_button(quick_row, "Data", command=lambda: self._apply_quick('Data')).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        
        # Search formats
        search_holder = theme.create_styled_frame(main_frame)
        search_holder.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        self.search_formats = modern_widgets.create_search_entry(search_holder, "Search formats…")
        self.search_formats.pack(fill=tk.X)
        
        # Categories + Formats
        categories_frame = theme.create_styled_frame(main_frame)
        categories_frame.pack(fill=tk.BOTH, expand=True)
        categories_frame.grid_columnconfigure(0, weight=1)
        categories_frame.grid_columnconfigure(1, weight=2)
        
        left_frame = theme.create_styled_frame(categories_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACING['sm']))
        
        cat_label = theme.create_styled_label(left_frame, "Categories",
                                            font=theme.FONTS['body'],
                                            foreground=theme.COLORS['text_secondary'])
        cat_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        self.categories_listbox = theme.create_styled_listbox(left_frame, height=8)
        self.categories_listbox.pack(fill=tk.BOTH, expand=True)
        
        cat_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, 
                                     command=self.categories_listbox.yview)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.categories_listbox.config(yscrollcommand=cat_scrollbar.set)
        
        right_frame = theme.create_styled_frame(categories_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(theme.SPACING['sm'], 0))
        
        fmt_label = theme.create_styled_label(right_frame, "Formats",
                                            font=theme.FONTS['body'],
                                            foreground=theme.COLORS['text_secondary'])
        fmt_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        formats_frame = theme.create_styled_frame(right_frame)
        formats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.formats_canvas = tk.Canvas(formats_frame, 
                                       bg=theme.COLORS['surface'],
                                       highlightthickness=0)
        formats_scrollbar = ttk.Scrollbar(formats_frame, orient=tk.VERTICAL, 
                                        command=self.formats_canvas.yview)
        
        self.formats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        formats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.formats_canvas.config(yscrollcommand=formats_scrollbar.set)
        
        self.formats_content = theme.create_styled_frame(self.formats_canvas)
        self.formats_canvas.create_window((0, 0), window=self.formats_content, anchor="nw")
        
        # Bottom controls
        controls_frame = theme.create_styled_frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(theme.SPACING['sm'], 0))
        
        select_all_btn = theme.create_styled_button(controls_frame, "Select All",
                                                  command=self._select_all_formats)
        select_all_btn.pack(side=tk.LEFT, padx=(0, theme.SPACING['sm']))
        
        clear_all_btn = theme.create_styled_button(controls_frame, "Clear All",
                                                 command=self._clear_all_formats)
        clear_all_btn.pack(side=tk.LEFT)
        
        custom_frame = theme.create_styled_frame(controls_frame)
        custom_frame.pack(side=tk.RIGHT)
        
        ttk.Label(custom_frame, text="Custom:").pack(side=tk.LEFT)
        self.custom_entry = theme.create_styled_entry(custom_frame, width=15)
        self.custom_entry.pack(side=tk.LEFT, padx=theme.SPACING['xs'])
        
        add_btn = theme.create_styled_button(custom_frame, "Add",
                                           command=self._add_custom_format)
        add_btn.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        del_btn = theme.create_styled_button(custom_frame, "Delete",
                                           command=self._delete_custom_format)
        del_btn.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        
        self._populate_categories()
        
        all_formats = []
        for formats in self.format_categories.values():
            all_formats.extend(formats)
        if hasattr(self, 'search_widget'):
            self.search_widget.set_search_data(all_formats)

        # Active formats block
        active_frame = theme.create_styled_frame(main_frame)
        active_frame.pack(fill=tk.BOTH, expand=False, pady=(theme.SPACING['sm'], 0))
        theme.create_styled_label(active_frame, "Active Formats", font=theme.FONTS['body'],
                                  foreground=theme.COLORS['text_secondary']).pack(anchor=tk.W)
        inner = theme.create_styled_frame(active_frame)
        inner.pack(fill=tk.X)
        self.active_listbox = tk.Listbox(inner, height=5)
        self.active_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        rm_btn = theme.create_styled_button(inner, "Remove",
                                            command=self._remove_selected_active)
        rm_btn.pack(side=tk.LEFT, padx=(theme.SPACING['sm'], 0))
        self._update_active_listbox()
        
    def _setup_bindings(self):
        self.categories_listbox.bind('<<ListboxSelect>>', self._on_category_selected)
        self.formats_content.bind('<Configure>', self._on_canvas_configure)
        self.custom_entry.bind('<Return>', lambda e: self._add_custom_format())
    
    # Presets API (called from outside)
    def set_preset_names(self, names: List[str]):
        self.preset_combo['values'] = names
        if names:
            self.preset_combo.current(0)
    
    def set_on_apply_preset(self, cb: Callable[[str], None]):
        self.on_apply_preset = cb
    
    def set_on_save_preset(self, cb: Callable[[str, List[str]], None]):
        self.on_save_preset = cb
    
    def set_on_delete_preset(self, cb: Callable[[str], None]):
        self.on_delete_preset = cb
    
    def set_on_formats_changed(self, cb: Callable[[List[str]], None]):
        self.on_formats_changed = cb

    def set_formats(self, formats: List[str]):
        """Set selected formats from outside and refresh UI."""
        self.selected_formats = set([f.lower() if f else f for f in formats])
        self._update_count()
        self._populate_categories()
        self._update_active_listbox()

    def set_on_suggest_preset(self, cb: Callable[[], None]):
        self.on_suggest_preset = cb
    
    def _apply_selected_preset(self):
        name = self.preset_var.get().strip()
        if name and self.on_apply_preset:
            self.on_apply_preset(name)
    
    def _save_as_preset(self):
        dlg = tk.Toplevel(self)
        dlg.title("Save Preset")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text="Preset name:").pack(anchor=tk.W)
        name_var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=name_var, width=24)
        ent.pack(fill=tk.X, pady=(4, 8))
        def ok():
            name = name_var.get().strip()
            if name and self.on_save_preset:
                self.on_save_preset(name, list(self.selected_formats))
            dlg.destroy()
        theme.create_styled_button(frm, "Save", command=ok).pack(side=tk.RIGHT)
        ent.focus()
    
    def _delete_preset(self):
        name = self.preset_var.get().strip()
        if name and self.on_delete_preset:
            self.on_delete_preset(name)
    
    def _suggest_preset(self):
        if hasattr(self, 'on_suggest_preset') and self.on_suggest_preset:
            self.on_suggest_preset()

    def _apply_quick(self, name: str):
        mapping = {
            'Code': ['Programming', 'Web'],
            'Docs': ['Documentation'],
            'Data': ['Data']
        }
        buckets = mapping.get(name, [])
        for b in buckets:
            for f in self.format_categories.get(b, []):
                self.selected_formats.add(f)
        self._update_count()
        self._update_active_listbox()
        if self.on_formats_changed:
            self.on_formats_changed(list(self.selected_formats))
        # refresh current view
        self._on_category_selected(None)
    
    # Existing methods below (categories, toggles, etc.) remain unchanged

    def _on_canvas_configure(self, event):
        self.formats_canvas.configure(scrollregion=self.formats_canvas.bbox("all"))

    def _populate_categories(self):
        self.categories_listbox.delete(0, tk.END)
        for category in sorted(self.format_categories.keys()):
            self.categories_listbox.insert(tk.END, category)
        # show first category by default
        if self.categories_listbox.size() > 0:
            self.categories_listbox.selection_set(0)
            self._on_category_selected(None)

    def _on_category_selected(self, event):
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self._show_category_formats(category)

    def _show_category_formats(self, category: str):
        # clear
        for w in self.formats_content.winfo_children():
            w.destroy()
        formats = sorted(self.format_categories.get(category, []))
        for i, fmt in enumerate(formats):
            var = tk.BooleanVar(value=(fmt in self.selected_formats))
            def _on_toggle(f=fmt, v=var):
                if v.get():
                    self.selected_formats.add(f)
                else:
                    self.selected_formats.discard(f)
                self._update_count()
                if self.on_formats_changed:
                    self.on_formats_changed(list(self.selected_formats))
            var.trace_add('write', lambda *_args, cb=_on_toggle: cb())
            cb = theme.create_styled_checkbutton(self.formats_content, fmt, var)
            cb.grid(row=i//2, column=i%2, sticky="w", padx=theme.SPACING['xs'], pady=theme.SPACING['xs'])
        self._update_active_listbox()

    def _select_all_formats(self):
        for category, fmts in self.format_categories.items():
            for f in fmts:
                self.selected_formats.add(f)
        self._update_count()
        if self.on_formats_changed:
            self.on_formats_changed(list(self.selected_formats))
        # refresh current view
        self._on_category_selected(None)
        self._update_active_listbox()

    def _clear_all_formats(self):
        self.selected_formats.clear()
        self._update_count()
        if self.on_formats_changed:
            self.on_formats_changed(list(self.selected_formats))
        self._on_category_selected(None)
        self._update_active_listbox()

    def _add_custom_format(self):
        fmt = self.custom_entry.get().strip()
        if fmt:
            if not fmt.startswith('.'):
                fmt = '.' + fmt
            self.selected_formats.add(fmt)
            self._update_count()
            if self.on_formats_changed:
                self.on_formats_changed(list(self.selected_formats))
            # add to a "Custom" category bucket
            self.format_categories.setdefault('Custom', [])
            if fmt not in self.format_categories['Custom']:
                self.format_categories['Custom'].append(fmt)
            self._populate_categories()
            self.custom_entry.delete(0, tk.END)
            self._update_active_listbox()

    def _delete_custom_format(self):
        fmt = self.custom_entry.get().strip()
        if not fmt:
            return
        if not fmt.startswith('.'):
            fmt = '.' + fmt
        # remove from Custom bucket
        if 'Custom' in self.format_categories and fmt in self.format_categories['Custom']:
            self.format_categories['Custom'].remove(fmt)
        # remove from selected if present
        if fmt in self.selected_formats:
            self.selected_formats.discard(fmt)
            self._update_count()
            if self.on_formats_changed:
                self.on_formats_changed(list(self.selected_formats))
        self._populate_categories()
        self._update_active_listbox()

    def _update_count(self):
        count = len(self.selected_formats)
        self.count_label.config(text=f"{count} formats selected")

    def _update_active_listbox(self):
        if not hasattr(self, 'active_listbox'):
            return
        self.active_listbox.delete(0, tk.END)
        for fmt in sorted(self.selected_formats):
            self.active_listbox.insert(tk.END, fmt)

    def _remove_selected_active(self):
        sel = self.active_listbox.curselection()
        if not sel:
            return
        to_remove = set()
        for i in sel:
            to_remove.add(self.active_listbox.get(i))
        if to_remove:
            self.selected_formats -= to_remove
            # also remove from Custom bucket if present
            if 'Custom' in self.format_categories:
                self.format_categories['Custom'] = [f for f in self.format_categories['Custom'] if f not in to_remove]
            self._update_count()
            if self.on_formats_changed:
                self.on_formats_changed(list(self.selected_formats))
            self._populate_categories()
            self._update_active_listbox()
