import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import streamlit as st
import os
from dotenv import load_dotenv


load_dotenv()
st.set_page_config(page_title="Weather Logistics Dashboard", layout="wide")
st.title("Weather Logistics Risk Dashboard")
st.markdown("Real-time weather risk analytics for delivery planning.")

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

col1, col2 = st.columns(2)
with col1:
    st.header("Precipitation Trends by City")
    st.bar_chart(data=df, x="city_name", y="precipitation_sum", use_container_width=False)

with col2:
    st.header("Temperature Trends by City")
    st.line_chart(data=df, x="city_name" , y=["temp_min", "temp_max"], use_container_width=False)


st.header("Wind Speed Trends by City")
st.line_chart(data=df, x="city_name", y="wind_speed_max", use_container_width=False)


df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
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

st.dataframe(filtered_df, use_container_width=True)


if not filtered_df.empty and 'lat' in filtered_df.columns:

  fig = px.scatter_map(
      filtered_df,
      lat="lat",
      lon="lang",
      size="risk_score", 
      color="risk_level",  
      color_discrete_map={
          "LOW": "green",
          "MEDIUM": "orange",
          "HIGH": "red",
      },  
      hover_name="city_name",
      hover_data=["temp_max", "wind_speed_max", "risk_score"],
      zoom=5, 
      center={"lat": 31.7917, "lon": -7.0926}, 
      map_style="open-street-map", 
  )

  fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=450)

  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning(
      "⚠️ Map data unavailable. Ensure latitude and longitude columns are included in your SQL query."
  )
