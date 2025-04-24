# AI Entrepreneur Mentor Chatbot

An AI chatbot that provides entrepreneurship mentorship with text and voice interaction, using FastAPI, Llama 3.2, and Streamlit.

## Features

- **Text and Voice Interaction**: Communicate with the chatbot using text or voice
- **Topic-Specific Entrepreneurship Responses**: Get focused advice on business topics
- **Interactive Q&A with Follow-up Suggestions**: Receive contextual follow-up questions
- **Voice Transcription**: Convert voice queries to text using OpenAI Whisper
- **Text-to-Speech**: Convert AI responses to audio using pyttsx3
- **Dual Interface**: FastAPI backend with Streamlit frontend

## Technical Stack

- **Backend**: FastAPI with Pydantic
- **Frontend**: Streamlit web interface
- **AI Model**: Llama 3.2 (3B parameters) running locally via Ollama
- **Voice Processing**:
  - Speech-to-Text: OpenAI Whisper (turbo model)
  - Text-to-Speech: pyttsx3 with male voice
- **Memory**: In-memory conversation history using LangChain

## Setup Instructions

### Prerequisites

- Python 3.8+
- Ollama with Llama 3.2 model installed
- CUDA-compatible GPU (optional, for faster inference)

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

4. Install and run Ollama:
   - Follow instructions at [Ollama.ai](https://ollama.ai/)
   - Pull the Llama 3.2 model: `ollama pull llama3.2:3B`

5. Start the FastAPI backend:
   ```
   uvicorn agent:app --host 0.0.0.0 --port 5505
   ```

6. Start the Streamlit frontend in a separate terminal:
   ```
   streamlit run streamlit_app.py
   ```

7. Access the application:
   - Open your browser and go to the URL shown in the Streamlit terminal output (typically http://localhost:8501)

## API Endpoints

- **POST /ask**: Process text input and return AI response with suggestions and audio URL
- **POST /whisper**: Process voice input (audio file) and return transcribed text

## Project Structure

```
├── agent.py                # FastAPI backend with LLM integration
├── streamlit_app.py        # Streamlit frontend interface
├── static/                 # Static files directory
│   └── audio/              # Generated audio responses
└── uploads/                # Temporary upload directory
    └── audio/              # Uploaded audio files for transcription
```

## How It Works

1. **Text Interaction**:
   - User enters a question in the Streamlit interface
   - Question is sent to the FastAPI backend
   - LLM generates a structured response with follow-up suggestions
   - Response is converted to audio using pyttsx3
   - Text response and audio URL are returned to the frontend

2. **Voice Interaction**:
   - User records audio in the Streamlit interface
   - Audio is sent to the Whisper endpoint for transcription
   - Transcribed text is processed by the LLM
   - Response follows the same path as text interaction

## Prompt Structure

The AI mentor provides responses in a structured format:

1. **Mentorship Response**: Direct actionable advice for the user's query
2. **Engagement Question**: A thought-provoking question for deeper reflection
3. **Next Interaction Prompts**: Four specific follow-up questions the user could ask next
