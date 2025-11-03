
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

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjhiYzgzNmNhYmEzOTRhYzdiNjE3OWVhMmQ1NjgyOWRjIiwiaCI6Im11cm11cjY0In0="
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
    st.header("🔍 Bus Live Tracker & Dynamic Rerouting")

    bus_no = st.text_input("Enter Bus Number (e.g., 335E, 500D, 600K, 201R):")
    if bus_no:
        with st.spinner(f"Fetching data for bus {bus_no}..."):
            info = fetch_bus_data(bus_no)
            time.sleep(0.5)

            if not info:
                st.error("❌ Bus not found. Try 335E, 500D, 600K, or 201R.")
            else:
                lat, lon = info["lat"], info["lon"]
                diverted = info["diverted"]

                start = (lat, lon)
                destination = (12.980, 77.605)
                traffic_spot = (12.975, 77.597)
                alt_waypoint = (12.977, 77.600)

                try:
                    if USE_MOCK_ROUTES:
                        route = None
                    else:
                        coords = [start[::-1], (alt_waypoint[::-1] if diverted else traffic_spot[::-1]), destination[::-1]]
                        route = get_route(tuple(coords))
                except Exception:
                    st.warning("⚠️ Route service unavailable, using mock path.")
                    route = None

                # Map
                m = folium.Map(location=start, zoom_start=14)
                color = "orange" if diverted else "blue"
                label = "Diverted Route" if diverted else "Original Route"

                if route:
                    folium.GeoJson(route, style_function=lambda x: {'color': color, 'weight': 4, 'opacity': 0.8}, tooltip=label).add_to(m)
                folium.Marker(location=start, popup=f"🚌 Bus {bus_no}", icon=folium.Icon(color="blue", icon="bus", prefix="fa")).add_to(m)
                folium.Marker(location=destination, popup="Destination", icon=folium.Icon(color="green")).add_to(m)

                if diverted:
                    folium.Marker(location=alt_waypoint, icon=folium.Icon(color="orange"), popup="Alternate Route").add_to(m)
                else:
                    folium.CircleMarker(location=traffic_spot, radius=10, color="red", fill=True, fill_color="red", popup="Traffic Spot").add_to(m)

                st_folium(m, width=850, height=500)

                st.markdown(f"""
                **🚌 Bus {bus_no} Details**
                - Route: {info['route']}
                - Status: {"🚧 Diverted due to traffic" if diverted else "✅ On original route"}
                - Avg Delay: {info['delay']} min
                """)

# ---------- ADMIN TAB ----------
with tab_admin:
    import pandas as pd
    from folium.plugins import MarkerCluster

    st.header("🧭 Admin Dashboard – Active Buses + Traffic Prediction")
    st.write("Monitor active buses and congestion-prone zones in Bangalore.")

    # ---- Mock bus data (replace with live API data) ----
    bus_data = {
        "335E": {"lat": 12.9716, "lon": 77.5946, "route": "Majestic → Electronic City", "diverted": False},
        "500D": {"lat": 12.9250, "lon": 77.5930, "route": "Hebbal → Silk Board", "diverted": True},
        "600K": {"lat": 12.983, "lon": 77.605, "route": "Kengeri → ITPL", "diverted": False},
    }

    # ---- Load your traffic spot prediction dataset ----
    traffic_df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
    coords_df = pd.read_csv("utc/src/BangaloreAreaLatLongDetails.csv")

    traffic_df['Area Name'] = traffic_df['Area Name'].str.strip().str.lower()
    coords_df['Area'] = coords_df['Area'].str.strip().str.lower()

    merged = traffic_df.merge(coords_df, left_on="Area Name", right_on="Area", how="left")
    merged['Latitude'] = pd.to_numeric(merged['Latitude'], errors='coerce')
    merged['Longitude'] = pd.to_numeric(merged['Longitude'], errors='coerce')
    latest = merged.sort_values("Date").groupby("Area Name").tail(1)

    # ---- Map setup ----
    admin_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(admin_map)

    # ---- Add traffic predictions ----
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
                popup=f"{row['Area Name'].title()} – Congestion: {row['Congestion Level']:.1f}%"
            ).add_to(marker_cluster)

    # ---- Add buses on the same map ----
    for bus, info in bus_data.items():
        color = "orange" if info["diverted"] else "blue"
        folium.Marker(
            location=(info["lat"], info["lon"]),
            popup=f"Bus {bus} – {info['route']} ({'Diverted' if info['diverted'] else 'Normal'})",
            icon=folium.Icon(color=color, icon="bus", prefix="fa")
        ).add_to(admin_map)

    # ---- Display merged map ----
    st_folium(admin_map, width=850, height=550)
    st.success("✅ Admin map loaded with live buses and predicted traffic spots.")

# ---------- ANALYTICS TAB ----------
with tab_analytics:
    import pandas as pd
    import plotly.express as px
    from folium.plugins import HeatMap

    st.header("📊 Analytics & Insights")
    st.subheader("🚦 Transit Efficiency Dashboard")

    # --- Sample analytics data (mock for now) ---
    bus_data = {
        "335E": {"lat": 12.9716, "lon": 77.5946, "diverted": False, "delay": 5, "route": "Majestic → Electronic City"},
        "500D": {"lat": 12.9250, "lon": 77.5930, "diverted": True, "delay": 12, "route": "Hebbal → Silk Board"},
        "600K": {"lat": 12.9830, "lon": 77.6050, "diverted": False, "delay": 7, "route": "Kengeri → ITPL"},
        "201R": {"lat": 12.9500, "lon": 77.5800, "diverted": True, "delay": 15, "route": "Banashankari → Yeshwanthpur"},
        "V-365B": {"lat": 12.9600, "lon": 77.6900, "diverted": False, "delay": 8, "route": "Banashankari → Kadugodi"},
    }

    df = pd.DataFrame(bus_data).T.reset_index().rename(columns={"index": "Bus"})
    df["status"] = df["diverted"].apply(lambda x: "Diverted" if x else "Normal")

    col1, col2 = st.columns(2)

    # --- Average Delay per Bus ---
    with col1:
        st.markdown("### ⏱️ Average Delay per Bus")
        fig = px.bar(
            df,
            x="Bus",
            y="delay",
            color="status",
            barmode="group",
            labels={"delay": "Delay (minutes)"},
            title="Bus Delay Overview",
            color_discrete_map={"Normal": "blue", "Diverted": "orange"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Diverted vs Normal Ratio ---
    with col2:
        st.markdown("### 📈 Diverted vs Normal Buses")
        count_chart = px.pie(
            df,
            names="status",
            title="Route Diversion Ratio",
            color_discrete_sequence=["blue", "orange"]
        )
        st.plotly_chart(count_chart, use_container_width=True)

    # --- Most Congested Routes ---
    st.markdown("### 🚧 Most Traffic-Prone Routes")
    top_routes = df.sort_values(by="delay", ascending=False).head(3)
    st.table(
        top_routes[["Bus", "route", "delay"]]
        .rename(columns={"delay": "Avg Delay (min)", "route": "Route"})
        .reset_index(drop=True)
    )

    # --- Heatmap Visualization ---
    st.markdown("### 🗺️ Congestion Heatmap (Simulated Data)")
    heat_data = [(info["lat"], info["lon"], info["delay"]) for info in bus_data.values()]
    heatmap = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    HeatMap(heat_data, radius=20, blur=15).add_to(heatmap)
    st_folium(heatmap, width=850, height=500)

    st.success("✅ Analytics dashboard loaded successfully!")