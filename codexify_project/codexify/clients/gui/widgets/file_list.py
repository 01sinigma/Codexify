"""
Modern file list widget with enhanced functionality.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from ..styles import theme, modern_widgets

class FileList(ttk.Frame):
    """Enhanced file list widget with search, filtering, and better UX."""
    
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.files: List[str] = []
        self.filtered_files: List[str] = []
        self.on_file_selected: Optional[Callable] = None
        self.on_files_moved: Optional[Callable] = None
        
        self._create_widgets()
        self._setup_bindings()
    
    def _create_widgets(self):
        """Create the widget components."""
        # Header frame
        header_frame = theme.create_styled_frame(self)
        header_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        # Title label
        title_label = theme.create_styled_label(header_frame, self.title, 
                                              font=theme.FONTS['subheading'])
        title_label.pack(side=tk.LEFT)
        
        # File count label
        self.count_label = theme.create_styled_label(header_frame, "0 files", 
                                                   foreground=theme.COLORS['text_secondary'])
        self.count_label.pack(side=tk.RIGHT)
        
        # Search frame
        search_frame = theme.create_styled_frame(self)
        search_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        self.search_entry = modern_widgets.create_search_entry(search_frame, "Search files...", 
                                                             textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Clear search button
        clear_btn = theme.create_styled_button(search_frame, "×", 
                                             command=self._clear_search,
                                             width=3)
        clear_btn.pack(side=tk.RIGHT, padx=(theme.SPACING['sm'], 0))
        
        # Listbox frame
        list_frame = theme.create_styled_frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # File listbox
        self.listbox = theme.create_styled_listbox(list_frame, selectmode=tk.EXTENDED)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Create the right-click context menu."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open File", command=self._open_file)
        self.context_menu.add_command(label="Open in Explorer", command=self._open_in_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Path", command=self._copy_path)
        self.context_menu.add_command(label="Copy Name", command=self._copy_name)
        
        # Bind right-click
        self.listbox.bind("<Button-3>", self._show_context_menu)
    
    def _setup_bindings(self):
        """Setup keyboard and mouse bindings."""
        # Double-click to open
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        
        # Selection change
        self.listbox.bind("<<ListboxSelect>>", self._on_selection_changed)
        
        # Keyboard shortcuts
        self.listbox.bind("<Control-a>", self._select_all)
        self.listbox.bind("<Control-f>", lambda e: self.search_entry.focus())
        
        # Search entry focus
        self.search_entry.bind("<Escape>", lambda e: self.search_entry.selection_clear())
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        search_term = self.search_var.get().lower()
        if search_term == "search files...":
            search_term = ""
        
        if search_term:
            self.filtered_files = [f for f in self.files if search_term in f.lower()]
        else:
            self.filtered_files = self.files.copy()
        
        self._refresh_display()
    
    def _clear_search(self):
        """Clear the search field."""
        self.search_var.set("")
        self.search_entry.focus()
    
    def _refresh_display(self):
        """Refresh the listbox display."""
        self.listbox.delete(0, tk.END)
        for file_path in self.filtered_files:
            # Show only filename, not full path
            filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
            self.listbox.insert(tk.END, filename)
        
        self._update_count()
    
    def _update_count(self):
        """Update the file count display."""
        total = len(self.files)
        filtered = len(self.filtered_files)
        
        if total == filtered:
            self.count_label.config(text=f"{total} files")
        else:
            self.count_label.config(text=f"{filtered} of {total} files")
    
    def _on_selection_changed(self, event):
        """Handle listbox selection changes."""
        if self.on_file_selected:
            selected_files = self.get_selected_files()
            self.on_file_selected(selected_files)
    
    def _on_double_click(self, event):
        """Handle double-click on file."""
        self._open_file()
    
    def _show_context_menu(self, event):
        """Show the context menu at cursor position."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _open_file(self):
        """Open the selected file."""
        selected_files = self.get_selected_files()
        if selected_files:
            # This would typically open the file in the default application
            print(f"Opening: {selected_files[0]}")
    
    def _open_in_explorer(self):
        """Open the file location in explorer."""
        selected_files = self.get_selected_files()
        if selected_files:
            import os
            import subprocess
            file_path = selected_files[0]
            if os.path.exists(file_path):
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', file_path])
                else:  # Unix/Linux
                    subprocess.run(['xdg-open', os.path.dirname(file_path)])
    
    def _copy_path(self):
        """Copy the full file path to clipboard."""
        selected_files = self.get_selected_files()
        if selected_files:
            self.clipboard_clear()
            self.clipboard_append(selected_files[0])
    
    def _copy_name(self):
        """Copy the filename to clipboard."""
        selected_files = self.get_selected_files()
        if selected_files:
            filename = selected_files[0].split('/')[-1] if '/' in selected_files[0] else selected_files[0].split('\\')[-1]
            self.clipboard_clear()
            self.clipboard_append(filename)
    
    def _select_all(self, event):
        """Select all files in the list."""
        self.listbox.selection_set(0, tk.END)
        return "break"  # Prevent default behavior
    
    def set_files(self, files: List[str]):
        """Set the list of files to display."""
        self.files = files.copy()
        self.filtered_files = files.copy()
        self._refresh_display()
    
    def get_selected_files(self) -> List[str]:
        """Get the currently selected files."""
        selected_indices = self.listbox.curselection()
        selected_files = []
        
        for index in selected_indices:
            if index < len(self.filtered_files):
                # Map back to original file list
                filename = self.listbox.get(index)
                for file_path in self.files:
                    if file_path.endswith(filename):
                        selected_files.append(file_path)
                        break
        
        return selected_files
    
    def clear_selection(self):
        """Clear the current selection."""
        self.listbox.selection_clear(0, tk.END)
    
    def select_file(self, file_path: str):
        """Select a specific file in the list."""
        filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
        for i in range(self.listbox.size()):
            if self.listbox.get(i) == filename:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break
    
    def set_on_file_selected(self, callback: Callable[[List[str]], None]):
        """Set the callback for when files are selected."""
        self.on_file_selected = callback
    
    def set_on_files_moved(self, callback: Callable[[List[str], str], None]):
        """Set the callback for when files are moved."""
        self.on_files_moved = callback
