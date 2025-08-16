import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium
import pandas as pd

# Google Maps API key
API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"
gmaps = googlemaps.Client(key=API_KEY)

st.title("Church Bus Route Planner")
st.caption('Enter address in this format: "23, Anywhere Street, AH23 5AH"')

# User inputs
starting_point = st.text_input("Enter Starting Address")
final_point = st.text_input("Enter Final Address")
stops = st.text_area("Enter Stops (one per line)").splitlines()

if st.button("Calculate Optimized Route"):
    if starting_point and final_point:
        # Optimize route using Google Maps
        directions_result = gmaps.directions(
            origin=starting_point,
            destination=final_point,
            waypoints=["optimize:true"] + stops if stops else None,
            mode="driving"
        )

        if directions_result:
            route = directions_result[0]['legs']
            
            # Create a folium map
            m = folium.Map(location=[route[0]['start_location']['lat'], route[0]['start_location']['lng']], zoom_start=12)

            # Draw route polyline
            for leg in route:
                steps = leg['steps']
                for step in steps:
                    polyline = step['polyline']['points']
                    points = googlemaps.convert.decode_polyline(polyline)
                    folium.PolyLine([(p['lat'], p['lng']) for p in points], color="blue", weight=3).add_to(m)

            # Add markers for stops
            for i, leg in enumerate(route):
                folium.Marker(
                    location=[leg['start_location']['lat'], leg['start_location']['lng']],
                    popup=f"Stop {i+1}: {leg['start_address']}"
                ).add_to(m)
            
            # Add final destination marker
            folium.Marker(
                location=[route[-1]['end_location']['lat'], route[-1]['end_location']['lng']],
                popup=f"Final Destination: {route[-1]['end_address']}",
                icon=folium.Icon(color="red")
            ).add_to(m)

            # Use two columns to prevent display disappearing
            col1, col2 = st.columns(2)

            # Map on the left
            with col1:
                st_folium(m, width=600, height=500)

            # Table on the right
            table_data = []
            for i, leg in enumerate(route):
                table_data.append({
                    "Leg": f"{i+1}",
                    "From": leg['start_address'],
                    "To": leg['end_address'],
                    "Distance": leg['distance']['text'],
                    "Duration": leg['duration']['text']
                })
            df = pd.DataFrame(table_data)

            with col2:
                st.subheader("Route Details:")
                st.table(df)

        else:
            st.error("No route found. Please check the addresses.")
    else:
        st.error("Please enter both a starting and final address.")
