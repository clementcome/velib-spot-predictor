from pathlib import Path

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

# douzieme_shp = gpd.read_file("data/external/douzieme_polygon.shx").loc[
#     0, "geometry"
# ]

# velib_folder = Path("data/interim/")

# for velib_path in tqdm(sorted(list(velib_folder.glob("*.pkl")))):
#     print("---")
#     print(velib_path)
#     print("Reading file")
#     velib_df = pd.read_pickle(velib_path)
#     print("Converting to GeoDataFrame")
#     velib_gdf = gpd.GeoDataFrame(
#         velib_df, geometry=gpd.points_from_xy(velib_df["lon"], velib_df["lat"])
#     )
#     print("Filtering")
#     douzieme_velib_gdf = velib_gdf[velib_gdf.within(douzieme_shp)]
#     print("Saving")
#     douzieme_velib_gdf.to_pickle(velib_folder / "douzieme" / velib_path.name)
#     del velib_df
#     del velib_gdf
#     del douzieme_velib_gdf
# break


# Concatenate files
velib_douzieme_folder = Path("data/interim/douzieme/")
douzieme_velib_dict = {}
for velib_path in tqdm(sorted(list(velib_douzieme_folder.glob("data_*.pkl")))):
    douzieme_velib_dict[velib_path.stem] = pd.read_pickle(velib_path)

douzieme_velib_df = (
    pd.concat(douzieme_velib_dict, axis=0)
    .reset_index(drop=True)
    .sort_values(["datetime", "station_id"])
)
douzieme_velib_df.to_pickle(velib_douzieme_folder / "aggregated.pkl")
