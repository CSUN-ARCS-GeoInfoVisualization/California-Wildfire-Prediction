# Directory setup notes: in the same dir as this .py file, there should be
# the PreprocessingFunctions.py, and 1 data folders:
# raw_data/NDVI(all the NDVI images, Lookup csv file, and California_County_Boundaries.geojs)

import rasterio.mask
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import os
import glob
from osgeo import gdal
import numpy as np
import datetime as dt
from shapely.geometry import mapping

from timeit import default_timer as timer
from PreprocessingFunctions import PreprocessingFunctions as auxFuncts


def main():
    start = timer()
    process = auxFuncts()
    process.create_paths()

    os.chdir(process.NDVI_inDir)  # Change to raw_data directory
    shapefile = glob.glob(
        "California_County_Boundaries.geojson"
    )  # Search for shapefile
    # Read the shapefile
    counties = gpd.read_file(shapefile[0])

    EVIFiles = glob.glob(
        "MOD13A1.061__500m_16_days_NDVI_**.tif"
    )  # Search for and create a list of EVI files
    EVIqualityFiles = glob.glob(
        "MOD13A1.061__500m_16_days_VI_Quality**.tif"
    )  # Search the directory for the associated quality .tifs
    EVIlut = glob.glob(
        "MOD13A1-061-500m-16-days-VI-Quality-lookup.csv"
    )  # Search for look up table
    EVI_v6_QA_lut = pd.read_csv(EVIlut[0])
    EVIgoodQuality = process.extracting_good_quality_vals_from_NDVI_lut(EVI_v6_QA_lut)

    ## Initialize Dataframe for final results
    NDVI_result = []

    # Traverse through the list of NDVI files
    for i in range(0, len(EVIFiles)):
        os.chdir(process.NDVI_inDir)

        quality_file = EVIFiles[i].replace("NDVI", "VI_Quality")
        # Check if the quality file exists
        if not os.path.exists(quality_file):
            print(f"No quality file found for {EVIFiles[i]}")
            continue

        EVI = gdal.Open(EVIFiles[i])  # Read file in dir raw_data

        dataset_metadata = EVI.GetMetadata()
        print("Metadata:", dataset_metadata)

        # Get scale factor from metadata
        scale_factor_key = "scale_factor"
        scale_factor = dataset_metadata.get(scale_factor_key)

        EVIquality = gdal.Open(quality_file)  # Open the first quality file

        EVIdate = process.getEVI_Date_Year_Month(
            EVIFiles[i], "D"
        )  # Get the Date of the file in format MM/DD/YYYY

        EVIscaleFactor = float(scale_factor)  # Set EVI Scale factor

        for index, county_masked in counties.iterrows():
            county_geom = [mapping(county_masked["geometry"])]
            process.maskByShapefileAndStore(EVIFiles[i], quality_file, county_geom)

            os.chdir(process.out_dir)  # out_dir
            EVI = gdal.Open(
                process.EVI_temp
            )  # Read EVI temporary file for current county in the loop
            EVIBand = EVI.GetRasterBand(1)  # Read the band (layer)
            EVIData = EVIBand.ReadAsArray().astype(
                "float"
            )  # Import band as an array with type float

            EVIquality = gdal.Open(
                process.EVIQA_temp
            )  # Open temporary EVI quality file
            EVIqualityData = EVIquality.GetRasterBand(
                1
            ).ReadAsArray()  # Read in as an array
            EVIquality = None

            EVIScaled = process.get_scaled_df(
                EVIBand, EVIData, EVIscaleFactor
            )  # Apply the scale factor using simple multiplication
            EVI = None  # Close the GeoTIFF file

            # ----- MASK AND GET MEAN VALUE -----#
            EVI_masked = np.ma.MaskedArray(
                EVIScaled, np.in1d(EVIqualityData, EVIgoodQuality, invert=True)
            )  # Apply QA mask to the EVI data

            # Compress the masked array to remove masked elements
            compressed_array = EVI_masked.compressed()

            # Check if the compressed array is empty or contains only NaN values
            if compressed_array.size == 0 or np.all(np.isnan(compressed_array)):
                # Handle the empty slice case, you might want to set it to NaN, zero, or some other value
                EVI_mean = (
                    np.nan
                )  # or another appropriate value like 0 or a custom flag
            else:
                # Calculate the mean if the array is not empty and does not contain only NaNs
                EVI_mean = np.nanmean(compressed_array)

            currentTime = timer() - start  # calculate curretn running time

            # ----- STORE IT IN RESULT DATAFRAME -----#
            NDVI_result.append(
                [
                    EVIdate,
                    EVI_mean,
                    county_masked["COUNTY_FIPS"],
                    county_masked["COUNTY_NAME"],
                ]
            )
        # print files information
        print(
            "index: {}  --- FileName: {}   ---- QualityFile: {}".format(
                i, EVIFiles[i], quality_file
            )
        )

    # print running time
    print("Total Processing Time: ", currentTime)

    # Delete the temp files
    if os.path.exists(process.EVI_temp):
        os.remove(process.EVI_temp)
    if os.path.exists(process.EVIQA_temp):
        os.remove(process.EVIQA_temp)

    # add header to output dataframe
    result_df = pd.DataFrame(
        NDVI_result, columns=["Date", "NDVI", "County_FIP", "County_Name"]
    )

    # fill null values with mean
    result_df["NDVI"].fillna(result_df["NDVI"].mean(), inplace=True)

    # sort values by county fip
    result_df = result_df.sort_values(["County_FIP"], ascending=(True))

    # change to output directory
    os.chdir(process.out_dir)

    # Export to CSV
    result_df.to_csv("NDVI_result.csv", index=False)


if __name__ == "__main__":
    main()
