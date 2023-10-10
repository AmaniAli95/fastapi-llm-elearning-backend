import openai
import json
import tiktoken
import nltk
import shortuuid
import pandas as pd
from langchain.document_loaders import UnstructuredMarkdownLoader
from dotenv import load_dotenv
from uuid import uuid4

from db.supabase import get_sb
from tasks.jobs import get_topic_id

nltk.download('punkt')
load_dotenv()

def get_token_count(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(string)
    num_tokens = len(encoding.encode(string))
    return num_tokens, tokens

def extract_syllabus_from_text(text_chunk, model):
    """Extract the syllabus from the given text content using OpenAI Calling Function."""
    function_descriptions = [
        {
            "name": "extract_syllabus",
            "description": "Extract the syllabus from the given text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text content to be analyzed.",
                    },
                    "subtopic": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The subtopic of the text content.",
                    },
                    "descriptions": {
                        "type": "string",
                        "description": "A concise and comprehensive summary of the main topics covered in the text content. Please provide a well-structured paragraph highlighting the key points and themes addressed in the content.",
                    },  
                    "objective": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of learning objectives of the text content. Please provide at least 5 learning objectives.",
                    },
                    "duration": {
                        "type": "number",
                        "description": "An estimated duration of time for students to learn the text content, in minutes.",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Relevant keywords associated with the text content. Please provide at least 5 relevant keywords.",
                    },
                    "prerequisites": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of prerequisite topics",
                    },
                    "complexity": {
                        "type": "string",
                        "description": "The complexity level of the text content (beginner, elementary, intermediate, advanced or expert)",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Return Null",
                        #"description": "Utilize OpenAI Embedding to generate embeddings for the topics, followed by calculating the cosine similarity between these embeddings. Subsequently, assign topics with significant similarity to share a common parent_id. Finally, return the topic IDs, now designated as their respective parent_ids.",
                    },
                    "weight": {
                        "type": "number",
                        "description": """The importance weight score of the topic. 
                                            Assign weights based on the following criteria:
                                            - Prerequisite knowledge: 0.1
                                            - Foundational concept: 0.3
                                            - Moderate importance: 0.5
                                            - Supplementary material: 0.5
                                            - Core learning objective: 0.8
                                            - Critical skill: 0.9
                                            Please select the weight that best represents the importance of the topic.
                                        """,
                    },
                },
                "required": ["content", "subtopic", "descriptions", "objective", "duration", "keywords", "prerequisites", "complexity", "weight","parent_id"],
            },
        }
    ]
    user_prompt = f"""You are a skilled syllabus creator. 
                    Your task is to carefully analyze the given {text_chunk} and extract the syllabus.
                    Please maintain consistency in the language used for the chunk. 
                    Use only the Malay language and refrain from using English or Indonesian"""
    conversation = [{"role": "user", "content": user_prompt}]
    response = openai.ChatCompletion.create(
            model=model,
            messages=conversation,
            functions=function_descriptions,
            function_call="auto",
        )
    return response.choices[0].message

def extract_syllabus(temp_file_path_output_list, vector_values_list,file_location_list,file_name_list,chapter_id):   
    output_chunks = [] 
    for index, temp_file_path_output in enumerate(temp_file_path_output_list):
        vector_values = vector_values_list[index]
        file_name = file_name_list[index]
        file_location = file_location_list[index]
        loader = UnstructuredMarkdownLoader(temp_file_path_output)
        doc = loader.load()
        for text_chunk in doc:
            content = text_chunk.page_content
            token_count, tokens = get_token_count(content, "cl100k_base")

            if token_count < 2000:
                response = extract_syllabus_from_text(text_chunk, "gpt-3.5-turbo")
            else:
                response = extract_syllabus_from_text(text_chunk, "gpt-3.5-turbo-16k")
            metadata = json.loads(response.function_call.arguments)
            
            topicName = file_name
            parent_id = "33ff05a2-dae8-4ef4-bcd9-6e276645e1bf"
            chapter_id = chapter_id
            significance = 0.5
            weight = metadata["weight"]
            topic_score = significance * weight
            corpus_location = file_location
            vector_id = vector_values
            del metadata["weight"]
            del metadata["parent_id"]
            
            get_sb().table("topics").insert({"name":f"{topicName}","chapter_id":f"{chapter_id}","parent_id":f"{parent_id}"
                                        ,"metadata":f"{metadata}","weight":f"{weight}","significance":f"{significance}", "topic_score":f"{topic_score}"
                                        ,"content_location":f"{corpus_location}","vector_id":f"{vector_id}"}).execute()
            topicID = get_topic_id(topicName)
            output_chunks.append({
                "id" : topicID,
                "name" : topicName,
                "parent_id" : parent_id,
                "chapter_id" : chapter_id,
                "significance" : significance,
                "weight" : weight,
                "topic_score" : topic_score,
                "corpus_location" : corpus_location,
                "vector_id" : vector_id,
                "metadata": metadata
                })
    return output_chunks, doc

