# Real-Time Earthquake Monitoring System

An automated system for collecting and analyzing seismic data using Apache Airflow, Docker, and PostgreSQL. The project collects data from the USGS (United States Geological Survey) API and enriches the information with detailed geographic data using the OpenCage API.

## About the Project

This system performs continuous monitoring of global seismic activities, collecting data every 10 minutes and storing it in a PostgreSQL database. The project uses Docker for containerization, ensuring consistency between development and production environments.

## Features

- Automatic collection of seismic data from USGS API
- Updates every 10 minutes
- Data enrichment with detailed geographic information (city, state, country)
- Tracking of changes in earthquake data
- Web interface for data visualization (via pgAdmin)
- Logging system for statistics monitoring

## Technologies Used

- Python 3.x
- Apache Airflow 2.10.2
- PostgreSQL 16
- Docker and Docker Compose
- pgAdmin 4
- Redis 7.2
- OpenCage Geocoding API
- USGS Earthquake API

## Project Structure

```
earthquake-monitoring/
├── dags/
│   └── earthquake_monitoring.py    # Main DAG
├── docker-compose.yml             # Docker configuration
├── logs/                         # Airflow logs
├── plugins/                      # Airflow plugins
└── README.md
```

## Requirements

- Docker and Docker Compose installed
- OpenCage API key (free)
- Minimum 4GB RAM
- Minimum 2 CPUs
- Minimum 10GB disk space

## Database Structure

### Table: earthquakes
- id: Unique earthquake identifier
- time: Event date and time
- latitude/longitude: Coordinates
- depth: Depth
- magnitude: Earthquake magnitude
- place: Descriptive location
- type: Event type
- alert: Alert level
- tsunami: Tsunami risk indicator
- Enriched geographic data (city, state, country)

### Table: earthquake_updates
- Tracking of data changes
- Update history per event

## Data Pipeline

1. Collection: Data obtained from USGS API every 10 minutes
2. Enrichment: Geographic data added via OpenCage API
3. Processing: Verification of updates and new events
4. Storage: Persistence in PostgreSQL
5. Monitoring: Statistics and event logs

## Monitoring

The system generates automatic statistics including:
- Event count by country
- Average magnitudes by region
- Updates to existing data
- Pipeline performance

## Important Notes

- OpenCage API has request limits
- 2-second delay implemented between API calls
- Fallback system for coordinates when geocoding fails
- Optimized indexes for frequent queries

Let me know if you need any clarification or have specific sections you'd like me to expand upon!
