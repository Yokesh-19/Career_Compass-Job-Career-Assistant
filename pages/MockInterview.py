import streamlit as st
import asyncio
import edge_tts
import speech_recognition as sr
from services.InterviewModel import start_interview_langchain, continue_interview

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="AI Mock Interview", page_icon="🤖", layout="centered")
st.title("🤖 AI Mock Interview")

if "allow_mock" not in st.session_state or not st.session_state.allow_mock:
    st.error("⚠️ You must analyze a resume before entering the mock interview.")
    st.stop()

st.write("Get interviewed by an AI for your desired role!")

# ---------------- Session State ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "interview_isOver" not in st.session_state:
    st.session_state.interview_isOver = False

# ----------------- Edge TTS Function -----------------
async def speak(text, filename="qn.mp3", voice="en-GB-RyanNeural", rate="+25%"):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(filename)

def speak_sync(text, filename="qn.mp3"):
    asyncio.run(speak(text, filename))

# ----------------- Speech-to-Text Function -----------------
def get_audio_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Please speak now... Max 15 seconds")
        # audio = r.listen(source, phrase_time_limit=15)
        audio = r.record(source, duration=15)
    try:
        text = r.recognize_google(audio)
        st.success(f"🗣 You said: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Sorry, could not understand audio")
        return ""
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return ""

# ---------------- Input Role ----------------
role = st.text_input(
    "Enter the job role:",
    value=st.session_state.get('role', ''),
    placeholder="e.g., Java Developer",
    disabled=st.session_state.interview_active
)

# ---------------- Start Interview ----------------
if st.button("Start Interview", disabled=st.session_state.interview_active):
    if role.strip():
        with st.spinner("Starting the interview..."):
            try:
                first_q = start_interview_langchain(role.strip(), st.session_state.resume.strip())
                st.session_state.chat_history = [("Interviewer", first_q)]
                st.session_state.interview_active = True
                speak_sync(first_q)
            except Exception as e:
                st.error(f"Failed to start interview: {e}")
    else:
        st.warning("Please enter a role before starting.")

# ---------------- Display Chat History ----------------
if st.session_state.interview_active:
    st.subheader("Interview Conversation")

    for speaker, text in st.session_state.chat_history:
        if speaker == "Interviewer":
            with st.chat_message("Interviewer", avatar="🧑‍💼"):
                st.write(text)
        else:
            with st.chat_message("Candidate", avatar="🙋"):
                st.write(text)

    st.markdown(
        """
        <style>
        audio {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.audio("qn.mp3", autoplay=True)

    # ---------------- Candidate Voice Input ----------------
    if not st.session_state.interview_isOver:
        if st.button("🎤 Record Answer"):
            candidate_answer = get_audio_input()
            if candidate_answer:
                st.session_state.chat_history.append(("Candidate", candidate_answer))

                with st.spinner("AI is thinking..."):
                    reply = continue_interview(candidate_answer)

                st.session_state.chat_history.append(("Interviewer", reply))
                speak_sync(reply)

                if "not selected" in reply.lower() or "selected" in reply.lower():
                    st.success("Interview Ended")
                    st.session_state.interview_isOver = True

                st.rerun()

    if st.session_state.interview_isOver:
        if st.button("End Interview"):
            st.session_state.chat_session = None
            st.session_state.chat_history = []
            st.session_state.interview_active = False
            st.session_state.interview_isOver = False
            st.rerun()