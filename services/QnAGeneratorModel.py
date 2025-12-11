import os, re, json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

def generate_qna_from_resume(resume_text: str, job_role: str, num_questions: int = 10):
    MAX_CHARS = 10000
    if len(resume_text) > MAX_CHARS:
        resume_text = resume_text[:MAX_CHARS]
    
    """
    Generate Q&A pairs based on candidate resume, job role, and real-world DSA problems.
    """
    prompt = f"""
    You are an expert technical interviewer for the role of {job_role}.
    The candidate's resume is below:
    ---
    {resume_text}
    ---
    Based on this, generate {num_questions} high-quality interview questions and answers.

    Format output as JSON with this structure:
    [
      {{
        "Category": "Technical / DSA / Behavioral / Scenario",
        "Question": "...",
        "Answer": "..."
      }},
      ...
    ]

    Ensure:
    - 50% of questions are job-specific technical questions.
    - 30% are DSA or problem-solving related.
    - 20% are behavioral or scenario-based.
    Keep answers concise, practical, and easy to understand.
    """

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=api_key,
        temperature=0.3
    )
    response = llm.invoke(prompt)

    try:
        import json
        content = response.content
        cleaned = re.sub(r"^```json|```$", "", content.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "error": "Could not parse JSON",
            "raw_output": response.content if hasattr(response, "content") else response,
            "exception": str(e)
        }