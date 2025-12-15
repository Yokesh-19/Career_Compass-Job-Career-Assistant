import os
os.environ["GRPC_VERBOSITY"] = "ERROR"  # Reduce logging overhead

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)
import streamlit as st
import asyncio
import edge_tts
import speech_recognition as sr
import time
import os
import tempfile
from pathlib import Path
from services.InterviewModel import start_interview_langchain, continue_interview

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Mock Interview",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# LOAD CSS
# ============================================
def load_css(path):
    try:
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css("assets/style.css")

# ============================================
# CUSTOM CSS
# ============================================
st.markdown(
    """
    <style>
    .interview-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .interview-status {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem;
    }
    
    .status-active {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .stChatMessage {
        animation: slideIn 0.4s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    audio {
        width: 100%;
        margin: 1rem 0;
        border-radius: 8px;
    }
    
    .stop-button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================
# CHECK ACCESS
# ============================================
if "allow_mock" not in st.session_state or not st.session_state.allow_mock:
    st.error("⚠️ You must analyze a resume before entering the mock interview.")
    st.markdown("---")
    if st.button("🏠 Go to Home Page", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# ============================================
# SESSION STATE
# ============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "interview_isOver" not in st.session_state:
    st.session_state.interview_isOver = False
if "current_audio_file" not in st.session_state:
    st.session_state.current_audio_file = None
if "interview_stopped_early" not in st.session_state:
    st.session_state.interview_stopped_early = False

# ============================================
# TTS FUNCTIONS
# ============================================
def generate_speech(text, output_file="interview_audio.mp3"):
    """Generate speech using edge-tts with full error handling"""
    try:
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                time.sleep(0.2)
            except:
                output_file = f"interview_audio_{int(time.time())}.mp3"
        
        async def _generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice="en-GB-RyanNeural",
                rate="+20%",
                volume="+10%"
            )
            await communicate.save(output_file)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate())
            loop.close()
        except:
            asyncio.run(_generate())
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            st.session_state.current_audio_file = output_file
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"🔊 Audio generation error: {str(e)}")
        return False

# ============================================
# SPEECH RECOGNITION
# ============================================
def record_audio():
    """Record audio with maximum clarity and reliability"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.5
    
    try:
        with sr.Microphone(sample_rate=16000) as source:
            status_placeholder = st.empty()
            status_placeholder.info("🎤 Calibrating microphone... Please wait (2 seconds)")
            
            recognizer.adjust_for_ambient_noise(source, duration=2)
            
            status_placeholder.info("🔴 **Recording NOW! Speak clearly...**")
            
            try:
                audio_data = recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=20
                )
                
                status_placeholder.info("⏳ Processing your speech... Please wait")
                
                try:
                    text = recognizer.recognize_google(
                        audio_data,
                        language="en-US",
                        show_all=False
                    )
                    
                    status_placeholder.success(f"✅ **Recognized:** {text}")
                    time.sleep(2)
                    status_placeholder.empty()
                    return text
                    
                except sr.UnknownValueError:
                    status_placeholder.error("❌ Could not understand. Please speak more clearly.")
                    time.sleep(2)
                    status_placeholder.empty()
                    return None
                    
                except sr.RequestError as e:
                    status_placeholder.error(f"❌ Recognition service error: {e}")
                    time.sleep(2)
                    status_placeholder.empty()
                    return None
                    
            except sr.WaitTimeoutError:
                status_placeholder.warning("⏱️ No speech detected. Please try again and speak louder.")
                time.sleep(2)
                status_placeholder.empty()
                return None
                
    except Exception as e:
        st.error(f"❌ Microphone error: {str(e)}")
        st.info("💡 **Troubleshooting:**\n- Check microphone connection\n- Grant browser microphone permission\n- Close other apps using microphone")
        return None

# ============================================
# GENERATE INTERVIEW FEEDBACK
# ============================================
def generate_interview_feedback():
    """Generate feedback based on interview performance"""
    if not st.session_state.chat_history:
        return "No interview data to analyze."
    
    total_questions = len([m for m in st.session_state.chat_history if m[0] == "Interviewer"])
    total_answers = len([m for m in st.session_state.chat_history if m[0] == "Candidate"])
    
    feedback = f"""
## 📊 Interview Performance Summary

**Interview Statistics:**
- Total Questions Asked: {total_questions}
- Total Answers Provided: {total_answers}
- Interview Status: {"Stopped Early" if st.session_state.interview_stopped_early else "Completed"}

**Performance Highlights:**
"""
    
    if total_answers >= 5:
        feedback += "\n- ✅ Good engagement - answered multiple questions"
    elif total_answers >= 3:
        feedback += "\n- ⚡ Moderate engagement - consider practicing more"
    else:
        feedback += "\n- 📝 Limited engagement - more practice recommended"
    
    feedback += """

**Recommendations:**
1. 🎯 Review your answers and identify areas for improvement
2. 📚 Research common questions for your target role
3. 💪 Practice with mock interviews regularly
4. 🗣️ Work on clarity and confidence in delivery
5. ⏱️ Keep answers concise yet comprehensive (2-3 minutes ideal)

**Next Steps:**
- Review the conversation above for self-assessment
- Practice with more mock interviews
- Get feedback from mentors or peers
- Refine your STAR method responses
"""
    
    return feedback

# ============================================
# HEADER
# ============================================
st.markdown(
    """
    <div class='interview-header'>
        <h1 style='margin: 0; font-size: 2.5rem;'>🎤 AI Mock Interview</h1>
        <p style='margin-top: 0.5rem; color: #94a3b8;'>
            Practice with AI-powered voice interview simulation
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================
# STATUS
# ============================================
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.interview_active and not st.session_state.interview_isOver:
        st.markdown("<div class='interview-status status-active'>🔴 Live</div>", unsafe_allow_html=True)
    else:
        st.metric("📊 Status", "Ready" if not st.session_state.interview_isOver else "Ended")

with col2:
    q_count = len([m for m in st.session_state.chat_history if m[0] == "Interviewer"])
    st.metric("❓ Questions", q_count)

with col3:
    a_count = len([m for m in st.session_state.chat_history if m[0] == "Candidate"])
    st.metric("💬 Answers", a_count)

st.markdown("---")

# ============================================
# START INTERVIEW
# ============================================
if not st.session_state.interview_active:
    st.markdown("### 🎯 Start Your Mock Interview")
    
    role = st.text_input(
        "Job Role",
        value=st.session_state.get("role", ""),
        placeholder="e.g., Software Engineer",
        help="Role you're interviewing for"
    )

    if st.button("🚀 Begin Interview", use_container_width=True, type="primary"):
        if role.strip():
            with st.spinner("🤖 Preparing interview..."):
                try:
                    first_question = start_interview_langchain(
                        role.strip(),
                        st.session_state.resume.strip()
                    )
                    
                    st.session_state.chat_history = [("Interviewer", first_question)]
                    st.session_state.interview_active = True
                    st.session_state.interview_stopped_early = False
                    
                    if generate_speech(first_question):
                        st.success("✅ Interview started! Listen to the question below.")
                    else:
                        st.warning("⚠️ Audio generation failed. Please read the question.")
                    
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to start: {str(e)}")
        else:
            st.warning("⚠️ Please enter a job role")

# ============================================
# ACTIVE INTERVIEW
# ============================================
if st.session_state.interview_active:
    st.markdown("### 💬 Interview in Progress")
    
    # Display conversation
    for speaker, message in st.session_state.chat_history:
        if speaker == "Interviewer":
            with st.chat_message("assistant", avatar="🧑‍💼"):
                st.markdown(f"**Interviewer:** {message}")
        else:
            with st.chat_message("user", avatar="🙋"):
                st.markdown(f"**You:** {message}")
    
    # Play latest audio
    if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
        st.markdown("---")
        st.markdown("#### 🔊 Listen to the Question:")
        
        with open(st.session_state.current_audio_file, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
    
    st.markdown("---")
    
    # Record answer or stop interview
    if not st.session_state.interview_isOver:
        st.markdown("### 🎤 Your Turn")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🎙️ Click to Record Your Answer", use_container_width=True, type="primary"):
                user_answer = record_audio()
                
                if user_answer:
                    st.session_state.chat_history.append(("Candidate", user_answer))
                    
                    with st.spinner("🤖 AI is thinking..."):
                        try:
                            ai_response = continue_interview(user_answer)
                            st.session_state.chat_history.append(("Interviewer", ai_response))
                            
                            generate_speech(ai_response)
                            
                            if "not selected" in ai_response.lower() or "selected" in ai_response.lower():
                                st.session_state.interview_isOver = True
                                if "selected" in ai_response.lower():
                                    st.balloons()
                            
                            time.sleep(0.5)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ AI error: {str(e)}")
                else:
                    st.warning("⚠️ No speech detected. Please try again.")
        
        with col2:
            if st.button("🛑 Stop Interview", use_container_width=True, type="secondary"):
                st.session_state.interview_isOver = True
                st.session_state.interview_stopped_early = True
                st.rerun()
        
        with st.expander("💡 Tips"):
            st.markdown("""
            **Before Recording:**
            - Find a quiet space
            - Test microphone
            - Prepare your thoughts
            
            **While Recording:**
            - Speak clearly
            - Normal pace
            - Natural pauses OK
            """)
    
    # Interview ended
    if st.session_state.interview_isOver:
        st.markdown("---")
        st.markdown("### 🏁 Interview Complete!")
        
        # Display feedback
        feedback = generate_interview_feedback()
        st.markdown(feedback)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Interview", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.interview_active = False
                st.session_state.interview_isOver = False
                st.session_state.current_audio_file = None
                st.session_state.interview_stopped_early = False
                st.rerun()
        
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("Home.py")

# ============================================
# TROUBLESHOOTING
# ============================================
if st.session_state.interview_active:
    with st.expander("🔧 Having Issues?"):
        st.markdown("""
        ### Audio Not Playing?
        1. Check device volume
        2. Try clicking the play button manually
        3. Refresh the page
        4. Check browser audio permissions
        
        ### Microphone Not Working?
        1. **Chrome:** Settings → Privacy → Microphone → Allow
        2. **Firefox:** Click 🔒 in address bar → Permissions
        3. Close other apps using microphone (Zoom, Teams, etc.)
        4. Check Windows/Mac microphone settings
        5. Try using Chrome browser (most compatible)
        
        ### Speech Not Recognized?
        1. Speak louder and clearer
        2. Reduce background noise
        3. Use better microphone/headset
        4. Speak in shorter sentences
        5. Wait for "Recording NOW!" message
        """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b;'>"
    # "<p>🤖 Powered by Google Gemini AI & Edge TTS</p>"
    "</div>",
    unsafe_allow_html=True
)