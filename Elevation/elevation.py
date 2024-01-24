import os
import pandas as pd
import rasterio
from rasterio.windows import Window
import numpy as np


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
        # Convert geographical coordinates to raster coordinates
        row, col = src.index(longitude, latitude)

        # Calculate the window size
        # Updated to use fixed width and height of 345x463
        window_width = 345
        pixels_per_side_width = int(window_width / pixel_size)
        window_height = 463
        pixels_per_side_height = int(window_height / pixel_size)
        window = Window(
            col - pixels_per_side_width // 2,
            row - pixels_per_side_height // 2,
            pixels_per_side_width,
            pixels_per_side_height,
        )

        # Read the data in the window
        elevation_data = src.read(1, window=window)
        quality_data = quality_src.read(1, window=window)

        # Filter out unreliable elevation data
        reliable_elevation_data = elevation_data[
            (quality_data != 1) & (quality_data != 5)
        ]

        # Calculate the average elevation, ignoring missing data
        avg_elevation = np.nanmean(reliable_elevation_data)

        return avg_elevation


# Get the current directory
current_dir = os.getcwd()

# Define the file paths relative to the current directory
quality_file_path = os.path.join(
    current_dir, "data", "SRTMGL1_NUMNC.003_SRTMGL1_NUM_doy2000042_aid0001.tif"
)
csv_file_path = os.path.join(current_dir, "data", "2013data.csv")

# Extract the name of the CSV file without extension
csv_file_name = os.path.splitext(os.path.basename(csv_file_path))[0]

srtm_file_path = os.path.join(
    current_dir, "data", "SRTMGL1_NC.003_SRTMGL1_DEM_doy2000042_aid0001.tif"
)

# Load the CSV file
data = pd.read_csv(csv_file_path)

# Iterate over the DataFrame and calculate elevation for each row
elevations = []
for index, row in data.iterrows():
    longitude = row["Longitude"]
    latitude = row["Latitude"]
    elevation = get_average_elevation(
        srtm_file_path, quality_file_path, longitude, latitude
    )
    elevations.append(elevation)

# Add the elevation data to the DataFrame
data["Elevation"] = elevations

# Define the output folder path
output_folder_path = os.path.join(current_dir, "output")

# Check if the "output" folder exists, and create it if not
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

# Save the updated DataFrame to a new CSV file with the CSV file name included
output_csv_file_path = os.path.join(
    output_folder_path, f"{csv_file_name}_Elevation.csv"
)
data.to_csv(output_csv_file_path, index=False)

print(f"Updated CSV file saved to {output_csv_file_path}")
