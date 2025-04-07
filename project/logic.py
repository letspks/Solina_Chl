import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import rasterio
import time
import ee
import geemap

def apply_alert_level(app):
    if app.image_array is None:
        return

    alert_value = app.alert_level.get()
    invert = app.invert_alert.get()
    grayscale_cmap = plt.get_cmap(app.cmap_combobox.get())
    norm_array = (app.image_array - np.min(app.image_array)) / (np.max(app.image_array) - np.min(app.image_array))

    if invert:
        alert_mask = app.image_array < alert_value
    else:
        alert_mask = app.image_array > alert_value

    grayscale_image = grayscale_cmap(norm_array)[:, :, :3]
    alert_image = np.copy(grayscale_image)
    alert_image[alert_mask] = [1, 0, 0]
    alert_image = (alert_image * 255).astype(np.uint8)
    img = Image.fromarray(alert_image)
    img.thumbnail((900, 900))
    app.map_photo = ImageTk.PhotoImage(img)
    app.map_label.config(image=app.map_photo)

def update_alert_entry(app, value):
    app.alert_entry.delete(0, tk.END)
    app.alert_entry.insert(0, f"{float(value):.2f}")

def update_alert_slider(app, event):
    try:
        value_str = app.alert_entry.get().strip()
        if not value_str:
            app.alert_entry.insert(0, f"{app.alert_slider.get():.2f}")
            return
        value = float(value_str)
        if 0 <= value <= 1:
            app.alert_slider.set(value)
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror("Błąd", "Wpisz liczbę między 0 a 1.")
        app.alert_entry.delete(0, tk.END)
        app.alert_entry.insert(0, f"{app.alert_slider.get():.2f}")

def update_pixel_info(app, event):
    if app.image_array is None:
        return
    x, y = event.x, event.y
    img_width, img_height = app.map_photo.width(), app.map_photo.height()
    array_height, array_width = app.image_array.shape
    offset_x = (app.map_label.winfo_width() - img_width) // 2
    offset_y = (app.map_label.winfo_height() - img_height) // 2
    relative_x = x - offset_x
    relative_y = y - offset_y
    scale_x = array_width / img_width
    scale_y = array_height / img_height
    if 0 <= relative_x < img_width and 0 <= relative_y < img_height:
        orig_x = int(relative_x * scale_x)
        orig_y = int(relative_y * scale_y)
        pixel_value = app.image_array[orig_y, orig_x]
        app.pixel_info_label.config(text=f"X: {orig_x}, Y: {orig_y}, Value: {pixel_value:.2f}")
    else:
        app.pixel_info_label.config(text="X: -, Y: -, Value: -")

def load_map(app):
    file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF Files", "*.tif;*.tiff")])
    if file_path:
        app.tif_path = file_path
        display_map(app)

def display_map(app):
    if not app.tif_path:
        return
    try:
        with rasterio.open(app.tif_path) as dataset:
            app.image_array = dataset.read(1)
            if np.isnan(app.image_array).all():
                messagebox.showerror("ERROR", "TIFF file contains only NaN values!")
                return
            app.image_array = np.nan_to_num(app.image_array)
            cmap = plt.get_cmap(app.cmap_combobox.get())
            colored_image = cmap((app.image_array - np.min(app.image_array)) / (np.max(app.image_array) - np.min(app.image_array)))[:, :, :3]
            colored_image = (colored_image * 255).astype(np.uint8)
            img = Image.fromarray(colored_image)
            img.thumbnail((900, 900))
            app.map_photo = ImageTk.PhotoImage(img)
            app.map_label.config(image=app.map_photo)
    except Exception as e:
        messagebox.showerror("ERROR", f"File couldn't be read: {e}")

def download_gee_image(app):
    def compute_chl(image):
        chl = image.expression('((B5-B4) / (B5+B4)+1)/2', {'B5': image.select('B5'), 'B4': image.select('B4')}).rename('Chl_a')
        return image.addBands(chl)
    try:
        ee.Initialize(project='ee-solinachlorofil')
        start_date = app.start_date.get_date().strftime('%Y-%m-%d')
        end_date = app.end_date.get_date().strftime('%Y-%m-%d')
        aoi = ee.Geometry.Rectangle([22.396522,49.300936,22.535404,49.436130 ])
        sentinel2 = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                    .filterDate(start_date, end_date)
                    .filterBounds(aoi)
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                    .sort('CLOUDY_PIXEL_PERCENTAGE'))
        image = sentinel2.first()
        image_date_millis = image.get("system:time_start").getInfo()
        image = sentinel2.mosaic().clip(aoi)
        image_date = time.strftime('%Y-%m-%d', time.gmtime(image_date_millis / 1000))
        messagebox.showinfo("Pobrano obraz", f"Pobrano obraz z dnia: {image_date}")
        chl_image = compute_chl(image).select('Chl_a').clip(aoi)
        output_path = "chl_image_solina.tif"
        geemap.ee_export_image(chl_image, filename=output_path, scale=10, region=aoi, file_per_band=False, crs='EPSG:4326')
        app.tif_path = output_path
        display_map(app)
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się pobrać obrazu: {e}")