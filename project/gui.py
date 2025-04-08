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

        self.date_label = tk.Label(self.control_frame, text="Date of displayed image: -", font=("Arial", 12, "bold"), bg="white")
        self.date_label.pack(side=tk.TOP, pady=(5, 0))

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

        # Kontener po prawej stronie — mapa
        self.map_container = tk.Frame(self.root, bg="#cccccc")  # duży kontener
        self.map_container.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Ramka na mapę wewnątrz kontenera — ma ramkę i jest wyśrodkowana
        self.map_frame = tk.Frame(self.map_container, bg="#cccccc", bd=1, relief="solid")
        self.map_frame.place(relx=0.5, rely=0.5, anchor="center")  # wyśrodkowanie

        # Label z obrazem
        self.map_label = tk.Label(self.map_frame, bg="#cccccc")
        self.map_label.pack()


        self.map_label.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Legenda (gradient colormap)
        self.legend_label = tk.Label(self.control_frame, text="Colormap Legend:")
        self.legend_label.pack(pady=(5, 2))

        self.legend_canvas = tk.Canvas(self.control_frame, width=256, height=58, bg="white", highlightthickness=0, highlightbackground="gray")
        self.legend_canvas.pack(pady=(0, 15))

        




        self.pixel_info_label = tk.Label(self.root, text="X: -, Y: -, Value: -", font=("Arial", 10), bg="white")
        self.pixel_info_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        self.map_label.bind("<Motion>", self.update_pixel_info)

        self.tif_files = []  # lista ścieżek do plików
        self.current_index = tk.IntVar(value=0)

        self.slider_label = tk.Label(self.control_frame, text="Time Slider:")
        self.slider_label.pack(pady=5)

        self.time_slider = tk.Scale(self.control_frame, from_=0, to=0, orient=tk.HORIZONTAL,
                                    variable=self.current_index, command=self.on_slider_change, length=300)
        self.time_slider.pack(pady=5)

        self.load_folder_button = tk.Button(self.control_frame, text="Load all TIFs from folder", command=self.load_tif_folder)
        self.load_folder_button.pack(pady=5)


        self.download_all_button = tk.Button(self.control_frame, text="Download all images from 2021 till now - WARNING", command=lambda: logic.download_all_gee_images(self))
        self.download_all_button.pack(pady=5)


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

        import os
        import re

        tif_files = []
        for file in os.listdir(folder_path):
            if file.endswith(".tif") or file.endswith(".tiff"):
                match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
                if match:
                    date_str = match.group(1)
                    tif_files.append((date_str, os.path.join(folder_path, file)))

        tif_files.sort()  # sortuj wg daty
        self.tif_files = tif_files  # <--- zachowujemy datę i ścieżkę!

        if not self.tif_files:
            messagebox.showerror("Błąd", "Nie znaleziono żadnych plików .tif w folderze.")
            return

        self.time_slider.config(to=len(self.tif_files) - 1)
        self.current_index.set(0)
        self.tif_path = self.tif_files[0][1]  # tylko ścieżka
        self.display_map()


    def on_slider_change(self, value):
        index = int(value)
        if 0 <= index < len(self.tif_files):
            self.tif_path = self.tif_files[index][1]  # tylko ścieżka
            self.display_map()

