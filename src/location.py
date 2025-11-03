import pandas as pd
from geopy.geocoders import Nominatim
import time

df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")


df['Area Name'] = df['Area Name'].str.strip().str.lower()
coords_df['Area'] = coords_df['Area'].str.strip().str.lower()


merged = df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')


print("Total rows in dataset:", merged.shape[0])
print("Rows with valid coordinates:", merged[['Latitude','Longitude']].notnull().all(axis=1).sum())


missing_areas = merged[merged['Latitude'].isnull()]['Area Name'].unique()
print("Missing areas:", missing_areas[:20])

# 6. Use geopy to fill missing
geolocator = Nominatim(user_agent="traffic_app")

def fetch_coords(area):
    try:
        location = geolocator.geocode(f"{area}, Bangalore, India")
        if location:
            return pd.Series([location.latitude, location.longitude])
    except:
        return pd.Series([None, None])

coords_filled = pd.DataFrame(missing_areas, columns=['Area Name'])
coords_filled[['Latitude','Longitude']] = coords_filled['Area Name'].apply(fetch_coords)
time.sleep(1)

# 7. Merge filled coords back
merged = merged.merge(coords_filled, on='Area Name', how='left', suffixes=('','_new'))
merged['Latitude'] = merged['Latitude'].fillna(merged['Latitude_new'])
merged['Longitude'] = merged['Longitude'].fillna(merged['Longitude_new'])
merged = merged.drop(columns=['Latitude_new','Longitude_new'])

print("After geocoding, rows with coordinates:", merged[['Latitude','Longitude']].notnull().all(axis=1).sum())
