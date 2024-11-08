from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from geopy.geocoders import OpenCage
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
import psycopg2
from psycopg2 import sql
import json
import os
import logging
import time

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def get_location_details(latitude, longitude):
    opencage_api_key = os.getenv('OPENCAGE_API_KEY')
    
    if not opencage_api_key:
        logging.warning("OpenCage API key not found.")
        return {
            'city': 'Unknown',
            'state_province': 'Unknown',
            'country': 'Unknown',
            'country_code': 'UN',
            'formatted_address': f'Coordinates: {latitude}, {longitude}'
        }
    
    try:
        geolocator = OpenCage(opencage_api_key)
        location = geolocator.reverse(f"{latitude}, {longitude}", language='en', timeout=10)
        
        if location:
            components = location.raw['components']
            return {
                'city': components.get('city', components.get('town', components.get('village', 'Unknown'))),
                'state_province': components.get('state', components.get('province', 'Unknown')),
                'country': components.get('country', 'Unknown'),
                'country_code': components.get('country_code', 'UN').upper(),
                'formatted_address': location.address
            }
        else:
            logging.warning(f"No location details found for coordinates: {latitude}, {longitude}")
            return {
                'city': 'Unknown',
                'state_province': 'Unknown',
                'country': 'Unknown',
                'country_code': 'UN',
                'formatted_address': f'Coordinates: {latitude}, {longitude}'
            }
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logging.error(f"Geocoding error: {e}")
        return {
            'city': 'Unknown',
            'state_province': 'Unknown',
            'country': 'Unknown',
            'country_code': 'UN',
            'formatted_address': f'Coordinates: {latitude}, {longitude}'
        }

def get_postgres_connection():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        database=os.getenv('POSTGRES_DB', 'airflow'),
        user=os.getenv('POSTGRES_USER', 'airflow'),
        password=os.getenv('POSTGRES_PASSWORD', 'airflow')
    )
    conn.autocommit = True
    return conn

def setup_database():
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS earthquakes (
            id TEXT PRIMARY KEY,
            time TIMESTAMP,
            latitude REAL,
            longitude REAL,
            depth REAL,
            magnitude REAL,
            place TEXT,
            type TEXT,
            alert TEXT,
            tsunami INTEGER,
            city TEXT,
            state_province TEXT,
            country TEXT,
            country_code TEXT,
            formatted_address TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_time ON earthquakes(time)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_magnitude ON earthquakes(magnitude)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_location ON earthquakes(latitude, longitude)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_country ON earthquakes(country)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_state ON earthquakes(state_province)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS earthquake_updates (
            id SERIAL PRIMARY KEY,
            earthquake_id TEXT,
            field_name TEXT,
            old_value TEXT,
            new_value TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (earthquake_id) REFERENCES earthquakes(id)
        )
    """)
    cur.close()
    conn.close()

def fetch_earthquake_data(time_range='day'):
    url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time_range}.geojson"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def track_updates(cur, earthquake_id, field_name, old_value, new_value):
    cur.execute("""
        INSERT INTO earthquake_updates (earthquake_id, field_name, old_value, new_value)
        VALUES (%s, %s, %s, %s)
    """, (earthquake_id, field_name, old_value, new_value))

def process_and_store_data(**context):
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    setup_database()
    
    data = fetch_earthquake_data('day')
    
    for feature in data['features']:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        event_time = datetime.fromtimestamp(props['time'] / 1000.0)
        
        location_details = get_location_details(coords[1], coords[0])
        time.sleep(2)  # Pausa entre as chamadas à API OpenCage
        
        earthquake_data = {
            'id': feature['id'],
            'time': event_time,
            'latitude': coords[1],
            'longitude': coords[0],
            'depth': coords[2],
            'magnitude': props['mag'],
            'place': props['place'],
            'type': props['type'],
            'alert': props.get('alert', 'none'),
            'tsunami': props.get('tsunami', 0),
            'city': location_details['city'],
            'state_province': location_details['state_province'],
            'country': location_details['country'],
            'country_code': location_details['country_code'],
            'formatted_address': location_details['formatted_address']
        }
        
        cur.execute("SELECT * FROM earthquakes WHERE id = %s", (feature['id'],))
        existing_data = cur.fetchone()
        
        if existing_data:
            columns = [desc.name for desc in cur.description]
            existing_dict = dict(zip(columns, existing_data))
            
            updates = []
            update_values = []
            
            for key, new_value in earthquake_data.items():
                if key in existing_dict and existing_dict[key] != new_value:
                    updates.append(f"{key} = %s")
                    update_values.append(new_value)
                    track_updates(cur, feature['id'], key, existing_dict[key], new_value)
            
            if updates:
                update_values.append(datetime.now())
                update_values.append(feature['id'])
                update_sql = f"""
                    UPDATE earthquakes 
                    SET {', '.join(updates)}, updated_at = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, update_values)
        else:
            placeholders = ','.join(['%s' for _ in earthquake_data])
            columns = ','.join(earthquake_data.keys())
            cur.execute(f"""
                INSERT INTO earthquakes ({columns})
                VALUES ({placeholders})
            """, list(earthquake_data.values()))
    
    conn.commit()
    
    cur.execute("""
        SELECT 
            country,
            COUNT(*) as event_count,
            AVG(magnitude) as avg_magnitude
        FROM earthquakes 
        WHERE time >= NOW() - INTERVAL '1 day'
        GROUP BY country
        ORDER BY event_count DESC
        LIMIT 5
    """)
    
    recent_stats = cur.fetchall()
    logging.info("Estatísticas das últimas 24 horas por país:")
    for country, count, avg_mag in recent_stats:
        logging.info(f"{country}: {count} eventos, magnitude média: {avg_mag:.2f}")
    
    cur.close()
    conn.close()

dag = DAG(
    'earthquake_monitoring',
    default_args=default_args,
    description='Coleta dados de terremotos com informações geográficas detalhadas',
    schedule_interval='*/10 * * * *',
    catchup=False
)

fetch_and_store = PythonOperator(
    task_id='fetch_and_store_earthquakes',
    python_callable=process_and_store_data,
    dag=dag
)