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

col3, col4 = st.columns(2)
with col3:
    st.title("HIGH RISK ALERTS")
    high_risk_df = df[df["risk_level"] == "HIGH"]
    if not high_risk_df.empty:
        st.dataframe(high_risk_df, use_container_width=True, color="red")
    else:
        st.info("No high-risk alerts at the moment.")

with col4:
    st.title("top City with Highest temperature")
    query1 = """select c.city_name , MAX(w.temp_max) as temperature_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by temperature_max DESC"""
    df1 = pd.read_sql(query1, create_engine(database_url))
    if not df1.empty:
        col1, col2, col3 = st.columns(3)
        for i, row in df1.head(3).iterrows():
            col1.metric("Highest Temperature City", row["city_name"])
            col2.metric("Highest Temperature", f"{row['temperature_max']} °C")
            col3.metric(label="Statut", value="HIGH", delta="ALERT TEMPERATURE" , delta_color="inverse",)
    else:
        st.info("No data available.")

col5, col6 = st.columns(2)
with col5:
    st.title("top City with Highest Precipitation")
    query2 = """select c.city_name , MAX(w.precipitation_sum) as precipitation_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by precipitation_max DESC"""
    df2 = pd.read_sql(query2, create_engine(database_url))
    if not df2.empty:
        col1, col2, col3 = st.columns(3)
        for i, row in df2.head(3).iterrows():
            col1.metric("Highest Precipitation City", row["city_name"])
            col2.metric("Highest Precipitation", f"{row['precipitation_max']} mm")
            col3.metric(label="Statut", value="HIGH", delta="ALERT PRECIPITATION" , delta_color="inverse",)
    else:
        st.info("No data available.")

with col6:
    st.title("top city with Highest Risk Score")
    query3 = """select c.city_name , MAX(w.risk_score) as risk_score from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by risk_score DESC"""
    df3 = pd.read_sql(query3, create_engine(database_url))
    if not df3.empty:
        col1, col2, col3 = st.columns(3)
        for i, row in df3.head(3).iterrows():
            col1.metric("Highest Risk Score City", row["city_name"])
            col2.metric("Highest Risk Score", f"{row['risk_score']}")
    else:
        st.info("No data available.")
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
