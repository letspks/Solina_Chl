import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
from tooltip import Tooltip
import logic

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solina Lake water monitoring system")
        self.root.geometry("1200x900")

        self.image_array = None
        self.tif_path = None

        self.control_frame = tk.Frame(self.root, width=350, bg='white')
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.logo = Image.open("logo.png")
        self.logo = self.logo.resize((150, 150), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo)
        self.logo_label = tk.Label(self.control_frame, image=self.logo_photo, bg="#23272A")
        self.logo_label.pack(pady=5)

        tk.Label(self.control_frame, text="Start date:").pack(pady=5)
        self.start_date = DateEntry(self.control_frame)
        self.start_date.pack(pady=5)
        Tooltip(self.start_date, "Select start date.")

        tk.Label(self.control_frame, text="End date:").pack(pady=5)
        self.end_date = DateEntry(self.control_frame)
        self.end_date.pack(pady=5)
        Tooltip(self.end_date, "Select end date.")

        tk.Label(self.control_frame, text="Select model (temporary):").pack(pady=5)
        self.model_combobox = ttk.Combobox(self.control_frame, values=["Model A", "Model B", "Model C"])
        self.model_combobox.pack(pady=5)
        Tooltip(self.model_combobox, "Model selection.")

        tk.Label(self.control_frame, text="Choose colormap:").pack(pady=5)
        self.cmap_combobox = ttk.Combobox(self.control_frame, values=plt.colormaps(), state="readonly")
        self.cmap_combobox.set("Spectral_r")
        self.cmap_combobox.pack(pady=5)
        Tooltip(self.cmap_combobox, "Colormap selection")

        self.alert_level = tk.DoubleVar(value=0.2)
        self.alert_entry = ttk.Entry(self.control_frame, width=7)
        self.alert_entry.pack(pady=5)

        self.alert_slider = tk.Scale(self.control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                                     variable=self.alert_level, command=self.update_alert_entry)
        self.alert_slider.pack(pady=5, fill="x")
        Tooltip(self.alert_slider, "Adjust the alert threshold using this slider.")

        self.alert_entry.bind("<Return>", self.update_alert_slider)
        self.alert_entry.bind("<FocusOut>", self.update_alert_slider)

        self.invert_alert = tk.BooleanVar()
        self.invert_checkbutton = tk.Checkbutton(self.control_frame, text="Invert Alert Level", variable=self.invert_alert)
        self.invert_checkbutton.pack(pady=5)

        self.alert_button = tk.Button(self.control_frame, text="Show Alert Level", command=self.apply_alert_level)
        self.alert_button.pack(pady=5)
        Tooltip(self.alert_button, "Shows pixels with alert.")

        self.calculate_button = tk.Button(self.control_frame, text="Generate map", command=self.process_map)
        self.calculate_button.pack(pady=5)
        Tooltip(self.calculate_button, "Calculates map with desired data.")

        self.load_button = tk.Button(self.control_frame, text="Load own map", command=self.load_map)
        self.load_button.pack(pady=5)
        Tooltip(self.load_button, "Loads selected file.")

        self.change_cmap_button = tk.Button(self.control_frame, text="Change colormap", command=self.display_map)
        self.change_cmap_button.pack(pady=5)
        Tooltip(self.change_cmap_button, "Changes colormap to selected.")

        self.map_label = tk.Label(self.root)
        self.map_label.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.pixel_info_label = tk.Label(self.root, text="X: -, Y: -, Value: -", font=("Arial", 10), bg="white")
        self.pixel_info_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        self.map_label.bind("<Motion>", self.update_pixel_info)

    def apply_alert_level(self):
        logic.apply_alert_level(self)

    def update_alert_entry(self, value):
        logic.update_alert_entry(self, value)

    def update_alert_slider(self, event):
        logic.update_alert_slider(self, event)

    def update_pixel_info(self, event):
        logic.update_pixel_info(self, event)

    def load_map(self):
        logic.load_map(self)

    def display_map(self):
        logic.display_map(self)

    def process_map(self):
        logic.download_gee_image(self)