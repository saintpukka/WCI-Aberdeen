import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta
import pandas as pd

# Function to convert postcode to latitude and longitude
def geocode_postcode(postcode, retries=3):
    """Convert postcode to latitude and longitude with retries."""
    geolocator = Nominatim(user_agent="route_planner", timeout=5)
    for i in range(retries):
        try:
            location = geolocator.geocode(postcode)
            if location:
                return (location.latitude, location.longitude)
            else:
                return None
        except GeocoderTimedOut:
            continue
    return None

# Function to compute the best route and travel times
def get_best_route(start_postcode, destination_postcodes, final_postcode, speed_kmh=35, pickup_time=1.5, extra_delay=0.5):
    """Find the best route from start through multiple destinations and ending at a final destination."""
    
    # Geocode starting postcode
    start_coords = geocode_postcode(start_postcode)
    if not start_coords:
        return "Invalid starting postcode.", None
    
    # Geocode destination postcodes
    destination_coords = [(pc, geocode_postcode(pc)) for pc in destination_postcodes]
    destination_coords = [(pc, coord) for pc, coord in destination_coords if coord]
    
    # Geocode final destination
    final_coords = geocode_postcode(final_postcode)
    if not final_coords:
        return "Invalid final destination.", None
    
    if not destination_coords:
        return "No valid destinations.", None
    
    # Get graph from OpenStreetMap for the area
    G = ox.graph_from_point(start_coords, dist=20000, network_type='drive')
    
    # Find nearest nodes to start, destinations, and final destination
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    destination_nodes = [(pc, ox.distance.nearest_nodes(G, lon, lat)) for pc, (lat, lon) in destination_coords]
    final_node = ox.distance.nearest_nodes(G, final_coords[1], final_coords[0])
    
    # Sort intermediate destinations based on shortest path distance from start
    destination_nodes.sort(key=lambda x: nx.shortest_path_length(G, start_node, x[1], weight='length'))
    
    # Compute shortest paths and travel times
    travel_details = []
    total_time = 0
    total_distance = 0
    current_node = start_node
    current_postcode = start_postcode
    
    # Prompt for journey start time
    start_time = "08:00"  # Default time
    current_time = datetime.strptime(start_time, "%H:%M")
    
    for pc, dest_node in destination_nodes:
        # Calculate distance and travel time
        route_length_m = nx.shortest_path_length(G, current_node, dest_node, weight='length')  # in meters
        route_length_mi = route_length_m * 0.000621371  # Convert meters to miles
        travel_time = (route_length_m / 1000) / (speed_kmh / 60)  # Convert to minutes
        total_time += travel_time + extra_delay + pickup_time
        total_distance += route_length_mi
        arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)
        pickup_complete_time = arrival_time + timedelta(minutes=pickup_time)
        
        # Format travel details
        travel_details.append([f"{current_postcode} to {pc}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])
        
        # Update current location and time
        current_node = dest_node
        current_postcode = pc
        current_time = pickup_complete_time
    
    # Final destination calculation
    route_length_m = nx.shortest_path_length(G, current_node, final_node, weight='length')  # in meters
    route_length_mi = route_length_m * 0.000621371  # Convert meters to miles
    travel_time = (route_length_m / 1000) / (speed_kmh / 60)  # Convert to minutes
    total_time += travel_time + extra_delay
    total_distance += route_length_mi
    arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)
    
    travel_details.append([f"{current_postcode} to {final_postcode}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])
    
    travel_details.append(["Total", f"{total_distance:.2f} mi", f"{total_time:.2f} min", "-", "-"])
    
    return travel_details, total_time

# Streamlit UI
st.title(" WCI Route Planner")

# User inputs
start_postcode = st.text_input("Enter starting postcode:")
num_destinations = st.number_input("Enter number of destinations:", min_value=1, step=1)
destination_postcodes = [st.text_input(f"Enter postcode {i+1}:") for i in range(num_destinations)]
final_postcode = st.text_input("Enter final destination postcode:")

if st.button("Calculate Route"):
    travel_details, travel_time = get_best_route(start_postcode, destination_postcodes, final_postcode)
    if isinstance(travel_details, str):
        st.error(travel_details)
    else:
        df = pd.DataFrame(travel_details, columns=["Location", "Miles", "Time Taken", "Departure", "Arrival"])
        st.table(df)
        st.success(f"Total Estimated Travel Time: {round(travel_time, 2)} minutes")
