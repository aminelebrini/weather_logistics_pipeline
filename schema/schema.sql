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

ALTER TABLE weather_forecasts
    ALTER COLUMN city_id TYPE INTEGER USING city_id::integer;

SELECT c.city_name, c.lat, c.lang, w.forecast_date, w.temp_min, w.precipitation_sum, 
w.wind_speed_max, w.precipitation_probability_max, w.temp_max, w.risk_score, w.risk_level 
FROM weather_forecasts as w JOIN dim_cities as c ON w.city_id = c.city_id;

select c.city_name , MAX(w.temp_max) as temperature_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by temperature_max DESC

select c.city_name , MAX(w.precipitation_sum) as precipitation_max from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by precipitation_max DESC

select c.city_name , MAX(w.risk_score) as risk_score from dim_cities c join weather_forecasts w
        on c.city_id = w.city_id group by c.city_name order by risk_score DESC