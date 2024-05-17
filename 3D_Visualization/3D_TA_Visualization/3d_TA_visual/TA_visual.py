from multiprocessing import Pool
import os
import imageio
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import mapping
from PIL import Image, ImageDraw, ImageFont


def get_california_boundary():
    # Load California boundary GeoJSON file
    california_boundary = gpd.read_file("California_State_Boundary.geojson")

    # Convert to GeoJSON format
    california_boundary_json = [mapping(poly) for poly in california_boundary.geometry]
    return california_boundary_json


# Image processing function (EDIT THIS)
def process_image(f, california_boundary):
    with rasterio.open(f) as src:
        # Clip image to California boundary
        out_image, out_transform = mask(src, california_boundary, crop=True)
        out_meta = src.meta.copy()

        # generate blank image to be edited
        im = Image.new(mode="RGB", size=(out_image.shape[2], out_image.shape[1]))
        pixels = im.load()

        # open source tiff file
        TAarray = np.array(out_image)

        # assign values to pixels(output) according to source tiff file
        for r in range(out_image.shape[1]):
            for c in range(out_image.shape[2]):
                val = TAarray[0, r, c]
                if val == 3:
                    pixels[c, r] = (0, 0, 255)  # water
                elif val == 4:
                    pixels[c, r] = (255, 255, 255)  # cloud
                elif val == 5:  # land
                    pixels[c, r] = (0, 255, 0)
                elif val >= 7 and val <= 9:
                    pixels[c, r] = (255, 0, 0)
                else:
                    pixels[c, r] = (0, 0, 0)  # none

        # Add text
        year = f[27:31]
        day = f[31:34]
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("Arial.ttf", 30)
        draw.text(
            (600, 50),
            "Year: " + year + ", Day: " + day,
            font=font,
            fill=(255, 255, 255),
        )

        # Write to destination
        imageio.imwrite(
            "TA_output/" + f[3:] + ".png",
            im,
        )


# Set up files and pool
if __name__ == "__main__":

    # Get all image files in the TA directory
    directory = "TA"
    currFile = 0
    totalFile = len(os.listdir(directory))
    files = []

    california_boundary = get_california_boundary()

    print("Getting Files...")
    # iterate over files in source dir
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f):
            # add files to array
            files.append(f)

    print("Generating Images...")
    with Pool() as pool:
        # Process images with the obtained dimensions
        pool.starmap(process_image, [(f, california_boundary) for f in files])
