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

def getvectorId(file_name_list,temp_file_path_output_list):
    #Connect to your indexes
    index_name = "chapiq-index"
    index = pinecone.Index(index_name)
    output = index.query(
        top_k=367,
        vector= [0] * 384, # embedding dimension
        namespace='chapiq-namespace',
        include_values=True # Your filters here
    )
    ids = [match['id'] for match in output['matches']]
    print(ids)
    return ids

    #def getvectorId(file_name_list,temp_file_path_output_list):
    #model = SentenceTransformer('all-MiniLM-L6-v2')
    #contents = []
    #tiktoken_encoding = tiktoken.get_encoding("gpt2")
    #for index, temp_file_path_output in enumerate(temp_file_path_output_list):
    #    loader = UnstructuredMarkdownLoader(temp_file_path_output)
    #    doc = loader.load()
    #    for text_chunk in doc:
    #        content = text_chunk.page_content
    #        token_count, tokens = get_token_count(content, "cl100k_base")
    #        contents.append((text_chunk, content, token_count))
    #    df = pd.DataFrame(contents, columns=['filename', 'file_content', 'tokens'])
    #    df["vectorEmbed"] = df.file_content.apply(lambda x: model.encode(x).tolist()) 
    #    df['id'] = [str(uuid4()) for _ in range(len(df))]
    #    # Loop through each row in the DataFrame 'df'
    #vector_data_list = []
    #for _, row in df.iterrows():
    #    vector_data = {
    #        'id': row['id'],
    #        'vectorEmbed': row['vectorEmbed'],  # Use the list directly, assuming 'vectorEmbed' is a list
    #        'metadata': {'content': row['file_content'], 'file_name': row['filename'], 'weights': row['weights']}
    #    }
    #    vector_data_list.append(vector_data)
    #    # Upsert the vector data into the Pinecone index
    #upsert_response = index.upsert(vectors=vector_data_list, namespace='chapiq-namespace')
    #return df, vector_data_list




