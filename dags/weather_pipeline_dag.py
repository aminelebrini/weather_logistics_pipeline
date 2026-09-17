from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from extraction.extract import get_cities_data , get_weather_data
from transformation.transform import transformation_data
from load.load import load_data_to_db

def execute_full_etl():
    get_cities_data()
    get_weather_data()

    transformed_df = transformation_data()

    load_data_to_db()


default_args = {
    'owner': 'AMINE LEBRINI',
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

with DAG(
    dag_id='weather_pipeline_dag',
    default_args=default_args,
    schedule=timedelta(days=1),
    start_date=datetime(2024, 9, 17),
    catchup=False,
) as dag:
  execute_etl_task = PythonOperator(
      task_id='execute_full_etl',
      python_callable=execute_full_etl,
  )
execute_etl_task
