import streamlit as st
import pandas as pd
import re
from geopy.distance import geodesic

def extract_postcode(address):
    """Extracts and returns only the postcode from the provided address."""
    postcode_match = re.search(r'([A-Za-z]{1,2}\d{1,2}[A-Za-z]? \d[A-Za-z]{2})$', address.strip())
    return postcode_match.group(1).upper().replace(" ", "") if postcode_match else None

def calculate_distance_time(start, stops, final):
    """Calculates total distance and estimated travel time between postcodes."""
    locations = [start] + stops + [final]
    total_distance = 0.0
    total_time = 0.0  # In minutes
    travel_details = []

    for i in range(len(locations) - 1):
        distance = 2.5  # Placeholder distance in miles (adjust based on actual calculations)
        time = (distance / 30) * 60  # Assuming 30 mph average speed
        total_distance += distance
        total_time += time
        travel_details.append([f"{locations[i]} to {locations[i+1]}", f"{distance:.2f} mi", f"{time:.0f} min"])
    
    return travel_details, total_distance, total_time

st.title("WCI Aberdeen Route Planner")

start_address = extract_postcode(st.text_input("Enter Starting Postcode:", "AB10 7AY"))
num_stops = st.number_input("Enter number of stops:", min_value=0, max_value=10, value=3, step=1)
stop_addresses = [extract_postcode(st.text_input(f"Enter stop {i+1} postcode:")) for i in range(num_stops)]
final_destination = extract_postcode(st.text_input("Enter Final Destination Postcode:", "AB24 5ES"))

if st.button("Calculate Route"):
    stop_addresses = [stop for stop in stop_addresses if stop]
    
    if not start_address or not final_destination:
        st.error("Please enter valid postcodes for the starting point and final destination.")
    else:
        travel_data, total_dist, total_time = calculate_distance_time(start_address, stop_addresses, final_destination)
        
        df = pd.DataFrame(travel_data, columns=["Location", "Miles", "Time (min)"])
        st.table(df)
        
        st.write(f"**Total Distance:** {total_dist:.2f} miles")
        st.write(f"**Estimated Total Travel Time:** {total_time:.0f} minutes")
