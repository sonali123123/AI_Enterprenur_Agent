# AI Entrepreneur Mentor Chatbot

An AI chatbot that provides entrepreneurship mentorship with text and voice interaction, using FastAPI, Llama 3.1, and PostgreSQL.

## Features

- **Text and Voice Interaction**: Communicate with the chatbot using text or voice
- **Topic-Specific Entrepreneurship Responses**: Get focused advice on business topics
- **Interactive Q&A with Follow-up Suggestions**: Receive contextual follow-up questions
- **PostgreSQL Database**: Store conversation history for personalized interactions

## Technical Stack

- **Web Framework**: FastAPI with Pydantic
- **AI Model**: Llama 3.1 (8B parameters) running locally via Ollama
- **Voice Processing**: Google Text-to-Speech (gTTS) and Google Speech-to-Text
- **Database**: PostgreSQL

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Ollama with Llama 3.1 model installed

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd AI_Enterpreneur_Agent
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL:
   - Create a database named `entrepreneur_chatbot`
   - Update the `.env` file with your database credentials

5. Install and run Ollama:
   - Follow instructions at [Ollama.ai](https://ollama.ai/)
   - Pull the Llama 3.1 model: `ollama pull llama3.1:8b`

6. Start the application:
   ```
   uvicorn app.main:app --reload
   ```

7. Access the API documentation:
   - Open your browser and go to `http://localhost:8000/docs`

## API Endpoints

- **POST /api/text**: Process text input and return AI response with suggestions
- **POST /api/voice**: Process voice input and return AI voice response
- **POST /api/suggestions**: Get follow-up suggestions based on conversation context
- **GET /api/audio/{text}**: Convert text to speech and return audio stream

## Project Structure

```
app/
├── api/
│   ├── __init__.py
│   └── routes.py
├── models/
│   ├── __init__.py
│   ├── request_models.py
│   └── response_models.py
├── services/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── voice_service.py
│   └── suggestion_service.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── __init__.py
├── config.py
├── database.py
└── main.py
```
