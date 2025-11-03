"""
Flask API backend for Bangalore Urban Transit Optimizer
Integrates dynamic rerouting with Bangalore traffic data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
from dynamic_rerouting import Edge, compute_updated_route
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load Bangalore data
try:
    areas_df = pd.read_csv('BangaloreAreaLatLongDetails.csv')
    traffic_df = pd.read_csv('Banglore_traffic_Dataset.csv')
    print(f"Loaded {len(areas_df)} areas and {len(traffic_df)} traffic records")
except Exception as e:
    print(f"Error loading data: {e}")
    areas_df = pd.DataFrame()
    traffic_df = pd.DataFrame()

def get_area_coordinates(area_name):
    """Get lat/long for a Bangalore area"""
    area_data = areas_df[areas_df['Area'].str.contains(area_name, case=False, na=False)]
    if not area_data.empty:
        return area_data.iloc[0]['Latitude'], area_data.iloc[0]['Longitude']
    return None, None

def create_bangalore_network():
    """Create a simplified network graph for Bangalore areas"""
    edges = []
    
    # Create connections between major Bangalore areas
    major_areas = ['Indiranagar', 'Koramangala', 'M.G. Road', 'Jayanagar', 'Whitefield', 
                   'Banashankari', 'Bangalore City H.O.', 'Bangalore G.P.O.']
    
    # Add edges between connected areas (simplified topology)
    connections = [
        ('Indiranagar', 'Koramangala', 8.0),
        ('Koramangala', 'Jayanagar', 12.0),
        ('Jayanagar', 'Banashankari', 6.0),
        ('Indiranagar', 'M.G. Road', 5.0),
        ('M.G. Road', 'Bangalore City H.O.', 3.0),
        ('Bangalore City H.O.', 'Bangalore G.P.O.', 2.0),
        ('Whitefield', 'Indiranagar', 15.0),
        ('Koramangala', 'Banashankari', 10.0),
        ('M.G. Road', 'Jayanagar', 8.0),
    ]
    
    for u, v, time in connections:
        edges.append(Edge(u, v, time))
        # Add reverse edge
        edges.append(Edge(v, u, time))
    
    return edges

def get_current_traffic_data():
    """Extract current traffic congestion levels from Bangalore dataset"""
    traffic_data = {}
    
    # Get latest traffic data (assuming most recent date)
    if not traffic_df.empty:
        latest_date = traffic_df['Date'].max()
        latest_data = traffic_df[traffic_df['Date'] == latest_date]
        
        for _, row in latest_data.iterrows():
            area = row['Area Name']
            congestion_level = row['Congestion Level'] / 100.0  # Convert to 0-1 scale
            
            # Map to simplified network areas
            if area in ['Indiranagar', 'Koramangala', 'M.G. Road', 'Jayanagar', 'Whitefield', 
                       'Banashankari', 'Bangalore City H.O.', 'Bangalore G.P.O.']:
                # Create edge keys for major routes
                road_name = row['Road/Intersection Name']
                
                # Map specific roads to network edges
                if '100 Feet Road' in road_name and area == 'Indiranagar':
                    traffic_data[('Indiranagar', 'Koramangala')] = congestion_level
                elif 'CMH Road' in road_name and area == 'Indiranagar':
                    traffic_data[('Indiranagar', 'M.G. Road')] = congestion_level
                elif 'Sony World Junction' in road_name and area == 'Koramangala':
                    traffic_data[('Koramangala', 'Jayanagar')] = congestion_level
                elif 'Sarjapur Road' in road_name and area == 'Koramangala':
                    traffic_data[('Koramangala', 'Banashankari')] = congestion_level
                elif 'Trinity Circle' in road_name and area == 'M.G. Road':
                    traffic_data[('M.G. Road', 'Bangalore City H.O.')] = congestion_level
                elif 'Anil Kumble Circle' in road_name and area == 'M.G. Road':
                    traffic_data[('M.G. Road', 'Jayanagar')] = congestion_level
                elif 'Jayanagar 4th Block' in road_name and area == 'Jayanagar':
                    traffic_data[('Jayanagar', 'Banashankari')] = congestion_level
                elif 'South End Circle' in road_name and area == 'Jayanagar':
                    traffic_data[('Jayanagar', 'Banashankari')] = congestion_level
                elif 'Marathahalli Bridge' in road_name and area == 'Whitefield':
                    traffic_data[('Whitefield', 'Indiranagar')] = congestion_level
    
    return traffic_data

@app.route('/api/areas', methods=['GET'])
def get_areas():
    """Get list of available Bangalore areas"""
    if areas_df.empty:
        return jsonify({'error': 'No area data available'}), 500
    
    areas = areas_df['Area'].tolist()
    return jsonify({'areas': areas})

@app.route('/api/route', methods=['POST'])
def compute_route():
    """Compute dynamic route with congestion avoidance"""
    try:
        data = request.json
        current_stop = data.get('current_stop')
        destination = data.get('destination')
        intermediate_a = data.get('intermediate_a')
        intermediate_b = data.get('intermediate_b')
        
        if not all([current_stop, destination, intermediate_a, intermediate_b]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Create Bangalore network
        edges = create_bangalore_network()
        
        # Get current traffic data
        traffic_data = get_current_traffic_data()
        
        # Compute updated route
        result = compute_updated_route(
            edges=edges,
            traffic_data=traffic_data,
            current_stop=current_stop,
            destination=destination,
            intermediate_a=intermediate_a,
            intermediate_b=intermediate_b
        )
        
        # Convert route to coordinates for frontend
        route_coords = []
        for stop in result['path']:
            lat, lon = get_area_coordinates(stop)
            if lat and lon:
                route_coords.append([lat, lon])
        
        return jsonify({
            'path': result['path'],
            'route_coords': route_coords,
            'total_time': result['total_time'],
            'visited_order': result['visited_order'],
            'congested_edges': result['congested_edges'],
            'traffic_data': traffic_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/traffic', methods=['GET'])
def get_traffic_data():
    """Get current traffic congestion data"""
    traffic_data = get_current_traffic_data()
    return jsonify({'traffic': traffic_data})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'areas_loaded': len(areas_df), 'traffic_records': len(traffic_df)})

if __name__ == '__main__':
    print("Starting Bangalore Urban Transit API...")
    print("Available areas:", areas_df['Area'].tolist()[:10] if not areas_df.empty else "None")
    app.run(debug=True, port=5000)

