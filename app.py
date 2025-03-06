import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta
import pandas as pd
import folium
from streamlit_folium import folium_static
from itertools import permutations

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

# Function to compute the best route using TSP

def get_best_route(start_location, destination_locations, final_location, start_time, speed_mph=30, pickup_time=1, extra_delay=0.2):
    """Find the optimal route through multiple destinations ending at a final destination."""

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

    # Function to calculate the path length
    def path_length(path):
        length = 0
        for i in range(len(path) - 1):
            length += nx.shortest_path_length(G, path[i], path[i + 1], weight='length')
        return length

    # Find the best permutation of destinations
    best_path = None
    best_length = float("inf")

    for perm in permutations(destination_nodes):
        current_path = [start_node] + [node for _, node in perm] + [final_node]
        current_length = path_length(current_path)

        if current_length < best_length:
            best_length = current_length
            best_path = current_path
            best_order = [loc for loc, _ in perm]

    # Compute shortest paths and travel times
    travel_details = []
    total_time = 0
    total_distance = 0

    current_time = datetime.strptime(start_time, "%H:%M")
    current_location = start_location

    for i in range(len(best_path) - 1):
        route_length_m = nx.shortest_path_length(G, best_path[i], best_path[i + 1], weight='length')
        route_length_mi = route_length_m * 0.000621371
        travel_time = (route_length_mi) / (speed_mph / 60)

        if i < len(best_path) - 2:
            loc = best_order[i]
            total_time += travel_time + extra_delay + pickup_time
            arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)
            pickup_complete_time = arrival_time + timedelta(minutes=pickup_time)
        else:
            loc = final_location
            total_time += travel_time + extra_delay
            arrival_time = current_time + timedelta(minutes=travel_time + extra_delay)

        travel_details.append([f"{current_location} to {loc}", f"{route_length_mi:.2f} mi", f"{travel_time + extra_delay:.2f} min", current_time.strftime('%H:%M'), arrival_time.strftime('%H:%M')])

        current_location = loc
        current_time = arrival_time if i == len(best_path) - 2 else pickup_complete_time

        total_distance += route_length_mi

    travel_details.append(["Total", f"{total_distance:.2f} mi", f"{total_time:.2f} min", "-", "-"])

    return travel_details, total_time, G

# Streamlit UI
st.title("WCI Aberdeen Route Planner")
st.markdown("<small>Address format: 23, Anywhere Street, AH23 5AH</small>", unsafe_allow_html=True)

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

            # Generate map visualization
            st.subheader("Route Map")
            map_center = geocode_location(start_location)
            if map_center:
                route_map = folium.Map(location=map_center, zoom_start=12)

                folium.Marker(location=map_center, popup="Start", icon=folium.Icon(color="green")).add_to(route_map)

                for i, loc in enumerate(df.iloc[:-1, 0]):
                    coord = geocode_location(loc.split(" to ")[1])
                    if coord:
                        folium.Marker(
                            location=coord,
                            popup=f"{i + 1}: {loc.split(' to ')[1]}",
                            icon=folium.Icon(color="blue", icon=f"{i + 1}", prefix='fa')
                        ).add_to(route_map)

                final_coord = geocode_location(final_location)
                if final_coord:
                    folium.Marker(location=final_coord, popup="Final Destination", icon=folium.Icon(color="red")).add_to(route_map)

                folium_static(route_map)
            else:
                st.warning("Unable to load map due to geocoding issues.")

    except ValueError:
        st.error("Invalid time format. Please enter time in HH:MM format.")
