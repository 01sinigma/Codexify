"""
Modern styling and theming for Codexify GUI.
Provides consistent colors, fonts, and visual elements.
"""

import tkinter as tk
from tkinter import ttk
import platform

class CodexifyTheme:
    """Modern theme configuration for Codexify GUI."""
    
    # Color palette
    COLORS = {
        'primary': '#2563eb',      # Blue
        'primary_hover': '#1d4ed8', # Darker blue
        'secondary': '#64748b',    # Slate
        'accent': '#10b981',       # Green
        'accent_hover': '#059669', # Darker green
        'warning': '#f59e0b',      # Amber
        'error': '#ef4444',        # Red
        'success': '#22c55e',      # Green
        'background': '#ffffff',   # White
        'surface': '#f8fafc',      # Light gray
        'border': '#e2e8f0',      # Border gray
        'text_primary': '#1e293b', # Dark text
        'text_secondary': '#64748b', # Secondary text
        'text_muted': '#94a3b8',   # Muted text
        'shadow': '#00000010',     # Subtle shadow
    }
    
    # Font configurations
    FONTS = {
        'heading': ('Segoe UI', 16, 'bold'),
        'subheading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'monospace': ('Consolas', 9),
        'small': ('Segoe UI', 9),
    }
    
    # Spacing and sizing
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'xxl': 32,
    }
    
    # Border radius
    BORDER_RADIUS = 8
    
    @classmethod
    def apply_theme(cls, root):
        """Apply the modern theme to the root window."""
        style = ttk.Style()
        
        # Configure common styles
        style.configure('Codexify.TFrame', background=cls.COLORS['background'])
        style.configure('Codexify.TLabel', 
                       background=cls.COLORS['background'],
                       foreground=cls.COLORS['text_primary'],
                       font=cls.FONTS['body'])
        
        # Button styles
        style.configure('Codexify.TButton',
                       background=cls.COLORS['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=cls.FONTS['body'])
        
        style.map('Codexify.TButton',
                 background=[('active', cls.COLORS['primary_hover']),
                           ('pressed', cls.COLORS['primary_hover'])])
        
        # Accent button style
        style.configure('Codexify.Accent.TButton',
                       background=cls.COLORS['accent'],
                       foreground='white')
        
        style.map('Codexify.Accent.TButton',
                 background=[('active', cls.COLORS['accent_hover']),
                           ('pressed', cls.COLORS['accent_hover'])])
        
        # Entry style
        style.configure('Codexify.TEntry',
                       fieldbackground=cls.COLORS['surface'],
                       borderwidth=1,
                       relief='solid',
                       font=cls.FONTS['body'],
                       foreground=cls.COLORS['text_primary'])

        # Placeholder style for Entry
        style.configure('Placeholder.TEntry',
                       fieldbackground=cls.COLORS['surface'],
                       borderwidth=1,
                       relief='solid',
                       font=cls.FONTS['body'],
                       foreground=cls.COLORS['text_muted'])
        
        # Combobox style
        style.configure('Codexify.TCombobox',
                       fieldbackground=cls.COLORS['surface'],
                       borderwidth=1,
                       relief='solid',
                       font=cls.FONTS['body'])
        
        # Listbox style
        style.configure('Codexify.TListbox',
                       background=cls.COLORS['surface'],
                       foreground=cls.COLORS['text_primary'],
                       selectbackground=cls.COLORS['primary'],
                       selectforeground='white',
                       font=cls.FONTS['body'])
        
        # Checkbutton style
        style.configure('Codexify.TCheckbutton',
                       background=cls.COLORS['background'],
                       foreground=cls.COLORS['text_primary'],
                       font=cls.FONTS['body'])
        
        # LabelFrame style
        style.configure('Codexify.TLabelframe',
                       background=cls.COLORS['background'],
                       foreground=cls.COLORS['text_primary'],
                       font=cls.FONTS['subheading'])
        
        style.configure('Codexify.TLabelframe.Label',
                       background=cls.COLORS['background'],
                       foreground=cls.COLORS['primary'],
                       font=cls.FONTS['subheading'])
        
        # Progress bar style
        style.configure('Codexify.Horizontal.TProgressbar',
                       background=cls.COLORS['primary'],
                       troughcolor=cls.COLORS['surface'],
                       borderwidth=0,
                       lightcolor=cls.COLORS['primary'],
                       darkcolor=cls.COLORS['primary'])
 
        # Paned window sash style
        style.configure('Codexify.Sash', sashrelief='solid', sashwidth=4, background=cls.COLORS['border'])
        
        # Apply theme to root
        root.configure(bg=cls.COLORS['background'])
        
        # Set system-specific configurations
        if platform.system() == 'Windows':
            root.option_add('*TFrame*background', cls.COLORS['background'])
            root.option_add('*TLabel*background', cls.COLORS['background'])
            root.option_add('*TButton*background', cls.COLORS['primary'])
            root.option_add('*TButton*foreground', 'white')
    
    @classmethod
    def create_styled_frame(cls, parent, **kwargs):
        """Create a styled frame with consistent spacing."""
        frame = ttk.Frame(parent, style='Codexify.TFrame', **kwargs)
        return frame
    
    @classmethod
    def create_styled_button(cls, parent, text, command=None, style='Codexify.TButton', **kwargs):
        """Create a styled button."""
        button = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
        return button
    
    @classmethod
    def create_styled_entry(cls, parent, **kwargs):
        """Create a styled entry widget."""
        entry = ttk.Entry(parent, style='Codexify.TEntry', **kwargs)
        return entry
    
    @classmethod
    def create_styled_listbox(cls, parent, **kwargs):
        """Create a styled listbox widget."""
        listbox = tk.Listbox(parent, 
                            bg=cls.COLORS['surface'],
                            fg=cls.COLORS['text_primary'],
                            selectbackground=cls.COLORS['primary'],
                            selectforeground='white',
                            font=cls.FONTS['body'],
                            relief='solid',
                            borderwidth=1,
                            **kwargs)
        return listbox
    
    @classmethod
    def create_styled_label(cls, parent, text, style='Codexify.TLabel', **kwargs):
        """Create a styled label."""
        label = ttk.Label(parent, text=text, style=style, **kwargs)
        return label
    
    @classmethod
    def create_styled_checkbutton(cls, parent, text, variable, **kwargs):
        """Create a styled checkbutton."""
        checkbutton = ttk.Checkbutton(parent, text=text, variable=variable, 
                                    style='Codexify.TCheckbutton', **kwargs)
        return checkbutton
    
    @classmethod
    def create_styled_labelframe(cls, parent, text, **kwargs):
        """Create a styled labelframe."""
        labelframe = ttk.LabelFrame(parent, text=text, style='Codexify.TLabelframe', **kwargs)
        return labelframe
    
    @classmethod
    def create_styled_progressbar(cls, parent, **kwargs):
        """Create a styled progress bar."""
        progressbar = ttk.Progressbar(parent, style='Codexify.Horizontal.TProgressbar', **kwargs)
        return progressbar


class ModernWidgets:
    """Modern widget implementations with enhanced functionality."""
    
    @staticmethod
    def create_tooltip(widget, text):
        """Create a tooltip for a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, 
                           background=CodexifyTheme.COLORS['text_primary'],
                           foreground='white',
                           relief='solid',
                           borderwidth=1,
                           font=CodexifyTheme.FONTS['small'])
            label.pack()
            
            def hide_tooltip(event):
                tooltip.destroy()
            
            widget.bind('<Leave>', hide_tooltip)
            tooltip.bind('<Leave>', hide_tooltip)
        
        widget.bind('<Enter>', show_tooltip)
    
    @staticmethod
    def create_animated_button(parent, text, command=None, **kwargs):
        """Create a button with hover animation."""
        button = CodexifyTheme.create_styled_button(parent, text, command, **kwargs)
        
        def on_enter(event):
            button.configure(style='Codexify.TButton')
        
        def on_leave(event):
            button.configure(style='Codexify.TButton')
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
        
        return button
    
    @staticmethod
    def create_icon_button(parent, text, icon, command=None, style='Codexify.TButton', **kwargs):
        """Create a button with an icon and text."""
        button = ttk.Button(parent, text=text, image=icon, compound=tk.LEFT, command=command, style=style, **kwargs)
        return button
    
    @staticmethod
    def create_search_entry(parent, placeholder="Search...", **kwargs):
        """Create a search entry with placeholder text."""
        entry = CodexifyTheme.create_styled_entry(parent, **kwargs)
        
        # Placeholder functionality
        entry.insert(0, placeholder)
        entry.configure(style='Placeholder.TEntry')
        
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.configure(style='Codexify.TEntry')
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.configure(style='Placeholder.TEntry')
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        return entry


# Global theme instance
theme = CodexifyTheme()
modern_widgets = ModernWidgets()
