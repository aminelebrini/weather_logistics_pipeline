import requests
import pandas as pd
import json
from pathlib import Path
import json
import logging
from datetime import datetime

def logs_json(level, message, module_name="extraction", **kwargs):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "module": module_name,
        "extra": kwargs
    }
    print(json.dumps(log_entry))
def get_cities_data():

    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        file_path = BASE_DIR / "data" / "bronze" / "my_cities.csv"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        url = "https://simplemaps.com/static/data/country-cities/ma/ma.csv"
        
        response = requests.get(url)
        
        data = response.content

        with open(file_path, "wb") as file:
            file.write(data)

        logs_json("INFO", "Success to fetching cities data from the API !!!", path=str(file_path))
    except requests.exceptions.RequestException as e:
        logs_json("ERROR", f"Error fetching cities data from the API: {e}", path=str(file_path))
def get_weather_data():
    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / "data" / "bronze" / "my_cities.csv"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    json_file_path = BASE_DIR / "data" / "bronze" / "weather_data.json"
    json_file_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(file_path)

    df_small = df.head(100)

    weather_list = []

    for _, row in df_small.iterrows():
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": row["lat"],
            "longitude": row["lng"],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "weather_code"
            ],
            "forecast_days": 7,
            "timezone": "auto"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            data["city"] = row["city"]
            weather_list.append(data)
            logs_json("INFO", f"Success fetching weather data for {row['city']} !!!", city=row['city'])

        except requests.exceptions.RequestException as e:
            logs_json("ERROR", f"Error fetching weather data for {row['city']}: {e}", city=row['city'])

    with open(json_file_path, "w") as f:
        json.dump(weather_list, f, indent=2)

    print("✅ Finished and saved to data/bronze/weather_raw.json!")

if __name__ == "__main__":
    get_cities_data()
