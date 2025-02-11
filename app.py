import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta
import pandas as pd
import re

# Function to normalize and extract postcode from address
def clean_postcode(address):
    """Extract and standardize postcode from an address."""
    address = address.strip().upper()  # Normalize case and remove extra spaces
    postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})$', address)
    if postcode_match:
        return postcode_match.group(1).replace(" ", "")  # Remove unnecessary spaces
    return None

# Function to geocode address
def geocode_address(address, retries=3):
    """Convert full address to latitude and longitude with retries."""
    geolocator = Nominatim(user_agent="route_planner", timeout=5)
    for i in range(retries):
        try:
            location = geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            else:
                return None
        except GeocoderTimedOut:
            continue
    return None

# Function to compute the best route and travel times
def get_best_route(start_address, destination_addresses, speed_kmh=35, pickup_time=1.5, extra_delay=0.5):
    """Find the best route from start to multiple destinations using full addresses."""
    
    # Geocode starting address
    start_coords = geocode_address(start_address)
    if not start_coords:
        return "Invalid starting address.", None
    
    # Geocode destination addresses
    destination_coords = [(addr, geocode_address(addr)) for addr in destination_addresses]
    destination_coords = [(addr, coord) for addr, coord in destination_coords if coord]
    
    if not destination_coords:
        return "No valid destinations.", None
    
    # Get graph from OpenStreetMap for the area
    G = ox.graph_from_point(start_coords, dist=20000, network_type='drive')
    
    # Find nearest nodes to start and destinations
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    destination_nodes = [(addr, ox.distance.nearest_nodes(G, lon, lat)) for addr, (lat, lon) in destination_coords]
    
    # Sort destinations based on shortest path distance from start
    destination_nodes.sort(key=lambda x: nx.shortest_path_length(G, start_node, x[1], weight='length'))
    
    # Compute shortest paths and travel times
    travel_details = []
    total_time = 0
    total_distance = 0
    current_node = start_node
    current_address = start_address
    
    # Prompt for journey start time
    start_time = "08:00"  # Default time
    current_time = datetime.strptime(start_time, "%H:%M")
    
    for addr, dest_node in destination_nodes:
        # Calculate distance and travel time
        route_length_m = nx.shortest_path_length(G, current_node, dest_node, weight='length')  # in meters
        route_length_mi = route_length_m * 0.000621371  # Convert meters to miles
        travel_time = (route_length_m / 1000) / (speed_kmh / 60)  # Convert to minutes
        total_time += travel_time + extra_delay + pickup_time
        total_distance += route_length_mi
        arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)
        pickup_complete_time = arrival_time + timedelta(minutes=pickup_time)
        
        # Format travel details
        travel_details.append([f"{current_address} to {addr}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])
        
        # Update current location and time
        current_node = dest_node
        current_address = addr
        current_time = pickup_complete_time
    
    travel_details.append(["Total", f"{total_distance:.2f} mi", f"{total_time:.2f} min", "-", "-"])
    
    return travel_details, total_time

# Streamlit UI
st.title(" WCI Route Planner")

# User inputs
start_address = st.text_input("Enter starting address:")
num_destinations = st.number_input("Enter number of destinations:", min_value=1, step=1)
destination_addresses = [st.text_input(f"Enter destination {i+1}:") for i in range(num_destinations)]

if st.button("Calculate Route"):
    travel_details, travel_time = get_best_route(start_address, destination_addresses)
    if isinstance(travel_details, str):
        st.error(travel_details)
    else:
        df = pd.DataFrame(travel_details, columns=["Location", "Miles", "Time Taken", "Departure", "Arrival"])
        st.table(df)
        st.success(f"Total Estimated Travel Time: {round(travel_time, 2)} minutes")
