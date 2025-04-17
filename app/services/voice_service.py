import io
import logging
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
from typing import Tuple, Optional

from app.config import VOICE_LANGUAGE, VOICE_SLOW

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.language = VOICE_LANGUAGE
        self.slow = VOICE_SLOW
        self.recognizer = sr.Recognizer()
    
    def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using Google Text-to-Speech."""
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_filename = temp_file.name
            
            # Generate speech
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(temp_filename)
            
            # Read the file as bytes
            with open(temp_filename, "rb") as audio_file:
                audio_content = audio_file.read()
            
            # Clean up the temporary file
            os.unlink(temp_filename)
            
            return audio_content
        
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {str(e)}")
            raise
    
    def speech_to_text(self, audio_data) -> Tuple[bool, Optional[str]]:
        """Convert speech to text using Google Speech Recognition."""
        try:
            # Convert the audio data to an AudioData object
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            
            # Use Google Speech Recognition to convert speech to text
            text = self.recognizer.recognize_google(audio, language=self.language)
            
            return True, text
        
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return False, "I couldn't understand the audio. Please try again."
        
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {str(e)}")
            return False, "There was an issue with the speech recognition service. Please try again later."
        
        except Exception as e:
            logger.error(f"Error in speech-to-text conversion: {str(e)}")
            return False, f"An error occurred: {str(e)}"

# Create a singleton instance
voice_service = VoiceService()
