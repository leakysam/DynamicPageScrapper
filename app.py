from fastapi import FastAPI
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from sqlalchemy import create_engine
import pandas as pd
import json
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Database URL and connection setup
DATABASE_URL = "postgresql://sam:9955@localhost:5432/forebet"
engine = create_engine(DATABASE_URL)

# Ollama setup
ollama = OllamaLLM(model="llama3.2")  # Update with correct model

# Pydantic model to capture user input
class PromptRequest(BaseModel):
    prompt: str

# Query function: Fetch data from the database
def fetch_data(sql_query):
    try:
        with engine.connect() as connection:
            result = pd.read_sql(sql_query, connection)
        
        # Ensure a valid response structure even if no data is found
        return {"data": result.to_dict(orient="records")}  # Always return 'data' key

    except Exception as e:
        return {"error": f"Error fetching data: {e}"}

def query_with_ollama(prompt):
    """
    Use Ollama to interpret the prompt and generate SQL queries or insights.
    Ensure prompt clearly describes the SQL task.
    """
    try:
        # Generate SQL query with Ollama based on the user prompt
        response = ollama.invoke(prompt)
        
        # Log or print the response to inspect its format
        print("Ollama response:", response)  # This is to check what Ollama returns
        
        # If response is a dictionary, handle it accordingly
        if isinstance(response, dict):
            # If Ollama response has a key for SQL query, extract it
            sql_query = response.get('sql_query', '')  # Replace 'sql_query' with the actual key if needed
        else:
            sql_query = response
        
        # Ensure the query is valid SQL (basic check here)
        if not sql_query.strip().lower().startswith("select"):
            return {"error": "Generated SQL query is not a valid SELECT query."}
        
        # Ensure the table name is included in the SQL query
        if "forebet" not in sql_query:  # Ensure 'forebet' is present
            return {"error": "Error: Table name 'forebet' missing in SQL query."}
        
        # Execute the query and return the data
        return fetch_data(sql_query)
    except Exception as e:
        return {"error": f"Error with Ollama: {e}"}

