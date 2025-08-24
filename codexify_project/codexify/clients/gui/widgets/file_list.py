"""
Modern file list widget with enhanced functionality.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional, Dict
try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except Exception:
    _DND_AVAILABLE = False
from ..styles import theme, modern_widgets

FILE_ICONS = {
    '.py': '🐍', '.js': '🟨', '.ts': '🟦', '.java': '☕', '.kt': '🟪', '.md': '📝',
    '.json': '🗂', '.yml': '🧾', '.yaml': '🧾', '.html': '🌐', '.css': '🎨',
    '.exe': '🧩', '.mp3': '🎵', '.png': '🖼', '.jpg': '🖼', '.jpeg': '🖼', '.gif': '🖼'
}

class FileList(ttk.Frame):
    """Enhanced file list widget with search, filtering, and better UX.
    Displays flat rows with icon, type, name, size, path.
    """
    
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.files: List[str] = []
        self.filtered_files: List[str] = []
        self.size_map: Dict[str, int] = {}
        self.on_file_selected: Optional[Callable] = None
        self.on_files_moved: Optional[Callable] = None
        self._widgets_ready: bool = False
        self._sort_col = 'name'
        self._sort_reverse = False
        
        self._create_widgets()
        self._setup_bindings()
    
    def _create_widgets(self):
        header_frame = theme.create_styled_frame(self)
        header_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        title_label = theme.create_styled_label(header_frame, self.title, 
                                              font=theme.FONTS['subheading'])
        title_label.pack(side=tk.LEFT)
        
        self.count_label = theme.create_styled_label(header_frame, "0 files", 
                                                   foreground=theme.COLORS['text_secondary'])
        self.count_label.pack(side=tk.RIGHT)
        
        search_frame = theme.create_styled_frame(self)
        search_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        self.search_var = tk.StringVar()
        self.search_entry = modern_widgets.create_search_entry(search_frame, "Search files...", 
                                                             textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        clear_btn = theme.create_styled_button(search_frame, "×", 
                                             command=self._clear_search,
                                             width=3)
        clear_btn.pack(side=tk.RIGHT, padx=(theme.SPACING['sm'], 0))
        
        # Filter row (type and size)
        filter_row = theme.create_styled_frame(self)
        filter_row.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        ttk.Label(filter_row, text="Type:").pack(side=tk.LEFT)
        self.type_filter_var = tk.StringVar()
        self.type_filter = ttk.Combobox(filter_row, textvariable=self.type_filter_var, width=8)
        self.type_filter.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['sm']))
        ttk.Label(filter_row, text="Min KB:").pack(side=tk.LEFT)
        self.size_min_var = tk.StringVar()
        ttk.Entry(filter_row, textvariable=self.size_min_var, width=7).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['sm']))
        ttk.Label(filter_row, text="Max KB:").pack(side=tk.LEFT)
        self.size_max_var = tk.StringVar()
        ttk.Entry(filter_row, textvariable=self.size_max_var, width=7).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['sm']))
        self.hide_hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_row, text="No hidden", variable=self.hide_hidden_var).pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['sm']))
        theme.create_styled_button(filter_row, "Apply", command=self._apply_filters).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(filter_row, "Clear", command=self._clear_filters).pack(side=tk.LEFT)

        # Saved filters controls
        saved_row = theme.create_styled_frame(self)
        saved_row.pack(fill=tk.X, pady=(0, theme.SPACING['xs']))
        ttk.Label(saved_row, text="Saved filters:").pack(side=tk.LEFT)
        self.saved_filter_var = tk.StringVar()
        self.saved_filters_combo = ttk.Combobox(saved_row, textvariable=self.saved_filter_var, width=18, state='readonly')
        self.saved_filters_combo.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], theme.SPACING['xs']))
        theme.create_styled_button(saved_row, "Use", command=self._use_saved_filter).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(saved_row, "Save As…", command=self._save_current_filter).pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        theme.create_styled_button(saved_row, "Delete", command=self._delete_saved_filter).pack(side=tk.LEFT)
        
        list_frame = theme.create_styled_frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview with columns for icon/type/name/size/path (flat list)
        self.tree = ttk.Treeview(list_frame, columns=('type', 'name', 'size', 'path'), show='tree headings')
        self.tree.heading('#0', text='')  # icon space
        self.tree.heading('type', text='Type', command=lambda: self._sort_by('type'))
        self.tree.heading('name', text='Name', command=lambda: self._sort_by('name'))
        self.tree.heading('size', text='Size', command=lambda: self._sort_by('size'))
        self.tree.heading('path', text='Path', command=lambda: self._sort_by('path'))
        self.tree.column('#0', width=28, anchor='w')
        self.tree.column('type', width=80, anchor='w')
        self.tree.column('name', width=240, anchor='w')
        self.tree.column('size', width=90, anchor='e')
        self.tree.column('path', width=420, anchor='w')
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        vscroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vscroll.set)
        
        hscroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        hscroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=hscroll.set)
        
        # Backwards compatibility alias
        self.listbox = self.tree
        
        self._create_context_menu()
        
        self.search_var.trace('w', self._on_search_changed)
        self._widgets_ready = True
        self._refresh_display()
        # Enable OS drag-and-drop into the tree
        if _DND_AVAILABLE:
            try:
                self.tree.drop_target_register(DND_FILES)
                self.tree.dnd_bind('<<Drop>>', self._on_external_drop)
            except Exception:
                pass
    
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy Name", command=self._copy_name)
        self.context_menu.add_command(label="Copy Path", command=self._copy_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Add Tag…", command=self._add_tag)
        self.context_menu.add_command(label="Edit Note…", command=self._edit_note)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select: Same Extension", command=self._select_same_ext)
        self.context_menu.add_command(label="Select: By Pattern…", command=self._select_by_pattern)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open File", command=self._open_file)
        self.context_menu.add_command(label="Open in Explorer", command=self._open_in_explorer)
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def add_context_action(self, label: str, callback: Callable[[], None]):
        self.context_menu.add_command(label=label, command=callback)
    
    def widget_bbox(self):
        x = self.tree.winfo_rootx()
        y = self.tree.winfo_rooty()
        return (x, y, x + self.tree.winfo_width(), y + self.tree.winfo_height())
    
    def _setup_bindings(self):
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self.tree.bind("<Double-Button-1>", lambda e: self._open_file())
        self.tree.bind("<Control-c>", self._copy_paths_to_clipboard)
        self.tree.bind("<Control-v>", self._on_paste_paths)
        # remember column width changes (simple)
        self.tree.bind("<ButtonRelease-1>", lambda e: self.event_generate('<<ColumnsChanged>>'))
        
    # ------- Data rendering -------
    def _file_row_values(self, path: str):
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        icon = FILE_ICONS.get(ext, '📄')
        ftype = ext if ext else 'file'
        # size
        def _fmt_size(sz: int) -> str:
            units = ['B','KB','MB','GB','TB']
            i = 0
            f = float(sz)
            while f >= 1024 and i < len(units)-1:
                f /= 1024
                i += 1
            return f"{f:.1f} {units[i]}" if i > 0 else f"{int(f)} {units[i]}"
        if os.path.exists(path) and os.path.isfile(path):
            try:
                size_val = os.path.getsize(path)
                self.size_map[path] = size_val
                size = _fmt_size(size_val)
            except Exception:
                self.size_map[path] = -1
                size = "-"
        else:
            self.size_map[path] = -1
            size = "-"
        return icon, ftype, name, size, path
    
    def _populate_tree(self, file_paths: List[str]):
        self.tree.delete(*self.tree.get_children())
        # sorting
        def key_func(p: str):
            if self._sort_col == 'type':
                return os.path.splitext(p)[1].lower()
            if self._sort_col == 'name':
                return os.path.basename(p).lower()
            if self._sort_col == 'size':
                return self.size_map.get(p, -1)
            if self._sort_col == 'path':
                return p.lower()
            return p.lower()
        sorted_files = sorted(file_paths, key=key_func, reverse=self._sort_reverse)
        for path in sorted_files:
            icon, ftype, name, size, full = self._file_row_values(path)
            self.tree.insert('', 'end', text=icon, values=(ftype, name, size, full))
    
    def _sort_by(self, column: str):
        if self._sort_col == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = column
            self._sort_reverse = False
        self._refresh_display()
    
    def _apply_filters(self):
        term = self.search_var.get().lower().strip()
        ext = self.type_filter_var.get().lower().strip()
        size_min_str = self.size_min_var.get().strip()
        size_max_str = getattr(self, 'size_max_var', tk.StringVar(value='')).get().strip()
        min_bytes = 0
        max_bytes = None
        if size_min_str:
            try:
                min_kb = float(size_min_str)
                min_bytes = int(min_kb * 1024)
            except Exception:
                min_bytes = 0
        if size_max_str:
            try:
                max_kb = float(size_max_str)
                max_bytes = int(max_kb * 1024)
            except Exception:
                max_bytes = None
        result = []
        for p in self.files:
            if term and term not in p.lower():
                continue
            if ext and os.path.splitext(p)[1].lower() != ext:
                continue
            if getattr(self, 'hide_hidden_var', None) and self.hide_hidden_var.get():
                base = os.path.basename(p)
                if base.startswith('.'):
                    continue
            size_val = self.size_map.get(p)
            if size_val is None:
                try:
                    size_val = os.path.getsize(p) if os.path.exists(p) else -1
                    self.size_map[p] = size_val
                except Exception:
                    size_val = -1
                    self.size_map[p] = size_val
            if size_val >= 0 and size_val < min_bytes:
                continue
            if max_bytes is not None and size_val >= 0 and size_val > max_bytes:
                continue
            result.append(p)
        self.filtered_files = result
        self._refresh_display()
    
    def _rebuild_type_filter(self):
        exts = sorted({os.path.splitext(os.path.basename(p))[1].lower() for p in self.files if p})
        self.type_filter['values'] = exts
    
    def _clear_filters(self):
        self.search_var.set("")
        self.type_filter_var.set("")
        self.size_min_var.set("")
        if hasattr(self, 'size_max_var'):
            self.size_max_var.set("")
        if hasattr(self, 'hide_hidden_var'):
            self.hide_hidden_var.set(False)
        self.filtered_files = self.files.copy()
        self._refresh_display()

    # Saved filters integration hooks (connected by MainWindow)
    def set_saved_filters(self, names: List[str]):
        self.saved_filters_combo['values'] = names
        if names:
            self.saved_filters_combo.current(0)

    def set_on_filters_save(self, cb: Callable[[str, str, str, str], None]):
        self._on_filters_save = cb

    def set_on_filters_delete(self, cb: Callable[[str], None]):
        self._on_filters_delete = cb

    def set_on_filters_apply(self, cb: Callable[[str], None]):
        self._on_filters_apply = cb

    def _use_saved_filter(self):
        name = self.saved_filter_var.get().strip()
        if name and hasattr(self, '_on_filters_apply') and self._on_filters_apply:
            self._on_filters_apply(name)

    def _save_current_filter(self):
        dlg = tk.Toplevel(self)
        dlg.title("Save Filter")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text="Filter name:").pack(anchor=tk.W)
        name_var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=name_var, width=24)
        ent.pack(fill=tk.X, pady=(4,8))
        def ok():
            name = name_var.get().strip()
            if name and hasattr(self, '_on_filters_save') and self._on_filters_save:
                self._on_filters_save(name, self.search_var.get(), self.type_filter_var.get(), self.size_min_var.get())
            dlg.destroy()
        theme.create_styled_button(frm, "Save", command=ok).pack(anchor=tk.E)
        ent.focus()

    def _delete_saved_filter(self):
        name = self.saved_filter_var.get().strip()
        if name and hasattr(self, '_on_filters_delete') and self._on_filters_delete:
            self._on_filters_delete(name)
    
    def _on_search_changed(self, *args):
        if not self._widgets_ready:
            return
        term = self.search_var.get().lower()
        if term == "search files...":
            term = ""
        self.filtered_files = [p for p in self.files if term in p.lower()] if term else self.files.copy()
        self._refresh_display()
    
    def _clear_search(self):
        self.search_var.set("")
        self.search_entry.focus()
    
    def _refresh_display(self):
        self._rebuild_type_filter()
        self._populate_tree(self.filtered_files)
        self._update_count()
    
    def _update_count(self):
        self.count_label.config(text=f"{len(self.filtered_files)} files")
    
    # ------- Selection/actions -------
    def _selected_paths(self) -> List[str]:
        items = self.tree.selection()
        paths = []
        for it in items:
            vals = self.tree.item(it, 'values')
            if len(vals) >= 4:
                paths.append(vals[3])
        return paths
    
    def _on_selection_changed(self, event):
        if self.on_file_selected:
            self.on_file_selected(self.get_selected_files())
    
    def _open_file(self):
        paths = self._selected_paths()
        if paths:
            print(f"Opening: {paths[0]}")
    
    def _open_in_explorer(self):
        paths = self._selected_paths()
        if paths:
            import subprocess
            path = paths[0]
            if os.path.exists(path):
                if os.name == 'nt':
                    subprocess.run(['explorer', '/select,', path])
                else:
                    subprocess.run(['xdg-open', os.path.dirname(path)])
    
    def _copy_path(self):
        paths = self._selected_paths()
        if paths:
            self.clipboard_clear()
            self.clipboard_append(paths[0])
    
    def _copy_name(self):
        paths = self._selected_paths()
        if paths:
            self.clipboard_clear()
            self.clipboard_append(os.path.basename(paths[0]))

    def _add_tag(self):
        try:
            from codexify.systems.config_manager import get_config_manager
            cm = get_config_manager()
            paths = self._selected_paths()
            if not paths:
                return
            dlg = tk.Toplevel(self)
            dlg.title("Add Tag")
            frm = theme.create_styled_frame(dlg)
            frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            ttk.Label(frm, text=os.path.basename(paths[0])).pack(anchor=tk.W)
            tag_var = tk.StringVar()
            ent = ttk.Entry(frm, textvariable=tag_var)
            ent.pack(fill=tk.X, pady=(6,6))
            def ok():
                t = tag_var.get().strip()
                if t:
                    for p in paths:
                        cm.add_tag(p, t)
                dlg.destroy()
            theme.create_styled_button(frm, "Save", command=ok).pack(anchor=tk.E)
            ent.focus()
        except Exception:
            pass

    def _edit_note(self):
        try:
            from codexify.systems.config_manager import get_config_manager
            cm = get_config_manager()
            paths = self._selected_paths()
            if not paths:
                return
            p = paths[0]
            meta = cm.get_item_meta(p)
            dlg = tk.Toplevel(self)
            dlg.title("Edit Note")
            frm = theme.create_styled_frame(dlg)
            frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            ttk.Label(frm, text=os.path.basename(p)).pack(anchor=tk.W)
            txt = tk.Text(frm, height=6)
            txt.pack(fill=tk.BOTH, expand=True, pady=(6,6))
            txt.insert('1.0', meta.get('note',''))
            def ok():
                cm.set_note(p, txt.get('1.0', tk.END).strip())
                dlg.destroy()
            theme.create_styled_button(frm, "Save", command=ok).pack(anchor=tk.E)
        except Exception:
            pass
    
    def _copy_paths_to_clipboard(self, event=None):
        paths = self._selected_paths()
        if paths:
            self.clipboard_clear()
            self.clipboard_append("\n".join(paths))
            return "break"
        return None

    def _select_same_ext(self):
        paths = self._selected_paths()
        if not paths:
            return
        ext = os.path.splitext(paths[0])[1].lower()
        to_select = []
        for it in self.tree.get_children(''):
            vals = self.tree.item(it, 'values')
            if len(vals) >= 4 and os.path.splitext(vals[3])[1].lower() == ext:
                to_select.append(it)
        self.clear_selection()
        for it in to_select:
            self.tree.selection_add(it)
        if to_select:
            self.tree.see(to_select[0])

    def _select_by_pattern(self):
        dlg = tk.Toplevel(self)
        dlg.title("Select by Pattern")
        frm = theme.create_styled_frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text="Use glob (e.g., *.py) or substring").pack(anchor=tk.W)
        pat_var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=pat_var)
        ent.pack(fill=tk.X, pady=(6,6))
        def ok():
            pat = pat_var.get().strip()
            self.clear_selection()
            import fnmatch
            to_select = []
            for it in self.tree.get_children(''):
                vals = self.tree.item(it, 'values')
                if len(vals) >= 4:
                    p = vals[3]
                    if pat and (fnmatch.fnmatch(p, pat) or pat.lower() in p.lower()):
                        to_select.append(it)
            for it in to_select:
                self.tree.selection_add(it)
            if to_select:
                self.tree.see(to_select[0])
            dlg.destroy()
        theme.create_styled_button(frm, "Select", command=ok).pack(anchor=tk.E)
        ent.focus()

    # --- Public helpers for palette integration ---
    def select_same_extension(self):
        self._select_same_ext()

    def select_by_pattern(self):
        self._select_by_pattern()

    def _on_paste_paths(self, event=None):
        try:
            data = self.clipboard_get() or ''
        except Exception:
            return None
        raw_paths = [p.strip().strip('"') for p in data.splitlines() if p.strip()]
        if raw_paths and hasattr(self, '_external_drop_cb') and self._external_drop_cb:
            self._external_drop_cb(raw_paths)
            return "break"
        return None

    def _on_external_drop(self, event):
        data = event.data or ''
        # Windows paths may come wrapped in braces when containing spaces
        tokens: List[str] = []
        token = ''
        in_brace = False
        for ch in data:
            if ch == '{':
                in_brace = True
                token = ''
                continue
            if ch == '}':
                in_brace = False
                tokens.append(token)
                token = ''
                continue
            if ch == ' ' and not in_brace:
                if token:
                    tokens.append(token)
                    token = ''
            else:
                token += ch
        if token:
            tokens.append(token)
        if tokens and hasattr(self, '_external_drop_cb') and self._external_drop_cb:
            self._external_drop_cb(tokens)
        return "break"

    def set_on_external_drop(self, callback: Callable[[List[str]], None]):
        """Set callback for external file/folder drops and clipboard paste.
        Callback receives a list of absolute paths.
        """
        self._external_drop_cb = callback
    
    # ------- Public API -------
    def set_files(self, files: List[str]):
        self.files = files.copy()
        self.filtered_files = files.copy()
        self._refresh_display()
    
    def get_selected_files(self) -> List[str]:
        return self._selected_paths()
    
    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())
    
    def select_file(self, file_path: str):
        for it in self.tree.get_children(''):
            vals = self.tree.item(it, 'values')
            if len(vals) >= 4 and vals[3] == file_path:
                self.clear_selection()
                self.tree.selection_add(it)
                self.tree.see(it)
                break
    
    def set_on_file_selected(self, callback: Callable[[List[str]], None]):
        self.on_file_selected = callback
    
    def set_on_files_moved(self, callback: Callable[[List[str], str], None]):
        self.on_files_moved = callback

    # Optional external accessors for layout persistence
    def get_column_widths(self) -> Dict[str, int]:
        return {col: self.tree.column(col, width=None) for col in ('type','name','size','path')}
    
    def set_column_widths(self, widths: Dict[str, int]):
        for col, w in widths.items():
            try:
                self.tree.column(col, width=int(w))
            except Exception:
                pass
