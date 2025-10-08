import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import threading
import time
import langdetect  # For language detection

# ----------------- OPTIONAL FIRESTORE -----------------
try:
    from google.cloud import firestore
except ImportError:
    firestore = None
    st.warning("⚠ Firestore not installed — skipping database features.")

# ----------------- CONFIGURE GEMINI API -----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ----------------- TEXT-TO-SPEECH ENGINE (cached) -----------------


@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    return engine


engine = get_tts_engine()
voices = engine.getProperty("voices")

# Prefer Hindi voice if available
for voice in voices:
    if "hindi" in voice.name.lower() or "hi" in voice.id.lower():
        engine.setProperty("voice", voice.id)
        break

# ----------------- SYSTEM PROMPT -----------------
SYSTEM_PROMPT = """
You are Swasthya Sanket – an AI Health Assistant for ASHA workers.
If the user speaks Hindi, reply only in simple Hindi.
If the user speaks English, reply bilingually (English + Hindi).
Focus on NCDs, lifestyle tips, risk prevention, and practical rural advice.
Be empathetic and easy to understand.
"""

# ----------------- FUNCTIONS -----------------


def detect_language(text):
    """Detect language (hi or en)"""
    try:
        return langdetect.detect(text)
    except:
        return "en"


def clean_text(text):
    """Remove special characters and Markdown for TTS"""
    return (
        text.replace("*", "")
            .replace("#", "")
            .replace("**", "")
            .replace("_", "")
            .replace("`", "")
            .replace("🤖", "")
            .replace("🧠", "")
            .strip()
    )


def speak_text(text, lang="en"):
    """Speak response asynchronously (so Streamlit doesn’t freeze)"""
    def run_speech():
        try:
            engine.stop()
            text_to_speak = clean_text(text)

            # Switch voice dynamically
            if lang == "hi":
                for v in voices:
                    if "hindi" in v.name.lower() or "hi" in v.id.lower():
                        engine.setProperty("voice", v.id)
                        break
            else:
                # default English voice
                engine.setProperty("voice", voices[0].id)

            engine.say(text_to_speak)
            engine.runAndWait()
        except Exception as e:
            st.warning(f"Speech error: {e}")

    threading.Thread(target=run_speech, daemon=True).start()


def get_gemini_response(query, lang):
    """Send query to Gemini model with language context"""
    if lang == "hi":
        prompt = f"{SYSTEM_PROMPT}\nUser asked in Hindi: {query}\nRespond only in simple Hindi."
    else:
        prompt = f"{SYSTEM_PROMPT}\nUser asked in English: {query}\nRespond in both English and Hindi."

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "माफ कीजिए, मैं अभी उत्तर देने में असमर्थ हूँ।"

# ----------------- MAIN APP -----------------


def main():
    st.set_page_config(
        page_title="🧠 Swasthya Sanket Chatbot", layout="centered")
    st.title("🧠 Swasthya Sanket - स्वास्थ्य संकेत")
    st.markdown("#### आपका स्वास्थ्य साथी (Your Health Partner)")

    if "history" not in st.session_state:
        st.session_state.history = []

    # Input area
    col1, col2 = st.columns(2)
    user_input = ""

    with col1:
        user_input = st.text_input(
            "Type your question 👇",
            placeholder="जैसे - मुझे डायबिटीज से बचने के उपाय बताइए..."
        )

    with col2:
        if st.button("🎙 Voice Input"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎤 बोलिए... सुन रहा हूँ")
                audio = recognizer.listen(source)
                try:
                    text = recognizer.recognize_google(audio, language="hi-IN")
                    user_input = text
                    st.success(f"आपने कहा: {text}")
                except Exception:
                    st.error("⚠ आपकी आवाज़ समझ नहीं आई, कृपया दुबारा बोलें।")

    # Chatbot response
    if st.button("पूछें") or user_input:
        if user_input.strip():
            lang = detect_language(user_input)
            bot_response = get_gemini_response(user_input, lang)
            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("Swasthya Sanket", bot_response))
            st.success(bot_response)
            speak_text(bot_response, lang)
        else:
            st.warning("कृपया पहले कुछ लिखिए या बोलिए।")

    # Chat history
    if st.session_state.history:
        st.markdown("---")
        for role, msg in reversed(st.session_state.history):
            if role == "You":
                st.markdown(f"🧑 **{role}:** {msg}")
            else:
                st.markdown(f"🤖 **{role}:** {msg}")


# ----------------- RUN APP -----------------
if __name__ == "__main__":
    main()
