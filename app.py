            # Generate map visualization
            st.subheader("Route Map")
            map_center = geocode_location(start_location)
            if map_center:
                route_map = folium.Map(location=map_center, zoom_start=12)

                # Plot start point
                folium.Marker(location=map_center, popup="Start", icon=folium.Icon(color="green")).add_to(route_map)

                # Plot destinations with numbers
                for i, loc in enumerate(destination_locations):
                    coord = geocode_location(loc)
                    if coord:
                        folium.Marker(
                            location=coord,
                            popup=f"{i + 1}: {loc}",
                            icon=folium.DivIcon(html=f'<div style="font-size: 12pt; color: blue;">{i + 1}</div>')
                        ).add_to(route_map)

                # Plot final destination
                final_coord = geocode_location(final_location)
                if final_coord:
                    folium.Marker(location=final_coord, popup="Final Destination", icon=folium.Icon(color="red")).add_to(route_map)

                folium_static(route_map)
            else:
                st.warning("Unable to load map due to geocoding issues.")
