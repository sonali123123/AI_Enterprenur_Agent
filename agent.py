from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import whisper
import re
import os
import time
import asyncio
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
import torch
import pyttsx3

# App initialization
app = FastAPI()

# Directories for uploads and generated audio
UPLOAD_AUDIO_DIR = Path("uploads/audio")
RESPONSE_AUDIO_DIR = Path("static/audio")
for directory in (UPLOAD_AUDIO_DIR, RESPONSE_AUDIO_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load Whisper model once
whisper_model = whisper.load_model("turbo")

# Initialize TTS engine once
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty("voices")
for v in voices:
    if "male" in v.name.lower() or "male" in v.id:
        tts_engine.setProperty("voice", v.id)
        break

# Device selection for LLM
device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize LLM and parser
llm = OllamaLLM(model="llama3.2:3B", device=device)
parser = StrOutputParser()


# mentor_prompt_text = r"""
# You are an Entrepreneur Mentor Bot providing personalized, topic-specific guidance. Avoid generic responses. Structure every reply as follows:

# 1. **Mentorship Response**: Direct actionable advice for the user's entrepreneurial query.
# 2. **Engagement Question**: A thought-provoking question for deeper reflection.
# 3. **Next Interaction Prompts (3–4)**: Numbered suggestions for follow-up queries.

# ### Example:

# **User:** "I'm planning a sustainable clothing line. Where do I start?"

# **Mentorship Response:** Start by identifying a unique sustainability angle—such as recycled fabrics or zero-waste production. Partner with suppliers who share your environmental values, then create a small capsule collection to validate market interest. Focus on storytelling in your branding to connect with eco-conscious consumers.

# **Engagement Question:** Which sustainability practice resonates most with your vision, and how will you communicate it authentically to customers?

# **Next Interaction Prompts:**
# 1. How can I source affordable recycled materials for my clothing line?
# 2. What marketing strategies work best for eco-friendly fashion brands?
# 3. How do I measure and report my sustainability impact?
# 4. What platforms can I use to sell sustainable products effectively?


# {context}
# """


mentor_prompt_text = r"""
You are an **Entrepreneur Mentor Bot** providing personalized, topic-specific guidance. Avoid generic or example-only replies.

When the user asks an entrepreneurial question, structure your answer exactly as:

1. **Mentorship Response:**  
   [Your direct, actionable advice addressing their specific query.]

2. **Engagement Question:**  
   [A single, thought-provoking question to deepen their reflection.]

3. **Next Interaction Prompts:**  _(List four specific questions the user could ask next)_
   1. [Next user question #1]  
   2. [Next user question #2]  
   3. [Next user question #3]  
   4. [Next user question #4]

If the user’s input is just a greeting or too vague (e.g. “Hello,” “Hi there”), reply with:

1. **Mentorship Response:**  
   Hi there! Could you tell me more about what entrepreneurial challenge or goal you’d like help with today?

2. **Engagement Question:**  
   What stage of your business idea are you at (e.g. brainstorming, prototyping, fundraising)?

3. **Next Interaction Prompts:**  
   1. How can ***I*** define the core problem ***my*** business will solve?  
   2. How do ***I*** identify and describe ***my*** ideal customer?  
   3. How can ***I*** inventory and leverage ***my*** current skills and resources?  
   4. Which foundational step should ***I*** tackle first: market research, product design, or fundraising?

{context}
"""


# Build prompt template with history placeholder
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=mentor_prompt_text),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{query}")
])

# Build chain and wrap with in-memory history
chain = chat_prompt | llm | parser
store: dict[str, ChatMessageHistory] = {}
def get_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversation = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_history,
    input_messages_key="query",
    history_messages_key="history"
)


def parse_response_and_suggestions(raw: str) -> tuple[str, list[str]]:
    """
    Splits the raw response into:
      - main_text: everything before 'Next Interaction Prompts'
      - suggestions: numbered items (1., 2., 3., …) after that phrase
    """
    # 1. Split on “Next Interaction Prompts” (colon optional), case-insensitive
    marker = re.compile(r"Next Interaction Prompts\s*:?\s*", flags=re.IGNORECASE)
    parts = marker.split(raw, maxsplit=1)
    main_text = parts[0].strip()

    suggestions = []
    if len(parts) > 1:
        block = parts[1]
        # 2. Capture each “N. …” block up to the next number or end
        suggestions = re.findall(
            r"\d+\.\s*(.+?)(?=(?:\s*\d+\.|$))",
            block,
            flags=re.DOTALL
        )
        # 3. Normalize whitespace/newlines into single-line suggestions
        suggestions = [s.strip().replace("\n", " ") for s in suggestions if s.strip()]

    return main_text, suggestions



@app.post("/whisper")
async def whisper_endpoint(file: UploadFile = File(...)):
    path = UPLOAD_AUDIO_DIR / file.filename
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
        result = await asyncio.to_thread(whisper_model.transcribe, str(path))
        text = result.get("text", "")
        os.remove(path)
        return JSONResponse({"transcription": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(payload: dict = Body(...), background_tasks: BackgroundTasks = None):
    q = payload.get("query")
    if not q:
        raise HTTPException(status_code=400, detail="Query missing")
    session_id = "default_session"

    # Generate LLM response with history
    result = await asyncio.to_thread(
        conversation.invoke,
        {"query": q},
        {"session_id": session_id}
    )
    
    print(f"Query: {q}")
    response_text = result.get("output") if isinstance(result, dict) else str(result)
    response_text = response_text.replace("\n", "").replace("*", " ").replace("Mentorship Response", "").replace("Engagement Question", "").replace(": ", "").replace("   ", "")  
    print(f"Generated response: {response_text}")

    main_resp, suggestions = parse_response_and_suggestions(response_text)
    print(f"Parsed response: {main_resp}")
    print(f"Parsed suggestions: {suggestions}")


    # Queue TTS generation
    ts = int(time.time() * 1000)
    filename = f"response_{ts}.mp3"
    out_path = RESPONSE_AUDIO_DIR / filename
    background_tasks.add_task(generate_audio_from_response, main_resp, out_path)

    return JSONResponse({
        "response": main_resp,
        "suggestions": suggestions,
        "audio_url": f"http://10.7.0.28:5505/static/audio/{filename}"
    })

# Synchronous TTS worker
def generate_audio_from_response(response_text: str, out_path: Path) -> None:
    tts_engine.save_to_file(response_text, str(out_path))
    tts_engine.runAndWait()
