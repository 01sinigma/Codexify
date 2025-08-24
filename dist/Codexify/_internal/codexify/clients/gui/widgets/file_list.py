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
    '.json': '🗂', '.yml': '🧾', '.yaml': '🧾', '.html': '🌐', '.css': '🎨'
}

class FileList(ttk.Frame):
    """Enhanced file list widget with search, filtering, and better UX.
    Displays flat rows with icon, type, name, path.
    """
    
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.files: List[str] = []
        self.filtered_files: List[str] = []
        self.on_file_selected: Optional[Callable] = None
        self.on_files_moved: Optional[Callable] = None
        self._widgets_ready: bool = False
        
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
        
        list_frame = theme.create_styled_frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview with columns for icon/type/name/path (flat list)
        self.tree = ttk.Treeview(list_frame, columns=('type', 'name', 'path'), show='tree headings')
        self.tree.heading('#0', text='')  # icon space
        self.tree.heading('type', text='Type')
        self.tree.heading('name', text='Name')
        self.tree.heading('path', text='Path')
        self.tree.column('#0', width=28, anchor='w')
        self.tree.column('type', width=80, anchor='w')
        self.tree.column('name', width=220, anchor='w')
        self.tree.column('path', width=400, anchor='w')
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Backwards compatibility alias
        self.listbox = self.tree
        
        self._create_context_menu()
        
        self.search_var.trace('w', self._on_search_changed)
        self._widgets_ready = True
        self._refresh_display()
    
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy Name", command=self._copy_name)
        self.context_menu.add_command(label="Copy Path", command=self._copy_path)
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
        # Paste from clipboard (paths separated by newlines)
        self.tree.bind("<Control-v>", self._on_paste_paths)
        # External drag-and-drop via tkinterdnd2 (if available)
        if _DND_AVAILABLE and hasattr(self.tree, 'drop_target_register'):
            try:
                self.tree.drop_target_register(DND_FILES)
                self.tree.dnd_bind('<<Drop>>', self._on_external_drop)
            except Exception:
                pass
    
    # ------- Data rendering -------
    def _file_row_values(self, path: str):
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        icon = FILE_ICONS.get(ext, '📄')
        ftype = ext or 'file'
        return icon, ftype, name, path
    
    def _populate_tree(self, file_paths: List[str]):
        self.tree.delete(*self.tree.get_children())
        for path in sorted(file_paths, key=lambda p: p.lower()):
            icon, ftype, name, full = self._file_row_values(path)
            # Put icon in #0 text, rest in columns
            self.tree.insert('', 'end', text=icon, values=(ftype, name, full))
    
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
            if len(vals) >= 3:
                paths.append(vals[2])
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
    
    def _copy_paths_to_clipboard(self, event=None):
        paths = self._selected_paths()
        if paths:
            self.clipboard_clear()
            self.clipboard_append("\n".join(paths))
            return "break"
        return None

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
            if len(vals) >= 3 and vals[2] == file_path:
                self.clear_selection()
                self.tree.selection_add(it)
                self.tree.see(it)
                break
    
    def set_on_file_selected(self, callback: Callable[[List[str]], None]):
        self.on_file_selected = callback
    
    def set_on_files_moved(self, callback: Callable[[List[str], str], None]):
        self.on_files_moved = callback
