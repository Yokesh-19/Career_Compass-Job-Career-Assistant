import os
import json
import re
from dotenv import load_dotenv

# Defensive Streamlit import (display function will require it)
try:
    import streamlit as st
except Exception:
    st = None

# Use pdfplumber for robust PDF extraction (Home.py uses it too)
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# Optional resume parser
try:
    from pyresparser import ResumeParser
except Exception:
    ResumeParser = None

# LangChain / LangGraph / Gemini imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage, HumanMessage
except Exception:
    ChatGoogleGenerativeAI = None
    MemorySaver = None
    create_react_agent = None
    SystemMessage = None
    HumanMessage = None

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ---------------------------------------------------
# Setup LLM (optional — only if all deps + key present)
# ---------------------------------------------------
llm = None
memory = None
resume_agent = None
THREAD_ID = "resume-analysis-001"

if ChatGoogleGenerativeAI and create_react_agent and MemorySaver and api_key:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        memory = MemorySaver()
        resume_agent = create_react_agent(model=llm, tools=[], checkpointer=memory)
    except Exception:
        llm = None
        memory = None
        resume_agent = None

# -------------------------
# PDF reader (pdfplumber)
# -------------------------
def pdf_reader(path: str) -> str:
    if pdfplumber is None:
        raise ImportError("pdfplumber required for pdf_reader. Install: pip install pdfplumber")

    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF '{path}': {e}")
    return text

# -------------------------
# Basic info extraction
# -------------------------
def extract_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None) -> dict:
    basic = {
        "name": "Not Found",
        "email": "Not Found",
        "mobile_number": "Not Found",
        "no_of_pages": 0
    }

    if resume_data and isinstance(resume_data, dict):
        basic["name"] = resume_data.get("name") or basic["name"]
        basic["email"] = resume_data.get("email") or basic["email"]
        basic["mobile_number"] = resume_data.get("mobile_number") or resume_data.get("mobile") or basic["mobile_number"]
        basic["no_of_pages"] = resume_data.get("no_of_pages") or basic["no_of_pages"]

    text = ""
    if pdf_path:
        try:
            text = pdf_reader(pdf_path)
        except Exception:
            text = ""

    if text:
        if basic["email"] == "Not Found":
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if m:
                basic["email"] = m.group()

        if basic["mobile_number"] == "Not Found":
            m = re.search(r"\+?\d[\d\s\-]{8,15}", text)
            if m:
                basic["mobile_number"] = m.group().strip()

        if basic["name"] == "Not Found":
            for line in text.splitlines():
                s = line.strip()
                if s and not re.match(r"^(resume|curriculum vitae|cv)$", s, flags=re.I):
                    if len(s.split()) <= 6:
                        basic["name"] = s
                        break

        if basic["no_of_pages"] == 0:
            if pdfplumber is not None and pdf_path:
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        basic["no_of_pages"] = len(pdf.pages) or 1
                except Exception:
                    basic["no_of_pages"] = text.count("\f") + 1 if text else 1
            else:
                basic["no_of_pages"] = text.count("\f") + 1 if text else 1

    return basic

# -------------------------
# Streamlit display helper
# -------------------------
def display_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None):
    if st is None:
        raise ImportError("Streamlit required to use display_basic_info_from_resume()")

    if resume_data is None and pdf_path and ResumeParser:
        try:
            resume_data = ResumeParser(pdf_path).get_extracted_data()
        except Exception:
            resume_data = None

    basic = extract_basic_info_from_resume(resume_data=resume_data, pdf_path=pdf_path)

    st.header("**Resume Analysis**")
    st.success("Hello " + str(basic.get("name", "Not Found")))
    st.subheader("**Your Basic info**")
    st.text("Name: " + str(basic.get("name", "Not Found")))
    st.text("Email: " + str(basic.get("email", "Not Found")))
    st.text("Contact: " + str(basic.get("mobile_number", "Not Found")))
    st.text("Resume pages: " + str(basic.get("no_of_pages", "Not Found")))

    pages = int(basic.get("no_of_pages", 0) or 0)
    if pages == 1:
        st.markdown("You are looking Fresher.")
    elif pages == 2:
        st.markdown("You are at intermediate level!")
    elif pages >= 3:
        st.markdown("You are at experience level!")

# -------------------------
# Skill extraction helpers
# -------------------------
_SKILL_VOCAB = {
    "data_science": [
        "tensorflow", "keras", "pytorch", "machine learning", "deep learning",
        "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "sql"
    ],
    "web": [
        "react", "reactjs", "django", "node", "nodejs", "javascript", "html", "css",
        "flask", "express", "angular", "vue"
    ],
    "android": ["android", "flutter", "kotlin", "java"],
    "ios": ["ios", "swift", "objective-c", "xcode"],
    "uiux": ["figma", "adobe xd", "photoshop", "illustrator", "ux", "ui", "prototyping"]
}

# flattened
_FLATTENED_SKILLS = {s.lower() for g in _SKILL_VOCAB.values() for s in g}

def extract_skills_from_text(text: str) -> set:
    if not text:
        return set()
    txt = text.lower()
    found = set()

    m = re.search(r"(skills|technical skills|core skills|key skills)\s*[:\-\n]\s*(.+?)(\n\n|\r\r|\n\s*\w+?:|\Z)", txt, flags=re.S)
    if m:
        tokens = re.split(r"[,;\n•\u2022]", m.group(2))
        for t in tokens:
            s = t.strip()
            if s:
                found.add(s.lower())

    for skill in _FLATTENED_SKILLS:
        if " " in skill:
            if skill in txt:
                found.add(skill)
        else:
            if re.search(r"\b" + re.escape(skill) + r"\b", txt):
                found.add(skill)

    return found

def extract_required_skills_from_jd(job_role: str, job_description: str = "") -> set:
    combined = ((job_role or "") + "\n" + (job_description or "")).lower()
    required = set()

    if job_description:
        jd_text = job_description.lower()
        for skill in _FLATTENED_SKILLS:
            if " " in skill and skill in jd_text:
                required.add(skill)
            elif re.search(r"\b" + re.escape(skill) + r"\b", jd_text):
                required.add(skill)

    if not required and job_role:
        jr = job_role.lower()
        for skill in _FLATTENED_SKILLS:
            if " " in skill and skill in jr:
                required.add(skill)
            elif re.search(r"\b" + re.escape(skill) + r"\b", jr):
                required.add(skill)

    return required

def recommend_courses_for_required_skills(required_skills: set, courses_mapping: dict = None):
    field_scores = {
        field: len(required_skills & set([v.lower() for v in vocab]))
        for field, vocab in _SKILL_VOCAB.items()
    }

    best_field = max(field_scores, key=field_scores.get)
    if field_scores.get(best_field, 0) == 0:
        best_field = None

    if courses_mapping and best_field and best_field in courses_mapping:
        return [(t, u) for (t, u) in courses_mapping[best_field][:6]]

    if courses_mapping:
        fallback = []
        for k in courses_mapping:
            fallback.extend([(t, u) for (t, u) in courses_mapping[k][:2]])
        return fallback[:6]

    return [
        ("Intro to Machine Learning (Coursera)", "https://www.coursera.org/learn/machine-learning"),
        ("The Web Developer Bootcamp (Udemy)", "https://www.udemy.com/course/the-web-developer-bootcamp")
    ]

# -------------------------
# LangGraph/Gemini resume analysis
# -------------------------
# def analyze_resume_langgraph(resume_text: str, role: str):
#     if resume_agent is None:
#         raise RuntimeError("Resume analysis agent unavailable. Check GEMINI_API_KEY & dependencies.")

#     MAX_CHARS = 10000
#     if len(resume_text) > MAX_CHARS:
#         resume_text = resume_text[:MAX_CHARS]

#     system_prompt = """
#     You are an expert resume reviewer. Analyze the resume strictly and return clean JSON.
#     Follow EXACT schema. No explanations outside JSON.
#     """

#     human_prompt = f"""
#     Target Role: {role}
#     Resume:
#     {resume_text}

#     Return JSON in the exact format:
#     {{
#         "Overall_Score": <score out of 100>,
#         "Category_Scores": {{
#             "Presentation & Format": <score>,
#             "Skills": <score>,
#             "Projects": <score>,
#             "Education": <score>,
#             "Experience": <score>,
#             "Certifications": <score>,
#             "Achievements": <score>
#         }},
#         "Strengths": [],
#         "Weaknesses": {{
#             "Critical": [],
#             "Medium": [],
#             "Low": []
#         }},
#         "Suggestions": {{
#             "Critical": [],
#             "Medium": [],
#             "Low": []
#         }}
#     }}
#     """

#     stream = resume_agent.stream(
#         {"messages": [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]},
#         {"configurable": {"thread_id": THREAD_ID}}
#     )

#     final_message = None
#     for chunk in stream:
#         if "agent" in chunk:
#             final_message = chunk["agent"]["messages"][0].content

#     if final_message is None:
#         return {"error": "No response from model."}

#     cleaned = re.sub(r"```json|```", "", final_message).strip()

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         return {"error": "JSON parsing failed", "raw_output": final_message}

import os
os.environ["GRPC_VERBOSITY"] = "ERROR"  # Reduce logging overhead

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)
def analyze_resume_langgraph(resume_text: str, role: str, job_description: str = ""):
    if resume_agent is None:
        raise RuntimeError("Resume analysis agent unavailable. Check GEMINI_API_KEY & dependencies.")

    MAX_CHARS = 10000
    if len(resume_text) > MAX_CHARS:
        resume_text = resume_text[:MAX_CHARS]

    system_prompt = """
    You are an expert resume reviewer, career assistant, and job-matching specialist.
    Your task is to produce ONE combined JSON output containing:
    1. Resume Review
    2. Category Scores
    3. Strengths & Weaknesses
    4. Suggestions
    5. Skill Extraction
    6. Skill Gap Analysis
    7. Job Match Score + Label + Actionable Tip

    Return only valid JSON, no explanations.
    """

    human_prompt = f"""
    Resume:
    {resume_text}

    Target Role: {role}

    Job Description:
    {job_description}

    REQUIRED JSON OUTPUT:
    {{
      "Overall_Score": int,
      "Category_Scores": {{
        "Presentation & Format": int,
        "Skills": int,
        "Projects": int,
        "Education": int,
        "Experience": int,
        "Certifications": int,
        "Achievements": int
      }},
      "Strengths": [],
      "Weaknesses": {{
        "Critical": [],
        "Medium": [],
        "Low": []
      }},
      "Suggestions": {{
        "Critical": [],
        "Medium": [],
        "Low": []
      }},
      "resume_skills": [],
      "job_required_skills": [],
      "skills_to_improve": [],
      "job_match_score": float,
      "job_match_label": "Strong Match / Moderate Match / Weak Match",
      "job_match_tip": ""
    }}
    """

    stream = resume_agent.stream(
        {"messages": [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]},
        {"configurable": {"thread_id": THREAD_ID}}
    )

    final_message = None
    for chunk in stream:
        if "agent" in chunk:
            final_message = chunk["agent"]["messages"][0].content

    if final_message is None:
        return {"error": "No response from model."}

    cleaned = re.sub(r"```json|```", "", final_message).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "JSON parsing failed", "raw_output": final_message}


# -------------------------------------------------------
# NEW — Job Match Score + Actionable Tip from JD
# -------------------------------------------------------
def analyze_job_fit(resume_text, job_description):
    prompt = f"""
    You are an AI career assistant and you must evaluate job readiness ONLY based on the resume and job description.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Task:
    1. Give a Match Score on a scale of 0 to 10.
    2. Give a Match Label:
        - Strong Match (8.0 - 10)
        - Moderate Match (5.0 - 7.9)
        - Weak Match (0 - 4.9)
    3. Provide ONE very specific, actionable tip to strengthen the application.

    Format STRICTLY as JSON:
    {{
        "match_score": float,
        "match_label": "Strong Match / Moderate Match / Weak Match",
        "actionable_tip": "..."
    }}
    """

    from langchain_google_genai import ChatGoogleGenerativeAI
    import os, json, re

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.4
    )

    response = llm.invoke(prompt).content
    cleaned = re.sub(r"^```json|```$", "", response.strip(), flags=re.MULTILINE)

    try:
        return json.loads(cleaned)
    except Exception:
        return {"error": "Parsing failed", "raw_output": response}

# -------------------------
# Exports
# -------------------------
__all__ = [
    "pdf_reader",
    "extract_basic_info_from_resume",
    "display_basic_info_from_resume",
    "extract_skills_from_text",
    "extract_required_skills_from_jd",
    "recommend_courses_for_required_skills",
    "analyze_resume_langgraph",
    "analyze_job_fit",
    "_FLATTENED_SKILLS",
]