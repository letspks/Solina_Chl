import tkinter as tk

class Tooltip:
    def __init__(self, widget, text, delay=1):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.tooltip_id = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        self.tooltip_id = self.widget.after(int(self.delay * 500), self.create_tooltip, event)

    def create_tooltip(self, event):
        x = event.x_root + 15
        y = event.y_root + 15
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="black", foreground="white", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None
