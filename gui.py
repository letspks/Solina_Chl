import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import numpy as np
from PIL import ImageTk, Image
from map_handler import MapHandler
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import generate_legend

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solina Lake water monitoring system")
        self.root.geometry("1200x900")

        self.image_array = None
        self.tif_path = None

        # Ustawienie panelu bocznego
        self.control_frame = tk.Frame(self.root, width=350, bg='white')
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo
        self.logo = Image.open("logo.png")
        self.logo = self.logo.resize((150, 150), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo)
        self.logo_label = tk.Label(self.control_frame, image=self.logo_photo, bg="#23272A")
        self.logo_label.pack(pady=5)

        # Elementy GUI
        self.setup_controls()

        # Mapa
        self.map_label = tk.Label(self.root)
        self.map_label.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Legenda
        self.legend_frame = tk.Frame(self.control_frame, bg='lightgray', width=330)
        self.legend_frame.pack(pady=5)
        self.legend_title = ttk.Label(self.legend_frame, text="Legend", font=("Arial", 12, "bold"))
        self.legend_title.pack()

    def setup_controls(self):
        # Funkcjonalności przycisków, suwaków, itp. tutaj
        # Dodajemy panele z elementami GUI
        pass

    def display_map(self):
        if not self.tif_path:
            return

        try:
            MapHandler(self.tif_path).process_map()
            self.update_map_image()
        except Exception as e:
            messagebox.showerror("ERROR", f"File couldn't be read: {e}")

    def update_map_image(self):
        # Zaktualizuj obraz mapy po obróbce
        pass

    def process_map(self):
        if self.tif_path:
            print(f"Generating map via model: ...")

    def apply_alert_level(self):
        pass

    def update_alert_entry(self, value):
        pass

    def update_alert_slider(self, event):
        pass

    def update_pixel_info(self, event):
        pass
