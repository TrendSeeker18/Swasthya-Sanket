import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3

# Try to import Firestore (optional)
try:
    from google.cloud import firestore
except ImportError:
    firestore = None
    st.warning("⚠ Firestore not installed — skipping database features.")

# ----------------- CONFIGURE GEMINI API -----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ----------------- TEXT-TO-SPEECH ENGINE -----------------
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # Speed of speech

# ----------------- SYSTEM PROMPT -----------------
SYSTEM_PROMPT = """
You are Swasthya Sanket – an AI Health Assistant for ASHA workers.
You must reply in simple Hindi. If user asks in English, respond bilingually (English + Hindi).
Answer about NCDs (like diabetes, hypertension, heart disease, etc.), lifestyle tips, risk prevention,
and daily routines for rural areas. Be empathetic and practical.
"""

# ----------------- FUNCTIONS -----------------


def speak_text(text):
    try:
        engine.endLoop()  # ✅ Stop any previous loop safely
    except Exception:
        pass
    engine.say(text)
    engine.runAndWait()


def get_gemini_response(query):
    """Send query to Gemini model"""
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\nUser: {query}")
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

    # Chat history
    if "history" not in st.session_state:
        st.session_state.history = []

    # ----------------- USER INPUT SECTION -----------------
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

    # ----------------- CHATBOT RESPONSE -----------------
    if st.button("पूछें") or user_input:
        if user_input.strip():
            bot_response = get_gemini_response(user_input)
            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("Swasthya Sanket", bot_response))
            st.success(bot_response)
            speak_text(bot_response)
        else:
            st.warning("कृपया पहले कुछ लिखिए या बोलिए।")

    # ----------------- SHOW CHAT HISTORY -----------------
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
