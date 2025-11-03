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
    st.header("🧭 Admin Dashboard – Active Buses")
    st.write("Overview of buses currently tracked:")

    for bus, info in bus_data.items():
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"**Bus {bus}**")
        col2.write(info["route"])
        col3.write("🟠 Diverted" if info["diverted"] else "🔵 Normal")
        col4.write(f"📍 ({info['lat']:.4f}, {info['lon']:.4f})")

    admin_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    for bus, info in bus_data.items():
        color = "orange" if info["diverted"] else "blue"
        folium.Marker(
            location=(info["lat"], info["lon"]),
            popup=f"Bus {bus} – {'Diverted' if info['diverted'] else 'Normal'}",
            icon=folium.Icon(color=color, icon="bus", prefix="fa")
        ).add_to(admin_map)

    st_folium(admin_map, width=850, height=500)

# ---------- ANALYTICS TAB ----------
with tab_analytics:
    st.header("📊 Analytics & Insights")
    st.subheader("🚦 Transit Efficiency Dashboard")

    df = pd.DataFrame(bus_data).T.reset_index().rename(columns={"index": "Bus"})
    df["status"] = df["diverted"].apply(lambda x: "Diverted" if x else "Normal")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⏱️ Average Delay per Bus")
        fig = px.bar(df, x="Bus", y="delay", color="status", barmode="group",
                     labels={"delay": "Delay (minutes)"}, title="Bus Delay Overview")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📈 Diverted vs Normal Buses")
        count_chart = px.pie(df, names="status", title="Route Diversion Ratio", color_discrete_sequence=["blue", "orange"])
        st.plotly_chart(count_chart, use_container_width=True)

    st.markdown("### 🗺️ Congestion Heatmap (Simulated Data)")
    heat_data = [(info["lat"], info["lon"], info["delay"]) for info in bus_data.values()]
    heatmap = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    HeatMap(heat_data, radius=20, blur=15).add_to(heatmap)
    st_folium(heatmap, width=850, height=500)

    st.success("✅ Analytics dashboard loaded successfully!")
