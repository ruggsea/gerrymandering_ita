import pandas as pd
import geopandas as gpd

def load_data():
    file_path = 'politiche_2022_liste_camera_comuni.csv'
    df = pd.read_csv(file_path)

    gdf = gpd.read_file('comuni_italiani_trend_liste_2022_2024.geojson')[["name", "com_istat_code_num", "geometry"]]
    
    return df, gdf

if __name__ == "__main__":
    df, gdf = load_data()
    print(df.head())
    print(gdf.head())
