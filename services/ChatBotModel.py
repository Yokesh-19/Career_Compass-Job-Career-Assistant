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

# Initialize LLM with cheaper model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.4,
    max_tokens=500  # Limit output tokens
)

# Simple cache using session state
def get_cached_response(cache_key):
    if "chatbot_cache" not in st.session_state:
        st.session_state.chatbot_cache = {}
    return st.session_state.chatbot_cache.get(cache_key)

def set_cached_response(cache_key, response):
    if "chatbot_cache" not in st.session_state:
        st.session_state.chatbot_cache = {}
    # Limit cache size
    if len(st.session_state.chatbot_cache) > 50:
        st.session_state.chatbot_cache.clear()
    st.session_state.chatbot_cache[cache_key] = response

@with_rate_limit
def chatbot_reply(user_question, resume=None, role=None, job_description=None):
    """AI Career Assistant with caching"""
    
    # Create cache key
    cache_key = f"{user_question[:100]}_{role}_{hash(str(resume)[:200] if resume else '')}"
    
    # Check cache first
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    # Truncate inputs to save tokens
    context_parts = []
    if resume:
        context_parts.append(f"Resume: {resume[:1500]}")  # Reduced from 3000
    if role:
        context_parts.append(f"Role: {role}")
    if job_description:
        context_parts.append(f"JD: {job_description[:800]}")  # Reduced from 1500
    
    context = "\n".join(context_parts) if context_parts else "No context."
    
    # Shorter system prompt
    system_prompt = """You are an AI career assistant. Give concise, actionable advice on:
- Resume improvement
- Job search & interviews  
- Skills & career growth

Keep responses under 150 words. Only answer career topics."""
    
    full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQ: {user_question}\nA:"
    
    try:
        response = llm.invoke(full_prompt)
        result = response.content if hasattr(response, 'content') else str(response)
        
        # Cache the response
        set_cached_response(cache_key, result)
        return result
            
    except Exception as e:
        return f"Error: {str(e)}. Please try again in a moment."