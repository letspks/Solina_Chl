import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

import sys
sys.path.append("C:\Users\Piotrek\Desktop\studia\SPACE TECHNOLOGIES\RSAIAIST - Remote Sensing and Image Analysis in Space Tech\Solina")

from utils import generate_legend

class MapHandler:
    def __init__(self, tif_path):
        self.tif_path = tif_path
        self.image_array = None

    def process_map(self):
        try:
            with rasterio.open(self.tif_path) as dataset:
                self.image_array = dataset.read(1)  # first channel

                if np.isnan(self.image_array).all():
                    raise ValueError("TIFF file contains only NaN values!")

                self.image_array = np.nan_to_num(self.image_array)

                cmap = plt.get_cmap("Spectral_r")
                colored_image = cmap((self.image_array - np.min(self.image_array)) / (np.max(self.image_array) - np.min(self.image_array)))[:, :, :3]
                colored_image = (colored_image * 255).astype(np.uint8)

                return colored_image
        except Exception as e:
            messagebox.showerror("ERROR", f"Error while processing map: {e}")
            return None
