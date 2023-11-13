import rasterio
import datetime as dt
import numpy as np
import os


class PreprocessingFunctions:
    def __init__(self):
        # Setting up input directories
        self.out_dir = self.create_abs_path_from_relative("output")

        # Setting NDVI_inDir as a subfolder 'NDVI' within 'raw_data'
        raw_data_dir = self.create_abs_path_from_relative("raw_data")
        self.NDVI_inDir = os.path.join(raw_data_dir, "NDVI")

        self.EVI_temp = "EVI_temp.tif"
        self.EVIQA_temp = "EVIQA_temp.tif"
        self.BA_temp = "BA_temp.tif"
        self.BAQA_temp = "BAQA_temp.tif"

    def create_abs_path_from_relative(self, relative_dir_path):
        """Creates relative path from current directory to input file: 'raw_data' in project dir"""
        absolutepath = os.path.abspath(__file__)
        fileDirectory = os.path.dirname(absolutepath)
        return os.path.join(
            fileDirectory, relative_dir_path
        )  # Navigate to relative_dir_path directory

    def create_paths(self):
        """Create necessary directories if they do not exist."""
        for directory in [self.out_dir, self.NDVI_inDir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

    def extracting_good_quality_vals_from_NDVI_lut(self, lut):
        """Returns good quality values via look up table (LUT)"""
        # Include good quality based on MODLAND
        lut = lut[
            lut["MODLAND"].isin(
                ["VI produced with good quality", "VI produced, but check other QA"]
            )
        ]

        # Exclude lower quality VI usefulness
        VIU = [
            "Lowest quality",
            "Quality so low that it is not useful",
            "L1B data faulty",
            "Not useful for any other reason/not processed",
        ]
        lut = lut[~lut["VI Usefulness"].isin(VIU)]

        lut = lut[
            lut["Aerosol Quantity"].isin(["Low", "Average"])
        ]  # Include low or average aerosol
        lut = lut[
            lut["Adjacent cloud detected"] == "No"
        ]  # Include where adjacent cloud not detected
        lut = lut[
            lut["Mixed Clouds"] == "No"
        ]  # Include where mixed clouds not detected
        lut = lut[
            lut["Possible shadow"] == "No"
        ]  # Include where possible shadow not detected

        EVIgoodQuality = list(
            lut["Value"]
        )  # Retrieve list of possible QA values from the quality dataframe
        return EVIgoodQuality

    def go_to_parent_dir(self):
        path_parent = os.path.dirname(os.getcwd())
        os.chdir(path_parent)

    def getEVI_Date_Year_Month(self, productName, option):
        """Input: List of File Name, option: Y=year, M=month, D=date"""
        """ Returns: int Month or int Year, or String Date format MM/DD/YYYY"""
        EVIproductId = productName.split("_")[0]  # First: product name
        EVIlayerId = productName.split(EVIproductId + "_")[1].split("_doy")[
            0
        ]  # Second: layer name
        EVIyeardoy = productName.split(EVIlayerId + "_doy")[1].split("_aid")[
            0
        ]  # Third: date
        EVIaid = productName.split(EVIyeardoy + "_")[1].split(".tif")[
            0
        ]  # Fourth: unique ROI identifier (aid)
        EVIdate = dt.datetime.strptime(EVIyeardoy, "%Y%j").strftime(
            "%m/%d/%Y"
        )  # Convert YYYYDDD to MM/DD/YYYY
        EVI_year = dt.datetime.strptime(EVIyeardoy, "%Y%j").year
        EVI_month = dt.datetime.strptime(EVIyeardoy, "%Y%j").month
        if option == "Y":
            return EVI_year
        elif option == "M":
            return EVI_month
        else:
            return EVIdate

    def maskByShapefileAndStore(self, EVIFile, EVIqualityFile, county_shape):
        # Change to NDVI directory
        os.chdir(self.NDVI_inDir)
        EVIFile = rasterio.open(EVIFile, "r+")  # load NDVI
        EVIQAFile = rasterio.open(EVIqualityFile, "r+")  # load NDVI QA tif file

        EVI_out_image, EVI_out_transform = rasterio.mask.mask(
            EVIFile, county_shape, crop=True
        )
        EVIQA_out_image, EVIQA_out_transform = rasterio.mask.mask(
            EVIQAFile, county_shape, crop=True
        )

        # Get Metadata from source file and prepare for output file
        EVI_out_meta = EVIFile.meta
        EVIQA_out_meta = EVIQAFile.meta

        # Update output Matedata and send to a temp files.
        self.send_to_file(EVI_out_meta, EVI_out_transform, EVI_out_image, self.EVI_temp)
        self.send_to_file(
            EVIQA_out_meta, EVIQA_out_transform, EVIQA_out_image, self.EVIQA_temp
        )

    def send_to_file(self, out_metadata, out_transform, output_image, out_file_name):
        # update metadata
        out_metadata.update(
            {
                "driver": "GTiff",
                "height": output_image.shape[1],
                "width": output_image.shape[2],
                "transform": out_transform,
            }
        )
        # change to output directory
        os.chdir(self.out_dir)
        # write to file
        with rasterio.open(out_file_name, "w", **out_metadata) as dest:
            dest.write(output_image)

    def get_scaled_df(self, df_band, df_data, df_scaled_factor):
        df_fill = df_band.GetNoDataValue()  # Returns fill value
        df_data[
            df_data == df_fill
        ] = np.nan  # Set the fill value equal to NaN for the MaskedArray
        return df_data * df_scaled_factor  # Return Dataframe Scaled
