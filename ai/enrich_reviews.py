import os
import json
import re
import snowflake.connector
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(r"D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering\ai\.env", override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini model and review labels.
MODEL = "gemini-3.6-flash"
SAMPLE_N = 15
TOPICS = ["food quality", "delivery", "pricing", "service", "packaging", "other"]
PROMPT = f"You classify customer reviews for a food delivery app. Return JSON with sentiment_label, sentiment_score, topic ({TOPICS}), and key_issue (or null)."
model = genai.GenerativeModel(MODEL)


# Connect to Snowflake using environment variables.
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


# Create the target table once if it does not already exist.
def create_output_table(cursor):
    cursor.execute("CREATE SCHEMA IF NOT EXISTS FOOD_DELIVERY.AI")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FOOD_DELIVERY.AI.REVIEW_ENRICHED (
            REVIEW_ID STRING,
            SENTIMENT_LABEL STRING,
            SENTIMENT_SCORE FLOAT,
            TOPIC STRING,
            KEY_ISSUE STRING,
            MODEL STRING,
            ENRICHED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)


# Pull reviews that have not been enriched yet.
def get_reviews_to_enrich(cursor):
    cursor.execute(f"""
        SELECT REVIEW_ID, COMMENT
        FROM FOOD_DELIVERY.RAW.REVIEWS
        WHERE REVIEW_ID NOT IN (
            SELECT REVIEW_ID FROM FOOD_DELIVERY.AI.REVIEW_ENRICHED
        )
        LIMIT {SAMPLE_N}
    """)
    return cursor.fetchall()


# Extract the JSON object from Gemini output.
def parse_json_response(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output: {text}")
    return json.loads(cleaned[start:end + 1])


# Ask Gemini to classify one review and return parsed JSON.
def classify_review(comment):
    try:
        response = model.generate_content(
            f"{PROMPT}\n\nReview: {comment}",
            generation_config={"temperature": 0},
        )
        return parse_json_response(response.text)
    except Exception as e:
        message = str(e)
        if "429" in message or "quota" in message.lower():
            print("Gemini quota reached. Stop this batch and try again after quota resets or on a paid plan.")
            return None
        raise


# Insert all enriched rows into Snowflake in one batch.
def save_results(cursor, results):
    print(f"Saving {len(results)} enriched reviews to Snowflake...")
    if not results:
        return
    cursor.executemany(
        """
        INSERT INTO FOOD_DELIVERY.AI.REVIEW_ENRICHED
            (review_id, sentiment_label, sentiment_score, topic, key_issue, model)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        results,
    )


# End-to-end flow: fetch, classify, and save.
def main():
    conn = get_connection()
    cursor = conn.cursor() # the object you use to run SQL commands
    create_output_table(cursor)
    reviews = get_reviews_to_enrich(cursor)

    if len(reviews) == 0:
        print("No new reviews to enrich.")
        return

    print(f"Enriching {len(reviews)} reviews...")

    # Classify each review and collect rows for a single batch insert.
    results = []
    for review_id, comment in reviews:
        print(f"Classifying review {review_id}: {comment}")
        labels = classify_review(comment)
        if labels is None:
            break
        print(f"Labels for review {review_id}: {labels}")
        results.append((
                review_id,
                labels["sentiment_label"],
                labels["sentiment_score"],
                labels["topic"],
                labels["key_issue"],
                MODEL,
            ))

    # Save all successfully classified reviews together.
    save_results(cursor, results)
    if results:
        print(f"Saved {len(results)} enriched reviews to Snowflake.")
        conn.commit()
    else:
        print("No reviews were enriched because Gemini quota was exhausted.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()