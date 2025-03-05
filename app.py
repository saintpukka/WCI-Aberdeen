import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta
import pandas as pd
import folium
from streamlit_folium import folium_static

# Function to convert postcode or address to latitude and longitude
def geocode_location(location, retries=3):
    """Convert postcode or address to latitude and longitude with retries."""
    geolocator = Nominatim(user_agent="route_planner", timeout=5)
    for _ in range(retries):
        try:
            location = geolocator.geocode(location, addressdetails=True)
            if location:
                return (location.latitude, location.longitude)
        except GeocoderTimedOut:
            continue
    return None

# Function to create numbered markers
def create_numbered_icon(number, color="blue"):
    return folium.DivIcon(html=f"""
    <div style="font-size: 14px; color: white; background-color: {color}; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
        {number}
    </div>
    """)

# Function to compute the best route and travel times
def get_best_route(start_location, destination_locations, final_location, start_time, speed_kmh=35, pickup_time=1.5, extra_delay=0.5):
    """Find the best route from start through multiple destinations and ending at a final destination."""

    # Geocode starting location
    start_coords = geocode_location(start_location)
    if not start_coords:
        return "Invalid starting location.", None, None

    # Geocode destination locations
    destination_coords = [(loc, geocode_location(loc)) for loc in destination_locations]
    destination_coords = [(loc, coord) for loc, coord in destination_coords if coord]

    # Geocode final destination
    final_coords = geocode_location(final_location)
    if not final_coords:
        return "Invalid final destination.", None, None

    if not destination_coords:
        return "No valid destinations.", None, None

    # Get road network graph
    G = ox.graph_from_point(start_coords, dist=20000, network_type='drive')

    # Find nearest nodes to start, destinations, and final destination
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    destination_nodes = [(loc, ox.distance.nearest_nodes(G, lon, lat)) for loc, (lat, lon) in destination_coords]
    final_node = ox.distance.nearest_nodes(G, final_coords[1], final_coords[0])

    # Calculate shortest path distance to each destination and sort by closest
    destination_nodes.sort(key=lambda x: nx.shortest_path_length(G, start_node, x[1], weight='length'))

    # Compute shortest paths and travel times
    travel_details = []
    total_time = 0
    total_distance = 0
    current_node = start_node
    current_location = start_location

    # Convert start_time to datetime object
    current_time = datetime.strptime(start_time, "%H:%M")

    for i, (loc, dest_node) in enumerate(destination_nodes, start=1):
        # Calculate distance and travel time
        route = nx.shortest_path(G, current_node, dest_node, weight='length')
        route_length_m = sum(nx.get_edge_attributes(G, 'length')[edge] for edge in zip(route[:-1], route[1:]))
        route_length_mi = route_length_m * 0.000621371  # Convert meters to miles
        travel_time = (route_length_m / 1000) / (speed_kmh / 60)  # Convert to minutes
        total_time += travel_time + extra_delay + pickup_time
        total_distance += route_length_mi
        arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)
        pickup_complete_time = arrival_time + timedelta(minutes=pickup_time)

        # Format travel details
        travel_details.append([f"{current_location} to {loc}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])

        # Update current location and time
        current_node = dest_node
        current_location = loc
        current_time = pickup_complete_time

    # Final destination calculation
    route = nx.shortest_path(G, current_node, final_node, weight='length')
    route_length_m = sum(nx.get_edge_attributes(G, 'length')[edge] for edge in zip(route[:-1], route[1:]))
    route_length_mi = route_length_m * 0.000621371
    travel_time = (route_length_m / 1000) / (speed_kmh / 60)
    total_time += travel_time + extra_delay
    total_distance += route_length_mi
    arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)

    travel_details.append([f"{current_location} to {final_location}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])

    travel_details.append(["Total", f"{total_distance:.2f} mi", f"{total_time:.2f} min", "-", "-"])

    return travel_details, total_time, G

# Streamlit UI
st.title("WCI Aberdeen Route Planner")

# User inputs
start_location = st.text_input("Enter starting postcode or address:")
start_time = st.text_input("Enter journey start time (HH:MM):", value="08:00")
num_destinations = st.number_input("Enter number of destinations:", min_value=1, step=1)
destination_locations = [st.text_input(f"Enter destination {i+1} (postcode or address):") for i in range(num_destinations)]
final_location = st.text_input("Enter final destination (postcode or address):")

if st.button("Calculate Route"):
    try:
        # Validate start time format
        datetime.strptime(start_time, "%H:%M")

        travel_details, travel_time, G = get_best_route(start_location, destination_locations, final_location, start_time)

        if isinstance(travel_details, str):
            st.error(travel_details)
        else:
            df = pd.DataFrame(travel_details, columns=["Location", "Miles", "Time Taken", "Departure", "Arrival"])
            st.table(df)
            st.success(f"Total Estimated Travel Time: {round(travel_time, 2)} minutes")

    except ValueError:
        st.error("Invalid time format. Please enter time in HH:MM format.")
