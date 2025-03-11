import openeo
import os

# Connect to openEO back-end
con = openeo.connect("https://earthengine.openeo.org")
con.authenticate_basic("group11", "test123")

# Define spatial and temporal extent
spatial_extent = {"west": 16.06, "south": 48.06, "east": 16.65, "north": 48.35}
temporal_extent = ["2017-03-01", "2017-06-01"]

# Load Sentinel-2 data with necessary bands for NDCI computation (B04 - Red, B05 - Red Edge)
datacube = con.load_collection(
    "COPERNICUS/S2",
    spatial_extent=spatial_extent,
    temporal_extent=temporal_extent,
    bands=["B04", "B05"]
)

# Define the NDCI function
def ndci(red, red_edge):
    return (red_edge - red) / (red_edge + red)

# Apply NDCI calculation
datacube = datacube.apply(lambda x: ndci(x["B04"], x["B05"]))

# Convert NDCI to chlorophyll-a concentration using the given polynomial equation
chl_a = datacube.apply(lambda ndci_value: 826.57 * ndci_value**3 - 176.43 * ndci_value**2 + 19 * ndci_value + 4.071)

# Define output folder
output_folder = "chl_a"
os.makedirs(output_folder, exist_ok=True)

# Save the result as a GeoTIFF file in the chl_a folder
chl_a_result = chl_a.save_result(format="GTIFF")

# Create and start the job
job = chl_a_result.create_job()
job.start_and_wait().download_results(target=output_folder)

print(f"Chlorophyll-a index calculation completed. Results saved in {output_folder}")
