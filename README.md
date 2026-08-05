# Swiggy - Zomato AI Data Engineering Solution

End-to-end analytics pipeline for food-delivery data, combining data lake ingestion, Snowflake warehouse modeling, dbt transformations, and AI-powered review workflows.

## Architecture

![Architecture diagram](docs/architecture.png)

## What this project includes

- Source datasets for restaurants, users, orders, items, menu, food, and reviews.
- AWS S3-based raw landing zone.
- Snowflake raw, staging, and marts layers.
- dbt models for clean transformations and curated marts.
- AI review enrichment, RAG chat, and text-to-SQL capabilities.
- Orchestration with Airflow and delivery through Streamlit and Snowsight.

## Repository Layout

- `data/` - sample CSV datasets used as inputs.
- `data/sample/` - compact Git-friendly subset of the datasets for demos and testing.
- `aws/iam/` - IAM and trust policies for AWS and Snowflake integration.
- `snowflake/` - SQL scripts for setup, storage integration, staging, raw tables, and loading.
- `docs/` - supporting documentation and architecture visuals.

## High-Level Flow

1. CSV files are uploaded to S3 as the raw landing zone.
2. Snowflake ingests the raw data into bronze tables via storage integration.
3. dbt builds staging models and curated marts.
4. AI workflows enrich review data, power RAG search, and generate text-to-SQL responses.
5. Airflow orchestrates the pipeline, while Streamlit and Snowsight expose the results.

## Snowflake Staging Preview

![Snowflake staging preview](docs/screenshots/snowflake-staging-preview.png)

The image shows the Snowflake database explorer opened on the dbt staging model `STG_RESTAURANTS`. It confirms that the transformed restaurant data is loaded and queryable in the `FOOD_DELIVERY.STAGING` schema, with fields such as restaurant name, city, rating, rating count, cost for two, cuisine, and license number visible in the table view.

## Notes

- The architecture diagram in this README is stored at [docs/architecture.png](docs/architecture.png).
- Sample datasets are stored in [data/sample/](data/sample/) and are safe to commit to GitHub.
- SQL setup scripts are ordered to support a step-by-step deployment flow.
