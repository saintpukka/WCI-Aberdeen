import streamlit as st
import googlemaps
from datetime import datetime
import pandas as pd

# Title
st.title("🚍 Church Bus Route Planner")
st.caption("Enter addresses in this format: '23, Anywhere Street, AH23 5AH'")

# Input fields with unique keys
start = st.text_input("Starting Point", key="start")
stops_text = st.text_area("Enter Stops (one per line)", key="stops")
end = st.text_input("Final Destination", key="end")

if st.button("Plan Route"):
    if not start or not end:
        st.error("Please enter both a starting and final destination.")
    else:
        # Google Maps client
        API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"
        gmaps = googlemaps.Client(key=API_KEY)

        # Prepare waypoints with optimization
        waypoints = [s.strip() for s in stops_text.split("\n") if s.strip()]
        waypoints_param = ["optimize:true"] + waypoints if waypoints else None

        try:
            # Directions API call
            directions_result = gmaps.directions(
                origin=start,
                destination=end,
                waypoints=waypoints_param,
                mode="driving",
                departure_time=datetime.now()
            )

            if not directions_result:
                st.error("No route found. Please check addresses.")
            else:
                route = directions_result[0]["legs"]

                # Build route table
                table_data = []
                total_distance = 0
                total_duration = 0
                for i, leg in enumerate(route):
                    total_distance += leg["distance"]["value"]  # meters
                    total_duration += leg["duration"]["value"]  # seconds
                    table_data.append({
                        "Leg": f"{i+1}",
                        "From": leg["start_address"],
                        "To": leg["end_address"],
                        "Distance": leg["distance"]["text"],
                        "Duration": leg["duration"]["text"]
                    })

                # Add total row
                table_data.append({
                    "Leg": "Total",
                    "From": "",
                    "To": "",
                    "Distance": f"{round(total_distance/1000, 2)} km",
                    "Duration": f"{round(total_duration/60)} min"
                })

                st.subheader("📋 Route Summary")
                st.table(pd.DataFrame(table_data))

                # Build Google Maps embed URL with optimized stops
                base_url = "https://www.google.com/maps/embed/v1/directions"
                stops_str = "|".join([leg["end_address"] for leg in route[:-1]])  # optimized stops
                map_url = f"{base_url}?key={API_KEY}&origin={start}&destination={end}"
                if stops_str:
                    map_url += f"&waypoints={stops_str}"

                st.subheader("🗺️ Route Map")
                st.components.v1.iframe(map_url, height=500, scrolling=True)

        except Exception as e:
            st.error(f"Error: {e}")
