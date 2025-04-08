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
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solina Lake water monitoring system")
        self.root.geometry("1200x900")
        self.root.configure(bg="#143952")

        self.image_array = None
        self.tif_path = None
        self.current_index = ctk.IntVar(value=0)

        self.control_frame = ctk.CTkFrame(self.root, width=350, fg_color="#143952")
        self.control_frame.pack(side="left", fill="y", padx=20, pady=20)

        self.logo = Image.open("logo.png").convert("RGBA").resize((120, 120), Image.Resampling.LANCZOS)
        mask = Image.new("L", self.logo.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, self.logo.size[0], self.logo.size[1]), radius=30, fill=255)
        self.logo.putalpha(mask)
        blurred_logo = self.logo.filter(ImageFilter.GaussianBlur(0.5))
        

        self.logo_photo = ImageTk.PhotoImage(blurred_logo)
        self.logo_label = ctk.CTkLabel(self.control_frame, image=self.logo_photo, text="", fg_color="#143952")


        self.logo_label.pack(pady=(0, 10))

        self.date_label = ctk.CTkLabel(self.control_frame, text="Date of displayed image: -", font=("Segoe UI", 14, "bold"), text_color="white")
        self.date_label.pack(pady=(0, 20))

        self._label("Start date:")
        self.start_date = DateEntry(self.control_frame)
        self.start_date.pack(pady=5, fill="x")
        Tooltip(self.start_date, "Select start date.")

        self._label("End date:")
        self.end_date = DateEntry(self.control_frame)
        self.end_date.pack(pady=5, fill="x")
        Tooltip(self.end_date, "Select end date.")

        self._label("Choose colormap:")
        self.cmap_combobox = ctk.CTkComboBox(self.control_frame, values=plt.colormaps(), font=("Segoe UI", 10))
        self.cmap_combobox.set("Spectral_r")
        self.cmap_combobox.pack(pady=5, fill="x")
        Tooltip(self.cmap_combobox, "Colormap selection")

        self._button("Generate map", self.process_map)

        self._label("Alert level")
        self.alert_level = ctk.DoubleVar(value=0.2)
        self.alert_entry = ctk.CTkEntry(self.control_frame)
        self.alert_entry.pack(pady=(0, 5))
        self.alert_slider = ctk.CTkSlider(self.control_frame, from_=0, to=1, variable=self.alert_level, command=self.update_alert_entry)
        self.alert_slider.pack(pady=(0, 10), fill="x")
        Tooltip(self.alert_slider, "Adjust the alert threshold using this slider.")

        self.alert_entry.bind("<Return>", self.update_alert_slider)
        self.alert_entry.bind("<FocusOut>", self.update_alert_slider)

        

        self.show_alert_checkbox = ctk.CTkCheckBox(
        self.control_frame, text="Show Alert Level", command=self.display_map
        )
        self.show_alert_checkbox.pack(pady=5)
        self.invert_alert = ctk.BooleanVar()
        self.invert_checkbutton = ctk.CTkCheckBox(self.control_frame, text="Invert Alert Level", variable=self.invert_alert)
        self.invert_checkbutton.pack(pady=5)
        self._button("Load own map", self.load_map)
        #self._button("Change colormap", self.display_map)
        self._button("Load all TIFs from folder", self.load_tif_folder)

        self._label("Time Slider:")
        self.time_slider = ctk.CTkSlider(self.control_frame, from_=0, to=1, variable=self.current_index, command=self.on_slider_change)

        self.time_slider.pack(pady=(0, 10), fill="x")

        self._button("Download all images from 2021 till now - WARNING", lambda: logic.download_all_gee_images(self))

        self.map_container = ctk.CTkFrame(self.root, fg_color="#143952")
        self.map_container.pack(side="right", expand=True, fill="both")

        self.map_frame = ctk.CTkFrame(self.map_container, fg_color="white")
        self.map_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.map_label = ctk.CTkLabel(self.map_frame, text="", fg_color="white")
        self.map_label.pack(expand=True, fill="both")
        self.map_label.bind("<Motion>", self.update_pixel_info)

        bottom_frame = ctk.CTkFrame(self.root, fg_color="#143952")
        bottom_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self.pixel_info_label = ctk.CTkLabel(bottom_frame, text="X: -, Y: -, Value: -", font=("Segoe UI", 10), text_color="white")
        self.pixel_info_label.pack(side="left", padx=(0, 15))

        self.legend_canvas = tk.Canvas(bottom_frame, width=256, height=20, bg="white", highlightthickness=0)
        self.legend_canvas.pack(side="left")

        self.tif_files = []

    def _label(self, text):
        ctk.CTkLabel(self.control_frame, text=text, font=("Segoe UI", 10, "bold"), text_color="white", anchor="w").pack(pady=(5, 0), fill="x")

    def _button(self, text, command):
        ctk.CTkButton(self.control_frame, text=text, command=command, corner_radius=10).pack(pady=5, fill="x")

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
            messagebox.showerror("B\u0142\u0105d", "Nie znaleziono \u017cadnych plik\xf3w .tif w folderze.")
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
