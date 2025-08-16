import streamlit as st
import googlemaps
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("🚍 Church Bus Route Planner")
st.caption("Enter addresses in this format: '23, Anywhere Street, AH23 5AH'")

# Inputs with unique keys
start = st.text_input("Starting Point", key="start")
stops_text = st.text_area("Enter Stops (one per line)", key="stops")
end = st.text_input("Final Destination", key="end")

if "route_map" not in st.session_state:
    st.session_state["route_map"] = None
if "table_data" not in st.session_state:
    st.session_state["table_data"] = None

if st.button("Plan Route"):
    if not start or not end:
        st.error("Please enter both a starting and final destination.")
    else:
        API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"
        gmaps = googlemaps.Client(key=API_KEY)

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
                    total_distance += leg["distance"]["value"]
                    total_duration += leg["duration"]["value"]
                    table_data.append({
                        "Leg": f"{i+1}",
                        "From": leg["start_address"],
                        "To": leg["end_address"],
                        "Distance": leg["distance"]["text"],
                        "Duration": leg["duration"]["text"]
                    })

                table_data.append({
                    "Leg": "Total",
                    "From": "",
                    "To": "",
                    "Distance": f"{round(total_distance/1000, 2)} km",
                    "Duration": f"{round(total_duration/60)} min"
                })

                # Save table to session_state
                st.session_state["table_data"] = table_data

                # Build Folium map
                m = folium.Map(location=[route[0]["start_location"]["lat"], route[0]["start_location"]["lng"]], zoom_start=12)

                for i, leg in enumerate(route):
                    folium.Marker(
                        location=[leg["start_location"]["lat"], leg["start_location"]["lng"]],
                        popup=f"Stop {i+1}: {leg['start_address']}",
                        icon=folium.DivIcon(
                            html=f"<div style='font-size:12px;color:white;background:red;border-radius:50%;width:24px;height:24px;text-align:center;'>{i+1}</div>"
                        )
                    ).add_to(m)

                folium.Marker(
                    location=[route[-1]["end_location"]["lat"], route[-1]["end_location"]["lng"]],
                    popup=f"Final Destination: {route[-1]['end_address']}",
                    icon=folium.DivIcon(
                        html=f"<div style='font-size:12px;color:white;background:green;border-radius:50%;width:24px;height:24px;text-align:center;'>{len(route)}</div>"
                    )
                ).add_to(m)

                for leg in route:
                    for step in leg["steps"]:
                        points = googlemaps.convert.decode_polyline(step["polyline"]["points"])
                        folium.PolyLine([(p["lat"], p["lng"]) for p in points], color="blue", weight=3).add_to(m)

                # Save map to session_state
                st.session_state["route_map"] = m

        except Exception as e:
            st.error(f"Error: {e}")

# Display table and map from session_state
if st.session_state["table_data"]:
    st.subheader("📋 Route Summary")
    st.table(pd.DataFrame(st.session_state["table_data"]))

if st.session_state["route_map"]:
    st.subheader("🗺️ Route Map")
    st_folium(st.session_state["route_map"], width=800, height=500, key="route_map_display")
