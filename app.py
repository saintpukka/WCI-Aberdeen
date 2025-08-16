import streamlit as st
import requests
import polyline
import folium
from streamlit_folium import st_folium

# =========================
# CONFIGURATION
# =========================
API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"  # Replace with your actual key

# =========================
# STREAMLIT APP
# =========================
st.title("🚍 Smart Route Planner")
st.caption("Enter addresses in the format: `23, Anywhere Street, AH23 5AH`")

# Input fields
start = st.text_input("Starting Address")
stops = st.text_area("Stops (one per line)")
end = st.text_input("Final Destination")

if st.button("Calculate Best Route"):
    if start and end:
        # Process stops into list
        waypoints = stops.strip().split("\n") if stops.strip() else []

        # Build the request
        url = f"https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": start,
            "destination": end,
            "waypoints": "|".join(waypoints) if waypoints else None,
            "optimizeWaypoints": "true",  # Ensures best order
            "mode": "driving",
            "key": API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] == "OK":
            route = data["routes"][0]
            legs = route["legs"]

            # Extract polyline points
            points = polyline.decode(route["overview_polyline"]["points"])

            # Center map on first location
            start_loc = legs[0]["start_location"]
            m = folium.Map(location=[start_loc["lat"], start_loc["lng"]], zoom_start=12)

            # Draw route
            folium.PolyLine(points, color="blue", weight=5, opacity=0.8).add_to(m)

            # Add markers
            for i, leg in enumerate(legs):
                folium.Marker(
                    [leg["start_location"]["lat"], leg["start_location"]["lng"]],
                    popup=f"Stop {i+1}: {leg['start_address']}"
                ).add_to(m)

                if i == len(legs) - 1:
                    folium.Marker(
                        [leg["end_location"]["lat"], leg["end_location"]["lng"]],
                        popup=f"Final: {leg['end_address']}",
                        icon=folium.Icon(color="red")
                    ).add_to(m)

            # Display map
            st_map = st_folium(m, width=700, height=500)

            # Show table
            st.subheader("📍 Optimized Route")
            for i, leg in enumerate(legs):
                st.write(f"**{i+1}. {leg['start_address']} → {leg['end_address']}**")
                st.write(f"Distance: {leg['distance']['text']} | Duration: {leg['duration']['text']}")

        else:
            st.error(f"Error from Google Maps API: {data['status']}")
    else:
        st.warning("Please enter at least a start and final destination.")
