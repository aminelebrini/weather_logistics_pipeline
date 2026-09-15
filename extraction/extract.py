import requests
import pandas as pd
import json
def get_cities_data():

    try:
        url = "https://simplemaps.com/static/data/country-cities/ma/ma.csv"
        
        response = requests.get(url)
        
        data = response.content

        with open("../data/bronze/my_cities.csv", "wb") as file:
            file.write(data)

        print("File saved successfully in data/bronze/my_cities.csv !!!")
    except requests.exceptions.RequestException as e:
        print(f"error during request {e} !")

get_cities_data()

def get_weather_data():
    csv_path = "../data/bronze/my_cities.csv"
    df = pd.read_csv(csv_path)

    df_small = df.head(10)

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
            print(weather_list)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {row['city']}: {e}")

    with open("../data/bronze/weather_data.json", "w") as f:
        json.dump(weather_list, f, indent=2)

    print("✅ Finished and saved to data/bronze/weather_raw.json!")

get_weather_data()