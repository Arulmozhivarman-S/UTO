import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice
from functools import lru_cache
import time
import plotly.express as px
import pandas as pd
from folium.plugins import HeatMap

# ---------- CONFIG ----------
st.set_page_config(page_title="Urban Transit Optimizer – Bangalore", layout="wide")
st.title("🚏 Urban Transit Optimizer – Bangalore City")

ORS_API_KEY = "YOUR_OPENROUTESERVICE_KEY"
client = openrouteservice.Client(key=ORS_API_KEY)

USE_MOCK_ROUTES = False  # Set True if ORS is slow or throttled

# ---------- MOCK DATA ----------
bus_data = {
    "335E": {"lat": 12.9716, "lon": 77.5946, "route": "Majestic → Electronic City", "diverted": False, "delay": 3},
    "500D": {"lat": 12.9250, "lon": 77.5930, "route": "Hebbal → Silk Board", "diverted": True, "delay": 10},
    "600K": {"lat": 12.983, "lon": 77.605, "route": "Kengeri → ITPL", "diverted": False, "delay": 5},
    "201R": {"lat": 12.935, "lon": 77.585, "route": "Banashankari → Whitefield", "diverted": True, "delay": 12},
}

# ---------- FUNCTIONS ----------
@st.cache_data(show_spinner=False)
def get_route(coords):
    """Fetch route with caching."""
    return client.directions(coords, profile='driving-car', format='geojson')

def fetch_bus_data(bus_number):
    """Mock fetch (replace with BMTC API later)."""
    return bus_data.get(bus_number)

# ---------- TABS ----------
tab_driver, tab_admin, tab_analytics = st.tabs(["🚌 Driver Control / Bus Tracker", "🧭 Admin Dashboard", "📊 Analytics"])

# ---------- DRIVER TAB ----------
with tab_driver:
    import pandas as pd
    import folium
    from streamlit_folium import st_folium

    st.header("🚌 Driver Dashboard – Route & Live Map")
    st.write("Monitor your assigned bus route and see nearby stops or congestion zones.")

    # ---- Mock bus data (you can replace this with real route data later) ----
    bus_data = {
        "335E": {"lat": 12.9716, "lon": 77.5946, "route": "Majestic → Electronic City", "status": "On Time"},
        "500D": {"lat": 12.9250, "lon": 77.5930, "route": "Hebbal → Silk Board", "status": "Delayed"},
        "600K": {"lat": 12.983, "lon": 77.605, "route": "Kengeri → ITPL", "status": "On Time"},
    }

    # ---- Bus route selection ----
    selected_bus = st.selectbox("Select your Bus Number:", list(bus_data.keys()))

    # Get bus info
    bus_info = bus_data[selected_bus]
    st.markdown(f"### 🛣️ Route: `{bus_info['route']}`")
    st.markdown(f"**Current Status:** {bus_info['status']}")

    # ---- Map Setup ----
    driver_map = folium.Map(location=[bus_info["lat"], bus_info["lon"]], zoom_start=13)

    # Add current bus marker
    folium.Marker(
        location=[bus_info["lat"], bus_info["lon"]],
        popup=f"Bus {selected_bus} – {bus_info['route']}",
        icon=folium.Icon(color="blue", icon="bus", prefix="fa"),
    ).add_to(driver_map)

    # ---- Simulated Bus Stops (you can replace this with real stops later) ----
    stops = [
        {"name": "Majestic", "lat": 12.9778, "lon": 77.5713},
        {"name": "Richmond Circle", "lat": 12.9667, "lon": 77.6010},
        {"name": "Madiwala", "lat": 12.9179, "lon": 77.6101},
        {"name": "Silk Board", "lat": 12.9172, "lon": 77.6233},
    ]

    for stop in stops:
        folium.CircleMarker(
            location=(stop["lat"], stop["lon"]),
            radius=6,
            color="green",
            fill=True,
            fill_color="green",
            fill_opacity=0.6,
            popup=f"Stop: {stop['name']}",
        ).add_to(driver_map)

    # ---- Display map ----
    st_folium(driver_map, width=850, height=500)

    # ---- Notes or Alerts ----
    st.info("🟢 All systems normal. Bus is operating on its usual route.")

# ---------- ADMIN TAB ----------
with tab_admin:
    import pandas as pd
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium

    st.header("🧭 Admin Dashboard – Active Buses + Traffic Prediction")
    st.write("Monitor real-time bus positions and predicted congestion-prone zones across Bangalore.")

    # ---- Expanded bus data (mock live positions) ----
    bus_data = {
        "335E": {"lat": 12.9716, "lon": 77.5946, "route": "Majestic → Electronic City", "diverted": False},
        "500D": {"lat": 12.9250, "lon": 77.5930, "route": "Hebbal → Silk Board", "diverted": True},
        "600K": {"lat": 12.9830, "lon": 77.6050, "route": "Kengeri → ITPL", "diverted": False},
        "215C": {"lat": 12.9350, "lon": 77.6145, "route": "BTM → Majestic", "diverted": True},
        "201R": {"lat": 12.9575, "lon": 77.7002, "route": "JP Nagar → Whitefield", "diverted": False},
        "356B": {"lat": 12.9041, "lon": 77.6593, "route": "Marathahalli → Silk Board", "diverted": False},
        "600MA": {"lat": 12.9980, "lon": 77.5830, "route": "Yeshwanthpur → Kengeri", "diverted": False},
        "365J": {"lat": 12.9178, "lon": 77.6112, "route": "Banashankari → ITPL", "diverted": True},
        "210B": {"lat": 12.9405, "lon": 77.5350, "route": "Vijayanagar → BTM Layout", "diverted": False},
        "150E": {"lat": 12.9590, "lon": 77.6800, "route": "Domlur → KR Puram", "diverted": False},
        "KIAS5": {"lat": 13.0100, "lon": 77.6220, "route": "Kempegowda Intl Airport → Majestic", "diverted": True},
        "600CF": {"lat": 12.9350, "lon": 77.4850, "route": "RR Nagar → ITPL", "diverted": False},
        "500C": {"lat": 12.9880, "lon": 77.5500, "route": "Banashankari → Hebbal", "diverted": False},
        "MBS9": {"lat": 12.9490, "lon": 77.6400, "route": "Koramangala → Majestic", "diverted": True},
        "401K": {"lat": 13.0250, "lon": 77.5900, "route": "Peenya → Silk Board", "diverted": False},
    }

    # ---- Load your traffic spot prediction dataset ----
    traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
    coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

    traffic_df['Area Name'] = (
    traffic_df['Area Name']
    .str.strip()
    .str.lower()
    .str.replace(" ", "")
    )
    coords_df['Area'] = (
        coords_df['Area']
        .str.strip()
        .str.lower()
        .str.replace(" ", "")
    )

    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="inner")


    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
    merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
    merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')

    latest = merged.sort_values("Date").groupby("Area Name").tail(1)

    # ---- Map setup ----
    admin_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(admin_map)

    # ---- Helper to choose marker color ----
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

    # ---- Plot predicted traffic ----
    for _, row in latest.iterrows():
        if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
            color = congestion_color(row['Congestion Level'])
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"{row['Area Name'].title()} – Congestion: {row['Congestion Level']:.1f}%",
            ).add_to(marker_cluster)

    # ---- Plot all bus locations ----
    for bus, info in bus_data.items():
        color = "orange" if info["diverted"] else "blue"
        folium.Marker(
            location=(info["lat"], info["lon"]),
            popup=f"🚌 Bus {bus} – {info['route']} ({'Diverted' if info['diverted'] else 'Normal'})",
            icon=folium.Icon(color=color, icon="bus", prefix="fa"),
        ).add_to(admin_map)

    st_folium(admin_map, width=850, height=550)
    st.success("✅ Admin map loaded with 15 buses and congestion predictions.")


# ---------- ANALYTICS TAB ----------
# ---------- ANALYTICS TAB ----------
with tab_analytics:
    import plotly.express as px
    import pandas as pd
    import folium
    from folium.plugins import HeatMap
    from streamlit_folium import st_folium

    st.header("📊 Analytics & Insights")
    st.subheader("🚦 Transit Efficiency Dashboard")

    # ---- Bus delay + diversion mock stats ----
    bus_data = {
        "335E": {"delay": 6, "diverted": False},
        "500D": {"delay": 10, "diverted": True},
        "600K": {"delay": 8, "diverted": False},
        "215C": {"delay": 15, "diverted": True},
        "201R": {"delay": 4, "diverted": False},
        "356B": {"delay": 7, "diverted": False},
        "600MA": {"delay": 6, "diverted": False},
        "365J": {"delay": 13, "diverted": True},
        "210B": {"delay": 5, "diverted": False},
        "150E": {"delay": 9, "diverted": False},
        "KIAS5": {"delay": 20, "diverted": True},
        "600CF": {"delay": 8, "diverted": False},
        "500C": {"delay": 7, "diverted": False},
        "MBS9": {"delay": 12, "diverted": True},
        "401K": {"delay": 6, "diverted": False},
    }

    df = pd.DataFrame(bus_data).T.reset_index().rename(columns={"index": "Bus"})
    df["status"] = df["diverted"].apply(lambda x: "Diverted" if x else "Normal")

    # ---- Charts ----
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⏱️ Average Delay per Bus")
        fig = px.bar(df, x="Bus", y="delay", color="status",
                     labels={"delay": "Delay (minutes)"},
                     title="Bus Delay Overview")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📈 Route Diversion Ratio")
        count_chart = px.pie(df, names="status", title="Diverted vs Normal",
                             color_discrete_sequence=["blue", "orange"])
        st.plotly_chart(count_chart, use_container_width=True)

    # ---- Congestion heatmap ----
    st.markdown("### 🗺️ Congestion Heatmap (Predicted Traffic Data)")

    traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
    coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

    traffic_df['Area Name'] = traffic_df['Area Name'].str.strip().str.lower()
    coords_df['Area'] = coords_df['Area'].str.strip().str.lower()

    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
    merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
    merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')

    heat_data = [
        (row["Latitude"], row["Longitude"], row["Congestion Level"])
        for _, row in merged.iterrows()
        if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"])
    ]

    heatmap = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    HeatMap(heat_data, radius=18, blur=15, min_opacity=0.5).add_to(heatmap)
    st_folium(heatmap, width=850, height=500)

    # ---- Top congested areas ----
    st.markdown("### 🚧 Most Congested Areas")
    latest = merged.sort_values("Date").groupby("Area Name").tail(1)
    top_congested = latest.nlargest(7, "Congestion Level")[["Area Name", "Congestion Level"]]
    st.table(top_congested.rename(columns={"Area Name": "Area", "Congestion Level": "Congestion (%)"}))

    st.success("✅ Analytics dashboard loaded successfully with 15 buses + congestion insights.")


