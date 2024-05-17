from multiprocessing import Pool
import os
import imageio
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


def process_image(f, ROWS, COLS, california_boundary):
    with rasterio.open(f) as src:
        # Clip image to California boundary
        out_image, out_transform = mask(src, california_boundary, crop=True)
        out_meta = src.meta.copy()

        im = Image.new(mode="RGB", size=(out_image.shape[2], out_image.shape[1]))
        pixels = im.load()

        for r in range(out_image.shape[1]):
            for c in range(out_image.shape[2]):
                if out_image[0][r][c] > 0:
                    value = int(((out_image[0][r][c] + 2000) / 12000) * 350)
                    if value > 256:
                        pixels[c, r] = (0, 255, 0)
                    else:
                        pixels[c, r] = (255 - value, value, 0)
                else:
                    pixels[c, r] = (255, 255, 255)

        year = f[37:41]
        day = f[41:44]
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("Arial.ttf", 75)
        draw.text(
            (1600, 50), "Year: " + year + ", Day: " + day, font=font, fill=(0, 0, 0)
        )

        imageio.imwrite(
            "EVI_output/" + f[4:] + ".png",
            im,
        )


if __name__ == "__main__":

    # Get all image files in the EVI directory
    directory = "EVI"
    files = [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, filename))
    ]

    california_boundary = get_california_boundary()

    # Get dimensions of the first image
    with rasterio.open(files[0]) as src:
        ROWS, COLS = src.shape

    print("Generating Images...")
    with Pool() as pool:
        # Process images with the obtained dimensions
        pool.starmap(
            process_image, [(f, ROWS, COLS, california_boundary) for f in files]
        )
