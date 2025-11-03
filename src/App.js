import { useEffect, useState, useCallback, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// ✅ Fix marker icon issue
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
  iconUrl,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function App() {
  const [originalRoute, setOriginalRoute] = useState(null);
  const [reroutedPath, setReroutedPath] = useState(null);
  const [currentLocation, setCurrentLocation] = useState("Indiranagar");
  const [destination, setDestination] = useState("Jayanagar");

  // ✅ Bangalore coordinates for major areas
  const areaCoordinates = useMemo(() => ({
    "Indiranagar": [12.9716, 77.6402],
    "Koramangala": [12.9352, 77.6245],
    "Jayanagar": [12.9308, 77.5838],
    "Banashankari": [12.9255, 77.5468],
    "M.G. Road": [12.9716, 77.5946],
    "Whitefield": [12.9698, 77.7500],
    "Bangalore City H.O.": [12.9724, 77.5806],
    "Bangalore G.P.O.": [12.9724, 77.5806],
    "Marathahalli": [12.9586, 77.7010],
    "Electronic City": [12.8456, 77.6603]
  }), []);

  // Dummy traffic spots with congestion levels
  const trafficSpots = [
    { name: "Koramangala Traffic", coords: [12.9352, 77.6245], congestion: 0.8 },
    { name: "M.G. Road Junction", coords: [12.9716, 77.5946], congestion: 0.6 },
    { name: "Marathahalli Bridge", coords: [12.9586, 77.7010], congestion: 0.9 },
    { name: "Electronic City", coords: [12.8456, 77.6603], congestion: 0.7 }
  ];

  // Predefined road segments between areas (simulating real roads)
  const roadSegments = useMemo(() => ({
    "Indiranagar-Koramangala": [
      [12.9716, 77.6402], [12.9680, 77.6350], [12.9620, 77.6300], [12.9550, 77.6270], [12.9352, 77.6245]
    ],
    "Koramangala-Jayanagar": [
      [12.9352, 77.6245], [12.9330, 77.6200], [12.9310, 77.6150], [12.9308, 77.6100], [12.9308, 77.5838]
    ],
    "Indiranagar-M.G. Road": [
      [12.9716, 77.6402], [12.9716, 77.6200], [12.9716, 77.6000], [12.9716, 77.5946]
    ],
    "M.G. Road-Jayanagar": [
      [12.9716, 77.5946], [12.9600, 77.5900], [12.9450, 77.5850], [12.9308, 77.5838]
    ],
    "Jayanagar-Banashankari": [
      [12.9308, 77.5838], [12.9280, 77.5700], [12.9255, 77.5600], [12.9255, 77.5468]
    ],
    "Indiranagar-Whitefield": [
      [12.9716, 77.6402], [12.9700, 77.6800], [12.9698, 77.7200], [12.9698, 77.7500]
    ],
    "Whitefield-Marathahalli": [
      [12.9698, 77.7500], [12.9650, 77.7300], [12.9600, 77.7100], [12.9586, 77.7010]
    ],
    "Marathahalli-Electronic City": [
      [12.9586, 77.7010], [12.9200, 77.6800], [12.8800, 77.6700], [12.8456, 77.6603]
    ],
    "Indiranagar-Bangalore City H.O.": [
      [12.9716, 77.6402], [12.9720, 77.6200], [12.9724, 77.6000], [12.9724, 77.5806]
    ],
    "Bangalore City H.O.-Bangalore G.P.O.": [
      [12.9724, 77.5806], [12.9724, 77.5806]
    ]
  }), []);

  // Calculate distance between two coordinates
  const calculateDistance = useCallback((coord1, coord2) => {
    const lat1 = coord1[0];
    const lon1 = coord1[1];
    const lat2 = coord2[0];
    const lon2 = coord2[1];
    
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }, []);

  // Define connections between areas
  const findNeighbors = useCallback((location) => {
    const connections = {
      "Indiranagar": ["Koramangala", "M.G. Road", "Whitefield", "Bangalore City H.O."],
      "Koramangala": ["Indiranagar", "Jayanagar"],
      "Jayanagar": ["Koramangala", "Banashankari", "M.G. Road"],
      "Banashankari": ["Jayanagar"],
      "M.G. Road": ["Indiranagar", "Jayanagar", "Bangalore City H.O."],
      "Whitefield": ["Indiranagar", "Marathahalli"],
      "Marathahalli": ["Whitefield", "Electronic City"],
      "Electronic City": ["Marathahalli"],
      "Bangalore City H.O.": ["M.G. Road", "Bangalore G.P.O.", "Indiranagar"],
      "Bangalore G.P.O.": ["Bangalore City H.O."]
    };
    
    return connections[location] || [];
  }, []);

  // Get traffic penalty for a coordinate
  const getTrafficPenalty = useCallback((coord) => {
    let maxPenalty = 0;
    trafficSpots.forEach(spot => {
      const distance = calculateDistance(coord, spot.coords);
      if (distance < 1.0) { // Within 1km
        const penalty = spot.congestion * (1 - distance); // Closer = higher penalty
        maxPenalty = Math.max(maxPenalty, penalty);
      }
    });
    return maxPenalty;
  }, [trafficSpots, calculateDistance]);

  // Check if a coordinate is directly on a traffic spot
  const isOnTrafficSpot = useCallback((coord) => {
    return trafficSpots.some(spot => {
      const distance = calculateDistance(coord, spot.coords);
      return distance < 0.1; // Within 100 meters (essentially on the spot)
    });
  }, [trafficSpots, calculateDistance]);

  // Proper Dijkstra algorithm implementation
  const dijkstraShortestPath = useCallback((start, end, avoidTraffic = true) => {
    const distances = {};
    const previous = {};
    const visited = new Set();
    const queue = [];
    
    // Initialize distances
    Object.keys(areaCoordinates).forEach(location => {
      distances[location] = Infinity;
      previous[location] = null;
    });
    distances[start] = 0;
    
    // Add start to queue
    queue.push({ location: start, distance: 0 });
    
    while (queue.length > 0) {
      // Sort queue by distance (Dijkstra priority)
      queue.sort((a, b) => a.distance - b.distance);
      const { location: current, distance: currentDist } = queue.shift();
      
      if (visited.has(current)) continue;
      visited.add(current);
      
      if (current === end) break;
      
      // Get neighbors
      const neighbors = findNeighbors(current);
      
      for (const neighbor of neighbors) {
        if (visited.has(neighbor)) continue;
        
        const neighborCoords = areaCoordinates[neighbor];
        const currentCoords = areaCoordinates[current];
        
        // Calculate base distance
        const baseDistance = calculateDistance(currentCoords, neighborCoords);
        
        let totalDistance = baseDistance;
        
        if (avoidTraffic) {
          // For traffic-avoiding route: completely block traffic spots
          if (isOnTrafficSpot(neighborCoords)) {
            continue; // Skip this neighbor entirely
          }
          
          // Add heavy penalty for areas near traffic
          const trafficPenalty = getTrafficPenalty(neighborCoords);
          totalDistance = baseDistance + (trafficPenalty * 20); // Very heavy penalty
        }
        // For shortest route: no penalties, just base distance
        
        const newDistance = currentDist + totalDistance;
        
        if (newDistance < distances[neighbor]) {
          distances[neighbor] = newDistance;
          previous[neighbor] = current;
          queue.push({ location: neighbor, distance: newDistance });
        }
      }
    }
    
    // Reconstruct path
    const path = [];
    let current = end;
    
    while (current !== null) {
      path.unshift(current);
      current = previous[current];
    }
    
    // Convert path to coordinates with road segments
    const routeCoords = [];
    for (let i = 0; i < path.length - 1; i++) {
      const from = path[i];
      const to = path[i + 1];
      const segmentKey = `${from}-${to}`;
      const reverseKey = `${to}-${from}`;
      
      let roadPath = roadSegments[segmentKey] || roadSegments[reverseKey];
      if (!roadPath) {
        // If no predefined road, create direct path
        roadPath = [areaCoordinates[from], areaCoordinates[to]];
      }
      
      if (i === 0) {
        routeCoords.push(...roadPath);
      } else {
        routeCoords.push(...roadPath.slice(1)); // Skip first point to avoid duplication
      }
    }
    
    return routeCoords;
  }, [areaCoordinates, roadSegments, calculateDistance, isOnTrafficSpot, getTrafficPenalty, findNeighbors]);

  // Modular function to calculate original shortest path
  const calculateOriginalPath = useCallback((start, end) => {
    return dijkstraShortestPath(start, end, false);
  }, [dijkstraShortestPath]);

  // Modular function to calculate rerouted path that avoids traffic
  const calculateReroutedPath = useCallback((start, end) => {
    return dijkstraShortestPath(start, end, true);
  }, [dijkstraShortestPath]);

  // Main function to compute both routes
  const computeRoutes = useCallback(() => {
    const start = areaCoordinates[currentLocation];
    const end = areaCoordinates[destination];
    
    if (!start || !end) return;

    // Calculate original shortest path (through traffic)
    const originalPath = calculateOriginalPath(currentLocation, destination);
    setOriginalRoute(originalPath);

    // Calculate rerouted path (avoids traffic and rejoins)
    const reroutedPath = calculateReroutedPath(currentLocation, destination);
    setReroutedPath(reroutedPath);
  }, [currentLocation, destination, areaCoordinates, calculateOriginalPath, calculateReroutedPath]);


  useEffect(() => {
    computeRoutes();
  }, [computeRoutes]);

  const handleLocationChange = (type, value) => {
    if (type === 'current') {
      setCurrentLocation(value);
    } else {
      setDestination(value);
    }
  };

  return (
    <div style={{ height: "100vh", width: "100%" }}>
      {/* Control Panel */}
      <div style={{ 
        position: "absolute", 
        top: "10px", 
        left: "10px", 
        zIndex: 1000, 
        background: "white", 
        padding: "15px", 
        borderRadius: "8px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
        minWidth: "300px"
      }}>
        <h3 style={{ margin: "0 0 15px 0", color: "#333" }}>Bangalore Transit Optimizer</h3>
        
        <div style={{ marginBottom: "10px" }}>
          <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Current Location:</label>
          <select 
            value={currentLocation} 
            onChange={(e) => handleLocationChange('current', e.target.value)}
            style={{ width: "100%", padding: "5px" }}
          >
            {Object.keys(areaCoordinates).map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: "15px" }}>
          <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Destination:</label>
          <select 
            value={destination} 
            onChange={(e) => handleLocationChange('destination', e.target.value)}
            style={{ width: "100%", padding: "5px" }}
          >
            {Object.keys(areaCoordinates).map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: "12px", color: "#666" }}>
          <div>🟢 Start Location</div>
          <div>🔴 Destination</div>
          <div>🚨 Traffic Spots (Red)</div>
          <div>🔵 Original Shortest Path (Blue) - Goes through traffic</div>
          <div>🟢 Rerouted Path (Green) - Avoids traffic and rejoins</div>
        </div>
      </div>

      <MapContainer 
        center={[12.9716, 77.5946]} 
        zoom={11} 
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Start Location Marker */}
        <Marker position={areaCoordinates[currentLocation]} icon={defaultIcon}>
          <Popup>
            <strong>🟢 Start Location:</strong> {currentLocation}
          </Popup>
        </Marker>

        {/* Destination Marker */}
        <Marker position={areaCoordinates[destination]} icon={defaultIcon}>
          <Popup>
            <strong>🔴 Destination:</strong> {destination}
          </Popup>
        </Marker>

        {/* Traffic Spots */}
        {trafficSpots.map((spot, index) => (
          <CircleMarker
            key={index}
            center={spot.coords}
            radius={15}
            color="red"
            fillColor="red"
            fillOpacity={0.7}
          >
            <Popup>
              <strong>🚨 Traffic Alert!</strong><br/>
              {spot.name}<br/>
              Congestion: {(spot.congestion * 100).toFixed(0)}%
            </Popup>
          </CircleMarker>
        ))}

        {/* Original Shortest Path (Blue) - Goes through traffic */}
        {originalRoute && (
          <Polyline 
            positions={originalRoute} 
            color="blue" 
            weight={5}
            opacity={0.8}
          />
        )}

        {/* Rerouted Path (Green) - Avoids traffic and rejoins */}
        {reroutedPath && (
          <Polyline 
            positions={reroutedPath} 
            color="green" 
            weight={5}
            opacity={0.8}
          />
        )}
      </MapContainer>
    </div>
  );
}

export default App;
