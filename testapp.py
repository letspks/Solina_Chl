import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import rasterio
import numpy as np
import folium
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt
import matplotlib.cm
from matplotlib.colors import Normalize
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Map Viewer")
        self.root.geometry("1200x900")
        
        self.image_array = None  # var to store tif data
        self.tif_path = None  # Path to tiff that we provide

        # side panel
        self.control_frame = tk.Frame(self.root, width=350, bg='lightgray')
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # date
        tk.Label(self.control_frame, text="Data początkowa:").pack(pady=5)
        self.start_date = DateEntry(self.control_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date.pack(pady=5)
        tk.Label(self.control_frame, text="Data końcowa:").pack(pady=5)
        self.end_date = DateEntry(self.control_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date.pack(pady=5)
        
        # model
        tk.Label(self.control_frame, text="Wybierz model:").pack(pady=5)
        self.model_combobox = ttk.Combobox(self.control_frame, values=["Model A", "Model B", "Model C"])
        self.model_combobox.pack(pady=5)
        
        # colormap selection pane
        tk.Label(self.control_frame, text="Wybierz colormap:").pack(pady=5)
        self.cmap_combobox = ttk.Combobox(self.control_frame, values=plt.colormaps(), state="readonly")
        self.cmap_combobox.set("viridis")  # Domyślna wartość
        self.cmap_combobox.pack(pady=5)
        
        # calculate
        self.calculate_button = tk.Button(self.control_frame, text="Oblicz mapę", command=self.process_map)
        self.calculate_button.pack(pady=10)
        
        # read file
        self.load_button = tk.Button(self.control_frame, text="Wczytaj mapę", command=self.load_map)
        self.load_button.pack(pady=10)
        
        # change cmap
        self.change_cmap_button = tk.Button(self.control_frame, text="Zmień colormap", command=self.display_map)
        self.change_cmap_button.pack(pady=10)
        
        # mape frame
        self.map_label = tk.Label(self.root)
        self.map_label.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # legend frame
        self.legend_frame = tk.Frame(self.control_frame, bg='lightgray', width=330)
        self.legend_frame.pack(pady=10)

    def generate_legend(self):
        """Generowanie legendy na podstawie rzeczywistych wartości z pliku TIFF"""
        if self.image_array is None:
            return 

        cmap_name = self.cmap_combobox.get()
        cmap = plt.get_cmap(cmap_name)
        norm = Normalize(vmin=np.min(self.image_array), vmax=np.max(self.image_array))
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        # legend fig
        fig, ax = plt.subplots(figsize=(2, 8))
        fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
        cbar = fig.colorbar(sm, cax=ax)
        cbar.set_label("Wartości")

        # fig to tink img conversion
        canvas = FigureCanvasTkAgg(fig, master=self.legend_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF Files", "*.tif;*.tiff")])
        if file_path:
            self.tif_path = file_path
            self.display_map()

    def display_map(self):
        if not self.tif_path:
            return

        try:
            with rasterio.open(self.tif_path) as dataset:
                self.image_array = dataset.read(1)  # first chanel
                if np.isnan(self.image_array).all():
                    messagebox.showerror("Błąd", "Plik TIFF zawiera tylko wartości NaN!")
                    return
                
                self.image_array = np.nan_to_num(self.image_array)  
                cmap_name = self.cmap_combobox.get()
                cmap = plt.get_cmap(cmap_name)  # colormap
                colored_image = cmap((self.image_array - np.min(self.image_array)) / (np.max(self.image_array) - np.min(self.image_array)))[:, :, :3]  # Normalizacja i zastosowanie colormap
                colored_image = (colored_image * 255).astype(np.uint8)
                img = Image.fromarray(colored_image)
                img.thumbnail((900, 900))
                
                self.map_photo = ImageTk.PhotoImage(img)
                self.map_label.config(image=self.map_photo)

                # real data legend
                for widget in self.legend_frame.winfo_children():
                    widget.destroy()  # delete old legend
                self.generate_legend()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać pliku: {e}")

    def process_map(self):
        if self.tif_path:
            print(f"Obliczanie mapy dla modelu: {self.model_combobox.get()} i zakresu dat: {self.start_date.get()} - {self.end_date.get()} z colormapą: {self.cmap_combobox.get()}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
