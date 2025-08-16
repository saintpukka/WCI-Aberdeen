import streamlit as st
import googlemaps
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium

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

                # Create Folium map centered on first location
                m = folium.Map(location=[route[0]["start_location"]["lat"], route[0]["start_location"]["lng"]], zoom_start=12)

                # Add markers and numbered icons
                for i, leg in enumerate(route):
                    folium.Marker(
                        location=[leg["start_location"]["lat"], leg["start_location"]["lng"]],
                        popup=f"Stop {i+1}: {leg['start_address']}",
                        icon=folium.DivIcon(
                            html=f"""<div style='font-size:12px;color:white;background:red;border-radius:50%;width:24px;height:24px;text-align:center;'>{i+1}</div>"""
                        )
                    ).add_to(m)

                # Add final destination marker with special color
                folium.Marker(
                    location=[route[-1]["end_location"]["lat"], route[-1]["end_location"]["lng"]],
                    popup=f"Final Destination: {route[-1]['end_address']}",
                    icon=folium.DivIcon(
                        html=f"""<div style='font-size:12px;color:white;background:green;border-radius:50%;width:24px;height:24px;text-align:center;'>{len(route)}</div>"""
                    )
                ).add_to(m)

                # Draw polylines for the route
                for leg in route:
                    for step in leg["steps"]:
                        points = googlemaps.convert.decode_polyline(step["polyline"]["points"])
                        folium.PolyLine([(p["lat"], p["lng"]) for p in points], color="blue", weight=3).add_to(m)

                st.subheader("🗺️ Route Map")
                st_folium(m, width=800, height=500, key="route_map")

        except Exception as e:
            st.error(f"Error: {e}")
