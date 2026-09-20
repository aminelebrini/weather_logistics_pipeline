import pandas as pd
import os
from sqlalchemy import create_engine , text
from dotenv import load_dotenv
from sqlalchemy.engine import URL
from pathlib import Path
from datetime import datetime
import logging
import json
load_dotenv()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dim_cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    lat FLOAT,
    lang FLOAT,
    region_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES dim_cities(city_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    temp_max FLOAT,
    temp_min FLOAT,
    precipitation_sum FLOAT,
    precipitation_probability_max FLOAT,
    wind_speed_max FLOAT,
    wind_gusts_max FLOAT,
    risk_score FLOAT,
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE weather_forecasts
    ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20);

ALTER TABLE weather_forecasts
    ADD COLUMN IF NOT EXISTS wind_gusts_max FLOAT;
"""


def logs_json(level, message, module_name="load", **kwargs):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "module": module_name,
        "extra": kwargs
    }
    print(json.dumps(log_entry))

def risk_calcul_data():

    logs_json("INFO", "Starting risk score calculation process !!!")

    BASE_DIR = Path(__file__).resolve().parent.parent
    transformed_data_path = BASE_DIR / "data" / "silver" / "clean_weather_data.csv"


    if not os.path.exists(transformed_data_path):
        print(f"File {transformed_data_path} not found! Run transform.py first.")
        return

    data_frame = pd.read_csv(transformed_data_path)

    risk_scores = []
    risk_levels = []
    total_risk_score = 0.0
    for index, row in data_frame.iterrows():
        precip_risk_perc = min(row["precipitation_sum"] / 20.0 , 1.0) * 35
        wind_risk_perc = min(row["wind_speed_max"] / 70.0, 1.0) * 30
        prob_risk_perc = (row.get("precipitation_probability_max", 0) / 100.0) * 15

        temp_risk_perc = 0
        if row["temp_max"] >= 40 or row["temp_min"] <= 0:
            temp_risk_perc = 20
        elif row["temp_max"] >= 35 or row["temp_min"] <= 5:
            temp_risk_perc = 10

        total_risk_score = round(precip_risk_perc + wind_risk_perc + prob_risk_perc + temp_risk_perc, 1)
        risk_scores.append(total_risk_score)

        if (total_risk_score >= 60):
            risk_levels.append("HIGH")
        elif (30 <= total_risk_score < 60):
            risk_levels.append("MEDIUM")
        else:
            risk_levels.append("LOW")
    
    data_frame["risk_score"] = risk_scores
    data_frame["risk_level"] = risk_levels


    return data_frame

def initialize_database_schema(engine):
    BASE_DIR = Path(__file__).resolve().parent.parent
    schema_path = BASE_DIR / "schema" / "schema.sql"

    if schema_path.exists():
        schema_sql = schema_path.read_text(encoding="utf-8")
    else:
        logs_json("WARNING", f"Schema file not found, using built-in schema: {schema_path}", "load.py")
        schema_sql = SCHEMA_SQL

    try:
        with engine.begin() as conn:
            for statement in schema_sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
        logs_json("INFO", "Database schema initialized successfully!", "load.py")
        return True
    except Exception as e:
        logs_json("ERROR", f"Error initializing database schema: {e}", "load.py")
        return False

def load_data_to_db():

    data_frame = risk_calcul_data()
    if data_frame is None:
        print("No data to save !!")
        return

    DB_USER = os.getenv("POSTGRES_USER","postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", os.getenv("POSTGRES_HOST_A", "localhost"))
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "weather_db")

    
    print(f"Connecting to PostgreSQL database at {DB_HOST}:{DB_PORT} with user {DB_USER} and database {DB_NAME} and password {DB_PASSWORD} ...")

    try:
        database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )

        engine = create_engine(database_url)
        with engine.connect() as conn:
            logs_json("INFO", "Connection successful!", "load.py")
    except Exception as e:
        logs_json("ERROR", f"Error connecting to the database: {e}", "load.py")
        return

    if not initialize_database_schema(engine):
        return

    unique_cities = data_frame[["city","lat", "lng","admin_name"]].drop_duplicates().reset_index(drop=True)
    logs_json("INFO", "Prepared unique cities for load", "load.py", city_count=len(unique_cities))

    

    with engine.begin() as conn:

        for _, row in unique_cities.iterrows():
            conn.execute(text("""
                INSERT INTO dim_cities (city_name, lat, lang, region_name)
                VALUES (:city, :lat, :lang, :region)
                ON CONFLICT (city_name) DO UPDATE
                SET lat = EXCLUDED.lat,
                    lang = EXCLUDED.lang,
                    region_name = EXCLUDED.region_name;
                """),{
                    "city": row["city"],
                    "lat": row.get("lat"),
                    "lang": row.get("lng"),
                    "region": row.get("admin_name")
                })

        
        cities_db = pd.read_sql(
            "SELECT city_id, city_name FROM dim_cities;", conn
        )

        city_map = dict(zip(cities_db["city_name"], cities_db["city_id"]))
        

        data_frame["city_id"] = data_frame["city"].map(city_map)
        missing_city_ids = data_frame[data_frame["city_id"].isna()]["city"].drop_duplicates().tolist()
        if missing_city_ids:
            logs_json("ERROR", "Some cities were not found in dim_cities after insert", "load.py", cities=missing_city_ids)
            return

        forecast = data_frame[["city_id", "forecast_date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_gusts_max", "precipitation_probability_max", "risk_score", "risk_level"]]
        city_ids = forecast["city_id"].dropna().unique().tolist()
        forecast_dates = forecast["forecast_date"].dropna().unique().tolist()

        conn.execute(
            text("""
                DELETE FROM weather_forecasts
                WHERE city_id = ANY(:city_ids)
                AND forecast_date = ANY(:forecast_dates);
            """),
            {"city_ids": city_ids, "forecast_dates": forecast_dates}
        )

        # print(forecast)
        forecast.to_sql(
            name="weather_forecasts",
            con=conn,
            if_exists="append", 
            index=False,  
            method="multi",
            chunksize=1000, 
        )

        logs_json("INFO", "Data loaded successfully!", "load.py")

if __name__ == "__main__":
    load_data_to_db()
