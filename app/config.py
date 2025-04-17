import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "entrepreneur_chatbot")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# AI Model configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b")

# Voice service configuration
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "en")
VOICE_SLOW = os.getenv("VOICE_SLOW", "False").lower() == "true"

# Application configuration
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
MAX_SUGGESTIONS = int(os.getenv("MAX_SUGGESTIONS", "4"))

# Entrepreneurship topics
ENTREPRENEURSHIP_TOPICS = [
    "business model canvas",
    "startup funding",
    "market research",
    "product development",
    "customer acquisition",
    "scaling strategies",
    "pitch deck creation",
    "financial planning",
    "team building",
    "competitive analysis",
    "intellectual property",
    "business registration",
    "marketing strategies",
    "sales techniques",
    "investor relations",
    "bootstrapping",
    "venture capital",
    "angel investing",
    "business plan development",
    "minimum viable product",
    "user experience",
    "customer feedback",
    "pivot strategies",
    "exit strategies",
    "business valuation",
]
