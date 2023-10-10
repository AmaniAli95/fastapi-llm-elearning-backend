import os
import time
import tiktoken
import pinecone
import pandas as pd
import numpy as np
from uuid import uuid4
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain.document_loaders import UnstructuredMarkdownLoader

from services.storage import download_and_split_files_output
from services.text_extract import get_token_count

pinecone.init(api_key=os.environ.get("PINECONE_KEY"), environment=os.environ.get("PINECONE_ENV"))

def get_vector_id(model, file_content):
    embeddings = model.encode(file_content).tolist()
    vector_id = pinecone.Index.create_index(data=embeddings)
    return vector_id

def calculate_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

def insert_vectors_to_pinecone(vector_data_list, pinecone_index_name):
    # Initialize Pinecone connection
    index = pinecone.Index(index_name=pinecone_index_name)

    # Upsert the vector data into the Pinecone index
    upsert_response = index.upsert(vectors=vector_data_list)
    return upsert_response

def get_vector_data(temp_file_path_output_list):
    # Initialize the SentenceTransformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Create an empty list to store content and token count
    contents = []

    # Iterate through the document chunks
    for temp_file_path_output in temp_file_path_output_list:
        loader = UnstructuredMarkdownLoader(temp_file_path_output)
        doc = loader.load()
        
        # Extract content and token count for each chunk
        for text_chunk in doc:
            content = text_chunk.page_content
            token_count, _ = get_token_count(content, "cl100k_base")
            contents.append((text_chunk, content, token_count))
    
    # Create a DataFrame from the contents
    df = pd.DataFrame(contents, columns=['filename', 'file_content', 'tokens'])
    
    # Encode content using SentenceTransformer
    df["vectorEmbed"] = df.file_content.apply(lambda x: model.encode(x).tolist())
    
    # Generate unique IDs for each row
    df['id'] = [str(uuid4()) for _ in range(len(df))]
    
    # Create a list of dictionaries for vector data
    vector_data_list = []
    for _, row in df.iterrows():
        vector_data = {
            'id': row['id'],
            'vectorEmbed': row['vectorEmbed'],
            'metadata': {'content': row['file_content'], 'file_name': row['filename']}
        }
        vector_data_list.append(vector_data)
    
    return df, vector_data_list




