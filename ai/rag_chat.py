import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from google import genai
from google.genai import types
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv

load_dotenv(r"D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering\ai\.env", override=True)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CHAT_MODEL = "gemini-3.6-flash"
NEW_REVIEWS = 500
TOP_K = 5
CACHE_FILE = "review_embeddings.parquet"

def read_reviews_from_snowflake():
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
    try:
        query = f"""
            SELECT REVIEW_ID, CITY, RATING, COMMENT
            FROM FOOD_DELIVERY.STAGING.STG_REVIEWS
            SAMPLE ({NEW_REVIEWS} ROWS)
        """
        df = conn.cursor().execute(query).fetch_pandas_all()
        df.columns = df.columns.str.lower()
        return df
    finally:
        conn.close()

@st.cache_data
def load_reviews():
    if os.path.exists(CACHE_FILE):
        return pd.read_parquet(CACHE_FILE)

    df = read_reviews_from_snowflake()
    df.to_parquet(CACHE_FILE)
    return df

st.title("Chat with your Food Delivery Reviews")
st.caption(f"Searches {NEW_REVIEWS} reviews and answers with {CHAT_MODEL}.")

def cosine_similarity(vec_a, vec_b):
    return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)))

def find_similar_reviews(question, df):
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([question, *df["comment"].tolist()]).toarray()
    question_vector = vectors[0]
    review_vectors = vectors[1:]
    df = df.copy()
    df["score"] = [cosine_similarity(question_vector, vec) for vec in review_vectors]
    return df.nlargest(TOP_K, "score")

def ask_llm(question, top_reviews):
    context = ""
    for _, row in top_reviews.iterrows():
        context += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"
    prompt = f"Answer only from the reviews below. Be short and direct.\n\nQuestion: {question}\n\nReviews:\n{context}"
    return client.models.generate_content(model=CHAT_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.2)).text

review_df = load_reviews()
question = st.text_input("Ask a question about your reviews:", placeholder="e.g. What are the most common complaints about delivery?")

if question:
    top_reviews = find_similar_reviews(question, review_df)
    st.markdown("**Answer:**")
    st.write(ask_llm(question, top_reviews))

    with st.expander("Reviews used"):
        st.dataframe(top_reviews[["city", "rating", "comment"]], hide_index=True)