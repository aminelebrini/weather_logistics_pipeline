import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging

def logs_json(level, message, module_name="transform", **kwargs):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "module": module_name,
        "extra": kwargs
    }
    print(json.dumps(log_entry))
def transformation_data():
    logs_json("INFO", "Starting data transformation and cleaning process !!!")

    BASE_DIR = Path(__file__).resolve().parent.parent
    cities_path = BASE_DIR / "data" / "bronze" / "my_cities.csv"
    weather_data_path = BASE_DIR / "data" / "bronze" / "weather_data.json"
    output_path = BASE_DIR / "data" / "silver" / "clean_weather_data.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    weather_data_array = []


    cities_dataframe = pd.read_csv(cities_path)

    rows = []

    with open(weather_data_path, "r", encoding="utf-8") as file:
        weather_data_array = json.load(file)


    for item in weather_data_array:
        city_name = item.get("city")
        daily = item.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip_sum = daily.get("precipitation_sum", [])
        precip_prob_max = daily.get("precipitation_probability_max", [])
        wind_speed_max = daily.get("wind_speed_10m_max",[])
        wind_gusts_max = daily.get("wind_gusts_10m_max",[])
        weather_code = daily.get("weather_code", [])


        for i in range(len(dates)):
            rows.append({
                "city" : city_name,
                "forecast_date" : dates[i],
                "temp_max" : temp_max[i],
                "temp_min" : temp_min[i],
                "precipitation_sum" : precip_sum[i],
                "precipitation_probability_max" : precip_prob_max[i],
                "wind_speed_max" : wind_speed_max[i],
                "wind_gusts_max" : wind_gusts_max[i],
                "weather_code" : weather_code[i],
            })

    weather_data_frame = pd.DataFrame(rows)

    final_data_frame = pd.merge(
        weather_data_frame,
        cities_dataframe[["city", "lat", "lng", "admin_name"]],
        on="city",
        how="inner"
    )

    # print(final_data_frame)

    logs_json("INFO", "Merging data completed successfully!", "transform.py")

    final_data_frame = final_data_frame.dropna(subset=["forecast_date", "temp_max", "temp_min"])
    final_data_frame = final_data_frame.sort_values(by=["city", "forecast_date"]).reset_index(drop=True)

    logs_json("INFO", "Success to transforming and cleaning your data !!!", "transform.py")

    # print(final_data_frame)

    try:
        final_data_frame.to_csv(output_path, index=False)
        logs_json("INFO", "Success to exporting data to CSV file !!!", path=str(output_path))
    except Exception as e:
        logs_json("ERROR", f"Failed to export data: {e}", path=str(output_path))

if __name__ == "__main__":
    transformation_data()




    
    
