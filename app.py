import streamlit as st
import googlemaps
from datetime import datetime, timedelta
import pandas as pd

# Title
st.title("🚍 Church Bus Route Planner")
st.caption("Enter addresses in this format: '23, Anywhere Street, AH23 5AH'")

# Input fields with unique keys
start = st.text_input("Starting Point", key="start")
stops_text = st.text_area("Enter Stops (one per line)", key="stops")
end = st.text_input("Final Destination", key="end")
start_time = st.time_input("Select Starting Time", key="start_time")

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
                current_time = datetime.combine(datetime.today(), start_time)
                wait_seconds = 20

                table_data = []
                total_distance = 0
                total_duration = 0
                for i, leg in enumerate(route):
                    leg_distance = leg["distance"]["value"]
                    leg_duration = leg["duration"]["value"]
                    total_distance += leg_distance
                    total_duration += leg_duration

                    arrival_time = current_time + timedelta(seconds=leg_duration)
                    table_data.append({
                        "Leg": f"{i+1}",
                        "From": leg["start_address"],
                        "To": leg["end_address"],
                        "Distance": leg["distance"]["text"],
                        "Duration": leg["duration"]["text"],
                        "Expected Arrival": arrival_time.strftime("%H:%M:%S")
                    })
                    current_time = arrival_time + timedelta(seconds=wait_seconds)

                # Add total row
                table_data.append({
                    "Leg": "Total",
                    "From": "",
                    "To": "",
                    "Distance": f"{round(total_distance/1000, 2)} km",
                    "Duration": f"{round(total_duration/60)} min",
                    "Expected Arrival": ""
                })

                st.subheader("📋 Route Summary")
                df = pd.DataFrame(table_data)

                # Styling for better aesthetics
                def highlight_total(row):
                    return ['background-color: lightgreen; font-weight: bold' if row.Leg == 'Total' else '' for _ in row]

                df_style = df.style.apply(highlight_total, axis=1)\
                                   .set_properties(**{'text-align': 'center', 'font-family': 'Arial, sans-serif'})\
                                   .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])

                st.dataframe(df_style, height=400)

                # Map embed
                base_url = "https://www.google.com/maps/embed/v1/directions"
                stops_str = "|".join([leg["end_address"] for leg in route[:-1]])
                map_url = f"{base_url}?key={API_KEY}&origin={start}&destination={end}"
                if stops_str:
                    map_url += f"&waypoints={stops_str}"

                st.subheader("🗺️ Route Map")
                st.components.v1.iframe(map_url, height=500, scrolling=True)

        except Exception as e:
            st.error(f"Error: {e}")
