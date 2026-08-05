# ELT Flow Notes

This file describes the ELT flow used in this project.

## Extract

- Source data is collected from food-delivery CSV datasets.
- The raw files are placed in an S3 landing zone before warehouse loading.
- This keeps the original data available for replay and validation.

## Load

- Raw data is loaded into Snowflake first.
- Snowflake acts as the warehouse where the bronze/raw layer is stored.
- Storage integration is used so the data can be ingested from the S3 landing zone.

## Transform

- dbt transforms the raw Snowflake data into staging models and curated marts.
- Staging models clean and standardize source tables such as restaurants, users, orders, menu, food, and reviews.
- The transformed data is then available for analytics, reporting, and downstream AI workflows.

## Why this is ELT

The project follows ELT because the data is loaded into Snowflake before transformation happens.  
That means the warehouse does the transformation work after the raw data is already available.

## Current project flow

1. CSV files are uploaded to the raw landing zone.
2. Snowflake loads the raw data from S3 into warehouse tables.
3. dbt builds staging views and marts.
4. Airflow can orchestrate the pipeline.
5. Streamlit and Snowsight expose the results.

## Notes

- ELT keeps raw data intact and easier to debug.
- dbt is the main transformation layer in this project.
- The Snowflake staging preview in the README shows the transformed output after dbt runs.
