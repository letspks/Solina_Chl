import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import matplotlib.pyplot as plt
import numpy as np
from tooltip import Tooltip
import logic
import os
import re
import tkinter as tk
from customtkinter import CTkImage

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solina Lake water monitoring system")
        self.root.geometry("1200x900")
        self.root.configure(bg="#f4f4f4")

        self.image_array = None
        self.tif_path = None
        self.current_index = ctk.IntVar(value=0)

        self.control_frame = ctk.CTkFrame(self.root, width=360, fg_color="#ffffff", corner_radius=20)
        self.control_frame.pack(side="left", fill="y", padx=25, pady=25)

        self.logo = Image.open("logo.png").convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)
        mask = Image.new("L", self.logo.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, self.logo.size[0], self.logo.size[1]), fill=255)
        self.logo.putalpha(mask)

        self.logo_photo = ImageTk.PhotoImage(self.logo)
        self.logo_label = ctk.CTkLabel(self.control_frame, image=self.logo_photo, text="", fg_color="#ffffff")
        self._pack_widget(self.logo_label, pady=(10, 20))

        self.date_label = ctk.CTkLabel(self.control_frame, text="Date of displayed image: -",
                                       font=("Segoe UI", 13, "bold"), text_color="#2e2e2e")
        self._pack_widget(self.date_label, pady=(0, 15))

        self._label("Start date:")
        self.start_date = DateEntry(self.control_frame)
        self._pack_widget(self.start_date, pady=5, fill="x")
        Tooltip(self.start_date, "Select start date.")

        self._label("End date:")
        self.end_date = DateEntry(self.control_frame)
        self._pack_widget(self.end_date, pady=5, fill="x")
        Tooltip(self.end_date, "Select end date.")

        self._label("Choose colormap:")
        self.cmap_combobox = ctk.CTkComboBox(self.control_frame, values=plt.colormaps(), font=("Segoe UI", 10))
        self.cmap_combobox.set("Spectral_r")
        self._pack_widget(self.cmap_combobox, pady=5, fill="x")
        Tooltip(self.cmap_combobox, "Colormap selection")

        self._label("Select satellite source:")
        self.source_combobox = ctk.CTkComboBox(self.control_frame, values=["Sentinel-2", "Sentinel-3"])
        self.source_combobox.set("Sentinel-2")
        self._pack_widget(self.source_combobox, pady=5, fill="x")
        Tooltip(self.source_combobox, "Choose data source (Sentinel-2 or Sentinel-3)")

        self._button("Generate map", self.process_map)

        self._label("Alert level")
        self.alert_level = ctk.DoubleVar(value=0.2)
        self.alert_entry = ctk.CTkEntry(self.control_frame)
        self._pack_widget(self.alert_entry, pady=(0, 5), fill="x")
        self.alert_slider = ctk.CTkSlider(self.control_frame, from_=0, to=1, variable=self.alert_level, command=self.update_alert_entry)
        self._pack_widget(self.alert_slider, pady=(0, 10), fill="x")
        Tooltip(self.alert_slider, "Adjust the alert threshold using this slider.")

        self.alert_entry.bind("<Return>", self.update_alert_slider)
        self.alert_entry.bind("<FocusOut>", self.update_alert_slider)

        self.show_alert_checkbox = ctk.CTkCheckBox(
            self.control_frame, text="Show Alert Level", command=self.display_map
        )
        self._pack_widget(self.show_alert_checkbox, pady=5)
        self.invert_alert = ctk.BooleanVar()
        self.invert_checkbutton = ctk.CTkCheckBox(self.control_frame, text="Invert Alert Level", variable=self.invert_alert)
        self._pack_widget(self.invert_checkbutton, pady=5)

        self._button("Load own map", self.load_map)
        self._button("Load all TIFs from folder", self.load_tif_folder)

        self._label("Time Slider:")
        self.time_slider = ctk.CTkSlider(self.control_frame, from_=0, to=1, variable=self.current_index, command=self.on_slider_change)
        self._pack_widget(self.time_slider, pady=(0, 10), fill="x")

        self._button("Download all images from 2021 till now - WARNING", lambda: logic.download_all_gee_images(self))

        self.map_container = ctk.CTkFrame(self.root, fg_color="#f4f4f4")
        self.map_container.pack(side="right", expand=True, fill="both")

        self.map_frame = ctk.CTkFrame(self.map_container, fg_color="#ffffff", corner_radius=15)
        self.map_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.map_label = ctk.CTkLabel(self.map_frame, text="", fg_color="#ffffff")
        self.map_label.pack(expand=True, fill="both")
        self.map_label.bind("<Motion>", self.update_pixel_info)

        bottom_frame = ctk.CTkFrame(self.root, fg_color="#f4f4f4")
        bottom_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self.pixel_info_label = ctk.CTkLabel(bottom_frame, text="X: -, Y: -, Value: -", font=("Segoe UI", 10), text_color="#2e2e2e")
        self.pixel_info_label.pack(side="left", padx=(0, 15))

        self.legend_canvas = tk.Canvas(bottom_frame, width=256, height=30, bg="#ffffff", highlightthickness=0)
        self.legend_canvas.pack(side="left")

        self.tif_files = []

    def _label(self, text):
        label = ctk.CTkLabel(self.control_frame, text=text, font=("Segoe UI", 10, "bold"), text_color="#2e2e2e", anchor="w")
        self._pack_widget(label, pady=(5, 0), fill="x")

    def _button(self, text, command):
        button = ctk.CTkButton(self.control_frame, text=text, command=command, corner_radius=15)
        self._pack_widget(button, pady=6, fill="x")

    def _pack_widget(self, widget, **kwargs):
        widget.pack(padx=5, **kwargs)

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

    def load_tif_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        tif_files = []
        for file in os.listdir(folder_path):
            if file.endswith(".tif") or file.endswith(".tiff"):
                match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
                if match:
                    date_str = match.group(1)
                    tif_files.append((date_str, os.path.join(folder_path, file)))

        tif_files.sort()
        self.tif_files = tif_files

        if not self.tif_files:
            messagebox.showerror("Błąd", "Nie znaleziono żadnych plików .tif w folderze.")
            return

        self.time_slider.configure(to=len(self.tif_files) - 1)

        self.current_index.set(0)
        self.tif_path = self.tif_files[0][1]
        self.display_map()

    def on_slider_change(self, value):
        index = int(float(value))
        if 0 <= index < len(self.tif_files):
            self.tif_path = self.tif_files[index][1]
            self.display_map()