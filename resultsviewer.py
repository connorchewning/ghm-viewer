import streamlit as st
import plotly.figure_factory as ff
import plotly.express as px
import utils
import time
import sys
import os


# Check command line arcguments
# try:
#     assert len(sys.argv) == 3
# except AssertionError:
#     raise ValueError('MODEL_NAME and LOCAL_MODEL_DIR arguments must be supplied')

# overall page configurations
TITLE = "Global Hydrological Model Results Viewer"
TAB_TITLE = "GHM Results Viewer"
TAB_ICON = ":earth_africa:"
SUB_TITLE = "Simulation results"
LOCAL_MODEL_DIR = r"Z:\GHM\GlobalHydro\LocalModel"
if len(sys.argv) > 1:
    LOCAL_MODEL_DIR = sys.argv[1]

    


### HEADER
st.set_page_config(TAB_TITLE, layout="wide", page_icon=TAB_ICON)
st.title(TITLE)

## Select local model
MODEL_NAME = st.selectbox(
    "Select Local Model",
    os.listdir(LOCAL_MODEL_DIR)
)
MODEL_PATH = os.path.join(LOCAL_MODEL_DIR, MODEL_NAME)

REQUIRED_PATHS = {
    'Basin shapes':             os.path.join('GHM_shapes', 'GHM_merged.shp'),
    'Observation points':       os.path.join('setup_Router', 'Qobs.csv'),
    'Verification statistics':  os.path.join('Results', 'Verification', 'Statistic_total.csv'),
}
missing = [
    f"- **{label}**: `{rel_path}`"
    for label, rel_path in REQUIRED_PATHS.items()
    if not os.path.exists(os.path.join(MODEL_PATH, rel_path))
]
if missing:
    st.warning(
        "**" + MODEL_NAME + "** does not appear to be a valid Local Model — "
        "the following required files are missing:\n\n" + "\n".join(missing)
    )
    st.stop()

st.subheader(f"{SUB_TITLE}: {MODEL_NAME}")

### LOAD DATA
# load basin dataframe
basins = utils.load_merged_basin(MODEL_PATH)
qobs = utils.load_obs_points(MODEL_PATH)

# map the selected stations
with st.expander('Overview of Discharge stations'):
    st.write(qobs.drop(columns=['geometry']))

### load the verification statistics and timeseries for all stations
verification_stats = utils.load_verification_statistics(MODEL_PATH)
with st.expander('Verification statistics'):
    st.write(verification_stats)

station_list = list(qobs.station.values)

if 'selected_station' not in st.session_state:
    st.session_state.selected_station = station_list[0]
if 'last_map_click' not in st.session_state:
    st.session_state.last_map_click = None

col1, col2, col3 = st.columns(spec=[0.33, 0.33, 0.33])

display_station = st.selectbox(
    "Select station to plot",
    station_list,
    index=station_list.index(st.session_state.selected_station),
)
st.session_state.selected_station = display_station

with col1:
    st.caption('Map of available discharge stations')
    map_data = utils.display_folium(basins, qobs, [display_station])

    clicked = (map_data or {}).get('last_object_clicked_popup')
    if clicked and clicked != st.session_state.last_map_click and clicked in station_list:
        st.session_state.last_map_click = clicked
        st.session_state.selected_station = clicked
        st.rerun()

with col2:
    criteria_map = {
        # 'Nash-Sutcliffe efficiecy (NSE)' : '',
        'Kling-Gupta efficiency (KGE)' : 'KGE  [-]',
        'Relative error in mean [%]' : 'WBL  [%]',
        'Correlation Coefficient' : 'Corr [-]',
        'R2' : 'R2   [-]',
    }
    criteria_type = st.selectbox(
        "Select evaluation criteria",
        list(criteria_map.keys())
    )
    fig = px.histogram(verification_stats.loc[verification_stats.ID != 'Average'], criteria_map[criteria_type], nbins=5)
    st.plotly_chart(fig)

with col3:
    stat_map = {
        'Area [km2]' : 'Area [km2]',
        'Average Flow [m3/s]' : 'Qavg [m3/s]',
        'Precipitation [mm/y]' : 'Prec [mm/y]',
        'Potential Evapotranspiration [mm/y]' : 'Epot [mm/y]',
        'Actual Evapotranspiration [mm/y]' : 'Eact [mm/y]',
        'Normalized Simulated Flow [mm/y]' : 'qsim [mm/y]',
        'Normalized Observed Flow [mm/y]' : 'qobs [mm/y]',
    }
    stat_type = st.selectbox(
        "Select evaluation criteria",
        list(stat_map.keys()),
    )
    fig1 = px.histogram(verification_stats.loc[verification_stats.ID != 'Average'], stat_map[stat_type], nbins=5)
    st.plotly_chart(fig1)


### load the verification timeseries data for the station
station_file_name = qobs.loc[qobs.station == display_station, 'grdc_no'].values[0]
station_timeseries = utils.load_station_timeseries(MODEL_PATH, station_file_name)

date_range = st.date_input(
    "Date range",
    value=(station_timeseries['Date'].min(), station_timeseries['Date'].max()),
    min_value=station_timeseries['Date'].min(),
    max_value=station_timeseries['Date'].max(),
)

if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (station_timeseries['Date'] >= str(start_date)) & (station_timeseries['Date'] <= str(end_date))
    ts = station_timeseries.loc[mask]
else:
    ts = station_timeseries

# Plot timeseries
st.line_chart(ts, x='Date', y=['Qsim', 'Qobs'])
st.line_chart(ts, x='Date', y=['QsimAcc', 'QobsAcc'])
yselections = st.multiselect('Select what to plot on y axis', ts.columns, default=['Qobs', 'Qsim'])
st.line_chart(ts, x='Date', y=yselections)