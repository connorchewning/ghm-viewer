
import os
import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import geopandas as gpd
import typing


@st.cache_data
def load_merged_basin(local_model_path : str) -> gpd.GeoDataFrame :
    """_summary_

    Parameters
    ----------
    local_model_path : str
        Path to the local model. Must follow typical GHM folder structure.

    Returns
    -------
    gpd.GeoDataFrame
        Merged basin shapes.
    """
    path = os.path.join(local_model_path, 'GHM_shapes', 'GHM_merged.shp')
    gdf = gpd.read_file(path)

    return gdf


@st.cache_data
def load_obs_points(local_model_path : str) -> gpd.GeoDataFrame :
    """Loads the csv that holds information on obseverd discharge points, and the downstream point used to make the local model.

    Parameters
    ----------
    local_model_path : str
        Path to the local model. Must follow typical GHM folder structure.

    Returns
    -------
    gpd.GeoDataFrame
        Points of the csv info
    """
    path = os.path.join(local_model_path, 'setup_Router', 'Qobs.csv')
    df = pd.read_csv(path)
    df = df.dropna(axis=1, how='all')

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.long, df.lat), crs='4326')

    return gdf

@st.cache_data
def load_verification_statistics(local_model_path) -> pd.DataFrame :

    path = os.path.join(local_model_path, 'Results', 'Verification', 'Statistic_total.csv')
    df = pd.read_csv(path, dtype={'PFAF':str})

    return df

@st.cache_data
def load_station_timeseries(local_model_path : str, station_id : str) -> pd.DataFrame :

    path = os.path.join(local_model_path, 'Results', 'Verification', f'{station_id}.csv')
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df.Date)

    return df

    
    

def display_folium(basins, qobs, display_stations):

    # Create and format map
    f_map = folium.Map()
    bounds = basins.total_bounds
    f_map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    ### Add data to maps
    folium.GeoJson(basins).add_to(f_map)
    
    # plot the stations in the list
    colors = np.repeat(['gray'], len(qobs))
    colors[qobs.station.isin(display_stations)] = 'blue'

    icons = np.repeat(['ruler-vertical'], len(qobs))
    icons[qobs.station=='DownStreamPoint'] = 'water'

    for row in qobs.itertuples():
        folium.Marker(
            location=[row.lat, row.long],
            popup=row.station,
            icon=folium.Icon(icon=icons[row.Index], prefix='fa',color=colors[row.Index])        
        ).add_to(f_map)

    ### add folium map to streamlit app
    st_map = st_folium(f_map, width=700, height=400)

    return st_map