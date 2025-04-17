from flask import Flask, render_template, request
import folium
import networkx as nx
import numpy as np
from scipy.interpolate import CubicSpline

app = Flask(__name__)

# Define metro stations and their coordinates
corridor_1 = {  # Red Line
    "Sarthana": (21.236086, 72.9084832),
    "Nature Park": (21.2290956, 72.8978939),
    "Varachha Chopati Garden": (21.2232511, 72.8860303),
    "Shri Swaminarayan Mandir (Kalakuj)": (21.2194506, 72.8764763),
    "Kapodra": (21.2164576, 72.8674935),
    "Labheshwar Chowk": (21.210109, 72.8572694),
    "Central Warehouse": (21.2059456, 72.8480292),
    "Surat Railway Station": (21.2041852,72.8426996),
    "Maskati Hospital": (21.197986,72.8329793),
    "Chowk Bazar": (21.1945927,72.8185266),
    "Kadarsha Ni Nal": (21.1869574,72.8193993),
    "Majura Gate": (21.1807111,72.8185441),
    "Rupali Canal": (21.1711507,72.8160023),
    "Althan Tenament": (21.161746,72.8114613),
    "Althan Gam": (21.1543952,72.8089202),
    "VIP Road": (21.1453708,72.8051957),
    "Woman ITI": (21.1360053,72.8009184),
    "Bhimrad": (21.130703,72.7983709),
    "Convention Center": (21.1224239,72.7995601),
    "Surat Dream City Station": (21.1092915,72.7986141)
}

corridor_2 = {  # Green Line
    "Bheshan": (21.2183247,72.7647846),
    "Botanical Garden": (21.2214452,72.7770538),
    "Ugat Vaarigruh": (21.2182041,72.7812077),
    "Palanpur Road": (21.2089361,72.7825809),
    "L P Savani School": (21.1999268,72.7826694),
    "Performing Art Centre": (21.1946262,72.7862638),
    "Adajan Gam": (21.1897933,72.7892611),
    "Aquarium": (21.1862338,72.792351),
    "Badri Narayan Temple": (21.1877719,72.8010253),
    "Athwa Chopati": (21.1848672,72.8083791),
    "Majura Gate": (21.1807111,72.8185441),  # Bnuuy
    "Udhna Darwaja": (21.183866,72.8321091),
    "Kamela Darwaja": (21.1870192,72.8390921),
    "Anjana Farm": (21.185375,72.8489572),
    "Model Town": (21.1861302,72.855636),
    "Magob": (21.1902815,72.868475),
    "Cancer Hospital": (21.1898563,72.878821),
    "Saroli": (21.1889488,72.8933009)
}

# Define intersection points
intersection_stations = ["Majura Gate"]

# Get unique stations for dropdown
stations = list(set(list(corridor_1.keys()) + list(corridor_2.keys())))

# Combine stations for path finding
all_stations = {**corridor_1, **corridor_2}

# Function to generate curved path between coordinates
def generate_curved_path(coords, num_points=10):
    """
    Generate a curved path between a series of coordinates using cubic spline interpolation.
    
    Args:
        coords: List of (lat, lng) tuples representing station coordinates
        num_points: Number of interpolation points between each pair of stations
    
    Returns:
        List of interpolated coordinates for a smooth curve
    """
    if len(coords) < 2:
        return coords
    
    # Extract latitudes and longitudes
    lats = [c[0] for c in coords]
    lngs = [c[1] for c in coords]
    
    # Create parameter t (cumulative distance)
    t = np.zeros(len(coords))
    for i in range(1, len(coords)):
        # Calculate Euclidean distance (simplified for small distances)
        dx = lats[i] - lats[i-1]
        dy = lngs[i] - lngs[i-1]
        t[i] = t[i-1] + np.sqrt(dx*dx + dy*dy)
    
    # Create new parameter values for interpolation
    t_new = np.linspace(t[0], t[-1], num=len(coords) * num_points)
    
    # Create cubic spline interpolation
    cs_lat = CubicSpline(t, lats)
    cs_lng = CubicSpline(t, lngs)
    
    # Interpolate
    lat_new = cs_lat(t_new)
    lng_new = cs_lng(t_new)
    
    # Combine interpolated coordinates
    return list(zip(lat_new, lng_new))

# Function to get which corridor a station belongs to
def get_station_line(station):
    if station in corridor_1:
        return "Red Line"
    elif station in corridor_2:
        return "Green Line"
    return None

# Function to find route with line changes
def find_route_with_changes(start, end):
    route = nx.shortest_path(G, start, end)
    route_with_changes = []
    current_line = get_station_line(route[0])
    
    for i, station in enumerate(route):
        station_line = get_station_line(station)
        
        # Add station to route
        if station in intersection_stations and i != 0 and i != len(route) - 1:
            # If this is an intersection point and not start/end, mark it as a transfer point
            route_with_changes.append({
                'station': station,
                'line': current_line,
                'is_transfer': True,
                'transfer_to': station_line if station_line != current_line else None
            })
            current_line = station_line
        else:
            route_with_changes.append({
                'station': station,
                'line': current_line,
                'is_transfer': False,
                'transfer_to': None
            })
    
    return route_with_changes

# Build a graph for shortest path calculation
G = nx.Graph()
for corridor in [corridor_1, corridor_2]:
    station_list = list(corridor.keys())
    for i in range(len(station_list) - 1):
        G.add_edge(station_list[i], station_list[i + 1])

@app.route("/", methods=["GET", "POST"])
def index():
    route = []
    start = end = None
    if request.method == "POST":
        start = request.form.get("start")
        end = request.form.get("end")

        if start in all_stations and end in all_stations:
            route = find_route_with_changes(start, end)

            # Create the map for the best route only
            metro_map = folium.Map(location=[21.2, 72.85], zoom_start=13, tiles='cartodbpositron')

            # Add markers and lines for each segment
            current_segment = []
            current_color = '#ff0000'  # Start with red

            for i, station_info in enumerate(route):
                coord = all_stations[station_info['station']]
                
                # Add marker
                popup_html = f"""
                <div style="font-family: Arial; text-align: center;">
                    <h4 style="margin: 0;">{station_info['station']}</h4>
                    <p style="margin: 5px 0;">🚉 {station_info['line']}</p>
                    {f'<p style="color: #ff6b6b;">Transfer to {station_info["transfer_to"]}</p>' if station_info["is_transfer"] else ''}
                </div>
                """
                
                folium.Marker(
                    location=coord,
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=station_info['station'],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size: 15px; text-align: center;">{"🔄" if station_info["is_transfer"] else "🚉"}</div>',
                        icon_size=(20, 20),
                        icon_anchor=(10, 10)
                    )
                ).add_to(metro_map)
                
                current_segment.append(coord)
                
                # If this is a transfer point or the last station, draw the segment
                if station_info['is_transfer'] or i == len(route) - 1:
                    if len(current_segment) > 1:
                        # Generate curved path
                        curved_segment = generate_curved_path(current_segment)
                        
                        # Add curved line
                        folium.PolyLine(
                            locations=curved_segment,
                            color=current_color,
                            weight=4,
                            opacity=1.0
                        ).add_to(metro_map)
                    current_segment = [coord]
                    current_color = '#00ff00' if current_color == '#ff0000' else '#ff0000'

            # Save the map
            metro_map.save("static/map.html")

    return render_template("index.html", 
                         stations=stations, 
                         start=start, 
                         end=end, 
                         route=route if route else None)

@app.route('/all_routes', methods=['GET', 'POST'])
def show_all_routes():
    # Create the map centered on Surat
    metro_map = folium.Map(location=[21.2, 72.85], zoom_start=12, tiles='cartodbpositron')
    
    # Define routes with their colors and stations
    routes = {
        'Red Line': {
            'stations': list(corridor_1.keys()),
            'color': '#ff0000',  # Bright red
            'coords': list(corridor_1.values()),
            'emoji': '🔴'
        },
        'Green Line': {
            'stations': list(corridor_2.keys()),
            'color': '#00ff00',  # Bright green
            'coords': list(corridor_2.values()),
            'emoji': '🟢'
        }
    }
    
    # Plot each route
    for route_name, route_data in routes.items():
        # Generate curved path
        curved_coords = generate_curved_path(route_data['coords'])
        
        # Draw the route line with curves
        folium.PolyLine(
            locations=curved_coords,
            color=route_data['color'],
            weight=4,
            opacity=1.0,
            popup=route_name
        ).add_to(metro_map)
        
        # Add station markers with emojis
        for station, coord in zip(route_data['stations'], route_data['coords']):
            # Create custom HTML for the popup
            popup_html = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4 style="margin: 0;">{station}</h4>
                <p style="margin: 5px 0;">{route_data['emoji']} {route_name}</p>
            </div>
            """
            
            # Add the marker with custom icon
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=station,  # Hover text
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 15px; text-align: center;">🚉</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10)
                )
            ).add_to(metro_map)
            
            # Add small circle marker under the emoji for better visibility
            folium.CircleMarker(
                location=coord,
                radius=3,
                color=route_data['color'],
                fill=True,
                fillColor=route_data['color'],
                fillOpacity=1,
                weight=2,
                opacity=0.8
            ).add_to(metro_map)
    
    # Save the map
    metro_map.save("static/map.html")
    
    # Return both the routes data and stations for the template
    return render_template('index.html', 
                         all_routes=routes, 
                         stations=stations,
                         show_map=True)

@app.route('/route_info', methods=['GET'])
def route_info():
    # Create the map centered on Surat
    metro_map = folium.Map(location=[21.2, 72.85], zoom_start=12, tiles='cartodbpositron')
    
    # Define routes with their colors and stations
    routes = {
        'Red Line': {
            'stations': list(corridor_1.keys()),
            'color': '#ff0000',  # Bright red
            'coords': list(corridor_1.values()),
            'emoji': '🔴'
        },
        'Green Line': {
            'stations': list(corridor_2.keys()),
            'color': '#00ff00',  # Bright green
            'coords': list(corridor_2.values()),
            'emoji': '🟢'
        }
    }
    
    # Plot each route
    for route_name, route_data in routes.items():
        # Generate curved path
        curved_coords = generate_curved_path(route_data['coords'])
        
        # Draw the route line with curves
        folium.PolyLine(
            locations=curved_coords,
            color=route_data['color'],
            weight=4,
            opacity=1.0,
            popup=route_name
        ).add_to(metro_map)
        
        # Add station markers with emojis
        for station, coord in zip(route_data['stations'], route_data['coords']):
            # Create custom HTML for the popup
            popup_html = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4 style="margin: 0;">{station}</h4>
                <p style="margin: 5px 0;">{route_data['emoji']} {route_name}</p>
            </div>
            """
            
            # Add the marker with custom icon
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=station,  # Hover text
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 15px; text-align: center;">🚉</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10)
                )
            ).add_to(metro_map)
            
            # Add small circle marker under the emoji for better visibility
            folium.CircleMarker(
                location=coord,
                radius=3,
                color=route_data['color'],
                fill=True,
                fillColor=route_data['color'],
                fillOpacity=1,
                weight=2,
                opacity=0.8
            ).add_to(metro_map)
    
    # Save the map
    metro_map.save("static/map.html")
    
    # Return the route information template
    return render_template('route_info.html', 
                         routes=routes,
                         intersection_stations=intersection_stations)

@app.route('/station_details')
def station_details():
    # Prepare station details
    station_list = []
    
    # Add Red Line stations
    for station in corridor_1.keys():
        station_info = {
            'name': station,
            'line': 'Red Line',
            'emoji': '🔴',
            'corridor_number': 1,
            'is_transfer': station in intersection_stations
        }
        station_list.append(station_info)
    
    # Add Green Line stations
    for station in corridor_2.keys():
        # Skip if station is already added (intersection stations)
        if station in intersection_stations and any(s['name'] == station for s in station_list):
            continue
            
        station_info = {
            'name': station,
            'line': 'Green Line',
            'emoji': '🟢',
            'corridor_number': 2,
            'is_transfer': station in intersection_stations
        }
        station_list.append(station_info)
    
    # Sort stations alphabetically
    station_list.sort(key=lambda x: x['name'])
    
    return render_template('station_details.html', stations=station_list)

if __name__ == "__main__":
    app.run(debug=True)