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

    import numpy as np
    from PIL import Image

    alert_value = app.alert_level.get()
    invert = app.invert_alert.get()

    # Utwórz pustą przezroczystą warstwę RGBA
    alert_overlay = np.zeros((*app.image_array.shape, 4), dtype=np.uint8)

    # Wygeneruj maskę alertów
    if invert:
        mask = app.image_array < alert_value
    else:
        mask = app.image_array > alert_value

    # Ustaw kolor tylko tam, gdzie maska True
    alert_overlay[mask] = [255, 0, 0, 255]  # czerwony, pełna przezroczystość gdzie indziej

    # Stwórz obraz z maską
    alert_img = Image.fromarray(alert_overlay, mode="RGBA")

    # Pobierz odpowiadający obraz RGB
    import os
    import re
    match = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(app.tif_path))
    rgb_img = None

    if match:
        date_str = match.group(1)
        rgb_path = f"sen2_cache_rgb/rgb_{date_str}_sen2.tif"
        if os.path.exists(rgb_path):
            with rasterio.open(rgb_path) as rgb_ds:
                rgb = rgb_ds.read([1, 2, 3])
                rgb = np.transpose(rgb, (1, 2, 0))
                rgb = np.clip(rgb, 0, 255).astype(np.uint8)
                rgb_img = Image.fromarray(rgb).convert("RGBA")

    if rgb_img:
        rgb_img = rgb_img.resize(alert_img.size)
        combined = Image.alpha_composite(rgb_img, alert_img)
    else:
        combined = alert_img  # fallback

    combined.thumbnail((900, 900))
    app.map_photo = ImageTk.PhotoImage(combined)
    app.map_label.configure(image=app.map_photo, fg_color="#cccccc")



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
        app.pixel_info_label.configure(text=f"X: {orig_x}, Y: {orig_y}, Value: {pixel_value:.2f}")
    else:
        app.pixel_info_label.configure(text="X: -, Y: -, Value: -")

def load_map(app):
    file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF Files", "*.tif;*.tiff")])
    if file_path:
        app.tif_path = file_path
        display_map(app)

def display_map(app):
    if not app.tif_path:
        return

    try:
        import os
        import re

        # === Krok 1: wyciągnij datę z nazwy ===
        chl_filename = os.path.basename(app.tif_path)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", chl_filename)
        date_str = match.group(1) if match else None

        # === Krok 2: spróbuj załadować RGB jako tło ===
        rgb_image = None
        if date_str:
            rgb_path = f"sen2_cache_rgb/rgb_{date_str}_sen2.tif"
            if os.path.exists(rgb_path):
            
                with rasterio.open(rgb_path) as rgb_ds:
                    rgb = rgb_ds.read([1, 2, 3])  # B4, B3, B2
                    rgb = np.transpose(rgb, (1, 2, 0))
                    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
                    rgb_image = Image.fromarray(rgb).convert("RGBA")

        # === Krok 3: wczytaj CHL ===
        with rasterio.open(app.tif_path) as dataset:
            app.image_array = dataset.read(1)

        if np.isnan(app.image_array).all():
            messagebox.showerror("ERROR", "TIFF file contains only NaN values!")
            return

        app.image_array = np.nan_to_num(app.image_array)
        masked_array = np.ma.masked_where(app.image_array == 0.0, app.image_array)
        norm_array = (masked_array - masked_array.min()) / (masked_array.max() - masked_array.min())

        # === Krok 4: przygotuj colormap z przezroczystym tłem ===
        cmap = plt.get_cmap(app.cmap_combobox.get()).copy()
        cmap.set_bad(color=(0, 0, 0, 0))  # transparent dla 0.0

        rgba_image = cmap(norm_array)  # (H, W, 4)
        rgba_image = (rgba_image * 255).astype(np.uint8)
        chl_img = Image.fromarray(rgba_image, mode="RGBA")

        # === Krok 5: jeśli RGB istnieje — nałóż CHL na RGB ===
        if rgb_image:

            rgb_resized = rgb_image.resize(chl_img.size)
            combined = Image.alpha_composite(rgb_resized, chl_img)
        else:

            combined = chl_img

        # === Krok 6: wyświetlenie ===
        combined.thumbnail((900, 900))
        app.map_photo = ImageTk.PhotoImage(combined)

        # ✅ Warunek: jeśli Show Alert Level jest zaznaczone, nakładamy alerty
        if hasattr(app, "show_alert_checkbox") and app.show_alert_checkbox.get():
            apply_alert_level(app)
        else:
            app.map_label.configure(image=app.map_photo, fg_color="#cccccc")
    

        draw_colormap_legend(app)

        if date_str:
            app.date_label.configure(text=f"Date of displayed image: {date_str}")
        else:
            app.date_label.configure(text="Date: Unknown")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("ERROR", f"File couldn't be read: {e}")




def download_gee_image(app):
    import ee
    import time
    import os
    from tkinter import messagebox
    from geemap import ee_export_image

    source = app.source_combobox.get()
    print(f"[INFO] Wybrano źródło: {source}")

    try:
        ee.Initialize(project='ee-solinachlorofil')
        start_date = app.start_date.get_date().strftime('%Y-%m-%d')
        end_date = app.end_date.get_date().strftime('%Y-%m-%d')
        aoi = ee.Geometry.Rectangle([22.396522, 49.300936, 22.535404, 49.436130])

        if source == "Sentinel-2":
            dataset = 'COPERNICUS/S2_SR_HARMONIZED'
            bands = ['B4', 'B3', 'B2']
            rgb_max = 3000
            expression = '((B5 - B4) / (B5 + B4) + 1)/2'
            chl_bands = {'B5': 'B5', 'B4': 'B4'}
            scl_band = 'SCL'
            water_class = 6

            def compute_chl(image):
                chl = image.expression(expression, chl_bands).rename('Chl_a')
                scl = image.select(scl_band)
                water_mask = scl.eq(water_class)
                return image.addBands(chl).updateMask(water_mask)

            sentinel = (ee.ImageCollection(dataset)
                        .filterDate(start_date, end_date)
                        .filterBounds(aoi)
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
                        .sort('CLOUDY_PIXEL_PERCENTAGE'))

            chl_folder = "sen2_cache"
            rgb_folder = "sen2_cache_rgb"
            file_suffix = "sen2"

            image = sentinel.first()
            if image is None:
                messagebox.showwarning("Brak danych", f"Nie znaleziono żadnych zobrazowań w podanym zakresie dla {source}.")
                return

            image_date_millis = image.get("system:time_start").getInfo()
            image_rgb = sentinel.select(bands).mosaic().clip(aoi)
            image_chl = sentinel.select(list(set(chl_bands.values()) + [scl_band])).mosaic().clip(aoi)

            rgb_image = image_rgb.visualize(
                bands=bands,
                min=0,
                max=rgb_max,
                gamma=1.2
            ).clip(aoi)

        elif source == "Sentinel-3":
            dataset = 'COPERNICUS/S3/OLCI'
            bands = ['Oa08_radiance', 'Oa06_radiance', 'Oa04_radiance']
            rgb_max = 0.05

            def compute_chl(image):
                bri = image.expression(
                    'B9 / (B11 + 1e-6)',
                    {
                        'B9': image.select('Oa09_radiance'),
                        'B11': image.select('Oa11_radiance')
                    }
                ).rename('BRI')
                return image.addBands(bri)

            sentinel = (ee.ImageCollection(dataset)
                        .filterDate(start_date, end_date)
                        .filterBounds(aoi)
                        .sort("system:time_start"))

            chl_folder = "s3_cache"
            rgb_folder = "s3_cache_rgb"
            file_suffix = "s3"

            first_image = sentinel.first()
            if first_image is None:
                messagebox.showwarning("Brak danych", f"Nie znaleziono żadnych zobrazowań w podanym zakresie dla {source}.")
                return

            image_date_millis = first_image.get("system:time_start").getInfo()
            image_chl = sentinel.select(['Oa09_radiance', 'Oa11_radiance']).mosaic().clip(aoi)

            # RGB z Sentinel-2 jako podkład
            s2_dataset = 'COPERNICUS/S2_SR_HARMONIZED'
            s2 = (ee.ImageCollection(s2_dataset)
                  .filterDate(start_date, end_date)
                  .filterBounds(aoi)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5)))

            s2_mosaic = s2.mosaic()
            sentinel2_rgb = s2_mosaic.select(['B4', 'B3', 'B2'])

            rgb_image = sentinel2_rgb.visualize(
                bands=['B4', 'B3', 'B2'],
                min=0,
                max=3000,
                gamma=1.2
            ).clip(aoi)

        else:
            messagebox.showerror("Błąd", "Nieznane źródło danych.")
            return

        os.makedirs(chl_folder, exist_ok=True)
        os.makedirs(rgb_folder, exist_ok=True)

        image_date = time.strftime('%Y-%m-%d', time.gmtime(image_date_millis / 1000))
        output_path = f"{chl_folder}/chl_{image_date}_{file_suffix}.tif"
        rgb_output_path = f"{rgb_folder}/rgb_{image_date}_{file_suffix}.tif"

        print(f"[INFO] Eksportuję chl do: {output_path}")
        print(f"[INFO] Eksportuję RGB do: {rgb_output_path}")

        if source == "Sentinel-3":
            chl_image = compute_chl(image_chl).select('BRI').clip(aoi)
        else:
            chl_image = compute_chl(image_chl).select('Chl_a').clip(aoi)

        ee_export_image(chl_image, filename=output_path, scale=10, region=aoi, file_per_band=False, crs='EPSG:4326')
        ee_export_image(rgb_image, filename=rgb_output_path, scale=10, region=aoi, file_per_band=False, crs='EPSG:4326')

        for _ in range(20):
            if os.path.exists(output_path):
                print("[INFO] Plik chl istnieje.")
                break
            time.sleep(0.5)

        if os.path.exists(output_path):
            app.tif_path = output_path
            messagebox.showinfo("Pobrano", f"Pobrano obraz z dnia: {image_date}")
            app.display_map()
        else:
            messagebox.showerror("Błąd", f"Plik {output_path} nie został utworzony.")
            print("[ERROR] Plik nie został znaleziony po eksporcie.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Błąd", f"Nie udało się pobrać obrazu: {e}")







def draw_colormap_legend(app):
    cmap = plt.get_cmap(app.cmap_combobox.get())
    width = 256
    height = 40

    gradient = np.linspace(0, 1, width).reshape(1, -1)
    gradient = np.repeat(gradient, height, axis=0)
    gradient_rgb = (cmap(gradient)[:, :, :3] * 255).astype(np.uint8)

    img = Image.fromarray(gradient_rgb)
    photo = ImageTk.PhotoImage(img)

    app.legend_canvas.delete("all")
    app.legend_canvas.image = photo  # keep reference
    app.legend_canvas.create_image(0, 0, anchor="nw", image=photo)

    # Dodaj liczby 0 i 1
    app.legend_canvas.create_text(0+5, height - 33, anchor="nw", text="0", font=("Arial", 8))
    app.legend_canvas.create_text(width-5, height - 33, anchor="ne", text="1", font=("Arial", 8))




def download_all_gee_images(app):
    import ee
    import time
    import os
    from datetime import datetime

    ee.Initialize(project='ee-solinachlorofil')

    aoi = ee.Geometry.Rectangle([22.396522, 49.300936, 22.535404, 49.436130])
    start_date = '2021-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')

    def compute_chl(image):
        chl = image.expression('((B5 - B4) / (B5 + B4) + 1)/2', {
            'B5': image.select('B5'),
            'B4': image.select('B4')
        }).rename('Chl_a')
        scl = image.select('SCL')
        water_mask = scl.eq(6)
        return image.addBands(chl).updateMask(water_mask)

    # Utwórz foldery jeśli nie istnieją
    os.makedirs("sen2_cache", exist_ok=True)
    os.makedirs("sen2_cache_rgb", exist_ok=True)

    sentinel2 = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterDate(start_date, end_date)
        .filterBounds(aoi)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    )

    image_list = sentinel2.toList(sentinel2.size())
    total = image_list.size().getInfo()

    for i in range(total):
        try:
            image = ee.Image(image_list.get(i))
            date_ms = image.date().millis().getInfo()
            date_str = time.strftime('%Y-%m-%d', time.gmtime(date_ms / 1000))

            chl_path = f"sen2_cache/chl_{date_str}_sen2.tif"
            rgb_path = f"sen2_cache_rgb/rgb_{date_str}_sen2.tif"

            if os.path.exists(chl_path) and os.path.exists(rgb_path):
                print(f"✅ {date_str} — już pobrane, pomijam.")
                continue

            print(f"⬇️  Pobieram: {date_str}")

            image_clipped = image.clip(aoi)
            chl_image = compute_chl(image_clipped).select('Chl_a')
            rgb_image = image_clipped.visualize(bands=['B4', 'B3', 'B2'], min=0, max=3000, gamma=1.2)

            # Eksport
            geemap.ee_export_image(
                chl_image, filename=chl_path, scale=10, region=aoi,
                file_per_band=False, crs='EPSG:4326'
            )

            geemap.ee_export_image(
                rgb_image, filename=rgb_path, scale=10, region=aoi,
                file_per_band=False, crs='EPSG:4326'
            )

            print(f"✅ Zapisano {date_str}")

        except Exception as e:
            print(f"❌ Błąd przy {i}: {e}")



