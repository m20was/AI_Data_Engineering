# Text to SQL Interview Notes

This note explains everything happening in `ai/text_to_sql.py` so you can talk through it in an interview.

## What the app does

The app lets a user type a plain-English question like:

```text
Top 10 cities by Gross Merchandise Value (GMV)
```

Then it:

1. sends the question to Gemini
2. asks Gemini to write a SQL query
3. validates the query is safe
4. runs the SQL in Snowflake
5. shows the SQL, result table, and chart in Streamlit

In short: English question -> Gemini SQL -> Snowflake result -> Streamlit output.

## Main idea

This is a text-to-SQL assistant for the food delivery project.

It is designed to:

- stay compact and easy to explain
- use Gemini instead of OpenAI
- use Snowflake as the data warehouse
- keep the user experience simple in Streamlit
- avoid unsafe SQL like `DROP`, `DELETE`, or `UPDATE`

## File structure and imports

The file imports these modules:

- `os` for environment variables
- `json` for parsing Gemini JSON output
- `pandas` for showing query results and charts
- `streamlit` for the web UI
- `snowflake.connector` for database access
- `load_dotenv` for loading local `.env` values
- `google.genai` and `types` for Gemini API calls

### Why `load_dotenv(...)` is used

The file loads the exact local `.env` file:

```python
load_dotenv(r"D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering\ai\.env", override=True)
```

This is important because:

- it forces the app to use the local project secrets
- `override=True` prevents stale environment variables from winning
- the app needs the correct Snowflake and Gemini credentials every time

## Constants

### `MODEL`

```python
MODEL = "gemini-3.6-flash"
```

This is the Gemini model used to generate SQL.

Why this matters:

- it matches the rest of the project’s Gemini setup
- it keeps the app consistent with your other AI features
- the model is lightweight enough for a quick demo flow

### `FORBIDDEN_WORDS`

```python
FORBIDDEN_WORDS = ["drop", "delete", "truncate", "alter", "update", "insert", "create", "replace", "grant", "revoke"]
```

This list blocks dangerous SQL keywords.

Purpose:

- prevent destructive commands
- keep the app read-only
- make the demo safer for interviews

### `EXAMPLE_QUESTIONS`

This is the sidebar list of example questions shown to the user.

Examples help the user:

- understand what the app can answer
- try the app quickly without thinking of a prompt
- see realistic business-style questions

## Gemini client

```python
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
```

This creates the Gemini client using the API key from the environment.

Why this is good:

- no secret is hardcoded
- the app uses the same SDK style as the other Gemini files in the project
- the client can be reused for SQL generation calls

## Prompt setup

The app defines two prompt blocks:

### `SCHEMA`

This is a plain-text list of available Snowflake tables and columns.

It tells Gemini what data it can use, for example:

- `FCT_ORDERS`
- `DIM_RESTAURANTS`
- `DIM_CUSTOMER`
- `MART_DAILY_CITY_REVENUE`
- `MART_RESTAURANT_PERFORMANCE`
- `MART_DELIVERY_SLA`

It also reminds Gemini that `gmv` means delivered revenue.

Why it matters:

- the model needs schema context to generate useful SQL
- it helps avoid hallucinated table names
- it nudges Gemini toward mart tables when appropriate

### `SYSTEM_PROMPT`

This is the instruction block sent to Gemini.

It tells the model to:

- write exactly one `SELECT` query
- never modify data
- use bare table names only
- limit the result to 100 rows or fewer unless a single total is asked
- return JSON in the format `{"sql": "..."}`

Why it matters:

- constrains the output format
- makes the response easy to parse
- keeps the app safe and predictable

## Function-by-function explanation

### `get_connection()`

```python
@st.cache_resource
def get_connection():
```

This function creates the Snowflake connection.

It reads these environment variables:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`

It also sets:

- `schema="MARTS"`
- `role="DBT_ROLE"`

Why `@st.cache_resource` is used:

- the connection object is reused between reruns
- Streamlit does not have to reconnect every time the user types
- it makes the app feel faster and cleaner

Interview explanation:

> This function centralizes the Snowflake connection so the UI code stays simple and the connection is cached for reuse.

### `generate_sql(question)`

This is the core Gemini function.

What it does:

1. sends the prompt and user question to Gemini
2. asks Gemini to respond as JSON
3. extracts the `sql` value from the JSON response
4. keeps the SQL focused on `FOOD_DELIVERY` tables only
5. trims whitespace and trailing semicolons

Why each step matters:

- `client.models.generate_content(...)` is the Gemini call
- `response_mime_type="application/json"` nudges Gemini toward structured output
- `json.loads(response.text)` converts the response into Python data
- the SQL generator now uses only `FOOD_DELIVERY` table names and no longer needs old project prefixes

Interview explanation:

> This function turns a natural-language question into executable SQL by giving Gemini the schema, response rules, and formatting constraints.

### `is_safe(sql)`

This function checks whether the generated SQL is safe to run.

It does two main checks:

1. the SQL must start with `select` or `with`
2. it must not contain forbidden words like `drop` or `delete`

Why it exists:

- Gemini could generate a query that is not read-only
- this function adds a basic guardrail before Snowflake runs anything
- it keeps the app safer for demos and interviews

Important note:

This is a simple safety check, not a full SQL parser.

Interview explanation:

> I added a lightweight guardrail to prevent destructive SQL and make sure the generated query is read-only.

### `run_query(sql)`

This function executes the SQL in Snowflake and returns a pandas DataFrame.

It:

- opens a cursor from the cached Snowflake connection
- runs the SQL
- converts the result to a pandas DataFrame with `fetch_pandas_all()`

Why this is useful:

- pandas makes it easy to display the result in Streamlit
- the same output can be shown as a table or chart
- the UI code stays clean because the database logic is isolated here

Interview explanation:

> This function is the execution layer. It takes validated SQL and converts the Snowflake result into a DataFrame for display.

## Streamlit UI flow

After the functions, the file builds the interface.

### Title and caption

```python
st.title("Chat with your Food Delivery Data")
st.caption(f"Ask in English, {MODEL} writes the SQL, Snowflake runs it")
```

This gives the page a clear purpose and tells the user what the app does.

### Sidebar examples

```python
with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f" - {q}")
```

This renders the helper examples on the left.

Why it matters:

- improves usability
- shows expected question types
- helps new users test the app immediately

### Question input

```python
question = st.text_input(...)
```

This is the main user input box.

It shows a placeholder like:

```text
Top 10 cities by Gross Merchandise Value (GMV)
```

Why it matters:

- it keeps the interface simple
- the whole app is driven by one natural-language question

### Main execution block

```python
if question:
```

Once the user enters a question, the app runs this sequence:

1. call `generate_sql(question)`
2. show the SQL with `st.code(...)`
3. check `is_safe(sql)`
4. run `run_query(sql)` if it is safe
5. show the row count
6. display the table
7. display a bar chart if the result has exactly two columns and the second column is numeric

Why this flow is good:

- the user sees the SQL, not just the answer
- the output is transparent and interview-friendly
- the chart appears automatically when the result is suitable

## Why the chart only appears sometimes

The code only shows a chart when:

- there are exactly 2 columns
- the second column is numeric

This is deliberate.

Why:

- not every SQL result makes sense as a chart
- forcing a chart for every query would make the UI noisy
- this simple rule keeps the demo clean

## Features worth mentioning in an interview

### 1. Gemini-powered text to SQL

The app converts English into SQL using Gemini instead of writing SQL manually.

### 2. Structured output

The model is asked to return JSON so the SQL can be extracted reliably.

### 3. Safety check

The app blocks destructive SQL before execution.

### 4. Snowflake execution

The final query runs against the warehouse, not locally.

### 5. Streamlit visualization

The result is shown as:

- SQL text
- table
- optional chart

### 6. Project-specific schema awareness

The prompt includes the real food delivery mart tables, which improves output quality.

### 7. Simple and compact design

The code is short enough to explain clearly in an interview, but still useful end to end.

## Good interview talking points

You can describe the app like this:

> This is a Gemini-based text-to-SQL app. The user asks a question in plain English, Gemini generates a SQL query using the project schema, the app validates the query is read-only, Snowflake executes it, and Streamlit displays the result as a table and chart.

You can also mention:

- I used `load_dotenv(..., override=True)` to guarantee the correct local credentials.
- I cached the Snowflake connection with `st.cache_resource`.
- I added a simple allow/block check to avoid dangerous SQL.
- I kept the app compact so it is easy to understand in an interview.

## Things to watch out for

- The safety check is basic and not a full SQL parser.
- Gemini can still produce a query that needs small cleanup.
- The chart logic is intentionally simple and only handles basic two-column outputs.
- The app depends on the correct Snowflake and Gemini environment variables being loaded.

## How to explain the file quickly

If someone asks for a short explanation, use this:

1. It loads local secrets.
2. It connects to Snowflake.
3. It asks Gemini to write SQL from a question.
4. It blocks unsafe SQL.
5. It executes the query.
6. It shows the result table and chart in Streamlit.

## One-line summary

`ai/text_to_sql.py` is a compact Gemini-powered Streamlit app that converts English questions into safe Snowflake SQL and displays the results visually.
