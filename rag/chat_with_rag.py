import streamlit as st
import requests

# API Endpoint URLs
RAG_API_URL = "http://localhost:8000/query/docs"  # FastAPI RAG endpoint
OLLAMA_URL = "http://localhost:11434/v1/completions"  # Ollama Mistral endpoint

# Model Configuration
MISTRAL_MODEL_NAME = "mistral:latest"

# Streamlit App
st.title("Kubeflow discovery bot")

# Input for user query
user_query = st.text_area("Enter your query:")

# Input for collection_name
collection_name = st.text_input("Input your collection name:", "kubeflow")

# Submit button
if st.button("Submit"):
    if user_query.strip():
        with st.spinner("Processing query with RAG and Mistral..."):
            try:
                # Step 1: Query the RAG API
                rag_response = requests.post(
                    RAG_API_URL,
                    json={"query_text": user_query, "top_k": 1, "collection":collection_name}
                )
                rag_response.raise_for_status()
                rag_results = rag_response.json()
                print(rag_results)

                # Prepare context from RAG results
                if rag_results:
                    context = "\n\n".join(
                        [f"ID: {result['id']}\nChunk: {result['text_chunk']}" for result in rag_results]
                    )
                    st.success("RAG context retrieved successfully!")
                else:
                    st.warning("No results found in RAG. Cannot proceed to Mistral.")
                    context = ""

                # Step 2: Pass RAG context + user query to Mistral
                if context:
                    mistral_prompt = f"Context:\n{context}\n\nQuery:\n{user_query}\n\nAnswer:"
                    headers = {"Content-Type": "application/json"}
                    mistral_payload = {
                        "model": MISTRAL_MODEL_NAME,
                        "prompt": mistral_prompt,
                        "max_tokens": 500,  # Adjust based on your needs
                        "temperature": 0.9,  # Adjust temperature for creativity
                    }
                    mistral_response = requests.post(
                        OLLAMA_URL,
                        headers=headers,
                        json=mistral_payload,
                        verify=False  # Use verify=False only if the server uses a self-signed certificate
                    )
                    mistral_response.raise_for_status()
                    mistral_result = mistral_response.json()

                    # Display Mistral's response
                    if "choices" in mistral_result:
                        st.success("Response from Mistral generated successfully!")
                        for choice in mistral_result["choices"]:
                            st.write(f"**Bot's Response:** {choice['text']}")
                    else:
                        st.warning("No response received from Mistral.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a query.")
