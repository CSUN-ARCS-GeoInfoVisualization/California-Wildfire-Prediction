import rasterio
import datetime as dt
import numpy as np
import os
from osgeo import gdal
from shapely.geometry import mapping

class BAPreprocessingFunctions:
    def __init__(self):
        # Set the output directory
        self.out_dir = "/Uses/wynshiesty/Desktop/Wildfire Machine Learning/California-Wildfire-Prediction/Data Processing/output"

        # Set the BA data directory
        self.BA_inDir = "/Usrs/wynshiesty/Desktop/Wildfire Machine Learning/California-Wildfire-Prediction/Data Processing/raw_data/BA"

        # Set the path for the shapefile
        self.shapefile_path = "/Usrs/wynshiesty/Desktop/Wildfire Machine Learning/California-Wildfire-Prediction/Data Processing/raw_data/BA/California_County_Boundaries.geojson"

        # Temporary file names for processing
        self.BA_temp = "BA_temp.tif"
        self.BAQA_temp = "BAQA_temp.tif"

        # Update paths to be absolute
        self.BA_temp_path = os.path.join(self.out_dir, self.BA_temp)
        self.BAQA_temp_path = os.path.join(self.out_dir, self.BAQA_temp)

    def create_paths(self):
        """Create necessary directories if they do not exist."""
        for directory in [self.out_dir, self.BA_inDir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

    def create_abs_path_from_relative(self, relative_dir_path):
        """Creates relative path from current directory to input file: 'raw_data' in project dir"""
        absolutepath = os.path.abspath(__file__)
        fileDirectory = os.path.dirname(absolutepath)
        return os.path.join(fileDirectory, relative_dir_path)

    def extract_custom_quality_vals_from_BA_lut(self, lut):
        # Step 1: Include rows where 'Valid data' is True
        lut = lut[lut['Valid data']]
        
        # Step 2: Include rows where 'Shortened mapping period' is False (as an example of a new condition)
        lut = lut[~lut['Shortened mapping period']]
        
        # Step 3: Exclude rows with certain 'Special circumstances unburned' conditions
        excluded_circumstances = [
            "Too few training observations or insufficient spectral separability between burned and unburned classes",
            "Valid observations spaced too sparsely in time",  # This is an additional condition to exclude
        ]
        lut = lut[~lut['Special circumstances unburned'].isin(excluded_circumstances)]
        
        # Step 4: Optionally, you might want to consider rows with 'Grid cell relabeled algorithm' as True
        lut = lut[lut['Grid cell relabeled algorithm']]
        
        # Retrieve list of possible QA values from the quality dataframe
        customQualityValues = list(lut['Value'])

        return customQualityValues

    def getBA_Date_Year_Month(self, productName, option):
        """Extracts date info from BA product name."""
        try:
            # The date part is the third element in the filename when split by '_'
            date_part = productName.split('_')[3]  # This should be 'doyYYYYDDD'
            print(f"Extracted date part from filename: {date_part}")

            # Parse the year, month, and full date
            BA_year = dt.datetime.strptime(date_part, 'doy%Y%j').year
            BA_month = dt.datetime.strptime(date_part, 'doy%Y%j').month
            BA_date = dt.datetime.strptime(date_part, 'doy%Y%j').strftime('%m/%d/%Y')

            if option == 'Y':
                return BA_year
            elif option == 'M':
                return BA_month
            else:
                return BA_date
        except Exception as e:
            print(f"Error in parsing date: {e}")
            return None

    def maskByShapefileAndStore(self, BAFile, BAqualityFile, county_shape):
        try:
            # Debugging print statement
            print("Trying to open BA file:", os.path.join(self.BA_inDir, BAFile))
            with rasterio.open(os.path.join(self.BA_inDir, BAFile)) as src:
                out_image, out_transform = rasterio.mask.mask(src, county_shape, crop=True)
                out_meta = src.meta
            out_meta.update({"driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})
            with rasterio.open(self.BA_temp_path, "w", **out_meta) as dest:
                dest.write(out_image)
                print(f"Temporary BA file created: {self.BA_temp_path}")

            # Handling the BA quality file
            print("Trying to open BA quality file:", os.path.join(self.BA_inDir, BAqualityFile))
            with rasterio.open(os.path.join(self.BA_inDir, BAqualityFile)) as src_quality:
                out_quality_image, out_quality_transform = rasterio.mask.mask(src_quality, county_shape, crop=True)
                out_quality_meta = src_quality.meta
            out_quality_meta.update({"driver": "GTiff", "height": out_quality_image.shape[1], "width": out_quality_image.shape[2], "transform": out_quality_transform})
            with rasterio.open(self.BAQA_temp_path, "w", **out_quality_meta) as dest_quality:
                dest_quality.write(out_quality_image)
                print(f"Temporary BA quality file created: {self.BAQA_temp_path}")

        except Exception as e:
            print(f"Error in maskByShapefileAndStore: {e}")


            
        
    
    def send_to_file(self, out_metadata, out_transform, output_image, out_file_name):
        """Writes processed data to a file."""
        out_metadata.update({"driver": "GTiff", "height": output_image.shape[1], "width": output_image.shape[2], "transform": out_transform})
        with rasterio.open(out_file_name, "w", **out_metadata) as dest:
            dest.write(output_image)

    def get_scaled_df(self, df_band, df_data, df_scaled_factor):
        """Scales the BA data according to a given scale factor."""
        df_fill = df_band.GetNoDataValue()  # Returns fill value
        df_data[df_data == df_fill] = np.nan  # Replace fill value with NaN
        return df_data * df_scaled_factor  # Return scaled data

