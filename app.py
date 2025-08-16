import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------- CONFIG ----------------
API_KEY = "AIzaSyBfbGRf4pRHfF-kwQ5uL9PYQRaHtRIJzmg"  # Replace with your API key

# ---------------- FUNCTIONS ----------------
def get_route(api_key, start, stops, end, units="imperial"):
    """Call Google Maps Directions API"""
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start,
        "destination": end,
        "waypoints": "|".join(stops) if stops else None,
        "optimizeWaypoints": "true",  # Optimizes stop order
        "key": api_key,
        "units": units  # "imperial" = miles, "metric" = km
    }

    response = requests.get(url, params=params)
    return response.json()

def display_map(route_data):
    """Draw route on Folium map"""
    if "routes" not in route_data or not route_data["routes"]:
        return None

    route = route_data["routes"][0]
    legs = route["legs"]

    # Center map on first location
    start_location = legs[0]["start_location"]
    m = folium.Map(location=[start_location["lat"], start_location["lng"]], zoom_start=13)

    # Add markers + route line
    for i, leg in enumerate(legs):
        start = leg["start_location"]
        end = leg["end_location"]

        folium.Marker([start["lat"], start["lng"]],
                      popup=f"Stop {i+1}: {leg['start_address']}").add_to(m)

        if i == len(legs) - 1:
            folium.Marker([end["lat"], end["lng"]],
                          popup=f"Final: {leg['end_address']}",
                          icon=folium.Icon(color="red")).add_to(m)

    # Add route polyline
    for step in legs:
        for s in step["steps"]:
            polyline = s["polyline"]["points"]
            points = decode_polyline(polyline)
            folium.PolyLine(points, color="blue", weight=4, opacity=0.7).add_to(m)

    return m

def decode_polyline(polyline_str):
    """Google polyline decoder"""
    index, lat, lng, points = 0, 0, 0, []
    while index < len(polyline_str):
        for coord in [lat, lng]:
            shift, result = 0, 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dcoord = ~(result >> 1) if result & 1 else (result >> 1)
            if coord == lat:
                lat += dcoord
            else:
                lng += dcoord
        points.append((lat / 1e5, lng / 1e5))
    return points

# ---------------- STREAMLIT APP ----------------
st.title("🚌 Route Planner with Google Maps")
st.caption("Enter addresses in this format: `23, Anywhere Street, AH23 5AH`")

start = st.text_input("Starting Address")
stops = st.text_area("Enter Stops (one per line)").split("\n")
stops = [s.strip() for s in stops if s.strip()]
end = st.text_input("Final Address")

if st.button("Plan Route"):
    if not start or not end:
        st.error("Please enter both a start and end address.")
    else:
        route_data = get_route(API_KEY, start, stops, end)

        if route_data["status"] != "OK":
            st.error(f"Error from API: {route_data['status']}")
        else:
            # Show route details
            st.subheader("📍 Route Steps")
            legs = route_data["routes"][0]["legs"]

            for i, leg in enumerate(legs):
                st.write(f"**Leg {i+1}: {leg['start_address']} → {leg['end_address']}**")
                st.write(f"Distance: {leg['distance']['text']}, Duration: {leg['duration']['text']}")

            # Display map
            st.subheader("🗺️ Route Map")
            map_object = display_map(route_data)
            if map_object:
                st_folium(map_object, width=700, height=500)
