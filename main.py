import streamlit as st
import requests

# FastAPI server URL
API_URL = "http://127.0.0.1:8000/query/"

# Streamlit user interface
st.title("Database Query with Ollama")

# Input for user prompt
prompt = st.text_area("Enter your query prompt:")

# If user submits a prompt
if st.button("Submit Query"):
    if prompt:
        # Send the prompt to the FastAPI backend
        response = requests.post(API_URL, json={"prompt": prompt})
        data = response.json()

        # Display result
        if "error" in data:
            st.error(data["error"])
        else:
            st.write("Query Results:")
            st.json(data["data"])  # Display the data in JSON format
    else:
        st.warning("Please enter a query prompt.")
