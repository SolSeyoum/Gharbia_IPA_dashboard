import matplotlib.cm as cm
import streamlit as st
from streamlit_folium import st_folium
from util import common2 as cm

Scheem_name = "Gharbia"
cm.set_page_container_style(
    Scheem_name=Scheem_name,
    max_width=1100,
    max_width_100_percent=True,
    padding_top=0,
    padding_right=0,
    padding_left=0,
    padding_bottom=0,
)

# dfm, geo = cm.read_df_and_geo("Maize")
logo_small, logo_wide = cm.logos()
# gdf = cm.get_gdf_from_json(geo)
# ipa_ds_path = r"data/Gharbia_ipa_results.nc"

# Initialize session state
session_state_defaults = {
    "last_clicked": None,
    "clicked_locations": [],
    "time_series_generated": False,
    "button_clicked": False,
}
for key, default_value in session_state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


with st.sidebar:
    st.logo(
        logo_wide, size="large", link="https://www.un-ihe.org/", icon_image=logo_small
    )
    st.title(f"{Scheem_name} Irrigation Performance Indicators")

    season_crop_lst = cm.extract_crop_list(f"{Scheem_name}_IPA_statistic", "*.csv")
    selected_season = st.selectbox("Select season", list(season_crop_lst.keys()))
    # selected_crop = st.selectbox("Select crop type", season_crop_lst[selected_season])

    dfm, geo = cm.read_df_and_geo(
        Scheem_name, selected_season, season_crop_lst[selected_season][0]
    )
    gdf = cm.get_gdf_from_json(geo)

    ipa_ds_path = rf"data/{Scheem_name}_ipa_results_{selected_season}.nc"
    season_year_list = list(dfm.season_year.unique())[::-1]

    ll = list(dfm.columns.unique())[:][::-1]
    indicator_lst = [" ".join(l.split("_")[1:]) for l in ll]
    indicator_lst = list(set(indicator_lst))
    indicator_lst = [x for x in indicator_lst if x != ""]
    indicator_lst = [x for x in indicator_lst if x != "year"]

    selected_season_year = st.selectbox("Select a year", season_year_list)
    indicator = st.selectbox("Select an indicator", indicator_lst, index=0)
    st.markdown("---")
    with st.expander("ℹ️ About the raster viewer"):
        st.markdown("""
        This viewer provides raster view of the Irrigation Performance Indicators.
        
        - Year/Season and indicators can be selected to view the raster for year/season and indicator selected.
        - 📊 The dataframe on the right side provides statistic of the selected raster                             
        - 📈 You can click points (as many points as needed) on the raster and generate a time series plot of the points.

        """)

try:
    # st.markdown(f"### Mwea IPA Raster Viewer")
    df_stats = None
    variable = indicator.replace(" ", "_")
    slected_time = selected_season_year.split("-")[
        1
    ]  # f'{selected_season_year }-12-31'

    ds, transform, crs, nodata, bounds = cm.read_dataset(ipa_ds_path)

    # data =  ds.sel(time=slected_time)[variable]
    data_var = ds[variable]
    data = data_var.sel(season=int(slected_time)).load()

    df_stats = cm.get_stats(data)

    col = st.columns((5.5, 2.5), gap="small")
    with col[0]:
        st.markdown(
            f"### {Scheem_name} Raster Viewer: {selected_season} of {selected_season_year}"
        )
        # with st.spinner("Loading and processing data..."):
        #
        # Process clicked locations and display map

        if map_data := st_folium(
            cm.create_folium_map(data, geo, bounds, crs, variable),
            height=500,
            width=None,
            returned_objects=["last_clicked"],
        ):
            # Process Click Event
            if (
                map_data["last_clicked"]
                and map_data["last_clicked"] != st.session_state.last_clicked
            ):
                lat, lon = (
                    map_data["last_clicked"]["lat"],
                    map_data["last_clicked"]["lng"],
                )

                if (lat, lon) not in st.session_state.clicked_locations:
                    st.session_state.last_clicked = map_data["last_clicked"]
                    st.session_state.clicked_locations.append((lat, lon))
                    # st.rerun()  # Rerun only when a new point is added

        filtered_markers = cm.filter_points_within_polygon(
            st.session_state.clicked_locations, gdf
        )

        if len(filtered_markers) > 0 and not st.session_state.button_clicked:
            # st.markdown("---")
            if st.button("📈 Generate Time Series"):
                st.session_state.time_series_generated = True
                st.session_state.button_clicked = True
                st.rerun()

    with col[1]:
        st.write("")
        title = f'<p style="font:Courier; color:gray; font-size: 20px;">Stats of {indicator} [{cm.units[indicator]}] - {selected_season} of {selected_season_year}</p>'
        st.markdown(title, unsafe_allow_html=True)
        st.dataframe(df_stats, use_container_width=True)

    # **Display all extracted values**
    locations = st.session_state.clicked_locations
    if st.session_state.time_series_generated:
        data_all_points = cm.extraxt_ts(data_var, locations)

        if len(data_all_points) > 0:
            chart, title = cm.alt_line_chart(data_all_points, variable)
            title = f'<p style="font:Courier; color:gray; font-size: 20px;">{title}</p>'
            st.markdown(title, unsafe_allow_html=True)
            st.altair_chart(chart, use_container_width=True)


except Exception as e:
    st.error(f"An error occurred while processing the data: {str(e)}")
