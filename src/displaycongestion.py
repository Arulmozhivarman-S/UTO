import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import time
import streamlit as st
from streamlit_folium import st_folium
import plotly.express as px

# --- Load Data ---
df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

df['Area Name'] = df['Area Name'].str.strip().str.lower()
coords_df['Area'] = coords_df['Area'].str.strip().str.lower()

merged = df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')

# --- Fill missing coordinates ---
missing_areas = merged[merged['Latitude'].isnull()]['Area Name'].unique()
if len(missing_areas) > 0:
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

    merged = merged.merge(coords_filled, on='Area Name', how='left', suffixes=('','_new'))
    merged['Latitude'] = merged['Latitude'].fillna(merged['Latitude_new'])
    merged['Longitude'] = merged['Longitude'].fillna(merged['Longitude_new'])
    merged = merged.drop(columns=['Latitude_new','Longitude_new'])

# --- Prepare latest data ---
latest = merged.sort_values("Date").groupby("Area Name").tail(1)

# --- Helper function ---
def congestion_color(level):
    try:
        level = float(level)
        if level > 80:
            return 'red'
        elif level > 50:
            return 'orange'
        else:
            return 'green'
    except:
        return 'gray'

# --- Streamlit Dashboard ---
st.set_page_config(page_title="Bangalore Traffic Dashboard", layout="wide")
st.title("🚌 Bangalore Traffic Dashboard")
st.markdown("Visualize congestion levels across Bangalore areas in real-time.")

# Sidebar filters
st.sidebar.header("Filters")
congestion_filter = st.sidebar.slider("Minimum Congestion Level (%)", 0, 100, 0)
areas_filter = st.sidebar.multiselect(
    "Select Areas",
    options=latest['Area Name'].str.title().tolist(),
    default=latest['Area Name'].str.title().tolist()
)

# Filter data
filtered_data = latest[
    (latest['Congestion Level'] >= congestion_filter) &
    (latest['Area Name'].str.title().isin(areas_filter))
]

# --- Top container: Map ---
with st.container():
    st.subheader("📍 Traffic Map")
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in filtered_data.iterrows():
        if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
            color = congestion_color(row['Congestion Level'])
            radius = max(5, min(30, float(row['Congestion Level']) / 5))
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"{row['Area Name'].title()} – Congestion: {row['Congestion Level']:.1f}%"
            ).add_to(marker_cluster)
    # Reduced width and height for better screen fit
    st_folium(m, width=800, height=450)

# --- Bottom container: Stats & Charts ---
with st.container():
    st.subheader("📊 Congestion Distribution")
    fig = px.histogram(
        filtered_data,
        x='Congestion Level',
        nbins=20,
        title="Distribution of Congestion Levels",
        labels={'Congestion Level': 'Congestion (%)'},
        color_discrete_sequence=['orange']
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔥 Top 5 Most Congested Areas")
    top5 = filtered_data.sort_values("Congestion Level", ascending=False).head(5)
    st.table(top5[['Area Name', 'Congestion Level']].rename(columns={'Area Name':'Area'}))