from tkinter import ttk

# Entry widget with a placeholder
class PlaceholderEntry(ttk.Entry):
    def __init__(self, container, placeholder, *args, **kwargs):
        super().__init__(container, *args, style='Placeholder.TEntry', **kwargs)
        self.placeholder = placeholder
        self.insert('0', self.placeholder)
        self.bind('<FocusIn>', self.clear_placeholder)
        self.bind('<FocusOut>', self.add_placeholder)
        
    def clear_placeholder(self, e):
        if self['style'] == 'Placeholder.TEntry':
            self.delete('0', 'end')
            self['style'] = 'TEntry'

    def add_placeholder(self, e):
        if not self.get():
            self.insert('0', self.placeholder)
            self['style'] = 'Placeholder.TEntry'

# Combobox widget with a placeholder
class PlaceholderCombobox(ttk.Combobox):
    def __init__(self, container, placeholder, *args, **kwargs):
        super().__init__(container, *args, style='Placeholder.TCombobox', **kwargs)
        self.placeholder = placeholder
        self.insert('0', self.placeholder)
        self.bind('<FocusIn>', self.clear_placeholder)
        self.bind('<FocusOut>', self.add_placeholder)

    def clear_placeholder(self, e):
        self['style'] = 'TCombobox'
        if self.get() == self.placeholder:
            self.delete('0', 'end')
        else:
            self['style'] = 'TCombobox'

    def add_placeholder(self, e):
        if not self.get():
            self.insert('0', self.placeholder)
            self['style'] = 'Placeholder.TCombobox'