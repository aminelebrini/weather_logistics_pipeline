import pandas as pd
import os
from sqlalchemy import create_engine , text
from dotenv import load_dotenv
from sqlalchemy.engine import URL
load_dotenv()

def risk_calcul_data():
    cleaned_data_file_path = "../data/silver/clean_weather_data.csv"


    if not os.path.exists(cleaned_data_file_path):
        print(f"File {cleaned_data_file_path} not found! Run transform.py first.")
        return

    data_frame = pd.read_csv(cleaned_data_file_path)

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

    
risk_calcul_data()


def load_data_to_db():

    data_frame = risk_calcul_data()
    if data_frame is None:
        print("No data to save !!")
        return

    DB_USER = os.getenv("POSTGRES_USER","postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
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
            print("Connection successful!")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    unique_cities = data_frame[["city","lat", "lng","admin_name"]].drop_duplicates().reset_index(drop=True)

    

    with engine.begin() as conn:

        # for _, row in unique_cities.iterrows():
        #     conn.execute(text("""
        #         INSERT INTO dim_cities (city_name, lat, lang, region_name)
        #         VALUES (:city, :lat, :lang, :region)
        #         ON CONFLICT (city_name) DO UPDATE 
        #         SET lat = EXCLUDED.lat, 
        #             lang = EXCLUDED.lang, 
        #             region_name = EXCLUDED.region_name;
        #         """),{
        #             "city": row["city"],
        #             "lat": row.get("lat"),
        #             "lang": row.get("lng"),
        #             "region": row.get("admin_name")
        #         })

        
        cities_db = pd.read_sql(
            "SELECT city_id, city_name FROM dim_cities;", conn
        )

        city_map = dict(zip(cities_db["city_name"], cities_db["city_id"]))

        data_frame["city_id"] = data_frame["city"].map(city_map)

        forecast = data_frame[["city_id", "forecast_date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "precipitation_probability_max", "risk_score", "risk_level"]]

        # print(forecast)
        forecast.to_sql(
            name="weather_forecasts",
            con=engine,
            if_exists="append", 
            index=False,  
            method="multi",
            chunksize=1000, 
        )

        print("Data loaded successfully!")

load_data_to_db()
