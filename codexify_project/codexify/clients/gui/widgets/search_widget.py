"""
Advanced search widget with filtering and autocomplete.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from ..styles import theme, modern_widgets

class SearchWidget(ttk.Frame):
    """Advanced search widget with real-time filtering and suggestions."""
    
    def __init__(self, parent, placeholder: str = "Search...", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.search_results: List[str] = []
        self.on_search_changed: Optional[Callable] = None
        self.on_result_selected: Optional[Callable] = None
        
        self._create_widgets()
        self._setup_bindings()
    
    def _create_widgets(self):
        """Create the search widget components."""
        # Search entry frame
        search_frame = theme.create_styled_frame(self)
        search_frame.pack(fill=tk.X)
        
        # Search icon
        search_icon = tk.Label(search_frame, text="🔍", 
                              font=("Segoe UI", 12),
                              bg=theme.COLORS['background'],
                              fg=theme.COLORS['text_secondary'])
        search_icon.pack(side=tk.LEFT, padx=(0, theme.SPACING['xs']))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = modern_widgets.create_search_entry(search_frame, self.placeholder,
                                                             textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Clear button
        self.clear_button = theme.create_styled_button(search_frame, "×", 
                                                     command=self._clear_search,
                                                     width=3)
        self.clear_button.pack(side=tk.RIGHT, padx=(theme.SPACING['sm'], 0))
        
        # Initially hide clear button
        self.clear_button.pack_forget()
        
        # Results frame (initially hidden)
        self.results_frame = theme.create_styled_frame(self)
        self.results_frame.pack(fill=tk.X, pady=(theme.SPACING['xs'], 0))
        
        # Results listbox
        self.results_listbox = theme.create_styled_listbox(self.results_frame, height=6)
        self.results_listbox.pack(fill=tk.X)
        
        # Results scrollbar
        results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, 
                                        command=self.results_listbox.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)
        
        # Initially hide results
        self.results_frame.pack_forget()
        
        # Status label
        self.status_label = theme.create_styled_label(self, "", 
                                                    foreground=theme.COLORS['text_secondary'],
                                                    font=theme.FONTS['small'])
        self.status_label.pack(anchor=tk.W, pady=(theme.SPACING['xs'], 0))
    
    def _setup_bindings(self):
        """Setup keyboard and mouse bindings."""
        # Search text changes
        self.search_var.trace('w', self._on_search_changed)
        
        # Entry focus events
        self.search_entry.bind('<FocusIn>', self._on_focus_in)
        self.search_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Keyboard navigation
        self.search_entry.bind('<Down>', self._navigate_results)
        self.search_entry.bind('<Up>', self._navigate_results)
        self.search_entry.bind('<Return>', self._select_result)
        self.search_entry.bind('<Escape>', self._hide_results)
        
        # Results selection
        self.results_listbox.bind('<<ListboxSelect>>', self._on_result_selected)
        self.results_listbox.bind('<Double-Button-1>', self._on_result_double_click)
        
        # Hide results when clicking outside
        self.bind('<Button-1>', self._on_click_outside)
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        search_term = self.search_var.get().strip()
        
        # Show/hide clear button
        if search_term and search_term != self.placeholder:
            self.clear_button.pack(side=tk.RIGHT, padx=(theme.SPACING['sm'], 0))
        else:
            self.clear_button.pack_forget()
        
        # Update results
        if search_term and search_term != self.placeholder:
            self._perform_search(search_term)
        else:
            self._hide_results()
        
        # Call callback
        if self.on_search_changed:
            self.on_search_changed(search_term)
    
    def _on_focus_in(self, event):
        """Handle search entry focus in."""
        if self.search_var.get() and self.search_var.get() != self.placeholder:
            self._show_results()
    
    def _on_focus_out(self, event):
        """Handle search entry focus out."""
        # Delay hiding to allow for result selection
        self.after(200, self._check_focus)
    
    def _check_focus(self):
        """Check if focus is still within the search widget."""
        focused_widget = self.focus_get()
        if not (focused_widget == self.search_entry or 
                focused_widget == self.results_listbox):
            self._hide_results()
    
    def _perform_search(self, search_term: str):
        """Perform the search operation."""
        # This would typically search through available data
        # For now, we'll simulate results
        if hasattr(self, '_search_data'):
            results = [item for item in self._search_data 
                      if search_term.lower() in item.lower()]
        else:
            results = []
        
        self._update_results(results)
        self._show_results()
    
    def _update_results(self, results: List[str]):
        """Update the search results display."""
        self.search_results = results
        
        # Clear current results
        self.results_listbox.delete(0, tk.END)
        
        # Add new results
        for result in results[:20]:  # Limit to 20 results
            self.results_listbox.insert(tk.END, result)
        
        # Update status
        if results:
            if len(results) > 20:
                self.status_label.config(text=f"Showing 20 of {len(results)} results")
            else:
                self.status_label.config(text=f"{len(results)} result(s)")
        else:
            self.status_label.config(text="No results found")
    
    def _show_results(self):
        """Show the results frame."""
        if self.search_results:
            self.results_frame.pack(fill=tk.X, pady=(theme.SPACING['xs'], 0))
            self.status_label.pack(anchor=tk.W, pady=(theme.SPACING['xs'], 0))
    
    def _hide_results(self):
        """Hide the results frame."""
        self.results_frame.pack_forget()
        self.status_label.pack_forget()
    
    def _navigate_results(self, event):
        """Navigate through results with arrow keys."""
        if not self.search_results:
            return
        
        current_selection = self.results_listbox.curselection()
        
        if event.keysym == 'Down':
            if not current_selection:
                self.results_listbox.selection_set(0)
            elif current_selection[0] < len(self.search_results) - 1:
                self.results_listbox.selection_clear(0, tk.END)
                self.results_listbox.selection_set(current_selection[0] + 1)
                self.results_listbox.see(current_selection[0] + 1)
        
        elif event.keysym == 'Up':
            if current_selection and current_selection[0] > 0:
                self.results_listbox.selection_clear(0, tk.END)
                self.results_listbox.selection_set(current_selection[0] - 1)
                self.results_listbox.see(current_selection[0] - 1)
        
        return "break"
    
    def _select_result(self, event):
        """Select the currently highlighted result."""
        current_selection = self.results_listbox.curselection()
        if current_selection:
            selected_result = self.search_results[current_selection[0]]
            self._on_result_selected(selected_result)
    
    def _on_result_selected(self, event):
        """Handle result selection from listbox."""
        current_selection = self.results_listbox.curselection()
        if current_selection:
            selected_result = self.search_results[current_selection[0]]
            if self.on_result_selected:
                self.on_result_selected(selected_result)
    
    def _on_result_double_click(self, event):
        """Handle double-click on result."""
        current_selection = self.results_listbox.curselection()
        if current_selection:
            selected_result = self.search_results[current_selection[0]]
            if self.on_result_selected:
                self.on_result_selected(selected_result)
    
    def _on_click_outside(self, event):
        """Handle clicks outside the search widget."""
        # This is a simple implementation - could be improved
        pass
    
    def _clear_search(self):
        """Clear the search field."""
        self.search_var.set("")
        self.search_entry.focus()
        self._hide_results()
    
    def set_search_data(self, data: List[str]):
        """Set the data to search through."""
        self._search_data = data
    
    def set_on_search_changed(self, callback: Callable[[str], None]):
        """Set the callback for when search text changes."""
        self.on_search_changed = callback
    
    def set_on_result_selected(self, callback: Callable[[str], None]):
        """Set the callback for when a result is selected."""
        self.on_result_selected = callback
    
    def get_search_term(self) -> str:
        """Get the current search term."""
        term = self.search_var.get()
        if term == self.placeholder:
            return ""
        return term.strip()
    
    def set_search_term(self, term: str):
        """Set the search term programmatically."""
        self.search_var.set(term)
    
    def focus_search(self):
        """Focus the search entry."""
        self.search_entry.focus()
        self.search_entry.select_range(0, tk.END)
