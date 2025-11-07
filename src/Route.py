import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice
import time
import plotly.express as px
import pandas as pd
from folium.plugins import HeatMap

# ---------- CONFIG ----------
st.set_page_config(page_title="Urban Transit Optimizer – Bangalore", layout="wide")
st.title("🚏 Urban Transit Optimizer – Bangalore City")

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjhiYzgzNmNhYmEzOTRhYzdiNjE3OWVhMmQ1NjgyOWRjIiwiaCI6Im11cm11cjY0In0"
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
def get_route(coords):
    """Fetch route with caching."""
    return client.directions(coords, profile='driving-car', format='geojson')

def fetch_bus_data(bus_number):
    """Mock fetch (replace with BMTC API later)."""
    return bus_data.get(bus_number)

# ---------- TABS ----------
tab_driver, tab_admin, tab_analytics = st.tabs(["🚌 Driver Control / Bus Tracker", "🧭 Admin Dashboard", "📊 Analytics"])


with tab_driver:
# ---------- DRIVER TAB ----------
    import streamlit as st
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import AntPath
    import json
    import time
    from geopy.distance import geodesic

    st.title("🚌 Driver Dashboard – Real Route + Live Traffic Diversion")

    # --- Load route data ---
    # @st.cache_data
    def load_routes():
        return pd.read_csv("utc/src/bmtc_routes_map.csv")

    # @st.cache_data
    def load_traffic_data():
    
        traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
        coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

        traffic_df["Area Name"] = traffic_df["Area Name"].str.strip().str.lower().str.replace(" ", "")
        coords_df["Area"] = coords_df["Area"].str.strip().str.lower().str.replace(" ", "")
        merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")

        merged = merged.dropna(subset=["Latitude", "Longitude"])
        latest = merged.sort_values("Date").groupby("Area Name").tail(1)
        return latest

    routes_df = load_routes()
    traffic_data = load_traffic_data()

        # --- Route Selection ---
    routes = routes_df["route_no"].unique()
    selected_route = st.selectbox("Select Bus Route", routes)

    route_data = routes_df[routes_df["route_no"] == selected_route].iloc[0]
    st.write(f"**Origin:** {route_data['origin']}")
    st.write(f"**Departure Times:** {route_data['departure_from_origin']}")

        # --- Parse Route JSON ---
    try:
        route_stops = json.loads(route_data["map_json_content"].replace("'", '"'))
    except Exception as e:
        st.error(f"Error parsing route JSON: {e}")
        st.stop()

    coords = [(float(stop["latlons"][0]), float(stop["latlons"][1])) for stop in route_stops]

        # --- Helper function for congestion color ---
    def congestion_color(level):
        if level > 80:
            return "red"
        elif level > 50:
            return "orange"
        else:
            return "green"

        # --- Detect congestion near the route ---
    def find_nearby_congested_points(coords, traffic_df, radius_m=300):
        congested_points = []
        for _, t in traffic_df.iterrows():
            point = (t["Latitude"], t["Longitude"])
            for c in coords:
                if geodesic(c, point).meters <= radius_m and t["Congestion Level"] > 60:
                    congested_points.append(point)
                    break
        return congested_points

    congested_points = find_nearby_congested_points(coords, traffic_data)

        # --- Map setup ---
    center = coords[len(coords)//2]
    m = folium.Map(location=center, zoom_start=13, tiles="CartoDB positron")

        # --- Plot traffic data ---
    for _, row in traffic_data.iterrows():
        color = congestion_color(row["Congestion Level"])
        folium.CircleMarker(
            location=(row["Latitude"], row["Longitude"]),
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
                popup=f"{row['Area Name'].title()} - {row['Congestion Level']:.1f}%"
            ).add_to(m)

        # --- Add main route ---
    AntPath(coords, color="green", delay=800, weight=4).add_to(m)

        # --- Add simulated diverted path if traffic ---
    diversion_coords = []
    if congested_points:
        st.warning("⚠️ Traffic detected on route. Simulating diversion...")
        diversion_coords = coords.copy()
        # Slight deviation for congested points (simulate bypass)
        for i, (lat, lon) in enumerate(diversion_coords):
            for c in congested_points:
                if geodesic((lat, lon), c).meters < 300:
                    diversion_coords[i] = (lat + 0.002, lon + 0.002)
            AntPath(diversion_coords, color="red", weight=3, dash_array=[10, 20]).add_to(m)

        # --- Plot stops ---
    for stop in route_stops:
        lat, lon = map(float, stop["latlons"])
        folium.CircleMarker(
            location=(lat, lon),
            radius=4,
            color="blue",
            fill=True,
            fill_color="blue",
            popup=stop["busstop"]
        ).add_to(m)

        # --- Simulation of bus movement ---
    st.subheader("🟢 Simulated Bus Movement")
    start_button = st.button("Start Simulation")

    if start_button:
        with st.empty():
            path = diversion_coords if diversion_coords else coords
            for i, (lat, lon) in enumerate(path):
                temp_map = folium.Map(location=center, zoom_start=13, tiles="CartoDB positron")
                # Re-draw route
                AntPath(path, color="green", delay=800, weight=4).add_to(temp_map)
                # Re-draw traffic
                for _, row in traffic_data.iterrows():
                    color = congestion_color(row["Congestion Level"])
                    folium.CircleMarker(
                        location=(row["Latitude"], row["Longitude"]),
                        radius=5,
                        color=color,
                        fill=True,
                        fill_color=color,
                            fill_opacity=0.6
                        ).add_to(temp_map)

                    # Add bus marker
                folium.Marker(
                    location=(lat, lon),
                    icon=folium.Icon(color="red", icon="bus", prefix="fa"),
                    popup=f"Bus moving... {i+1}/{len(path)}"
                ).add_to(temp_map)
                st_folium(temp_map, width=850, height=550)
                time.sleep(1.2)
    else:
        st_folium(m, width=850, height=550)







# ---------- ADMIN TAB ----------
with tab_admin:
    import pandas as pd
    import folium
    import json
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium

    st.header("🧭 Admin Dashboard – Active Buses, Traffic & Passenger Demand")
    st.write("Monitor real-time buses, predicted congestion, and passenger demand hotspots across Bangalore.")

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

    # ---- Load traffic spot prediction dataset ----
    traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
    coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

    traffic_df['Area Name'] = (
        traffic_df['Area Name'].str.strip().str.lower().str.replace(" ", "")
    )
    coords_df['Area'] = (
        coords_df['Area'].str.strip().str.lower().str.replace(" ", "")
    )

    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
    merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
    merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')
    latest = merged.sort_values("Date").groupby("Area Name").tail(1)

    # ---- Load passenger demand JSON ----
    try:
        with open("C:/Users/Anitha/Desktop/urban-transit/utc/src/demand.json", "r") as f:
            demand_data = json.load(f)["demand"]
    except Exception as e:
        st.warning(f"⚠️ Could not load passenger demand file: {e}")
        demand_data = {}

    # ---- Create map ----
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
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"🚦 {row['Area Name'].title()} – {row['Congestion Level']:.1f}% Congestion",
            ).add_to(marker_cluster)

    # ---- Plot passenger demand ----
    for stop, demand in demand_data.items():
        try:
            loc_name, coord_str = stop.split("|")
            lat, lon = map(float, coord_str.split(","))
            color = (
                "voilet" if demand ==1 else ""
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=2,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"👥 {loc_name}<br>Demand: {demand:.2f}",
            ).add_to(admin_map)
        except Exception as e:
            continue

    # ---- Plot all bus locations ----
    for bus, info in bus_data.items():
        color = "orange" if info["diverted"] else "blue"
        folium.Marker(
            location=(info["lat"], info["lon"]),
            popup=f"🚌 Bus {bus} – {info['route']} ({'Diverted' if info['diverted'] else 'Normal'})",
            icon=folium.Icon(color=color, icon="bus", prefix="fa"),
        ).add_to(admin_map)

    # ---- Display map ----
    st_folium(admin_map, width=850, height=550)
    st.success("✅ Admin map updated with buses, traffic predictions, and passenger demand overlays.")









# ---------- ANALYTICS TAB ----------
with tab_analytics:
    import plotly.express as px
    import pandas as pd
    import folium
    from folium.plugins import HeatMap
    from streamlit_folium import st_folium
    import random

    st.header("📊 Analytics & Insights")
    st.subheader("🚦 Transit Efficiency Dashboard (Dynamic Data)")

    # ---- Load route dataset ----
    try:
        routes_df = pd.read_csv("utc/src/bmtc_routes_map.csv")
    except Exception as e:
        st.error(f"❌ Could not load route data: {e}")
        st.stop()

    # ---- Prepare mock performance metrics using actual route count ----
    route_nos = routes_df["route_no"].unique().tolist()
    bus_data = []

    for route in route_nos[:15]:  # limit to 15 buses for clarity
        delay = random.uniform(3, 15)  # random delay 3–15 min
        diverted = random.choice([True, False])
        bus_data.append({"Bus": route, "delay": delay, "diverted": diverted})

    df = pd.DataFrame(bus_data)
    df["status"] = df["diverted"].apply(lambda x: "Diverted" if x else "Normal")

    # ---- Charts ----
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⏱️ Average Delay per Bus (Live Estimate)")
        fig = px.bar(df, x="Bus", y="delay", color="status",
                     labels={"delay": "Delay (minutes)"},
                     title="Bus Delay Overview (Based on Current Routes)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📈 Route Diversion Ratio")
        count_chart = px.pie(df, names="status", title="Diverted vs Normal Routes",
                             color_discrete_sequence=["blue", "orange"])
        st.plotly_chart(count_chart, use_container_width=True)

    # ---- Congestion heatmap ----
    st.markdown("### 🗺️ Congestion Heatmap (Predicted Traffic Data)")

    try:
        traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
        coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")
    except Exception as e:
        st.error(f"❌ Could not load traffic datasets: {e}")
        st.stop()

    traffic_df['Area Name'] = traffic_df['Area Name'].str.strip().str.lower()
    coords_df['Area'] = coords_df['Area'].str.strip().str.lower()

    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
    merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
    merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')

    # ---- Prepare heatmap data ----
    heat_data = [
        (row["Latitude"], row["Longitude"], row["Congestion Level"])
        for _, row in merged.iterrows()
        if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"])
    ]

    heatmap = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    HeatMap(heat_data, radius=18, blur=15, min_opacity=0.5).add_to(heatmap)
    st_folium(heatmap, width=850, height=500)

    # ---- Top congested areas ----
    st.markdown("### 🚧 Most Congested Areas (Latest Data)")
    latest = merged.sort_values("Date").groupby("Area Name").tail(1)
    top_congested = latest.nlargest(7, "Congestion Level")[["Area Name", "Congestion Level"]]
    st.table(top_congested.rename(columns={"Area Name": "Area", "Congestion Level": "Congestion (%)"}))

    # ---- Summary Stats ----
    avg_delay = round(df["delay"].mean(), 2)
    diversion_rate = round((df["diverted"].sum() / len(df)) * 100, 1)
    avg_congestion = round(latest["Congestion Level"].mean(), 1)

    st.info(f"""
    **System Summary**
    - 🚌 Average Bus Delay: **{avg_delay} min**
    - 🔁 Route Diversions: **{diversion_rate}%**
    - 🚦 Average Citywide Congestion: **{avg_congestion}%**
    """)

    st.success("✅ Analytics dashboard loaded dynamically from datasets.")

