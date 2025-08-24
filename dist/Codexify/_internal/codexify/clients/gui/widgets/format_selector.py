"""
Enhanced format selector widget with better UX.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Set, Optional
from ..styles import theme, modern_widgets

class FormatSelector(ttk.Frame):
    """Enhanced format selector with search, categories, and better organization."""
    
    def __init__(self, parent, title: str = "File Formats", **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.selected_formats: Set[str] = set()
        self.on_formats_changed: Optional[Callable] = None
        
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
        # Main frame
        main_frame = theme.create_styled_frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = theme.create_styled_frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        # Title
        title_label = theme.create_styled_label(header_frame, self.title,
                                              font=theme.FONTS['subheading'])
        title_label.pack(side=tk.LEFT)
        
        # Format count
        self.count_label = theme.create_styled_label(header_frame, "0 formats selected",
                                                   foreground=theme.COLORS['text_secondary'],
                                                   font=theme.FONTS['small'])
        self.count_label.pack(side=tk.RIGHT)
        
        # Search frame
        search_frame = theme.create_styled_frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, theme.SPACING['sm']))
        
        # Search widget
        from .search_widget import SearchWidget
        self.search_widget = SearchWidget(search_frame, "Search formats...")
        self.search_widget.pack(fill=tk.X)
        
        # Categories frame
        categories_frame = theme.create_styled_frame(main_frame)
        categories_frame.pack(fill=tk.BOTH, expand=True)
        categories_frame.grid_columnconfigure(0, weight=1)
        categories_frame.grid_columnconfigure(1, weight=1)
        
        # Left column - categories
        left_frame = theme.create_styled_frame(categories_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACING['sm']))
        
        # Categories label
        cat_label = theme.create_styled_label(left_frame, "Categories",
                                            font=theme.FONTS['body'],
                                            foreground=theme.COLORS['text_secondary'])
        cat_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        # Categories listbox
        self.categories_listbox = theme.create_styled_listbox(left_frame, height=8)
        self.categories_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Categories scrollbar
        cat_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, 
                                     command=self.categories_listbox.yview)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.categories_listbox.config(yscrollcommand=cat_scrollbar.set)
        
        # Right column - formats
        right_frame = theme.create_styled_frame(categories_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(theme.SPACING['sm'], 0))
        
        # Formats label
        fmt_label = theme.create_styled_label(right_frame, "Formats",
                                            font=theme.FONTS['body'],
                                            foreground=theme.COLORS['text_secondary'])
        fmt_label.pack(anchor=tk.W, pady=(0, theme.SPACING['xs']))
        
        # Formats frame
        formats_frame = theme.create_styled_frame(right_frame)
        formats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formats canvas and scrollbar
        self.formats_canvas = tk.Canvas(formats_frame, 
                                       bg=theme.COLORS['surface'],
                                       highlightthickness=0)
        formats_scrollbar = ttk.Scrollbar(formats_frame, orient=tk.VERTICAL, 
                                        command=self.formats_canvas.yview)
        
        self.formats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        formats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.formats_canvas.config(yscrollcommand=formats_scrollbar.set)
        
        # Formats content frame
        self.formats_content = theme.create_styled_frame(self.formats_canvas)
        self.formats_canvas.create_window((0, 0), window=self.formats_content, anchor="nw")
        
        # Bottom controls
        controls_frame = theme.create_styled_frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(theme.SPACING['sm'], 0))
        
        # Select all button
        select_all_btn = theme.create_styled_button(controls_frame, "Select All",
                                                  command=self._select_all_formats)
        select_all_btn.pack(side=tk.LEFT, padx=(0, theme.SPACING['sm']))
        
        # Clear all button
        clear_all_btn = theme.create_styled_button(controls_frame, "Clear All",
                                                 command=self._clear_all_formats)
        clear_all_btn.pack(side=tk.LEFT)
        
        # Custom format frame
        custom_frame = theme.create_styled_frame(controls_frame)
        custom_frame.pack(side=tk.RIGHT)
        
        # Custom format entry
        ttk.Label(custom_frame, text="Custom:").pack(side=tk.LEFT)
        self.custom_entry = theme.create_styled_entry(custom_frame, width=15)
        self.custom_entry.pack(side=tk.LEFT, padx=theme.SPACING['xs'])
        
        # Add custom format button
        add_btn = theme.create_styled_button(custom_frame, "Add",
                                           command=self._add_custom_format)
        add_btn.pack(side=tk.LEFT, padx=(theme.SPACING['xs'], 0))
        
        # Populate categories
        self._populate_categories()
        
        # Set search data
        all_formats = []
        for formats in self.format_categories.values():
            all_formats.extend(formats)
        self.search_widget.set_search_data(all_formats)
    
    def _setup_bindings(self):
        """Setup widget bindings."""
        # Category selection
        self.categories_listbox.bind('<<ListboxSelect>>', self._on_category_selected)
        
        # Search result selection
        self.search_widget.set_on_result_selected(self._on_search_result_selected)
        
        # Canvas scrolling
        self.formats_content.bind('<Configure>', self._on_canvas_configure)
        
        # Custom format entry
        self.custom_entry.bind('<Return>', lambda e: self._add_custom_format())
    
    def _populate_categories(self):
        """Populate the categories listbox."""
        for category in sorted(self.format_categories.keys()):
            self.categories_listbox.insert(tk.END, category)
    
    def _on_category_selected(self, event):
        """Handle category selection."""
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self._show_category_formats(category)
    
    def _show_category_formats(self, category: str):
        """Show formats for the selected category."""
        # Clear existing formats
        for widget in self.formats_content.winfo_children():
            widget.destroy()
        
        if category in self.format_categories:
            formats = self.format_categories[category]
            
            # Create format checkboxes
            for i, fmt in enumerate(sorted(formats)):
                var = tk.BooleanVar(value=fmt in self.selected_formats)
                var.trace('w', lambda *args, f=fmt, v=var: self._on_format_toggled(f, v))
                
                cb = theme.create_styled_checkbutton(self.formats_content, fmt, var)
                cb.grid(row=i//2, column=i%2, sticky="w", padx=theme.SPACING['xs'], 
                       pady=theme.SPACING['xs'])
    
    def _on_format_toggled(self, format_name: str, var: tk.BooleanVar):
        """Handle format checkbox toggle."""
        if var.get():
            self.selected_formats.add(format_name)
        else:
            self.selected_formats.discard(format_name)
        
        self._update_count()
        self._notify_change()
    
    def _on_search_result_selected(self, result: str):
        """Handle search result selection."""
        # Find the category for this format
        for category, formats in self.format_categories.items():
            if result in formats:
                # Select the category
                for i in range(self.categories_listbox.size()):
                    if self.categories_listbox.get(i) == category:
                        self.categories_listbox.selection_clear(0, tk.END)
                        self.categories_listbox.selection_set(i)
                        self.categories_listbox.see(i)
                        self._show_category_formats(category)
                        break
                break
    
    def _on_canvas_configure(self, event):
        """Handle canvas configuration changes."""
        self.formats_canvas.configure(scrollregion=self.formats_canvas.bbox("all"))
    
    def _select_all_formats(self):
        """Select all formats in the current category."""
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            if category in self.format_categories:
                formats = self.format_categories[category]
                for fmt in formats:
                    self.selected_formats.add(fmt)
                
                self._show_category_formats(category)  # Refresh display
                self._update_count()
                self._notify_change()
    
    def _clear_all_formats(self):
        """Clear all selected formats."""
        self.selected_formats.clear()
        self._update_count()
        self._notify_change()
        
        # Refresh current category display
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self._show_category_formats(category)
    
    def _add_custom_format(self):
        """Add a custom format."""
        custom_format = self.custom_entry.get().strip()
        if custom_format:
            if not custom_format.startswith('.'):
                custom_format = '.' + custom_format
            
            # Add to custom formats category
            if 'Custom' not in self.format_categories:
                self.format_categories['Custom'] = []
            
            if custom_format not in self.format_categories['Custom']:
                self.format_categories['Custom'].append(custom_format)
                
                # Refresh categories list
                self.categories_listbox.delete(0, tk.END)
                self._populate_categories()
                
                # Select custom category
                for i in range(self.categories_listbox.size()):
                    if self.categories_listbox.get(i) == 'Custom':
                        self.categories_listbox.selection_clear(0, tk.END)
                        self.categories_listbox.selection_set(i)
                        self.categories_listbox.see(i)
                        self._show_category_formats('Custom')
                        break
            
            self.custom_entry.delete(0, tk.END)
    
    def _update_count(self):
        """Update the format count display."""
        count = len(self.selected_formats)
        if count == 1:
            self.count_label.config(text="1 format selected")
        else:
            self.count_label.config(text=f"{count} formats selected")
    
    def _notify_change(self):
        """Notify listeners of format changes."""
        if self.on_formats_changed:
            self.on_formats_changed(list(self.selected_formats))
    
    def get_selected_formats(self) -> List[str]:
        """Get the list of selected formats."""
        return list(self.selected_formats)
    
    def set_selected_formats(self, formats: List[str]):
        """Set the selected formats."""
        self.selected_formats = set(formats)
        self._update_count()
        
        # Refresh current category display
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self._show_category_formats(category)
    
    def set_on_formats_changed(self, callback: Callable[[List[str]], None]):
        """Set the callback for when formats change."""
        self.on_formats_changed = callback
    
    def clear_selection(self):
        """Clear the current selection."""
        self.selected_formats.clear()
        self._update_count()
        self._notify_change()
        
        # Refresh display
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self._show_category_formats(category)
