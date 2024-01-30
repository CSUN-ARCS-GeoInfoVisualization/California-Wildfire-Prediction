import os
import pandas as pd
import rasterio
from rasterio.windows import Window
import numpy as np
import time


def get_average_elevation(srtm_file, quality_file, longitude, latitude, pixel_size=30):
    """
    Extracts the average elevation from a grid of pixels that approximately covers a given physical area size
    centered around the given coordinates, excluding pixels with unreliable elevation data based on the quality file.

    :param srtm_file: Path to the SRTM .tif file (elevation data).
    :param quality_file: Path to the corresponding quality .tif file.
    :param longitude: Longitude of the center point.
    :param latitude: Latitude of the center point.
    :param pixel_size: Size of each pixel in meters (default 30m for SRTM data).
    :param area_size: Size of the physical area to cover in meters.
    :return: Average elevation in meters, considering only reliable data.
    """
    with rasterio.open(srtm_file) as src, rasterio.open(quality_file) as quality_src:
        row, col = src.index(longitude, latitude)
        window_width = 345
        window_height = 463
        pixels_per_side_width = int(window_width / pixel_size)
        pixels_per_side_height = int(window_height / pixel_size)
        window = Window(
            col - pixels_per_side_width // 2,
            row - pixels_per_side_height // 2,
            pixels_per_side_width,
            pixels_per_side_height,
        )
        elevation_data = src.read(1, window=window)
        quality_data = quality_src.read(1, window=window)
        reliable_elevation_data = elevation_data[
            (quality_data != 1) & (quality_data != 5)
        ]

        if reliable_elevation_data.size == 0:
            return np.nan
        else:
            return np.nanmean(reliable_elevation_data)


# Measure the start time
start_time = time.time()

# Get the current directory
current_dir = os.getcwd()

# Define file paths relative to the current directory
quality_file_path = os.path.join(
    current_dir, "data", "SRTMGL1_NUMNC.003_SRTMGL1_NUM_doy2000042_aid0001.tif"
)
csv_file_path = os.path.join(current_dir, "data", "data_2013-2-21.csv")
srtm_file_path = os.path.join(
    current_dir, "data", "SRTMGL1_NC.003_SRTMGL1_DEM_doy2000042_aid0001.tif"
)

# Load the CSV file
data = pd.read_csv(csv_file_path)

# Extract unique coordinates
unique_coordinates = data[["Longitude", "Latitude"]].drop_duplicates()

# Calculate elevation for each unique coordinate
unique_coordinates["Elevation"] = unique_coordinates.apply(
    lambda row: get_average_elevation(
        srtm_file_path, quality_file_path, row["Longitude"], row["Latitude"]
    ),
    axis=1,
)

# Merge calculated elevation with the original DataFrame
data = pd.merge(data, unique_coordinates, on=["Longitude", "Latitude"], how="left")

# Define the output folder path
output_folder_path = os.path.join(current_dir, "output")

# Check if the "output" folder exists, and create it if not
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

# Save the updated DataFrame to a new CSV file
output_csv_file_path = os.path.join(
    output_folder_path,
    f"{os.path.splitext(os.path.basename(csv_file_path))[0]}_Elevation.csv",
)
data.to_csv(output_csv_file_path, index=False)

# Measure the end time
end_time = time.time()
# Calculate and print the running time
running_time = end_time - start_time
print(f"Updated CSV file saved to {output_csv_file_path}")
print(f"Running time: {running_time} seconds")
