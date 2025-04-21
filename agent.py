
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from fastapi.responses import JSONResponse
from gtts import gTTS
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Body, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from deep_translator import GoogleTranslator


import whisper
import time
import os







app = FastAPI()



whisper_model = whisper.load_model("turbo")  # Whisper model for transcription



# This will load the PDF files
def load_multiple_pdfs(file_paths):
    all_docs = []
    for file_path in file_paths:
        # Creating a PyMuPDFLoader object for each PDF
        loader = PyMuPDFLoader(file_path=file_path)
        
        # Loading the PDF file
        docs = loader.load()
        
        # Appending the loaded document to the list
        all_docs.extend(docs)
    
    # returning all the loaded documents
    return all_docs

# This will split the text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=20,
    length_function=len
)     
# Responsible for splitting the documents into several chunks
def split_docs(documents):
    
    chunks = text_splitter.split_documents(documents=documents)
    
    # returning the document chunks
    return chunks



# Get current date and time
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"Current date and time: {current_datetime}")

pdf_files = [
    r"data\book_1.pdf",
    r"data\book_2.pdf",
    r"data\book_3.pdf"
]
docs = load_multiple_pdfs(file_paths=pdf_files)
documents = split_docs(documents=docs)

llm = ChatOllama(model="llama3.2:3B", temperature=0)

print(f"Loaded {len(documents)} documents from the folder.")
 

splits = text_splitter.split_documents(documents)
print(f"Split the documents into {len(splits)} chunks.")

# This will create the embeddings
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
document_embeddings = embedding_function.embed_documents([split.page_content for split in splits])
#print(document_embeddings[0][:5])

# This will create the vector store
collection_name = 'my_collection'
vectorstore = Chroma.from_documents(
    collection_name=collection_name,
    documents=splits,
    embedding=embedding_function,
    persist_directory="./chroma_db"
)
print("Vectorstore created and persisted to './chroma_db'")

retriever = vectorstore.as_retriever(k=3)

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)



test_qa_pr_sh = """
## System Prompt

You are an expert entrepreneurship mentor with deep experience guiding founders from ideation through launch and growth. 
Your role is to act as a personalized coach—never generic—tailoring every response to the user’s unique situation.
Always:
 • Move from broad concepts to concrete, actionable steps.
 • Offer best practices, real‑world examples, and “mentor‑style” guidance.
 • Maintain a supportive, motivational tone.
 • End with 3–4 suggested follow‑up questions the user can ask next.



##  User Prompt

Context:
• Current topic: <e.g. “Validating my business idea in a competitive market”>
• User profile: <e.g. “Early‑stage founder with prototype but no paying customers”>

Task:
1. Provide a structured response that:
   a. Starts with an overview of the concept at a high level.  
   b. Narrows down to specific tactics or steps the user can take right now.  
   c. Highlights 2–3 best practices or pitfalls to avoid.  

2. Embed an interactive Q&A:
   • Ask clarifying questions where appropriate.  
   • Suggest 3–4 “Next Interaction Prompts” at the end, e.g.:  
     – “Would you like tips on pricing strategies?”  
     – “Shall we explore customer interview frameworks?”  
     – “Interested in funding options for this stage?”  
     – “Need advice on building a minimum viable product?”  

User’s input:
“<The user’s actual question or scenario here>”


{context}"""





qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", test_qa_pr_sh),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)





 #Chat history store for maintaining session histories
store = {}



rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create chat history for a session."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

UPLOAD_AUDIO_DIR = r"Upload_audio"
RESPONSE_AUDIO_DIR = r"Responses_audio"



# Whisper Endpoint
@app.post("/whisper")
async def whisper_endpoint(language: str,file: UploadFile = File(...)):
    
    
# Initialize Whisper model
    whisper_model = whisper.load_model("turbo")  # Specify weights_only=True if needed
    try:

        
        # Save the audio file temporarily
        temp_filename = f"{file.filename}"
        file_path = os.path.join(UPLOAD_AUDIO_DIR , temp_filename)

        
        with open(file_path, "wb") as f:
             f.write(await file.read())

        # Transcribe the audio file with automatic language detection
        result = whisper_model.transcribe(file_path,language = language )
        
        transcription_text = result.get("text", "")
        print(f"Text:{transcription_text}")
        
        # Delete the temporary file
        os.remove(file_path)
        
        # Return transcription result and detected language
        return JSONResponse(content={
            "transcription": transcription_text
        })
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {e}")




app.mount("/static", StaticFiles(directory="audio_files"), name="static")


@app.post("/ask")
async def ask(
    lang: str ,
    query: dict = Body(...),
    
    
    background_tasks: BackgroundTasks = None
):
    try:
        print(query)
        query_text = query.get("query", "")
        if not query_text:
            return JSONResponse(status_code=400, content={"error": "Query text is missing"})
        
        print(f"Received query: {query_text}")
        


        session_id = "default_session"  # Can be replaced with a unique ID for each user


        message = f"Query: {query_text}"
        
        print(message)
                    


        # Prepare chat input
        input_message = message
        translated_response= None

        
       
        response = generate_response(input_message,lang, session_id)
        print(f"Response from conversational_rag_chain: {response}")

        print(f"Generated response: {response}")

        # Generate audio response
        response_audio_path, translated_response = generate_audio_from_response(response,lang)
        print("Audio response generated.")
        print(store)
        

        # # Return audio response
        # return FileResponse(
        #     response_audio_path,
        #     media_type="audio/mpeg",
        #     filename="response.mp3"
        # )
    
        audio_url = f"http://10.7.0.28:5505/static/{os.path.basename(response_audio_path)}"
        return JSONResponse(content={"response": translated_response, "audio_url": audio_url})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



def transcribe_audio(audio_path):
    """Transcribe audio to text."""
    result = whisper_model.transcribe(audio_path, language='en')
    return result.get("text", "").strip()

def generate_response(query_text,lang, session_id="default_session"):
    """Generate a response based on the query."""
    try:
        # Translate query_text to English if not already in English
        if lang != "en":
            query_text = GoogleTranslator(source=lang, target="en").translate(query_text)
            print(lang)
            print(f"Translated query_text to English: {query_text}")

        print(f"Invoking conversational_rag_chain with session_id: {session_id}")

      
        

        # Ensure the session ID is passed correctly
        response = conversational_rag_chain.invoke(
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



def generate_audio_from_response(response_text,input_lang):
    """Generate audio from text using gTTS."""
    print(input_lang)
    response_audio_path = os.path.join("audio_files", f"response_{int(time.time())}.mp3")
    response_text =  GoogleTranslator(target=input_lang).translate(response_text)
    print(response_text)
    tts = gTTS(text=response_text, lang=input_lang, slow=False)
    tts.save(response_audio_path)
    return response_audio_path, response_text

