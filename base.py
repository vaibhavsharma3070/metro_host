from flask import Flask, render_template, request
import folium
import networkx as nx
import xml.etree.ElementTree as ET

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

# Extract route coordinates from KML file
def extract_route_coordinates_from_kml(kml_file_path):
    # Parse the KML file
    tree = ET.parse(kml_file_path)
    root = tree.getroot()
    
    # Define namespace for KML
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # Find all Placemarks
    routes = {}
    
    for placemark in root.findall('.//kml:Placemark', ns):
        # Get the name of the route
        name_elem = placemark.find('kml:name', ns)
        if name_elem is not None:
            route_name = name_elem.text
            
            # Find LineString coordinates
            coords_elem = placemark.find('.//kml:coordinates', ns)
            if coords_elem is not None:
                # Parse coordinates
                coord_text = coords_elem.text.strip()
                coordinates = []
                
                for coord in coord_text.split():
                    parts = coord.split(',')
                    if len(parts) >= 2:
                        # KML format is longitude,latitude,altitude - we need latitude,longitude for Folium
                        lon = float(parts[0])
                        lat = float(parts[1])
                        coordinates.append((lat, lon))
                
                routes[route_name] = coordinates
    
    return routes

# Make sure the function to get station line works
def get_station_line(station):
    if station in corridor_1:
        return "Red Line"  # This corresponds to "Orange Line" in KML
    elif station in corridor_2:
        return "Green Line"
    return None

# Build the graph for shortest path calculation
G = nx.Graph()
for corridor in [corridor_1, corridor_2]:
    station_list = list(corridor.keys())
    for i in range(len(station_list) - 1):
        G.add_edge(station_list[i], station_list[i + 1])

# Routes for station lookup
all_stations = {**corridor_1, **corridor_2}
stations = list(set(list(corridor_1.keys()) + list(corridor_2.keys())))
intersection_stations = ["Majura Gate"]  # As defined in your original code

@app.route('/all_routes', methods=['GET', 'POST'])
def show_all_routes():
    # Create the map centered on Surat
    metro_map = folium.Map(location=[21.2, 72.85], zoom_start=12, tiles='cartodbpositron')
    
    # Extract KML data (make sure the path is correct)
    kml_routes = extract_route_coordinates_from_kml('base.kml')
    
    # Map KML route names to our corridor names and colors
    route_mapping = {
        'Green Line': {
            'kml_name': 'Green Line',
            'color': '#00ff00',  # Bright green
            'emoji': '🟢',
            'stations': list(corridor_2.keys())
        },
        'Red Line': {  # This is "Orange Line" in the KML
            'kml_name': 'Orange Line',
            'color': '#ff0000',  # Bright red (or you could use orange: '#FFA500')
            'emoji': '🔴',
            'stations': list(corridor_1.keys())
        }
    }
    
    # Plot each route using KML data
    for route_name, route_data in route_mapping.items():
        kml_name = route_data['kml_name']
        
        if kml_name in kml_routes:
            # Draw the route line using KML coordinates
            folium.PolyLine(
                locations=kml_routes[kml_name],
                color=route_data['color'],
                weight=4,
                opacity=1.0,
                popup=route_name
            ).add_to(metro_map)
        
        # Add station markers
        for station in route_data['stations']:
            coord = all_stations[station]
            
            # Skip intersection stations that are already added
            if station in intersection_stations and route_name == 'Red Line' and station in corridor_2:
                continue
                
            # Create custom HTML for the popup
            popup_html = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4 style="margin: 0;">{station}</h4>
                <p style="margin: 5px 0;">{route_data['emoji']} {route_name}</p>
            </div>
            """
            
            # Add the marker
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=station,
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 15px; text-align: center;">🚉</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10)
                )
            ).add_to(metro_map)
            
            # Add circle marker for better visibility
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
    
    return render_template('index.html', 
                         all_routes=route_mapping, 
                         stations=stations,
                         show_map=True)

# Also update the route_info function to use KML data
@app.route('/route_info', methods=['GET'])
def route_info():
    # Create the map
    metro_map = folium.Map(location=[21.2, 72.85], zoom_start=12, tiles='cartodbpositron')
    
    # Extract KML data
    kml_routes = extract_route_coordinates_from_kml('base.kml')
    
    # Map KML route names to our corridor names and colors
    route_mapping = {
        'Green Line': {
            'kml_name': 'Green Line',
            'color': '#00ff00',
            'emoji': '🟢',
            'stations': list(corridor_2.keys()),
            'coords': list(corridor_2.values())
        },
        'Red Line': {  # This is "Orange Line" in the KML
            'kml_name': 'Orange Line',
            'color': '#ff0000',
            'emoji': '🔴',
            'stations': list(corridor_1.keys()),
            'coords': list(corridor_1.values())
        }
    }
    
    # Plot each route using KML data
    for route_name, route_data in route_mapping.items():
        kml_name = route_data['kml_name']
        
        if kml_name in kml_routes:
            # Draw the route line using KML coordinates
            folium.PolyLine(
                locations=kml_routes[kml_name],
                color=route_data['color'],
                weight=4,
                opacity=1.0,
                popup=route_name
            ).add_to(metro_map)
            
        # Add station markers
        for station, coord in zip(route_data['stations'], route_data['coords']):
            # Skip intersection stations already added
            if station in intersection_stations and route_name == 'Red Line' and station in corridor_2:
                continue
                
            # Create popup HTML
            popup_html = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4 style="margin: 0;">{station}</h4>
                <p style="margin: 5px 0;">{route_data['emoji']} {route_name}</p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=station,
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 15px; text-align: center;">🚉</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10)
                )
            ).add_to(metro_map)
            
            # Add circle marker
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
    
    return render_template('route_info.html', 
                         routes=route_mapping,
                         intersection_stations=intersection_stations)

# For the route selection function, we need to adapt to show KML routes for the selected stations
@app.route("/", methods=["GET", "POST"])
def index():
    route = []
    start = end = None
    
    if request.method == "POST":
        start = request.form.get("start")
        end = request.form.get("end")

        if start in all_stations and end in all_stations:
            # Find route with changes
            route = find_route_with_changes(start, end)
            
            # Create map
            metro_map = folium.Map(location=[21.2, 72.85], zoom_start=13, tiles='cartodbpositron')
            
            # Extract KML data
            kml_routes = extract_route_coordinates_from_kml('base.kml')
            
            # Route color mapping
            route_colors = {
                'Red Line': '#ff0000',
                'Green Line': '#00ff00'
            }
            
            # Determine which segments of the KML routes to highlight
            # This is a bit more complex - for now, we'll add the full KML routes but with reduced opacity
            # and then highlight the specific segments with station markers
            
            # Add full routes with reduced opacity as background
            if 'Green Line' in kml_routes:
                folium.PolyLine(
                    locations=kml_routes['Green Line'],
                    color='#00ff00',
                    weight=3,
                    opacity=0.3
                ).add_to(metro_map)
                
            if 'Orange Line' in kml_routes:
                folium.PolyLine(
                    locations=kml_routes['Orange Line'],
                    color='#ff0000',
                    weight=3,
                    opacity=0.3
                ).add_to(metro_map)
            
            # Add markers for the selected route
            for i, station_info in enumerate(route):
                coord = all_stations[station_info['station']]
                
                # Create popup
                popup_html = f"""
                <div style="font-family: Arial; text-align: center;">
                    <h4 style="margin: 0;">{station_info['station']}</h4>
                    <p style="margin: 5px 0;">🚉 {station_info['line']}</p>
                    {f'<p style="color: #ff6b6b;">Transfer to {station_info["transfer_to"]}</p>' if station_info["is_transfer"] else ''}
                </div>
                """
                
                # Add marker
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
                
                # Add circle with line color
                folium.CircleMarker(
                    location=coord,
                    radius=8,
                    color=route_colors.get(station_info['line'], '#ff0000'),
                    fill=True,
                    fillColor=route_colors.get(station_info['line'], '#ff0000'),
                    fillOpacity=0.8,
                    weight=2,
                    opacity=1.0
                ).add_to(metro_map)
            
            # Save the map
            metro_map.save("static/map.html")

    return render_template("index.html", 
                         stations=stations, 
                         start=start, 
                         end=end, 
                         route=route if route else None)

# Keep the original find_route_with_changes function
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
