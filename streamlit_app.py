import streamlit as st
import requests
import tempfile
import os

# Configure your FastAPI base URL
API_BASE = "http://10.7.0.28:5505"

st.set_page_config(
    page_title="Entrepreneur Mentor",
    page_icon="🤝",
    layout="centered",
)

st.title("🤝 Entrepreneur Mentor Bot")
st.markdown(
    """
    Ask your entrepreneurial questions in text or audio, and get personalized guidance, follow-up prompts, and even a TTS audio reply!
    """
)



# --- TAB SELECTION ---
tab = st.sidebar.radio("Mode", ["Text Query", "Audio Query"])



if tab == "Text Query":
    st.subheader("💬 Text Query")
    user_input = st.text_area("Enter your question here:", height=100)
    if st.button("Ask Mentor"):
        if not user_input.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Fetching advice…"):
                resp = requests.post(
                    f"{API_BASE}/ask",
                    json={"query": user_input},
                    timeout=60,
                )
            if resp.status_code != 200:
                st.error(f"API Error: {resp.text}")
            else:
                data = resp.json()
                st.markdown("**Mentor Response:**")
                st.write(data["response"])
                if data.get("suggestions"):
                    st.markdown("**Follow-up Prompts:**")
                    for idx, s in enumerate(data["suggestions"], 1):
                        st.write(f"{idx}. {s}")
                if data.get("audio_url"):
                    st.audio(data["audio_url"])

else:
    st.subheader("🎤 Audio Query")
    st.markdown("Record your question, then click **Transcribe & Ask**.")
    audio_bytes = st.audio_input(
        "Record your question" 
    )
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("Transcribe & Ask"):
            with st.spinner("Transcribing and asking…"):
                # 1) Upload to /whisper
                files = {"file": ("query.wav", audio_bytes, "audio/wav")}
                tresp = requests.post(f"{API_BASE}/whisper", files=files, timeout=60)
                if tresp.status_code != 200:
                    st.error(f"Transcription Error: {tresp.text}")
                else:
                    text = tresp.json().get("transcription", "")
                    st.markdown("**Transcription:**")
                    st.write(text)

                    # 2) Send transcription to /ask
                    aresp = requests.post(
                        f"{API_BASE}/ask",
                        json={"query": text},
                        timeout=60,
                    )
                    if aresp.status_code != 200:
                        st.error(f"Asking Error: {aresp.text}")
                    else:
                        data = aresp.json()
                        st.markdown("**Mentor Response:**")
                        st.write(data["response"])
                        if data.get("suggestions"):
                            st.markdown("**Follow-up Prompts:**")
                            for idx, s in enumerate(data["suggestions"], 1):
                                st.write(f"{idx}. {s}")
                        if data.get("audio_url"):
                            st.audio(data["audio_url"])

# --- STYLING ---
st.markdown(
    """
    <style>
    .stButton>button { background-color: #4CAF50; color: white; }
    .stButton>button:hover { background-color: #45a049; }
    .stTextArea textarea { border: 1px solid #4CAF50; }
    </style>
    """,
    unsafe_allow_html=True,
)