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

# User inputsimport streamlit as st
import googlemaps
from datetime import datetime
import pandas as pd

st.title("🚍 Church Bus Route Planner")
st.caption("Enter addresses in this format: '23, Anywhere Street, AH23 5AH'")

# Input fields
start = st.text_input("Starting Point")
stops_text = st.text_area("Enter Stops (one per line)")
end = st.text_input("Final Destination")

if st.button("Plan Route"):
    if not start or not end:
        st.error("Please enter both a starting and final destination.")
    else:
        # Use the API key you provided
        API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"
        gmaps = googlemaps.Client(key=API_KEY)

        # Prepare waypoints with optimization
        waypoints = [s.strip() for s in stops_text.split("\n") if s.strip()]
        waypoints_param = ["optimize:true"] + waypoints if waypoints else None

        try:
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
                    dist_value = leg["distance"]["value"]  # meters
                    dur_value = leg["duration"]["value"]  # seconds
                    total_distance += dist_value
                    total_duration += dur_value
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
                df = pd.DataFrame(table_data)
                st.table(df)

                # Build Google Maps embed URL with optimized order
                base_url = "https://www.google.com/maps/embed/v1/directions"
                stops_str = "|".join([leg["end_address"] for leg in route[:-1]])  # optimized stops
                map_url = f"{base_url}?key={API_KEY}&origin={start}&destination={end}"
                if stops_str:
                    map_url += f"&waypoints={stops_str}"

                st.subheader("🗺️ Route Map")
                st.components.v1.iframe(map_url, height=500, scrolling=True)

        except Exception as e:
            st.error(f"Error: {e}")

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

