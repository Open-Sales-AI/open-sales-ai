import streamlit as st
import requests

# Set the API endpoint URL
API_URL = "http://localhost:8000/query/docs"  # Update the URL if hosted on a different server or port

# Streamlit App
st.title("RAG manager tool")

import os
from pathlib import Path
import markdown
import streamlit as st
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import MarkdownTextSplitter

# Model and Milvus configuration
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MODEL_NAME = "WhereIsAI/UAE-Large-V1"

# Initialize the SentenceTransformer model
model = SentenceTransformer(MODEL_NAME)

# Connect to Milvus
connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

def read_markdown_files(directory):
    """Read Markdown files from a directory and convert them to HTML."""
    markdown_texts = []
    for file_path in Path(directory).rglob("*.md"):
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
            html = markdown.markdown(text)
            markdown_texts.append(html)
    return markdown_texts

def split_text_to_chunks(text, chunk_size=1000, chunk_overlap=500):
    """Split text into smaller chunks."""
    text_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)

def vectorize_and_insert(collection, markdown_directory):
    """Vectorize and insert Markdown content into a Milvus collection."""
    # Read and process markdown files
    markdown_texts = read_markdown_files(markdown_directory)

    all_chunks = []
    all_vectors = []

    for text in markdown_texts:
        chunks = split_text_to_chunks(text)
        embeddings = model.encode(chunks, show_progress_bar=True)
        
        all_chunks.extend(chunks)
        all_vectors.extend(embeddings)

    # Insert data into Milvus
    collection.insert([all_chunks, all_vectors])
    return len(all_vectors)

def create_milvus_collection(collection_name, markdown_directory):
    """Create a Milvus collection and insert Markdown data."""
    # Define schema
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text_chunk", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
    ]
    schema = CollectionSchema(fields, description="Schema for Markdown document embeddings")

    # Check if the collection exists, and create if not
    if not utility.has_collection(collection_name):
        collection = Collection(name=collection_name, schema=schema)
    else:
        collection = Collection(name=collection_name)
        st.success("Collection already exists")

    # Ensure an index exists on the embedding field
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    if not collection.has_index():
        collection.create_index(field_name="embedding", index_params=index_params)

    # Insert vectors and chunks into Milvus
    inserted_count = vectorize_and_insert(collection, markdown_directory)
    return inserted_count

# Streamlit UI
st.title("Milvus Markdown Collection Creator")

# Input box for the directory path
markdown_dir = st.text_input("Enter the path to your Markdown documents:", "/Users/Shrey/open-sales-ai")

# Input for the collection name
collection_name = st.text_input("Enter a name for the Milvus collection:", "kubeflow")

print(markdown_dir)
# Button to create the collection
if st.button("Create Collection"):
    if markdown_dir and Path(markdown_dir).exists():
        with st.spinner("Processing and creating collection..."):
            try:
                count = create_milvus_collection(collection_name, markdown_dir)
                st.success(f"Collection '{collection_name}' created successfully with {count} vectors inserted!")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid directory path.")

st.title("Query Milvus database")

# Input text box
query_text = st.text_input("Enter your query text:", "")

# Input for top_k
top_k = st.number_input("Number of top matches to retrieve:", min_value=1, max_value=10, value=3)

# Input for collection_name
collection_name = st.text_input("Input your collection name:", "kubeflow")

# Submit button
if st.button("Submit Query"):
    if query_text.strip():
        # Make API call
        with st.spinner("Querying..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"query_text": query_text, "top_k": top_k, "collection": collection_name}
                )
                response.raise_for_status()  # Raise exception for HTTP errors
                results = response.json()
                
                # Display results
                if results:
                    st.success("Results retrieved successfully!")
                    for result in results:
                        st.write(f"**ID**: {result['id']}")
                        st.markdown(result['text_chunk'], unsafe_allow_html=True) 
                        st.write(f"**Score**: {result['score']:.4f}")
                        st.write("---")
                else:
                    st.warning("No results found!")
            except requests.exceptions.RequestException as e:
                st.error(f"Error querying API: {e}")
    else:
        st.warning("Please enter query text.")


def delete_milvus_collection(collection_name):
    """Delete a Milvus collection if it exists."""
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
        return f"Collection '{collection_name}' deleted successfully."
    else:
        return f"Collection '{collection_name}' does not exist."

# Streamlit UI for Deleting a Collection
st.title("Delete Milvus Collection")

# Input for the collection name to delete
delete_collection_name = st.text_input("Enter the name of the collection to delete:", "")

# Button to delete the collection
if st.button("Delete Collection"):
    if delete_collection_name.strip():
        with st.spinner("Deleting collection..."):
            try:
                result_message = delete_milvus_collection(delete_collection_name)
                st.success(result_message)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a collection name.")

