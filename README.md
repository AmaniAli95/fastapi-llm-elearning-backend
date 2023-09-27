# FastApi LLM Elearning Backend

This repository contains a FastAPI backend Retrieval Augmented Generation (RAG) application that leverages large language models (LLMs) like GPT-3.5 for question-answering capabilities.

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Features](#overview)
- [Technologies](#technologies)
- [File Structure](#file-structure)

## Overview
The backend provides RESTful APIs for:
- **User management**: account creation, authentication, profiles
- **Question answering**: submit a question, get back an answer generated by an LLM
- **Explanations**: ask follow-up questions, get explanations from the LLM
- **Conversations**: chat with the LLM in a conversational format
The core question answering and explanations are powered by OpenAI's GPT-3 API. The backend handles prompt formatting, calling the API, and processing the response.

## Getting Started
### Prerequisites
- Python 3.9+
- OpenAI API key
- Docker

### Installation
```bash
$ git clone https://github.com/llm-question-answering
$ cd backend
$ pip install -r requirements.txt
```

### Configuration
Add OpenAI API keys:

```python
OPENAI_API_KEY = 'sk-...' 
```

Running

## Features
- **User auth**: JWT-based authentication and user accounts
- **Question API**: Submit questions, receive AI-generated answers
- **Conversations API**: Chatbot-style conversations with the LLM
- **Explanations API**: Ask follow-up questions to get explanations
- **Moderation**: Optional filtering of generated text
- **Analytics**: Track usage metrics and query patterns

## Technologies
- **FastAPI**: High performance web framework
- **OpenAI API**: Large language models like GPT-3
- **SQLAlchemy**: Database ORM
- **LangChain**: Helper library for LLMs
- **Docker**: Containerization

## File Structure
The project is structured into distinct directories, each serving a specific purpose. Below, we provide an in-depth breakdown of the project's file structure:

### app/routers
- **chapters.py:** This module contains routers responsible for handling `GET` requests to retrieve chapter details.
- **courses.py:** Within this module, you'll find routers that facilitate the retrieval of course information.
- **topics.py:** Here, you can access routers designed for fetching topic details.

### db
- **database.py:** This module houses functions responsible for core database operations, including uploading, deleting, and retrieving data from the Supabase database table.
- **supabase.py:** In this section, you'll find functions dedicated to obtaining and managing the Supabase client.

### services
- **assessment.py:** This module plays a pivotal role in generating assessment questions, managing their distribution, analyzing user responses, and generating proficiency profiles to assess users' knowledge and skills.
- **storage.py:** Within this module, you'll find functions crucial for effective file storage management, including `download_file`, `download_and_split_files`, and `download_and_split_files_output`. These functions handle file downloads from external sources, document splitting into smaller sections, and the management of splitting process outputs.
- **text_extract.py:** Responsible for the extraction of syllabus content from documents, this module carries out the necessary processes to achieve efficient content extraction.
- **text_split.py:** Managing the process of dividing documents into topics and subtopics, this module efficiently breaks down content to enable more granular access and navigation.

### tasks
- **jobs.py:** Focused on job management tasks, this module offers functions to create, update, and retrieve job statuses.

### main.py
- This FastAPI module provides endpoints for streamlining the extraction of syllabus content from documents. When you access the `GET /extract_syllabus/{chapter_id}` endpoint, the module initiates a process that checks whether the chapter has been processed previously. It downloads and splits the chapter's content into topics and subtopics, using specific headers as markers. The resulting data undergoes further processing, resulting in a JSON output representing the syllabus content. This JSON is temporarily stored, and its location is logged. Additionally, the module offers an endpoint, `GET /extract_syllabus/{chapter_id}/status`, to retrieve the status of the extraction job. Lastly, `GET /assessments/init` initiates an assessment process, generating proficiency profiles based on user responses to questions.

```bash
docker-compose up --build
```
The FastAPI server will be available at **http://localhost:8000**
