# ChapterIQ Backend

ChapterIQ is an AI-powered personalized learning platform. This repository contains the code for the ChapterIQ backend API built using LangChain and FastAPI.

## Features

The core features of the ChapterIQ backend include:

- **User Management** - Handles user accounts, profiles, authentication and authorization
- **Subjects API** - Manages subjects, chapters, topics and content
- **Assessments API** - Assembles personalized assessments and analyzes responses
- **Question Generator** - Generates MCQ questions using GPT-3 via LangChain 
- **Chatbot API** - Dialog agent for personalized teaching and explanations
- **Analytics API** - Aggregates usage data and generates insights

## Architecture

The backend follows a modular architecture with separate APIs for each feature area:

- **FastAPI** - Provides the core API routing and endpoints
- **PostgresQL** - Object relational mapper for PostgreSQL database
- **LangChain** - NLP library for question generator and chatbot
- **OpenAI API** - Connects to GPT-3 for text generation
- **Pinecone** - Vector database for semantic search

## Getting Started

### Dependencies

- Python 3.9+
- PostgreSQL
- OpenAI API key
- Pinecone API key 

### Installation

```bash
$ git clone https://github.com/chapteriq/backend
$ cd backend
$ pip install -r requirements.txt
```

### Configuration

Add API keys:

```python
OPENAI_API_KEY = 'sk-...' 
PINECONE_API_KEY = '...'
```

Initialize the database:

```bash
$ alembic upgrade head
```

### Running the App

```bash
$ uvicorn main:app --reload --port 5000
```

The API will be available at `http://localhost:5000`. See the documentation for endpoint details.

## Documentation

Full API documentation with explanations, samples requests/responses is available at [docs.chapteriq.com](http://docs.chapteriq.com) 
