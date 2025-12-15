import os
os.environ["GRPC_VERBOSITY"] = "ERROR"  # Reduce logging overhead

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)
import streamlit as st
from services.ChatBotModel import chatbot_reply

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
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
# CUSTOM CSS FOR CHAT PAGE
# ============================================
st.markdown(
    """
    <style>
    /* Main chat container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 100%;
    }
    
    /* Chat message styling */
    .stChatMessage {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #e0e7ff;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    
    /* Info boxes in sidebar */
    .sidebar-info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #c7d2fe;
    }
    
    .context-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================
# SESSION STATE
# ============================================
if "bot_chat_history" not in st.session_state:
    st.session_state.bot_chat_history = []

if "resume" not in st.session_state:
    st.session_state.resume = None

if "role" not in st.session_state:
    st.session_state.role = None

if "job_description" not in st.session_state:
    st.session_state.job_description = None

# ============================================
# SIDEBAR - CONTEXT & CONTROLS
# ============================================
with st.sidebar:
    st.title("💬 AI Career Assistant")
    st.markdown("---")
    
    # Context information
    st.markdown("### 📋 Current Context")
    
    has_resume = st.session_state.resume is not None
    has_role = st.session_state.role is not None
    has_jd = st.session_state.job_description is not None
    
    if has_resume:
        st.markdown("<span class='context-badge'>✅ Resume Loaded</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='context-badge' style='background: rgba(239, 68, 68, 0.2); color: #fca5a5;'>❌ No Resume</span>", unsafe_allow_html=True)
    
    if has_role:
        st.markdown(f"<span class='context-badge'>🎯 Role: {st.session_state.role[:20]}...</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='context-badge' style='background: rgba(239, 68, 68, 0.2); color: #fca5a5;'>❌ No Role</span>", unsafe_allow_html=True)
    
    if has_jd:
        st.markdown("<span class='context-badge'>📄 JD Loaded</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='context-badge' style='background: rgba(245, 158, 11, 0.2); color: #fcd34d;'>⚠️ No JD</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # What can I ask section
    st.markdown("### 💡 What Can I Ask?")
    
    with st.expander("📝 Resume Tips", expanded=False):
        st.markdown("""
        - How can I improve my resume?
        - What's missing in my resume?
        - Should I add more projects?
        - How to format my experience section?
        """)
    
    with st.expander("🎯 Job Search", expanded=False):
        st.markdown("""
        - What skills are in demand for [role]?
        - How do I tailor my resume for [company]?
        - What certifications should I pursue?
        - Best companies for [role]?
        """)
    
    with st.expander("🚀 Career Growth", expanded=False):
        st.markdown("""
        - What skills should I learn next?
        - How to transition to [new role]?
        - Career roadmap for [domain]?
        - Salary expectations for [role]?
        """)
    
    with st.expander("🎤 Interview Prep", expanded=False):
        st.markdown("""
        - Common interview questions for [role]?
        - How to answer behavioral questions?
        - Technical interview tips?
        - How to negotiate salary?
        """)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("Home.py")
    
    if st.button("📘 Generate Q&A", use_container_width=True):
        if has_resume:
            st.switch_page("pages/QnA.py")
        else:
            st.error("Please analyze a resume first!")
    
    if st.button("🎤 Mock Interview", use_container_width=True):
        if st.session_state.get("allow_mock", False):
            st.switch_page("pages/MockInterview.py")
        else:
            st.error("Please analyze a resume first!")
    
    if st.button("🔧 Fix Resume", use_container_width=True):
        if has_resume:
            st.switch_page("pages/FixResume.py")
        else:
            st.error("Please analyze a resume first!")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.bot_chat_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Tips
    st.markdown(
        """
        <div class='sidebar-info-box'>
            <strong>💡 Pro Tips:</strong><br>
            • Be specific in your questions<br>
            • Mention your target role for better advice<br>
            • Ask follow-up questions for clarity<br>
            • I only answer career-related questions!
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================
# MAIN CHAT INTERFACE
# ============================================
st.title("💬 AI Career Assistant Chat")

# Welcome message
if not st.session_state.bot_chat_history:
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); 
                    padding: 2rem; border-radius: 16px; margin-bottom: 2rem; 
                    border: 1px solid rgba(102, 126, 234, 0.2);'>
            <h2 style='margin: 0; color: #e0e7ff;'>👋 Welcome to Your AI Career Assistant!</h2>
            <p style='color: #c7d2fe; margin-top: 1rem; line-height: 1.6;'>
                I'm here to help you with:
            </p>
            <ul style='color: #c7d2fe; margin-top: 0.5rem;'>
                <li>📝 Resume improvement and formatting tips</li>
                <li>🎯 Job search strategies and role guidance</li>
                <li>🚀 Skill development and learning paths</li>
                <li>🎤 Interview preparation and career advice</li>
            </ul>
            <p style='color: #94a3b8; margin-top: 1rem; font-size: 0.9rem;'>
                💡 Tip: I have access to your resume and job details (if uploaded), so my advice will be personalized!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Suggested questions
    st.markdown("### 🎯 Quick Start Questions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 How can I improve my resume?", use_container_width=True):
            user_msg = "How can I improve my resume based on my target role?"
            st.session_state.bot_chat_history.append(("You", user_msg))
            bot_response = chatbot_reply(
                user_msg,
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description
            )
            st.session_state.bot_chat_history.append(("AI Bot", bot_response))
            st.rerun()
    
    with col2:
        if st.button("🎯 What skills should I learn?", use_container_width=True):
            user_msg = "What skills should I focus on learning for my target role?"
            st.session_state.bot_chat_history.append(("You", user_msg))
            bot_response = chatbot_reply(
                user_msg,
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description
            )
            st.session_state.bot_chat_history.append(("AI Bot", bot_response))
            st.rerun()
    
    with col3:
        if st.button("🎤 Interview preparation tips?", use_container_width=True):
            user_msg = "What are the key things I should prepare for interviews in my field?"
            st.session_state.bot_chat_history.append(("You", user_msg))
            bot_response = chatbot_reply(
                user_msg,
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description
            )
            st.session_state.bot_chat_history.append(("AI Bot", bot_response))
            st.rerun()
    
    st.markdown("---")

# ============================================
# DISPLAY CHAT HISTORY
# ============================================
for sender, message in st.session_state.bot_chat_history:
    if sender == "You":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(message)

# ============================================
# CHAT INPUT
# ============================================
user_msg = st.chat_input(
    "Ask me anything about your career, resume, skills, or interview prep...",
    key="chat_input"
)

if user_msg:
    # Add user message to history
    st.session_state.bot_chat_history.append(("You", user_msg))
    
    # Get bot response
    with st.spinner("🤔 Thinking..."):
        bot_response = chatbot_reply(
            user_question=user_msg,
            resume=st.session_state.resume,
            role=st.session_state.role,
            job_description=st.session_state.job_description
        )
    
    # Add bot response to history
    st.session_state.bot_chat_history.append(("AI Bot", bot_response))
    
    # Rerun to display new messages
    st.rerun()

# ============================================
# CHAT STATISTICS (if chat has started)
# ============================================
if st.session_state.bot_chat_history:
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        user_messages = len([m for m in st.session_state.bot_chat_history if m[0] == "You"])
        st.metric("💬 Your Questions", user_messages)
    
    with col2:
        bot_messages = len([m for m in st.session_state.bot_chat_history if m[0] == "AI Bot"])
        st.metric("🤖 AI Responses", bot_messages)
    
    with col3:
        total_messages = len(st.session_state.bot_chat_history)
        st.metric("📊 Total Messages", total_messages)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; padding: 1rem 0;'>
        # <p style='font-size: 0.9rem;'>🤖 Powered by Google Gemini AI</p>
        <p style='font-size: 0.8rem;'>💡 I only answer career-related questions. For other topics, please consult appropriate resources.</p>
    </div>
    """,
    unsafe_allow_html=True
)