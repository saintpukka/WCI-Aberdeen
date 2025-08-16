import streamlit as st
import googlemaps
from datetime import datetime

# Title
st.title("🚍 Church Bus Route Planner")
st.caption("Enter addresses in this format: '23, Anywhere Street, AH23 5AH'")

# Input fields
start = st.text_input("Starting Point")
stops = st.text_area("Enter Stops (one per line)")
end = st.text_input("Final Destination")

# Button
if st.button("Plan Route"):
    if not start or not end:
        st.error("Please enter both a starting and final destination.")
    else:
        # Setup Google Maps client
        API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"  # replace with your API key
        gmaps = googlemaps.Client(key=API_KEY)

        # Format stops into list
        waypoints = [s.strip() for s in stops.split("\n") if s.strip()]

        try:
            # Call Directions API
            directions_result = gmaps.directions(
                origin=start,
                destination=end,
                waypoints=waypoints,
                mode="driving",
                departure_time=datetime.now()
            )

            if not directions_result:
                st.error("No route found. Please check addresses.")
            else:
                # Extract route info
                route = directions_result[0]["legs"]

                # Build a summary table
                st.subheader("📋 Route Summary")
                for i, leg in enumerate(route):
                    st.write(f"**Leg {i+1}:** {leg['start_address']} → {leg['end_address']}")
                    st.write(f"- Distance: {leg['distance']['text']}")
                    st.write(f"- Duration: {leg['duration']['text']}")

                # Generate Google Maps embed URL
                base_url = "https://www.google.com/maps/embed/v1/directions"
                stops_str = "|".join(waypoints)
                map_url = (
                    f"{base_url}?key={API_KEY}"
                    f"&origin={start}"
                    f"&destination={end}"
                )
                if stops_str:
                    map_url += f"&waypoints={stops_str}"

                # Show Map in an iframe (persistent)
                st.subheader("🗺️ Route Map")
                st.components.v1.iframe(map_url, height=500, scrolling=True)

        except Exception as e:
            st.error(f"Error: {e}")
