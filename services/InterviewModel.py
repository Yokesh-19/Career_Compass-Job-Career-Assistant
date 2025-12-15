import os
os.environ["GRPC_VERBOSITY"] = "ERROR"  # Reduce logging overhead

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
from services.api_utils import with_rate_limit

load_dotenv()

# Use cheaper model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.4,
    max_tokens=300  # Shorter responses
)

# NO MORE LANGGRAPH! Direct conversation tracking in session state
@with_rate_limit
def start_interview_langchain(job_role, resume_text):
    # Truncate resume
    resume_text = resume_text[:2000]
    
    prompt = f"""You're a professional interviewer. Start a mock interview.

Role: {job_role}
Resume summary: {resume_text[:1000]}

Rules:
- Ask ONE question at a time
- 5-7 questions total
- End with "selected" or "not moving forward"
- Be concise (under 100 words)

Introduce yourself briefly and ask first question."""

    response = llm.invoke(prompt)
    return response.content

@with_rate_limit
def continue_interview(candidate_answer):
    """Continue interview with conversation history"""
    
    # Get history from session state
    if "interview_history" not in st.session_state:
        st.session_state.interview_history = []
    
    # Add to history
    st.session_state.interview_history.append(f"Candidate: {candidate_answer}")
    
    # Build conversation context (last 3 exchanges only!)
    context = "\n".join(st.session_state.interview_history[-6:])
    
    prompt = f"""Continue the interview. Previous conversation:

{context}

Respond with next question or conclusion. Keep under 100 words."""

    response = llm.invoke(prompt)
    
    # Add to history
    st.session_state.interview_history.append(f"Interviewer: {response.content}")
    
    return response.content