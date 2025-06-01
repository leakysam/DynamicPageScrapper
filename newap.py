
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
ollama = OllamaLLM(model="ollama-3.2")  # Update with correct model

# Pydantic model to capture user input
class PromptRequest(BaseModel):
    prompt: str

# Query function: Fetch data from the database
def fetch_data(sql_query):
    try:
        with engine.connect() as connection:
            result = pd.read_sql(sql_query, connection)
        return result.to_dict(orient="records")  # Convert to dict to return as JSON
    except Exception as e:
        return {"error": f"Error fetching data: {e}"}

# Ollama query function: Use Ollama to generate SQL
def query_with_ollama(prompt):
    try:
        # Generate SQL query with Ollama based on the user prompt
        response = ollama.invoke(prompt)
        return response
    except Exception as e:
        return f"Error with Ollama: {e}"

# API endpoint to handle the prompt
@app.post("/query/")
async def query_database(request: PromptRequest):
    prompt = request.prompt

    # Get SQL query from Ollama
    sql_query = query_with_ollama(prompt)
    
    if "Error" in sql_query:
        return {"error": sql_query}  # Return Ollama error if any

    # Ensure the query is valid SQL (basic check here)
    if not sql_query.strip().lower().startswith("select"):
        return {"error": "Generated SQL query is not a valid SELECT query."}

    # Fetch and return data
    data = fetch_data(sql_query)
    
    if "error" in data:
        return data  # Return database query error if any
    
    return {"data": data}
