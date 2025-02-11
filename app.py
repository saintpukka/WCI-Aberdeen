import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta
import pandas as pd
import folium
from streamlit_folium import folium_static

# Function to convert postcode to latitude and longitude
def geocode_postcode(postcode, retries=3):
    """Convert postcode to latitude and longitude with retries."""
    geolocator = Nominatim(user_agent="route_planner", timeout=5)
    for _ in range(retries):
        try:
            location = geolocator.geocode(postcode)
            if location:
                return (location.latitude, location.longitude)
        except GeocoderTimedOut:
            continue
    return None

# Function to compute the best route and travel times
def get_best_route(start_postcode, destination_postcodes, final_postcode, start_time, speed_kmh=35, pickup_time=1.5, extra_delay=0.5):
    """Find the best route from start through multiple destinations and ending at a final destination."""
    
    # Geocode starting postcode
    start_coords = geocode_postcode(start_postcode)
    if not start_coords:
        return "Invalid starting postcode.", None, None
    
    # Geocode destination postcodes
    destination_coords = [(pc, geocode_postcode(pc)) for pc in destination_postcodes]
    destination_coords = [(pc, coord) for pc, coord in destination_coords if coord]
    
    # Geocode final destination
    final_coords = geocode_postcode(final_postcode)
    if not final_coords:
        return "Invalid final destination.", None, None
    
    if not destination_coords:
        return "No valid destinations.", None, None
    
    # Get road network graph
    G = ox.graph_from_point(start_coords, dist=20000, network_type='drive')
    
    # Find nearest nodes to start, destinations, and final destination
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    destination_nodes = [(pc, ox.distance.nearest_nodes(G
