from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import router as api_router
from app.database import create_tables

# Create FastAPI app
app = FastAPI(
    title="AI Entrepreneur Mentor Chatbot",
    description="An AI chatbot that provides entrepreneurship mentorship with text and voice interaction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {
        "message": "AI Entrepreneur Mentor Chatbot API",
        "docs": "/docs",
        "endpoints": {
            "text": "/api/text",
            "voice": "/api/voice",
            "suggestions": "/api/suggestions"
        }
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
