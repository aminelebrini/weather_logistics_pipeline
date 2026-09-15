import pandas as pd
import os
from sqlalchemy import create_engine

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

    data = risk_calcul_data()
    print(data)

    

load_data_to_db()
