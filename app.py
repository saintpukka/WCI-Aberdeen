import streamlit as st
import pandas as pd
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.distance import geodesic

def standardize_address(address):
    """Cleans and standardizes addresses to ensure proper formatting."""
    address = address.strip().title()  # Convert to title case for consistency
    postcode_match = re.search(r'([A-Za-z]{1,2}\d{1,2}[A-Za-z]? \d[A-Za-z]{2})$', address)
    if postcode_match:
        postcode = postcode_match.group(1).upper().replace(" ", "")  # Remove extra spaces
        address = re.sub(r'([A-Za-z]{1,2}\d{1,2}[A-Za-z]? \d[A-Za-z]{2})$', postcode, address)  # Replace with formatted postcode
    return address

def get_coordinates(address):
    """Gets latitude and longitude for a given address."""
    geolocator = Nominatim(user_agent="route_planner")
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except GeocoderTimedOut:
        return None

def calculate_distance_time(start, stops, final):
    """Calculates total distance and estimated travel time between locations."""
    locations = [start] + stops + [final]
    total_distance = 0.0
    total_time = 0.0  # In minutes
    travel_details = []

    for i in range(len(locations) - 1):
        coord1 = get_coordinates(locations[i])
        coord2 = get_coordinates(locations[i + 1])
        if coord1 and coord2:
            distance = geodesic(coord1, coord2).miles
            time = (distance / 30) * 60  # Assuming 30 mph average speed
            total_distance += distance
            total_time += time
            travel_details.append([f"{locations[i]} to {locations[i+1]}", f"{distance:.2f} mi", f"{time:.0f} min"])
        else:
            travel_details.append([f"{locations[i]} to {locations[i+1]}", "Error", "Could not find location"])
    return travel_details, total_distance, total_time

st.title("WCI Aberdeen Route Planner")

start_address = st.text_input("Enter Starting Address:", "AB10 7AY")
num_stops = st.number_input("Enter number of stops:", min_value=0, max_value=10, value=3, step=1)
stop_addresses = [st.text_input(f"Enter stop {i+1}:") for i in range(num_stops)]
final_destination = st.text_input("Enter Final Destination:", "60 Nelson Street AB24 5ES")

if st.button("Calculate Route"):
    start_address = standardize_address(start_address)
    stop_addresses = [standardize_address(stop) for stop in stop_addresses if stop.strip()]
    final_destination = standardize_address(final_destination)
    
    travel_data, total_dist, total_time = calculate_distance_time(start_address, stop_addresses, final_destination)
    
    df = pd.DataFrame(travel_data, columns=["Location", "Miles", "Time (min)"])
    st.table(df)
    
    st.write(f"**Total Distance:** {total_dist:.2f} miles")
    st.write(f"**Estimated Total Travel Time:** {total_time:.0f} minutes")
