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
import time
import ee
import geemap

ee.Authenticate()
class Tooltip:
    def __init__(self, widget, text, delay=1):
        self.widget = widget
        self.text = text
        self.delay = delay  # Delay in seconds
        self.tooltip = None
        self.tooltip_id = None
        
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        # Function to show tooltip after delay
        self.tooltip_id = self.widget.after(int(self.delay * 500), self.create_tooltip, event)

    def create_tooltip(self, event):
        # Create the tooltip text widget
        x = event.x_root + 15  # Positioning the tooltip
        y = event.y_root + 15
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # No border/title bar
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

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solina Lake water monitoring system")
        self.root.geometry("1200x900")
        

        # # Styl dla nowoczesnego wyglądu
        # self.style = ttk.Style()
        # self.style.configure("TButton", font=("Arial", 12), padding=6)
        # self.style.configure("TLabel", background="#2C2F33", foreground="white", font=("Arial", 12))
        # self.style.configure("TFrame", background="#2C2F33")



        self.image_array = None  # var to store tif data
        self.tif_path = None  # Path to tiff that we provide

        # side panel
        self.control_frame = tk.Frame(self.root, width=350, bg='white')
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
# Logo
        self.logo = Image.open("logo.png")  # Załaduj własne logo
        self.logo = self.logo.resize((150, 150), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo)
        self.logo_label = tk.Label(self.control_frame, image=self.logo_photo, bg="#23272A")
        self.logo_label.pack(pady=5)
        # date
        tk.Label(self.control_frame, text="Start date:").pack(pady=5)
        self.start_date = DateEntry(self.control_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date.pack(pady=5)
        Tooltip(self.start_date, "Select start date.")
        tk.Label(self.control_frame, text="End date:").pack(pady=5)
        self.end_date = DateEntry(self.control_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date.pack(pady=5)
        Tooltip(self.end_date, "Select end date.")

        # model
        tk.Label(self.control_frame, text="Select model (temporary):").pack(pady=5)
        self.model_combobox = ttk.Combobox(self.control_frame, values=["Model A", "Model B", "Model C"])
        self.model_combobox.pack(pady=5)
        Tooltip(self.model_combobox, "Model selection.")

        # colormap selection pane
        tk.Label(self.control_frame, text="Choose colormap:").pack(pady=5)
        self.cmap_combobox = ttk.Combobox(self.control_frame, values=plt.colormaps(), state="readonly")
        self.cmap_combobox.set("Spectral_r") 
        self.cmap_combobox.pack(pady=5)
        Tooltip(self.cmap_combobox, "Colormap selection")
        # read file
        # Kontener na suwak i pole tekstowe w jednej linii
        alert_frame = tk.Frame(self.control_frame)
        alert_frame.pack(pady=5, fill="x")

        # Etykieta dla Alert Level
        tk.Label(alert_frame, text="Alert Level:").grid(row=0, column=0, padx=5)

        # Pole tekstowe do wpisywania wartości
        self.alert_level = tk.DoubleVar(value=0.2)
        self.alert_entry = ttk.Entry(alert_frame, width=7)
        self.alert_entry.grid(row=0, column=1, padx=5)

        # Suwak
        self.alert_slider = tk.Scale(alert_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                                    variable=self.alert_level, command=self.update_alert_entry)
        self.alert_slider.grid(row=0, column=2, padx=5, sticky="we")
        Tooltip(self.alert_slider, "Adjust the alert threshold using this slider.")
        # Rozciągnięcie suwaka na całą szerokość
        alert_frame.columnconfigure(2, weight=1)

        # Powiązanie wpisywania ręcznego
        self.alert_entry.bind("<Return>", self.update_alert_slider)
        self.alert_entry.bind("<FocusOut>", self.update_alert_slider)



        # inverse alert lvl
        self.invert_alert = tk.BooleanVar()
        self.invert_checkbutton = tk.Checkbutton(self.control_frame, text="Invert Alert Level", variable=self.invert_alert)
        self.invert_checkbutton.pack(pady=5)
        #Tooltip(self.invert_alert, "Marks values under desired level.")
        # display alert button
        self.alert_button = tk.Button(self.control_frame, text="Show Alert Level", command=self.apply_alert_level)
        self.alert_button.pack(pady=5)
        Tooltip(self.alert_button, "Shows pixels with alert.") 
        
        # calculate
        self.calculate_button = tk.Button(self.control_frame, text="Generate map", command=self.process_map)
        self.calculate_button.pack(pady=5)
        Tooltip(self.calculate_button, "Calculates map with desired data.")
        # read file
        self.load_button = tk.Button(self.control_frame, text="Load own map", command=self.load_map)
        self.load_button.pack(pady=5)
        Tooltip(self.load_button, "Loads selected file.")
        
        # change cmap
        self.change_cmap_button = tk.Button(self.control_frame, text="Change colormap", command=self.display_map)
        self.change_cmap_button.pack(pady=5)
        Tooltip(self.change_cmap_button, "Changes colormap to selected.")
        
        # mape frame
        self.map_label = tk.Label(self.root)
        self.map_label.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # legend frame
        self.legend_frame = tk.Frame(self.control_frame, bg='lightgray', width=280)
        self.legend_frame.pack(pady=5)
        self.legend_title = ttk.Label(self.legend_frame, text="Legend", font=("Arial", 12, "bold"))
        self.legend_title.pack()


        # Dodanie etykiety do wyświetlania wartości piksela
        self.pixel_info_label = tk.Label(self.root, text="X: -, Y: -, Value: -", font=("Arial", 10), bg="white")
        self.pixel_info_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # Prawy dolny róg

        # Powiązanie zdarzeń myszy z metodą aktualizacji
        self.map_label.bind("<Motion>", self.update_pixel_info)
    def generate_legend(self):
        """legend based on real values from tif"""
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
                    messagebox.showerror("ERROR", "TIFF file contains only NaN values!")
                    return
                
                self.image_array = np.nan_to_num(self.image_array)  
                cmap_name = self.cmap_combobox.get()
                cmap = plt.get_cmap(cmap_name)  # colormap
                colored_image = cmap((self.image_array - np.min(self.image_array)) / (np.max(self.image_array) - np.min(self.image_array)))[:, :, :3]  # Normalisation and using colormap
                colored_image = (colored_image * 255).astype(np.uint8)
                img = Image.fromarray(colored_image)
                img.thumbnail((900, 900))
                
                self.map_photo = ImageTk.PhotoImage(img)
                self.map_label.config(image=self.map_photo)
                if not hasattr(self, 'legend_title'):
                    self.legend_title = ttk.Label(self.legend_frame, text="Legend", font=("Arial", 12, "bold"))
                    self.legend_title.pack()

                # real data legend
                for widget in self.legend_frame.winfo_children():
                    if widget != self.legend_title:
                        widget.destroy()
                self.generate_legend()

                
        except Exception as e:
            messagebox.showerror("ERROR", f"File couldn't be read: {e}")

    def process_map(self):
        """ Pobiera i generuje mapę z Google Earth Engine """
        self.download_gee_image()  # Wywołuje pobranie danych z GEE


    def apply_alert_level(self):
        if self.image_array is None:
            return

        alert_value = self.alert_level.get()  # Pobranie wartości alertu
        invert = self.invert_alert.get()  # Sprawdzenie, czy invert jest aktywne

        grayscale_cmap = plt.get_cmap(self.cmap_combobox.get())  # Skala szarości
        norm_array = (self.image_array - np.min(self.image_array)) / (np.max(self.image_array) - np.min(self.image_array))

        # Warunek maski – zależnie od opcji invert
        if invert:
            alert_mask = self.image_array < alert_value  # Inwersja – zaznacza wartości poniżej
        else:
            alert_mask = self.image_array > alert_value  # Normalnie – zaznacza wartości powyżej

        # Konwersja do skali szarości
        grayscale_image = grayscale_cmap(norm_array)[:, :, :3]

        # Ustawienie pikseli na czerwono według maski
        alert_image = np.copy(grayscale_image)
        alert_image[alert_mask] = [1, 0, 0]  # RGB dla czerwonego

        # Konwersja do obrazu
        alert_image = (alert_image * 255).astype(np.uint8)
        img = Image.fromarray(alert_image)
        img.thumbnail((900, 900))

        # Aktualizacja mapy
        self.map_photo = ImageTk.PhotoImage(img)
        self.map_label.config(image=self.map_photo)

    def update_alert_entry(self, value):
        """Aktualizuje pole tekstowe, gdy użytkownik przesuwa suwak."""
        self.alert_entry.delete(0, tk.END)
        self.alert_entry.insert(0, f"{float(value):.2f}")  # Zaokrąglenie wartości


    def update_alert_slider(self, event):
        """Aktualizuje suwak, gdy użytkownik wpisze wartość w Entry."""
        try:
            value_str = self.alert_entry.get().strip()  # Pobierz wartość i usuń spacje
            if not value_str:  # Jeśli puste, przywróć aktualną wartość suwaka
                self.alert_entry.insert(0, f"{self.alert_slider.get():.2f}")
                return
            
            value = float(value_str)
            if 0 <= value <= 1:  # Sprawdzenie, czy wartość mieści się w zakresie
                self.alert_slider.set(value)  # Aktualizacja suwaka
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Błąd", "Wpisz liczbę między 0 a 1.")
            self.alert_entry.delete(0, tk.END)
            self.alert_entry.insert(0, f"{self.alert_slider.get():.2f}")  # Przywrócenie starej wartości

            
    def update_pixel_info(self, event):
        """Aktualizuje wyświetlane informacje o pikselu pod kursorem, uwzględniając przesunięcie, skalowanie obrazu oraz centrowanie."""
        if self.image_array is None:
            return

        # Pobieramy współrzędne kursora względem map_label (pozycja kursora w obrębie mapy)
        x = event.x
        y = event.y

        # Wymiary wyświetlanego obrazu w map_label
        img_width, img_height = self.map_photo.width(), self.map_photo.height()

        # Wymiary oryginalnego obrazu TIFF
        array_height, array_width = self.image_array.shape

        # Obliczanie przesunięcia obrazu w kontenerze
        map_label_width = self.map_label.winfo_width()
        map_label_height = self.map_label.winfo_height()

        # Centrowanie: obliczanie przesunięcia obrazu względem kontenera
        offset_x = (map_label_width - img_width) // 2
        offset_y = (map_label_height - img_height) // 2

        # Zidentyfikowanie współrzędnych kursora względem lewego górnego rogu obrazu (w kontenerze)
        relative_x = x - offset_x
        relative_y = y - offset_y

        # Dopasowanie skali (rozmiar wyświetlanego obrazu względem oryginalnego)
        scale_x = array_width / img_width
        scale_y = array_height / img_height

        # Tylko wtedy, gdy kursor znajduje się w obrębie mapy
        if 0 <= relative_x < img_width and 0 <= relative_y < img_height:
            # Skalowanie współrzędnych kursora do współrzędnych oryginalnego obrazu
            orig_x = int(relative_x * scale_x)
            orig_y = int(relative_y * scale_y)

            # Pobranie wartości piksela z oryginalnego obrazu TIFF
            pixel_value = self.image_array[orig_y, orig_x]

            # Aktualizacja etykiety z wartością piksela
            self.pixel_info_label.config(text=f"X: {orig_x}, Y: {orig_y}, Value: {pixel_value:.2f}")
        else:
            self.pixel_info_label.config(text="X: -, Y: -, Value: -")




    def download_gee_image(self):
    # """ Pobiera obraz Sentinel-2 z GEE, oblicza indeks Chl-a i zapisuje jako TIFF """
        # Definicja funkcji obliczającej indeks Chl-a
        def compute_chl(image):
            chl = image.expression(
                '((B5-B4) / (B5+B4)+1)/2',  # Przykładowy wzór na Chl-a
                {
                    'B5': image.select('B5'),
                    'B4': image.select('B4')
                }
            ).rename('Chl_a')
                
            return image.addBands(chl)
        try:
            ee.Initialize(project='ee-piotrkrajewski')
            
            # Pobierz zakres dat z interfejsu użytkownika
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date.get_date().strftime('%Y-%m-%d')

            # Definicja AOI (obszar zainteresowania) - SOLINA
            aoi = ee.Geometry.Rectangle([22.396522,49.300936,22.535404, 49.436130 ])

            # Pobranie danych Sentinel-2 i filtracja
            sentinel2 = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                        .filterDate(start_date, end_date)
                        .filterBounds(aoi)
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))  # Maks. 10% chmur
                        .sort('CLOUDY_PIXEL_PERCENTAGE'))

            # Pobranie pierwszego dostępnego obrazu
            image = sentinel2.first()
            image_date_millis = image.get("system:time_start").getInfo()  # Pobranie daty w milisekundach
            image = sentinel2.mosaic().clip(aoi)

            image_date = time.strftime('%Y-%m-%d', time.gmtime(image_date_millis / 1000))  # Konwersja do YYYY-MM-DD

            # Wyświetlenie informacji w GUI
            messagebox.showinfo("Pobrano obraz", f"Pobrano obraz z dnia: {image_date}")
            # Obliczenie indeksu Chl-a
            chl_image = compute_chl(image).select('Chl_a').clip(aoi)

            # Ścieżka do zapisu lokalnego
            output_path = "chl_image_solina.tif"

            # Eksport obrazu do pliku TIFF
            geemap.ee_export_image(chl_image, filename=output_path, scale=10, region=aoi, file_per_band=False,crs='EPSG:4326') #try epsg 32634

            self.tif_path = output_path
            self.display_map()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się pobrać obrazu: {e}")

        

    def download_gee_image_to_drive(self):
        """Pobiera obraz Sentinel-2 z GEE i zapisuje go na Google Drive"""
        try:
            # Pobierz zakres dat z interfejsu użytkownika
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date.get_date().strftime('%Y-%m-%d')

            # Definicja AOI (obszar zainteresowania)
            aoi = ee.Geometry.Rectangle([22.402142, 49.300599, 22.544342, 49.435929])

            # Pobranie danych z Sentinel-2
            sentinel2 = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                        .filterDate(start_date, end_date)
                        .filterBounds(aoi)
                        .sort('CLOUDY_PIXEL_PERCENTAGE'))

            image = sentinel2.first()

            # Parametry wizualizacji
            vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}

            # Eksport obrazu na Google Drive
            export_task = ee.batch.Export.image.toDrive(
                image=image,
                description='sentinel_image',  # Nazwa zadania eksportu
                folder='GEE_Exports',          # Folder na Google Drive
                fileNamePrefix='sentinel_image',  # Prefiks nazwy pliku
                scale=10,  # Skala w metrach (np. 10 dla Sentinel-2)
                region=aoi,  # Region (obszar zainteresowania)
                fileFormat='GeoTIFF'  # Format pliku
            )

            # Uruchomienie zadania eksportu
            export_task.start()

            print("Eksport rozpoczęty! Sprawdź Google Drive.")

            # Opcjonalnie monitorowanie postępu
            while export_task.active():
                print('Export is running...')
                time.sleep(10)  # Czekaj 10 sekund, zanim sprawdzisz status

            # Zakończenie
            print("Eksport zakończony!")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się pobrać mapy: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
