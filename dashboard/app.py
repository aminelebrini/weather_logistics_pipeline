import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import streamlit as st
import os
from dotenv import load_dotenv


load_dotenv()
st.set_page_config(page_title="Weather Logistics Dashboard", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #f4f7fb;
        --muted: #8291a6;
        --line: #263342;
        --surface: #101820;
        --surface-soft: #0b1117;
        --navy: #080d12;
        --teal: #21d4d0;
        --coral: #ff5c70;
        --amber: #f5b84b;
        --magenta: #d66bca;
    }

    .stApp {
        background: #191919;
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1440px;
        padding: 2rem 2.5rem 4rem;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stText"] {
        color: var(--muted);
    }

    [data-testid="stMetric"] {
        background: #202020;
        border: 1px solid #303030;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: none;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #303030;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: none;
    }

    .stPlotlyChart, [data-testid="stVegaLiteChart"] {
        background: #202020;
        border: 1px solid #303030;
        border-radius: 6px;
        padding: 0.25rem;
        box-shadow: none;
    }

    .hero-container {
        background: #202020;
        padding: 1.75rem 2rem;
        border-radius: 6px;
        box-shadow: none;
        border: 1px solid #303030;
        margin-bottom: 1.5rem;
        position: sticky;
        top: 0.75rem;
        z-index: 1000;
    }
    
    .hero-title {
        position: relative;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.5rem;
        padding-top: 0.85rem;
        letter-spacing: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .hero-subtitle {
        color: #91a5b9;
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 1.05rem;
        font-weight: 400;
        margin: 0;
    }
    
    .badge-live {
        position: absolute;
        top: 0;
        right: 0;
        background-color: #059669;
        color: #ecfdf5;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.625rem;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .powered-by {
        margin: 0.5rem 0 1.25rem;
        padding: 0.75rem 0.85rem;
        color: #8f9bab;
        background: #232323;
        border: 1px solid #343434;
        border-left: 3px solid var(--teal);
        border-radius: 5px;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
    }

    .powered-by strong {
        color: #d9fffb;
        font-weight: 700;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <header class="hero-container">
        <h1 class="hero-title">Weather Logistics Dashboard <span class="badge-live">LIVE</span></h1>
        <p class="hero-subtitle">Real-time insights into weather data, risk levels, and city-specific forecasts.</p>
    </header>
""",
    unsafe_allow_html=True,
)

DB_HOST = os.environ.get("POSTGRES_HOST_A", os.environ.get("DB_HOST", "postgres"))
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", os.environ.get("DB_NAME", "weather_db"))
DB_USER = os.environ.get("POSTGRES_USER", os.environ.get("DB_USER", "amine_amaf"))
DB_PASS = os.environ.get("POSTGRES_PASSWORD", os.environ.get("DB_PASSWORD", "code:12345@"))

database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )

print(f"Connecting to PostgreSQL database at {DB_HOST}:{DB_PORT} with user {DB_USER} and database {DB_NAME} and password {DB_PASS} ...")

def fetch_data_from_db(url):
    try:
        engine = create_engine(url)
        query_sql = """SELECT c.city_name, c.lat, c.lang, w.forecast_date, w.temp_min, w.precipitation_sum, w.wind_speed_max, w.precipitation_probability_max, w.temp_max, w.risk_score, w.risk_level FROM weather_forecasts as w JOIN dim_cities as c ON w.city_id = c.city_id;"""
        df = pd.read_sql(query_sql, engine)
        return df
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        return pd.DataFrame()

df = fetch_data_from_db(database_url)

st.markdown(
    """
    <style>
    .card-header {
        color: var(--ink);
        background: transparent;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid #303030;
        padding: 0.85rem 1rem;
        border-radius: 0;
    }
    .metric-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #202020;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.4rem;
        border: 1px solid var(--line);
        box-shadow: none;
    }
    .metric-title {
        color: var(--muted);
        font-size: 0.85rem;
        font-weight: 500;
    }
    .metric-value {
        color: var(--ink);
        font-size: 1.05rem;
        font-weight: 700;
    }
    .badge-alert {
        background-color: #991b1b;
        color: #ffffff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        text-transform: uppercase;
    }
    .badge-warning {
        background-color: #991b1b;
        color: #ffffff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        text-transform: uppercase;
    }

    .stButton > button {
        background: #292929;
        color: #b8f7f2;
        border: 1px solid #3a3a3a;
    }

    .stButton > button:hover {
        background: #333333;
        color: #ffffff;
        border-color: var(--teal);
    }

    [data-testid="stExpander"] {
        background: #202020;
        border-color: #303030;
    }
    .admin {
        color: white !important;
        text-decoration: none !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


col3, col4 = st.columns(2)
with col3:
    st.markdown(
        '<div class="card-header">🚨 HIGH RISK ALERTS</div>',
        unsafe_allow_html=True,
    )
    high_risk_df = df[df["risk_level"] == "HIGH"]
    if not high_risk_df.empty:
        st.dataframe(high_risk_df, use_container_width=True)
    else:
        st.info("No high-risk alerts at the moment.")

with col4:
    st.markdown(
        '<div class="card-header">🔥 Top City with Highest Temperature</div>',
        unsafe_allow_html=True,
    )
    query1 = """select c.city_name , MAX(w.temp_max) as temperature_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by temperature_max DESC"""
    df1 = pd.read_sql(query1, create_engine(database_url))
    if not df1.empty:
        for i, row in df1.head(3).iterrows():
            st.markdown(
                f"""
                <div class="metric-row">
                    <div>
                        <div class="metric-title">{row['city_name']}</div>
                        <div class="metric-value">{row['temperature_max']} °C</div>
                    </div>
                    <span class="badge-alert">ALERT TEMPERATURE</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No data available.")

st.markdown("<br>", unsafe_allow_html=True)

col7, col8 = st.columns(2)
with col7:
    st.markdown(
        '<div class="card-header">📅 Top Period with Highest Risk Score</div>',
        unsafe_allow_html=True,
    )
    query4 = """select DATE_TRUNC('week', forecast_date::DATE)::DATE as start_periode,
        (DATE_TRUNC('week', forecast_date::DATE) + interval '6 days')::DATE as end_periode,
        AVG(risk_score) as average_risk
        from weather_forecasts group by DATE_TRUNC('week', forecast_date::DATE) order by average_risk DESC"""

    df4 = pd.read_sql(query4, create_engine(database_url))
    if not df4.empty:
        for i, row in df4.head(3).iterrows():
            st.markdown(
                f"""
                <div class="metric-row">
                    <div>
                        <div class="metric-title">Du {row['start_periode']} au {row['end_periode']}</div>
                        <div class="metric-value">Score: {row['average_risk']:.2f}</div>
                    </div>
                    <span class="badge-warning">ALERT RISK SCORE</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No data available.")

with col8:
    st.markdown(
        '<div class="card-header">🏙️ Top Period Risk for Each City</div>',
        unsafe_allow_html=True,
    )
    query5 = """select c.city_name,  DATE_TRUNC('week', w.forecast_date::DATE)::DATE as start_periode,
        (DATE_TRUNC('week', w.forecast_date::DATE) + interval '6 days')::DATE as end_periode,
        AVG(w.risk_score) as average_risk from weather_forecasts as w join dim_cities as c
        on c.city_id = w.city_id group by DATE_TRUNC('week', w.forecast_date::DATE), c.city_name order by average_risk DESC"""

    df5 = pd.read_sql(query5, create_engine(database_url))
    if not df5.empty:
        st.dataframe(df5, use_container_width=True)
    else:
        st.info("No data available.")

st.markdown("<br>", unsafe_allow_html=True)

col5, col6 = st.columns(2)
with col5:
    st.markdown(
        '<div class="card-header">🌧️ Top City with Highest Precipitation</div>',
        unsafe_allow_html=True,
    )
    query2 = """select c.city_name , MAX(w.precipitation_sum) as precipitation_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by precipitation_max DESC"""
    df2 = pd.read_sql(query2, create_engine(database_url))
    if not df2.empty:
        for i, row in df2.head(3).iterrows():
            st.markdown(
                f"""
                <div class="metric-row">
                    <div>
                        <div class="metric-title">{row['city_name']}</div>
                        <div class="metric-value">{row['precipitation_max']} mm</div>
                    </div>
                    <span class="badge-alert">ALERT PRECIPITATION</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No data available.")

with col6:
    st.markdown(
        '<div class="card-header">⚠️ Top City with Highest Risk Score</div>',
        unsafe_allow_html=True,
    )
    query3 = """select c.city_name , MAX(w.risk_score) as risk_score from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by risk_score DESC"""
    df3 = pd.read_sql(query3, create_engine(database_url))
    if not df3.empty:
        for i, row in df3.head(3).iterrows():
            st.markdown(
                f"""
                <div class="metric-row">
                    <div>
                        <div class="metric-title">{row['city_name']}</div>
                        <div class="metric-value">Max Score: {row['risk_score']}</div>
                    </div>
                    <span class="badge-warning">HIGH RISK</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No data available.")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Precipitation Trends by City")
    st.bar_chart(
        data=df,
        x="city_name",
        y="precipitation_sum",
        use_container_width=True,
    )

with col2:
    st.subheader("Temperature Trends by City")
    st.line_chart(
        data=df,
        x="city_name",
        y=["temp_min", "temp_max"],
        use_container_width=True,
    )

st.subheader("Wind Speed Trends by City")
st.line_chart(
    data=df, x="city_name", y="wind_speed_max", use_container_width=True
)


df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
st.sidebar.markdown(
    '<div class="powered-by">Powered by <strong><a class="admin" href="https://github.com/aminelebrini" target="_blank">AMINE LEBRINI</a></strong></div>',
    unsafe_allow_html=True,
)
st.sidebar.header("Filter Options")
filtered_df = df.copy()

all_cities = df['city_name'].unique()
selected_cities = st.sidebar.multiselect("Select Cities", options=all_cities, default=all_cities.unique())
selected_risk_levels = st.sidebar.multiselect("Select RISK LEVELS", options=["LOW", "MEDIUM", "HIGH"], default=df['risk_level'].unique())
selected_dates = st.sidebar.multiselect("Select Forecast Dates", options=df['forecast_date'].unique(), default=[df['forecast_date'].min(), df['forecast_date'].max()])
if selected_cities:
    filtered_df = df[df["city_name"].isin(selected_cities)]
else:
    st.warning("Please select at least one city from the sidebar. !!!")
if selected_risk_levels:
    filtered_df = df[df["risk_level"].isin(selected_risk_levels)]
else:
    st.warning("Please select at least one risk level from the sidebar. !!!")

if selected_dates:
    filtered_df = df[df["forecast_date"].isin(selected_dates)]
else:
    st.warning("Please select at least one forecast date from the sidebar. !!!")


st.markdown(
    """
    <style>
    .map-card-header {
        color: #f8fafc;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- Map Header ---
st.markdown(
    '<div class="map-card-header">🗺️ Interactive Logistics Risk Map (Morocco)</div>',
    unsafe_allow_html=True,
)

# --- Map Rendering ---
if not filtered_df.empty and "lat" in filtered_df.columns:
    fig = px.scatter_map(
        filtered_df,
        lat="lat",
        lon="lang",
        size="risk_score",
        color="risk_level",
        color_discrete_map={
            "LOW": "#10b981",  # Modern Emerald Green
            "MEDIUM": "#f59e0b",  # Amber Orange
            "HIGH": "#991b1b",  # Red 800
        },
        hover_name="city_name",
        hover_data=["temp_max", "wind_speed_max", "risk_score"],
        zoom=5,
        center={"lat": 31.7917, "lon": -7.0926},
        map_style="carto-darkmatter",  
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(
        "⚠️ Map data unavailable. Ensure latitude and longitude columns are included in your SQL query."
    )
