CREATE TABLE IF NOT EXISTS dim_cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) UNIQUE NOT NULL,
    lat FLOAT,
    lang FLOAT,
    region_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL REFERENCES dim_cities(city_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    temp_max FLOAT,
    temp_min FLOAT,
    precipitation_sum FLOAT,
    precipitation_probability_max FLOAT,
    wind_speed_max FLOAT,
    wind_gusts_max FLOAT,
    risk_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);