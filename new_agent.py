from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
import whisper
import re
import os
import pyttsx3  # for male voice TTS
import time
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import torch


# App initialization
app = FastAPI()

# Ensure directories exist
UPLOAD_AUDIO_DIR = Path("uploads/audio")
RESPONSE_AUDIO_DIR = Path("responses/audio")
for directory in (UPLOAD_AUDIO_DIR, RESPONSE_AUDIO_DIR, Path("chroma_db")):
    directory.mkdir(parents=True, exist_ok=True)

# Device selection
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")



# Load Whisper model globally
whisper_model = whisper.load_model("turbo")

# PDF loading and splitting setup
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=20,
    length_function=len
)

def load_pdfs(paths: list[str]):
    docs = []
    for p in paths:
        loader = PyMuPDFLoader(file_path=p)
        docs.extend(loader.load())
    return docs

# Load and split once at startup
PDF_PATHS = ["data/book_1.pdf"]
raw_docs = load_pdfs(PDF_PATHS)
chunks = text_splitter.split_documents(raw_docs)
print(f"Loaded and split {len(chunks)} document chunks.")

# Embedding and vectorstore
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    collection_name="my_collection",
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
retriever = vectorstore.as_retriever(k=3)

# LLM and RAG chain setup
llm = ChatOllama(model="llama3.2:3B", temperature=0,device=device)

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

# Prompt to contextualize follow-up questions
context_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, context_prompt
)

mentor_prompt_text = """
## System Prompt

You are an Entrepreneur Mentor Bot, specifically designed to guide aspiring entrepreneurs with personalized, topic-specific advice. Your mentorship role involves providing detailed and actionable recommendations tailored to each user's specific entrepreneurship interests and queries. Avoid generic responses—always prioritize detailed, clear, and practical guidance.

Structure every response in the following way:

1. **Topic-Specific Mentorship Response**  
   - Directly address the user's entrepreneurial query.  
   - Provide practical, specific strategies, action steps, or detailed advice relevant to the user's expressed interest or challenge.

2. **Interactive Engagement Question**  
   - Include a relevant, thought-provoking question related to your response to encourage deeper reflection or continued engagement from the user.

3. **Next Interaction Prompts (3–4)**  
   - Provide three to four concise, clear, and intriguing suggestions for follow-up questions or queries that the user might explore next, related directly to the current entrepreneurial topic being discussed.

---

### Example:

**User:**  
"I'm interested in launching an online food delivery business targeting health-conscious customers. Where should I start?"

**Entrepreneur Mentor Response:**  
"Start by clearly defining your niche within the health-conscious market, such as vegan meals, keto-friendly options, or locally sourced produce. Conduct targeted market research to understand your audience’s dietary preferences, pain points, and spending habits. Develop a minimum viable product (MVP)—a simple menu with limited but appealing options—to test demand and get early feedback. Ensure your branding clearly communicates health and convenience. Set up an efficient online ordering system, possibly leveraging existing platforms initially, and focus early efforts on exceptional customer service and delivery logistics."

**Interactive Engagement Question:**  
"What specific type of health-conscious customer are you most excited to serve, and how do you envision your brand uniquely meeting their needs?"

**Next Interaction Prompts:**  
- "What steps should I take to validate the demand for my health-focused food delivery concept?"  
- "How can I effectively market my online food delivery business to attract health-conscious customers?"  
- "Could you advise me on managing logistics and maintaining food quality during delivery?"  
- "What pricing strategies work best for premium, health-focused meal delivery services?"

{context}
"""
# mentor_prompt_text = """
# ## System Prompt

# You are an Entrepreneur Mentor Bot, specifically designed to guide aspiring entrepreneurs with personalized, topic‑specific advice. Your mentorship role involves providing detailed and actionable recommendations tailored to each user’s specific entrepreneurship interests and queries. Avoid generic responses—always prioritize detailed, clear, and practical guidance.

# Whenever a user asks a question, reply with a JSON object containing exactly three keys:

# 1. **response**  
#    A in‑depth, topic‑specific mentorship response that directly addresses the user’s query and offers concrete strategies or action steps.

# 2. **interactive_engagement_question**  
#    A single, thought‑provoking question that invites the user to reflect or share more detail.

# 3. **suggestions**  
#    An array of **3 to 4** concise, clear, on‑topic follow‑up question prompts (each ending with a question mark) that the user might ask next.

# ---  
# ### Example

# **User:**  
# "I'm interested in launching an online food delivery business targeting health‑conscious customers. Where should I start?"

# **Assistant (output JSON):**  
# ```json
# {
#   "response": "To launch your health‑focused food delivery service, begin by defining a clear niche—such as organic vegan bowls, keto snack packs, or locally sourced smoothie kits. Conduct targeted market research via surveys and focus groups to pinpoint your audience’s top pain points and flavor preferences. Build a minimum viable product (MVP) menu with 3–5 signature items to test demand. Establish partnerships with local suppliers for fresh ingredients, and choose a delivery partner or build an in‑house logistics system that ensures meals arrive fresh. Finally, craft branding that emphasizes both health benefits and convenience, and pilot your offering in one neighborhood before scaling.",
#   "interactive_engagement_question": "Which specific dietary niche (e.g., vegan, keto, paleo) excites you most, and why?",
#   "suggestions": [
#     "What steps can I take to validate demand for my chosen dietary niche?",
#     "How should I structure pricing to balance affordability and profitability?",
#     "Which marketing channels will best reach health‑conscious customers?",
#     "What operational challenges should I prepare for in meal preparation and delivery?"
#   ]
# }

# {context}
# """



qa_prompt = ChatPromptTemplate.from_messages([
    ("system", mentor_prompt_text),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])
question_chain = create_stuff_documents_chain(llm, qa_prompt)

# Build RAG chain
rag = create_retrieval_chain(history_aware_retriever, question_chain)

# Session history management
store: dict[str, BaseChatMessageHistory] = {}

def get_history(sid: str) -> BaseChatMessageHistory:
    if sid not in store:
        store[sid] = ChatMessageHistory()
    return store[sid]

conversation = RunnableWithMessageHistory(
    rag,
    get_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

TMP_AUDIO_DIR = Path("static/audio")
TMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/whisper")
async def whisper_endpoint(file: UploadFile = File(...)):
    filename = UPLOAD_AUDIO_DIR / file.filename
    try:
        with open(filename, "wb") as f:
            f.write(await file.read())
        result = whisper_model.transcribe(str(filename))
        text = result.get("text", "")
        print(f"Transcription: {text}")
        os.remove(filename)
        # Return transcription result and detected language
        return JSONResponse(content={
            "transcription": text
        })
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {e}")


def parse_response_and_suggestions(raw: str) -> tuple[str, list[str]]:
    """
    Splits the raw response into:
      - main_text: everything before 'Next Interaction Prompts:'
      - suggestions: numbered items (1., 2., 3., …) after that phrase
    """
    # 1. Partition at the literal phrase (case-insensitive)
    marker = re.compile(r"Next Interaction Prompts\s*:", flags=re.IGNORECASE)
    split_result = marker.split(raw, maxsplit=1)
    main_text = split_result[0].strip()

    suggestions: list[str] = []
    if len(split_result) > 1:
        prompts_block = split_result[1]
        # 2. Find all occurrences of “number.” followed by text up to the next number or end
        #    This regex captures the text after each digit+dot
        suggestions = re.findall(r"\d+\.\s*([^(\d+\.)]+)", prompts_block)
        # 3. Clean up whitespace
        suggestions = [s.strip() for s in suggestions if s.strip()]

    return main_text, suggestions

@app.post("/ask")
async def ask(query: dict = Body(...), background_tasks: BackgroundTasks = None):
    try:
        print(f"Received query: {query}")
        q = query.get("query")
        if not q:
            raise JSONResponse(status_code=400, content={"error": "Query text is missing"})
        
        session_id = "default_session" 

        message = f"Query: {q}"
        
        print(message)

        # Prepare chat input
        input_message = message
        response = generate_response(input_message,session_id)
        response = response.replace("Interactive Engagement Question:","" ).replace("\n", "")
        print(f"Response from conversational_rag_chain: {response}")

        print(f"Generated response: {response}")

        # 2. Parse out the pure response vs. suggestions
        main_resp, suggestions = parse_response_and_suggestions(response)
        
        print(f"Main response: {main_resp}")
        print(f"Suggestions: {suggestions}")

        # Generate audio response
        audio_path= generate_audio_from_response(main_resp)
        print("Audio response generated.")
        print(store)
        
       
        audio_url = f"http://10.7.0.28:5505/static/audio/{audio_path.name}"
        return JSONResponse(
            content={
                "response": main_resp,
                "suggestions": suggestions,
                "audio_url": f"http://10.7.0.28:5505/static/audio/{audio_path.name}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# TTS engine setup
engine = pyttsx3.init()
voices = engine.getProperty("voices")
# Choose a male voice (first male found)
for v in voices:
    if "male" in v.name.lower() or "male" in v.id:
        engine.setProperty("voice", v.id)
        break


def generate_response(query_text,session_id="default_session"):
    """Generate a response based on the query."""
    try:
        
        # Ensure the session ID is passed correctly
        response = conversation.invoke(
            {'input': query_text},
            config={'session_id': session_id}  # Correct the dictionary key
        )["answer"]

        # Normalize the response text
        response_cleaned = response.replace("\n", "").replace("*", " ")
        print(f"Generated response: {response_cleaned}")
        return response_cleaned
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        return {"error": str(e)}

# Initialize once at startup (global)
# fastpitch = TTS(model_name="tts_models/en/ljspeech/fast_pitch")  # Fully-parallel TTS model with pitch prediction :contentReference[oaicite:1]{index=1}
TMP_AUDIO_DIR = Path("static/audio")

# def generate_audio_from_response(response_text: str) -> Path:
#     """
#     Synthesize response_text using FastPitch and save to a .wav file.
#     Returns the Path to the generated audio.
#     """
#     timestamp = int(time.time() * 1000)
#     out_path = TMP_AUDIO_DIR / f"response_{timestamp}.wav"

#     # Run synthesis (this blocks until file is written)
#     fastpitch.tts_to_file(text=response_text, file_path=str(out_path))
#     return out_path

engine = pyttsx3.init()
voices = engine.getProperty("voices")
for v in voices:
    if "male" in v.name.lower() or "male" in v.id:
        engine.setProperty("voice", v.id)
        break

def generate_audio_from_response(response_text: str) -> Path:
    """
    Synthesize `response_text` using pyttsx3 into an MP3
    and return the Path to the saved file.
    """
    # choose filename
    ts = int(time.time() * 1000)
    out_path = TMP_AUDIO_DIR / f"response_{ts}.mp3"

    # queue up the save
    engine.save_to_file(response_text, str(out_path))
    engine.runAndWait()    # perform synthesis & write file

    return out_path
