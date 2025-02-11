import streamlit as st
import networkx as nx
import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import folium
from streamlit_folium import st_folium
import re

# Function to extract and normalize postcodes
def extract_postcode(address):
    postcode_pattern = r"\b[a-zA-Z]{1,2}\d{1,2}[a-zA-Z]?\s?\d[a-zA-Z]{2}\b"
    match = re.search(postcode_pattern, address, re.IGNORECASE)
    return match.group(0).upper().replace(" ", "") if match else None

# Function to get latitude and longitude
def get_lat_lon(address):
    geolocator = Nominatim(user_agent="route_planner")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except GeocoderTimedOut:
        return None
    return None

# Function to calculate route and travel time
def get_optimized_route(start_address, destinations, final_destination):
    locations = {start_address: get_lat_lon(start_address)}
    for address in destinations:
        locations[address] = get_lat_lon(address)
    locations[final_destination] = get_lat_lon(final_destination)
    
    if any(loc is None for loc in locations.values()):
        return "Error: One or more addresses could not be geocoded.", None
    
    G = ox.graph_from_point(locations[start_address], dist=20000, network_type="drive")
    
    nodes = {addr: ox.nearest_nodes(G, lon=loc[1], lat=loc[0]) for addr, loc in locations.items()}
    
    all_addresses = [start_address] + destinations + [final_destination]
    sorted_addresses = [start_address]
    remaining = set(destinations)
    
    while remaining:
        last = sorted_addresses[-1]
        next_stop = min(remaining, key=lambda x: nx.shortest_path_length(G, nodes[last], nodes[x], weight='length'))
        sorted_addresses.append(next_stop)
        remaining.remove(next_stop)
    
    sorted_addresses.append(final_destination)
    
    travel_times = []
    speed_mps = (35 * 1000) / 3600  # Convert km/h to meters per second
    pickup_time = 90  # 1 minute 30 seconds per stop
    traffic_buffer = 30  # Additional buffer for traffic light
    
    total_time = 0
    total_distance = 0
    
    for i in range(len(sorted_addresses) - 1):
        origin, destination = sorted_addresses[i], sorted_addresses[i + 1]
        route = nx.shortest_path(G, nodes[origin], nodes[destination], weight='length')
        distance = sum(ox.utils_graph.get_route_edge_attributes(G, route, 'length')) / 1609.34  # Convert meters to miles
        travel_time = (distance * 1609.34) / speed_mps + pickup_time + traffic_buffer
        
        total_time += travel_time
        total_distance += distance
        travel_times.append((origin, destination, distance, travel_time))
    
    return travel_times, total_time, total_distance

# Streamlit UI
st.title("WCI Aberdeen Route Planner")

start_address = st.text_input("Enter Starting Address:")
num_stops = st.number_input("Enter number of stops:", min_value=1, step=1, format="%d")
destination_addresses = [st.text_input(f"Enter stop {i+1}:") for i in range(num_stops)]
final_destination = st.text_input("Enter Final Destination:")

if st.button("Calculate Route"):
    travel_times, total_time, total_distance = get_optimized_route(start_address, destination_addresses, final_destination)
    
    if isinstance(travel_times, str):
        st.error(travel_times)
    else:
        df = pd.DataFrame(travel_times, columns=["From", "To", "Distance (mi)", "Travel Time (s)"])
        df["Travel Time"] = df["Travel Time (s)"].apply(lambda x: f"{int(x//60)} min {int(x%60)} sec")
        df.drop(columns=["Travel Time (s)"], inplace=True)
        
        st.write("### Route Summary")
        st.dataframe(df)
        st.write(f"**Total Distance:** {total_distance:.2f} miles")
        st.write(f"**Total Estimated Travel Time:** {int(total_time//60)} min {int(total_time%60)} sec")
