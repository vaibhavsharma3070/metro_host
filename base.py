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


def find_nearest_point_index(kml_coords, station_coord):
    """
    Find the index of the point in kml_coords that is closest to station_coord
    """
    min_dist = float('inf')
    min_index = 0
    
    for i, coord in enumerate(kml_coords):
        # Calculate approximate distance (Euclidean, which is good enough for finding closest point)
        dist = ((coord[0] - station_coord[0]) ** 2 + (coord[1] - station_coord[1]) ** 2) ** 0.5
        
        if dist < min_dist:
            min_dist = dist
            min_index = i
    
    return min_index



def extract_route_segment(kml_coords, start_station_coord, end_station_coord):
    """
    Extract the segment of kml_coords that connects start_station_coord to end_station_coord
    with improved handling for finding the correct path
    """
    # Find indices of nearest points
    start_index = find_nearest_point_index(kml_coords, start_station_coord)
    end_index = find_nearest_point_index(kml_coords, end_station_coord)
    
    # Extract the segment (ensure proper order)
    if start_index <= end_index:
        return kml_coords[start_index:end_index + 1]
    else:
        # If the route goes backwards in the KML
        return list(reversed(kml_coords[end_index:start_index + 1]))

# Then update the index route function
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
            
            # Create map focused on the route only
            metro_map = folium.Map(location=[21.2, 72.85], zoom_start=13, tiles='cartodbpositron')
            
            # Extract KML data
            kml_routes = extract_route_coordinates_from_kml('base.kml')
            
            # Create a list of coordinates for all stations in the route
            route_coords = []
            for station_info in route:
                station_coord = all_stations[station_info['station']]
                if station_coord not in route_coords:  # Avoid duplicates for transfer stations
                    route_coords.append(station_coord)
            
            # Calculate bounds to focus the map on the route
            if route_coords:
                lats = [coord[0] for coord in route_coords]
                lons = [coord[1] for coord in route_coords]
                min_lat, max_lat = min(lats), max(lats)
                min_lon, max_lon = min(lons), max(lons)
                # Add some padding
                padding = 0.01  # about 1km
                bounds = [[min_lat - padding, min_lon - padding], 
                         [max_lat + padding, max_lon + padding]]
                metro_map.fit_bounds(bounds)
            
            # Route color mapping
            route_colors = {
                'Red Line': '#ff0000',
                'Green Line': '#00ff00'
            }
            
            # KML route name mapping
            kml_name_mapping = {
                'Red Line': 'Orange Line',  # The KML uses "Orange Line" for what we call "Red Line"
                'Green Line': 'Green Line'
            }
            
            # Group continuous segments by line
            segments_by_line = {}
            current_segment = []
            current_line = None
            
            for i, station_info in enumerate(route):
                station_name = station_info['station']
                station_coord = all_stations[station_name]
                station_line = station_info['line']
                
                # Start of a new segment or a new line
                if current_line is None or station_line != current_line:
                    # If there was a previous segment, finish it
                    if current_segment:
                        if current_line not in segments_by_line:
                            segments_by_line[current_line] = []
                        segments_by_line[current_line].append(current_segment)
                    
                    # Start a new segment on this line
                    current_segment = [station_name]
                    current_line = station_line
                else:
                    # Continue the current segment
                    current_segment.append(station_name)
            
            # Add the final segment
            if current_segment:
                if current_line not in segments_by_line:
                    segments_by_line[current_line] = []
                segments_by_line[current_line].append(current_segment)
            
            # Draw each line segment with appropriate color
            for line, segments in segments_by_line.items():
                kml_line_name = kml_name_mapping.get(line)
                line_color = route_colors.get(line)
                
                if kml_line_name in kml_routes:
                    for segment in segments:
                        if len(segment) >= 2:  # Need at least 2 stations to form a segment
                            # For each adjacent pair of stations in the segment
                            for j in range(len(segment) - 1):
                                start_station = segment[j]
                                end_station = segment[j+1]
                                start_coord = all_stations[start_station]
                                end_coord = all_stations[end_station]
                                
                                # Extract route segment from KML
                                route_segment = extract_route_segment(
                                    kml_routes[kml_line_name],
                                    start_coord,
                                    end_coord
                                )
                                
                                # Draw segment
                                folium.PolyLine(
                                    locations=route_segment,
                                    color=line_color,
                                    weight=5,
                                    opacity=1.0,
                                    tooltip=f"{start_station} to {end_station} ({line})"
                                ).add_to(metro_map)
            
            # Special handling for transfer stations - draw connector line if needed
            for i in range(len(route) - 1):
                curr_station = route[i]
                next_station = route[i+1]
                
                # If both entries refer to the same station but different lines, add a connector
                if curr_station['station'] == next_station['station'] and curr_station['line'] != next_station['line']:
                    station_coord = all_stations[curr_station['station']]
                    
                    # Add a visible connecting line at the transfer station
                    folium.PolyLine(
                        locations=[station_coord, station_coord],  # Same point, creates a dot
                        color="#FF6B6B",  # Bright red for transfer
                        weight=8,  # Make it wider than the route lines
                        opacity=0.8,
                        tooltip=f"Transfer at {curr_station['station']}: {curr_station['line']} to {next_station['line']}"
                    ).add_to(metro_map)
            
            # Add markers for all stations in the route
            for i, station_info in enumerate(route):
                station_name = station_info['station']
                station_coord = all_stations[station_name]
                station_line = station_info['line']
                
                # Skip duplicate markers for transfer stations (when the same station appears twice)
                skip = False
                if i > 0 and station_name == route[i-1]['station']:
                    skip = True
                
                if not skip:
                    # Create popup
                    popup_html = f"""
                    <div style="font-family: Arial; text-align: center;">
                        <h4 style="margin: 0;">{station_name}</h4>
                        <p style="margin: 5px 0;">🚉 {station_line}</p>
                        {f'<p style="color: #ff6b6b;">Transfer Station</p>' if station_name in intersection_stations else ''}
                    </div>
                    """
                    
                    # Use different icons for start, end, and transfer stations
                    icon_html = "🚉"  # Default
                    if i == 0:
                        icon_html = "🚆"  # Start station
                    elif i == len(route) - 1:
                        icon_html = "🏁"  # End station
                    elif station_name in intersection_stations:
                        icon_html = "🔄"  # Transfer station
                    
                    # Add marker
                    folium.Marker(
                        location=station_coord,
                        popup=folium.Popup(popup_html, max_width=200),
                        tooltip=station_name,
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 15px; text-align: center;">{icon_html}</div>',
                            icon_size=(20, 20),
                            icon_anchor=(10, 10)
                        )
                    ).add_to(metro_map)
                    
                    # Add circle with line color
                    folium.CircleMarker(
                        location=station_coord,
                        radius=8,
                        color=route_colors.get(station_line, '#ff0000'),
                        fill=True,
                        fillColor=route_colors.get(station_line, '#ff0000'),
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


def find_route_with_changes(start, end):
    """
    Find the best route between two stations, accounting for line transfers.
    
    Args:
        start (str): The starting station name
        end (str): The destination station name
        
    Returns:
        list: A list of dictionaries containing station information along the route
    """
    # Find the shortest path using networkx
    route = nx.shortest_path(G, start, end)
    route_with_changes = []
    
    # Get the starting line
    current_line = get_station_line(route[0])
    
    for i, station in enumerate(route):
        station_line = get_station_line(station)
        
        # Special handling for transfer stations
        if station in intersection_stations:
            # Check if this is a transfer point (not the start/end and line change is needed)
            is_transfer = False
            transfer_to = None
            
            if i > 0 and i < len(route) - 1:
                # Get the previous and next station's line to determine if we need to transfer
                prev_station = route[i - 1]
                next_station = route[i + 1]
                prev_line = get_station_line(prev_station)
                next_line = get_station_line(next_station)
                
                # If the next station is on a different line, this is a transfer point
                if next_line != prev_line:
                    is_transfer = True
                    transfer_to = next_line
                    
                    # Add the intersection station on the current line first
                    route_with_changes.append({
                        'station': station,
                        'line': prev_line,
                        'is_transfer': True,
                        'transfer_to': next_line
                    })
                    
                    # Then add it again as the starting point on the new line
                    route_with_changes.append({
                        'station': station,
                        'line': next_line,
                        'is_transfer': True,
                        'transfer_to': None  # Already transferred
                    })
                    
                    # Update current line
                    current_line = next_line
                    continue  # Skip the normal addition since we added it twice
            
            # If not a transfer or start/end, add normally
            if not is_transfer:
                route_with_changes.append({
                    'station': station,
                    'line': station_line if i == 0 or i == len(route) - 1 else current_line,
                    'is_transfer': False,
                    'transfer_to': None
                })
                # Update current line if this is the start
                if i == 0:
                    current_line = station_line
        else:
            # Regular station (not an intersection)
            route_with_changes.append({
                'station': station,
                'line': current_line,
                'is_transfer': False,
                'transfer_to': None
            })
    
    return route_with_changes


@app.route('/map', methods=['GET'])
def fullscreen_map():
    """
    API endpoint that returns just the map in full-screen view
    without any additional UI elements.
    
    Query parameters:
    - start: Optional starting station name
    - end: Optional ending station name
    - line: Optional line filter ('red', 'green', or 'all')
    """
    # Get query parameters
    start = request.args.get('start')
    end = request.args.get('end')
    line_filter = request.args.get('line', 'all').lower()
    
    # Create a clean map
    metro_map = folium.Map(location=[21.2, 72.85], zoom_start=12, tiles='cartodbpositron')
    
    # Extract KML data
    kml_routes = extract_route_coordinates_from_kml('base.kml')
    
    # Map KML route names to corridor names and colors
    route_mapping = {
        'Green Line': {
            'kml_name': 'Green Line',
            'color': '#00ff00',  # Bright green
            'emoji': '🟢',
            'stations': list(corridor_2.keys()),
            'coords': list(corridor_2.values())
        },
        'Red Line': {  # This is "Orange Line" in the KML
            'kml_name': 'Orange Line',
            'color': '#ff0000',  # Bright red
            'emoji': '🔴',
            'stations': list(corridor_1.keys()),
            'coords': list(corridor_1.values())
        }
    }
    
    if start and end and start in all_stations and end in all_stations:
        # Generate route between stations
        route = find_route_with_changes(start, end)
        
        # Create a list of coordinates for all stations in the route
        route_coords = []
        for station_info in route:
            station_coord = all_stations[station_info['station']]
            if station_coord not in route_coords:  # Avoid duplicates
                route_coords.append(station_coord)
        
        # Calculate bounds to focus the map on the route
        if route_coords:
            lats = [coord[0] for coord in route_coords]
            lons = [coord[1] for coord in route_coords]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            padding = 0.01  # about 1km
            bounds = [[min_lat - padding, min_lon - padding], 
                     [max_lat + padding, max_lon + padding]]
            metro_map.fit_bounds(bounds)
        
        # Route color mapping
        route_colors = {
            'Red Line': '#ff0000',
            'Green Line': '#00ff00'
        }
        
        # KML route name mapping
        kml_name_mapping = {
            'Red Line': 'Orange Line',  # KML uses "Orange Line" for "Red Line"
            'Green Line': 'Green Line'
        }
        
        # Group continuous segments by line
        segments_by_line = {}
        current_segment = []
        current_line = None
        
        for i, station_info in enumerate(route):
            station_name = station_info['station']
            station_line = station_info['line']
            
            # Start of a new segment or a new line
            if current_line is None or station_line != current_line:
                # If there was a previous segment, finish it
                if current_segment:
                    if current_line not in segments_by_line:
                        segments_by_line[current_line] = []
                    segments_by_line[current_line].append(current_segment)
                
                # Start a new segment on this line
                current_segment = [station_name]
                current_line = station_line
            else:
                # Continue the current segment
                current_segment.append(station_name)
        
        # Add the final segment
        if current_segment:
            if current_line not in segments_by_line:
                segments_by_line[current_line] = []
            segments_by_line[current_line].append(current_segment)
        
        # Draw each line segment with appropriate color
        for line, segments in segments_by_line.items():
            kml_line_name = kml_name_mapping.get(line)
            line_color = route_colors.get(line)
            
            if kml_line_name in kml_routes:
                for segment in segments:
                    if len(segment) >= 2:  # Need at least 2 stations
                        for j in range(len(segment) - 1):
                            start_station = segment[j]
                            end_station = segment[j+1]
                            start_coord = all_stations[start_station]
                            end_coord = all_stations[end_station]
                            
                            # Extract route segment from KML
                            route_segment = extract_route_segment(
                                kml_routes[kml_line_name],
                                start_coord,
                                end_coord
                            )
                            
                            # Draw segment
                            folium.PolyLine(
                                locations=route_segment,
                                color=line_color,
                                weight=5,
                                opacity=1.0,
                                tooltip=f"{start_station} to {end_station} ({line})"
                            ).add_to(metro_map)
        
        # Draw transfer points
        for i in range(len(route) - 1):
            curr_station = route[i]
            next_station = route[i+1]
            
            if curr_station['station'] == next_station['station'] and curr_station['line'] != next_station['line']:
                station_coord = all_stations[curr_station['station']]
                
                # Add transfer indicator
                folium.CircleMarker(
                    location=station_coord,
                    radius=10,
                    color="#FF6B6B",
                    fill=True,
                    fillColor="#FF6B6B",
                    fillOpacity=0.8,
                    weight=2,
                    tooltip=f"Transfer at {curr_station['station']}: {curr_station['line']} to {next_station['line']}"
                ).add_to(metro_map)
        
        # Add markers for all stations in the route
        for i, station_info in enumerate(route):
            station_name = station_info['station']
            station_coord = all_stations[station_name]
            station_line = station_info['line']
            
            # Skip duplicate markers for transfer stations
            skip = False
            if i > 0 and station_name == route[i-1]['station']:
                skip = True
            
            if not skip:
                # Use different icons for start, end, and transfer stations
                icon_html = "🚉"  # Default
                if i == 0:
                    icon_html = "🚆"  # Start station
                elif i == len(route) - 1:
                    icon_html = "🏁"  # End station
                elif station_name in intersection_stations:
                    icon_html = "🔄"  # Transfer station
                
                # Add marker
                folium.Marker(
                    location=station_coord,
                    tooltip=station_name,
                    icon=folium.DivIcon(
                        html=f'<div style="font-size: 15px; text-align: center;">{icon_html}</div>',
                        icon_size=(20, 20),
                        icon_anchor=(10, 10)
                    )
                ).add_to(metro_map)
                
                # Add circle with line color
                folium.CircleMarker(
                    location=station_coord,
                    radius=8,
                    color=route_colors.get(station_line, '#ff0000'),
                    fill=True,
                    fillColor=route_colors.get(station_line, '#ff0000'),
                    fillOpacity=0.8,
                    weight=2,
                    opacity=1.0
                ).add_to(metro_map)
    
    else:
        # No route specified, show all lines based on line_filter
        for route_name, route_data in route_mapping.items():
            if line_filter == 'all' or (line_filter == 'red' and route_name == 'Red Line') or (line_filter == 'green' and route_name == 'Green Line'):
                kml_name = route_data['kml_name']
                
                if kml_name in kml_routes:
                    # Draw the entire route line using KML coordinates
                    folium.PolyLine(
                        locations=kml_routes[kml_name],
                        color=route_data['color'],
                        weight=4,
                        opacity=1.0,
                        tooltip=route_name
                    ).add_to(metro_map)
                
                # Add station markers
                for station, coord in zip(route_data['stations'], route_data['coords']):
                    # Skip intersection stations that are already added
                    if station in intersection_stations and route_name == 'Red Line' and station in corridor_2:
                        continue
                    
                    # Add the marker
                    folium.Marker(
                        location=coord,
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
                        radius=5,
                        color=route_data['color'],
                        fill=True,
                        fillColor=route_data['color'],
                        fillOpacity=1,
                        weight=2,
                        opacity=0.8
                    ).add_to(metro_map)
                    
                    # Highlight intersection stations
                    if station in intersection_stations:
                        folium.CircleMarker(
                            location=coord,
                            radius=10,
                            color="#FF6B6B",
                            fill=False,
                            weight=2,
                            opacity=0.8,
                            tooltip=f"Transfer Station: {station}"
                        ).add_to(metro_map)
    
    # Save map to a temporary file
    map_html = metro_map._repr_html_()
    
    # Create a full-screen template
    fullscreen_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Surat Metro Map</title>
        <style>
            body, html {{
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
                overflow: hidden;
            }}
            #map {{
                height: 100%;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        {map_html}
    </body>
    </html>
    """
    
    return fullscreen_html

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
