import streamlit as st
import requests
import json

# Set the API endpoint URL and model name
OLLAMA_URL = "http://localhost:11434/v1/completions"
MODEL_NAME = "mistral:latest"

# Disable SSL warnings if needed (not recommended for production environments)
requests.packages.urllib3.disable_warnings()

# Streamlit App
st.title("Mistral Model Interaction")

# Input text box
prompt = st.text_area("Enter your prompt for the Mistral model:", "")

# Submit button
if st.button("Generate Response"):
    if prompt.strip():
        # Make API call
        with st.spinner("Generating response..."):
            try:
                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "max_tokens": 100,  # Adjust max tokens as per requirement
                    "temperature": 0.7,  # Adjust temperature for creativity
                }
                response = requests.post(
                    OLLAMA_URL,
                    headers=headers,
                    json=payload,
                    verify=False  # Use verify=False only if the server uses a self-signed certificate
                )
                response.raise_for_status()  # Raise exception for HTTP errors
                response_data = response.json()
                
                # Display results
                if "choices" in response_data:
                    st.success("Response generated successfully!")
                    for choice in response_data["choices"]:
                        st.write(f"**Response**: {choice['text']}")
                else:
                    st.warning("No response received!")
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with Mistral model: {e}")
    else:
        st.warning("Please enter a prompt.")