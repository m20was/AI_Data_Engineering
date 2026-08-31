# Staging vs Marts — What's the Difference in This Project

## TL;DR
- **Staging** = 1:1 cleanup of raw source tables. One staging model per raw table, materialized as a **view**, schema `staging`.
- **Marts** = business-ready dimensional/fact models and aggregates, built on top of staging models, materialized as a **table**, schema `marts`.

Configured in [dbt_project.yml](../food_delivery/dbt_project.yml):
```yaml
models:
  food_delivery:
    staging: { +materialized: view, +schema: staging }
    marts:   { +materialized: table, +schema: marts }
```

## Simple side-by-side (plain language)

| Staging | Marts |
|---|---|
| Cleans up one raw table | Combines many cleaned tables |
| Just fixes names, types, messy text | Adds real business meaning |
| No joins | Has joins |
| No math/aggregation | Has counts, sums, rates |
| Looks almost like the raw data, just tidy | Looks like a report/dashboard-ready table |
| Cheap view, always fresh | Saved as a table, built to be fast to query |
| Used only by other dbt models | Used by BI tools, dashboards, analysts |
| Answers: "is the data clean?" | Answers: "what does the business want to know?" |

## Staging layer (`models/staging/`)
- Reads directly from `{{ source('raw', ...) }}` — never from another staging model or from marts.
- One file per raw entity: [stg_orders.sql](../food_delivery/models/staging/stg_orders.sql), stg_order_items, stg_restaurants, stg_food, stg_menu, stg_users, stg_reviews.
- Responsibilities: renaming columns to consistent names (e.g. `r_id` → `restaurant_id`, `user_id` → `customer_id`), light type casting, and parsing messy raw text fields.
  - Example ([stg_restaurants.sql](../food_delivery/models/staging/stg_restaurants.sql)): converts `"50+ ratings"` → `50`, `"₹ 200"` → `200`, `"--"` rating → `null`, extracts city from a comma-separated string.
- No joins across entities, no aggregation, no business logic/derived KPIs.
- Materialized as **views** (cheap, always reflect latest raw data) since they're just cleanup passes.
- Tested for `unique`/`not_null` on primary keys in [_staging.yml](../food_delivery/models/staging/_staging.yml).

## Marts layer (`models/marts/`)
- Reads only from `{{ ref('stg_*') }}` models (or other marts), never directly from sources.
- Split into dimensions and facts (classic star schema) plus some reporting-style aggregate marts:
  - **Dimensions**: [dim_customer.sql](../food_delivery/models/marts/dim_customer.sql) (adds derived `age_segment` bucket), dim_restaurants, dim_food, dim_date.
  - **Facts**: [fct_orders.sql](../food_delivery/models/marts/fct_orders.sql), [fact_order_items.sql](../food_delivery/models/marts/fact_order_items.sql) — join staging models together (e.g. order_items + orders) and are `materialized='incremental'` with `merge` strategy, filtering on `order_timestamp > max(existing)`.
  - **Aggregate/reporting marts**: [mart_daily_city_revenune.sql](../food_delivery/models/marts/mart_daily_city_revenune.sql), mart_delivery_sla, mart_restaurant_performance — pre-aggregated metrics (GMV, cancel rate, AOV) grouped by date/city for BI consumption.
- Contains business logic: derived flags (`is_delivered`), segments (`age_segment`), rates (`cancel_rate`, `aov`), and referential-integrity tests (`relationships`, `accepted_values`) in [_marts.yml](../food_delivery/models/marts/_marts.yml).
- Materialized as **tables** by default (fast reads for BI/reporting), with fact tables overriding to `incremental` for performance on large/growing data.

## Summary table
| Aspect | Staging | Marts |
|---|---|---|
| Source | `source('raw', ...)` | `ref('stg_*')` / other marts |
| Granularity | 1:1 with raw table | Joined, aggregated, or dimensional |
| Materialization | view | table (facts: incremental) |
| Schema | `staging` | `marts` |
| Logic | rename/clean/cast | joins, derived columns, business rules, aggregates |
| Naming | `stg_<entity>` | `dim_*`, `fct_*`/`fact_*`, `mart_*` |

## Worked example: one restaurant row, step by step

**1. Raw source** (`raw.restaurants`, messy text from source system):
| id | name | city | rating | rating_count | cost |
|---|---|---|---|---|---|
| "12" | Spice Villa | "Koramangala, Bangalore" | "--" | "1.2k+ ratings" | "₹ 300 for two" |

**2. Staging — `stg_restaurants` (view)**: only renames/casts/parses this single table, no joins, no business rules.
```sql
select id::number as restaurant_id, name as restaurant_name,
    trim(coalesce(regexp_substr(city, '[^,]+$'), city)) as city,   -- "Koramangala, Bangalore" -> "Bangalore"
    try_to_decimal(nullif(rating, '--'), 3, 1) as rating,            -- "--" -> null
    try_to_number(regexp_substr(rating_count, '[0-9]+')) as rating_count, -- "1.2k+ ratings" -> 1
    try_to_number(regexp_substr(cost, '[0-9]+')) as cost_for_two      -- "₹ 300 for two" -> 300
from {{ source('raw', 'restaurants') }}
```
Result row: `restaurant_id=12, restaurant_name='Spice Villa', city='Bangalore', rating=null, rating_count=1, cost_for_two=300`.
Note `rating_count` parsing is naive here (grabs "1" from "1.2k+"), which is exactly the kind of thing marts-layer logic or better regex could later refine — but staging's job stops at "clean and typed", not "correct business meaning".

**3. Marts — `mart_restaurant_performance` (table)**: joins `stg_restaurants` with `fct_orders`/`fact_order_items` and adds business logic that has no place in staging:
```sql
select r.restaurant_id, r.restaurant_name, r.city,
    count(o.order_id) as total_orders,
    sum(iff(o.is_delivered, o.sales_amount, 0)) as gmv,
    round(div0(count_if(o.order_status='Cancelled'), count(*)), 4) as cancel_rate
from {{ ref('stg_restaurants') }} r
left join {{ ref('fct_orders') }} o using (restaurant_id)
group by 1,2,3
```
This mart couldn't exist in staging: it needs **another entity (orders)** and **aggregation/derived KPIs** (`gmv`, `cancel_rate`) — both are marts-layer responsibilities, not staging's.

**Why the split matters**: if `raw.restaurants` changes its rating format tomorrow, you fix it in one place (`stg_restaurants`). Every mart that depends on restaurant data (dim_restaurants, mart_restaurant_performance, etc.) automatically gets the fix without touching business logic.
