import os
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.mask
from osgeo import gdal
from shapely.geometry import mapping
import datetime as dt
from timeit import default_timer as timer

from BA_PreprocessingFunctions import BAPreprocessingFunctions as auxFuncts

def main():
    print("Script started.")
    start = timer()
    currentTime = 0  # Initialize currentTime at the start
    process = auxFuncts()
    process.create_paths()

    # Change to BA data directory
    os.chdir(process.BA_inDir)

    # Read the shapefile for geographic boundaries
    if not os.path.exists(process.shapefile_path):
        print(f"Shapefile not found at {process.shapefile_path}")
        return
    else:
        print(f"Shapefile found: {process.shapefile_path}")

    counties = gpd.read_file(process.shapefile_path)

    # Get list of BA files and associated quality files
    BAFiles = glob.glob("MCD64A1.061_Burn_Date_*.tif")
    
    # Verify each BA file has a corresponding quality file
    for ba_file in BAFiles:
        quality_file = ba_file.replace("Burn_Date", "QA")
        if not os.path.exists(quality_file):
            print(f"Quality file missing for {ba_file}")
            continue

    BAlut = glob.glob("MCD64A1-061-QA-lookup (1).csv")
    if not BAlut:
        print("No BA quality lookup files found.")
        return
    else:
        print(f"BA quality lookup file found: {BAlut[0]}")

    BA_v6_QA_lut = pd.read_csv(BAlut[0])
    BAgoodQuality = process.extract_custom_quality_vals_from_BA_lut(BA_v6_QA_lut)

    print(f"BA good quality values: {BAgoodQuality}")

    BA_result = []  # Initialize BA_result

    # Process each BA file
    for i, ba_file in enumerate(BAFiles):
        print(f"Processing file {i + 1}/{len(BAFiles)}: {ba_file}")
        try:
            os.chdir(process.BA_inDir)

            BA = gdal.Open(ba_file)
            dataset_metadata = BA.GetMetadata()
            print("Metadata:", dataset_metadata)

            scale_factor_key = "scale_factor"
            scale_factor = dataset_metadata.get(scale_factor_key, "1.0")
            BAquality = gdal.Open(quality_file)

            BADate = process.getBA_Date_Year_Month(ba_file, "D")

            BAscaleFactor = float(scale_factor)

            for index, county_masked in counties.iterrows():
                county_geom = [mapping(county_masked["geometry"])]
                process.maskByShapefileAndStore(ba_file, quality_file, county_geom)

                os.chdir(process.out_dir)
                BA = gdal.Open(process.BA_temp)
                BABand = BA.GetRasterBand(1)
                BAData = BABand.ReadAsArray().astype("float")
                BAquality = gdal.Open(process.BAQA_temp)
                BAqualityData = BAquality.GetRasterBand(1).ReadAsArray()
                BAquality = None

                BAScaled = process.get_scaled_df(BABand, BAData, BAscaleFactor)
                BA = None

                BA_masked = np.ma.MaskedArray(
                    BAScaled, np.in1d(BAqualityData, BAgoodQuality, invert=True)
                )

                compressed_array = BA_masked.compressed()
                if compressed_array.size == 0 or np.all(np.isnan(compressed_array)):
                    BA_mean = np.nan
                else:
                    BA_mean = np.nanmean(compressed_array)

                BA_result.append(
                    [
                        BADate,
                        BA_mean,
                        county_masked["COUNTY_FIPS"],
                        county_masked["COUNTY_NAME"],
                    ]
                )

                currentTime = timer() - start

            print(f"Finished processing file: {ba_file}")

        except Exception as e:
            print(f"An error occurred while processing {ba_file}: {e}")

    print("Total Processing Time: ", currentTime)

    # Clean up temporary files
    if os.path.exists(process.BA_temp):
        os.remove(process.BA_temp)
    if os.path.exists(process.BAQA_temp):
        os.remove(process.BAQA_temp)

    if BA_result:
        result_df = pd.DataFrame(
            BA_result, columns=["Date", "BA", "County_FIP", "County_Name"]
        )

        result_df["BA"].fillna(result_df["BA"].mean(), inplace=True)
        result_df = result_df.sort_values(["County_FIP"], ascending=True)
        os.chdir(process.out_dir)
        result_df.to_csv("BA_result.csv", index=False)
        print("Results have been saved to BA_result.csv")
    else:
        print("No data was processed. BA_result.csv was not created.")

if __name__ == "__main__":
    main()
