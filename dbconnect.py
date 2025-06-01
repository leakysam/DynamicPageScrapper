import os
import pandas as pd
from sqlalchemy import create_engine
from langchain_ollama import OllamaLLM
import streamlit as st

# Database connection
DATABASE_URL = "postgresql://sam:9955@localhost:5432/forebet"
engine = create_engine(DATABASE_URL)

# Initialize Ollama model
ollama = OllamaLLM(model="llama3.2")  # Replace with the correct Ollama model version

# Ollama query function
def query_with_ollama(prompt):
    """
    Use Ollama to interpret the prompt and generate SQL queries or insights.
    """
    try:
        response = ollama.invoke(prompt)  # Pass the prompt as a string
        return response
    except Exception as e:
        st.error(f"Ollama error: {e}")
        return None

# Function to query the database
def fetch_data(sql_query):
    """
    Execute SQL query and fetch data from the database.
    """
    try:
        with engine.connect() as connection:
            result = pd.read_sql(sql_query, connection)
        return result
    except Exception as e:
        st.error(f"Database query error: {e}")
        return None

# Streamlit application
st.title("AI-Powered SQL Query Interface")
st.write("Generate SQL queries and analyze data interactively using Ollama.")

# Input prompt
prompt = st.text_area("Enter your natural language query:")

if st.button("Analyze"):
    if prompt:
        st.info("Processing your query with Ollama...")
        sql_query = query_with_ollama(prompt)  # Generate SQL query

        if sql_query:
            st.write("Generated SQL Query:")
            st.code(sql_query, language="sql")

            st.info("Fetching data from the database...")
            data = fetch_data(sql_query)  # Fetch data using the SQL query

            if data is not None:
                st.write("Query Results:")
                st.dataframe(data)
            else:
                st.error("No data returned. Check your SQL query or database.")
    else:
        st.warning("Please enter a query to analyze.")
