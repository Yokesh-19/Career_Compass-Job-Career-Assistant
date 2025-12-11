# import os
# import json
# import re
# from dotenv import load_dotenv

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.prebuilt import create_react_agent
# from langchain_core.messages import SystemMessage, HumanMessage

# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise ValueError("⚠️ Missing GEMINI_API_KEY")

# # ---------------------------------------------------
# # Setup LLM
# # ---------------------------------------------------
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-lite",
#     google_api_key=api_key,
#     temperature=0.2,
#     convert_system_message_to_human=True   # REQUIRED for LangGraph
# )

# # ---------------------------------------------------
# # Setup memory
# # ---------------------------------------------------
# memory = MemorySaver()

# # ---------------------------------------------------
# # Create agent (no tools needed)
# # ---------------------------------------------------
# resume_agent = create_react_agent(
#     model=llm,
#     tools=[],         # No tools for resume analysis
#     checkpointer=memory
# )

# THREAD_ID = "resume-analysis-001"


# # ---------------------------------------------------
# # Resume Analysis Function
# # ---------------------------------------------------
# def analyze_resume_langgraph(resume_text: str, role: str):
#     MAX_CHARS = 10000
#     if len(resume_text) > MAX_CHARS:
#         resume_text = resume_text[:MAX_CHARS]

#     system_prompt = """
#     You are an expert resume reviewer. Analyze the resume strictly and return clean JSON.

#     Rules:
#     - Follow the exact JSON schema.
#     - Do NOT add explanations.
#     - Do NOT write outside JSON.
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
#         {"messages": [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=human_prompt)
#         ]},
#         {"configurable": {"thread_id": THREAD_ID}}
#     )

#     # Get response message
#     final_message = None
#     for chunk in stream:
#         if "agent" in chunk:
#             final_message = chunk["agent"]["messages"][0].content

#     if final_message is None:
#         return {"error": "No response from model."}

#     # Clean JSON formatting
#     cleaned = re.sub(r"```json|```", "", final_message).strip()

#     # Convert to Python dict
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         return {
#             "error": "JSON parsing failed",
#             "raw_output": final_message
#         }

# services/ResumeModel.py
# import os
# import json
# import re
# from dotenv import load_dotenv

# # Streamlit is used for display function
# try:
#     import streamlit as st
# except Exception:
#     st = None

# # pdfplumber is used for PDF text extraction (Home.py already uses pdfplumber)
# try:
#     import pdfplumber
# except Exception:
#     pdfplumber = None

# # LangChain / LangGraph / Gemini setup (kept as in your original file)
# # If these imports fail at module import time, the analyze function will raise at runtime.
# try:
#     from langchain_google_genai import ChatGoogleGenerativeAI
#     from langgraph.checkpoint.memory import MemorySaver
#     from langgraph.prebuilt import create_react_agent
#     from langchain_core.messages import SystemMessage, HumanMessage
# except Exception as e:
#     # Keep names defined so module import doesn't crash; analyze_resume_langgraph will raise if these are missing.
#     ChatGoogleGenerativeAI = None
#     MemorySaver = None
#     create_react_agent = None
#     SystemMessage = None
#     HumanMessage = None

# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     # We don't raise here so the module can still be imported for UI functions.
#     api_key = None

# # ---------------------------------------------------
# # Setup LLM (initialize only if dependencies available)
# # ---------------------------------------------------
# llm = None
# memory = None
# resume_agent = None
# THREAD_ID = "resume-analysis-001"

# if ChatGoogleGenerativeAI and create_react_agent and MemorySaver and api_key:
#     try:
#         llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash-lite",
#             google_api_key=api_key,
#             temperature=0.2,
#             convert_system_message_to_human=True   # REQUIRED for LangGraph
#         )

#         memory = MemorySaver()
#         resume_agent = create_react_agent(
#             model=llm,
#             tools=[],         # No tools for resume analysis
#             checkpointer=memory
#         )
#     except Exception:
#         llm = None
#         memory = None
#         resume_agent = None


# # -------------------------
# # PDF text extractor (uses pdfplumber)
# # -------------------------
# def pdf_reader(path: str) -> str:
#     """
#     Extract and return text from a PDF file using pdfplumber.
#     Also returns text where pages are concatenated with '\n' between pages.
#     Raises ImportError if pdfplumber not installed.
#     """
#     if pdfplumber is None:
#         raise ImportError("pdfplumber is required for pdf_reader. Install with `pip install pdfplumber`")

#     text = ""
#     try:
#         with pdfplumber.open(path) as pdf:
#             for page in pdf.pages:
#                 page_text = page.extract_text() or ""
#                 text += page_text + "\n"
#     except Exception as exc:
#         # Re-raise with clearer message
#         raise RuntimeError(f"Failed to read PDF '{path}': {exc}")

#     return text


# # -------------------------
# # Basic info extraction
# # -------------------------
# def extract_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None) -> dict:
#     """
#     Return dict: { name, email, mobile_number, no_of_pages }.
#     - resume_data: optional dict (if you already used ResumeParser)
#     - pdf_path: optional path to PDF (used to extract text/pages when resume_data is missing)
#     """
#     basic = {
#         "name": "Not Found",
#         "email": "Not Found",
#         "mobile_number": "Not Found",
#         "no_of_pages": 0
#     }

#     # Use fields from resume_data if provided
#     if resume_data and isinstance(resume_data, dict):
#         basic["name"] = resume_data.get("name") or basic["name"]
#         basic["email"] = resume_data.get("email") or basic["email"]
#         basic["mobile_number"] = resume_data.get("mobile_number") or resume_data.get("mobile") or basic["mobile_number"]
#         basic["no_of_pages"] = resume_data.get("no_of_pages") or basic["no_of_pages"]

#     # If pdf_path provided, extract text and fallback-mine fields
#     text = ""
#     if pdf_path:
#         try:
#             text = pdf_reader(pdf_path)
#         except Exception:
#             text = ""

#     if text:
#         # email fallback
#         if basic["email"] == "Not Found":
#             m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
#             if m:
#                 basic["email"] = m.group()

#         # phone fallback
#         if basic["mobile_number"] == "Not Found":
#             m = re.search(r"\+?\d[\d\s\-]{8,15}", text)
#             if m:
#                 basic["mobile_number"] = m.group().strip()

#         # name fallback: first non-empty line, heuristic
#         if basic["name"] == "Not Found":
#             for line in text.splitlines():
#                 s = line.strip()
#                 if s:
#                     # skip lines that are clearly headings like 'Resume' or 'Curriculum Vitae'
#                     if re.search(r"^(resume|curriculum vitae|cv)$", s, flags=re.I):
#                         continue
#                     # take first short line as name
#                     if len(s.split()) <= 6:
#                         basic["name"] = s
#                         break

#         # pages: estimate by counting pages in pdfplumber if available
#         if basic["no_of_pages"] == 0 and pdfplumber is not None:
#             try:
#                 with pdfplumber.open(pdf_path) as pdf:
#                     basic["no_of_pages"] = len(pdf.pages) or 1
#             except Exception:
#                 basic["no_of_pages"] = text.count("\f") + 1 if text else 1
#         elif basic["no_of_pages"] == 0:
#             basic["no_of_pages"] = text.count("\f") + 1 if text else 1

#     return basic


# # -------------------------
# # Streamlit display helper
# # -------------------------
# def display_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None):
#     """
#     Display the basic Resume Analysis block in Streamlit. (Uses streamlit st.* calls.)
#     Home.py calls this before the LLM analysis.
#     """
#     if st is None:
#         raise ImportError("Streamlit is required to use display_basic_info_from_resume().")

#     # If caller provided resume_data dict (from an external parser), use it; otherwise try to parse pdf_path
#     basic = extract_basic_info_from_resume(resume_data=resume_data, pdf_path=pdf_path)

#     st.header("**Resume Analysis**")
#     st.success("Hello " + str(basic.get("name", "Not Found")))

#     st.subheader("**Your Basic info**")
#     try:
#         st.text("Name: " + str(basic.get("name", "Not Found")))
#         st.text("Email: " + str(basic.get("email", "Not Found")))
#         st.text("Contact: " + str(basic.get("mobile_number", "Not Found")))
#         st.text("Resume pages: " + str(basic.get("no_of_pages", "Not Found")))
#     except Exception:
#         # swallow like original code
#         pass

#     # Show level message similar to your friend's app
#     try:
#         pages = int(basic.get("no_of_pages", 0) or 0)
#     except Exception:
#         pages = 0

#     if pages == 1:
#         st.markdown("You are looking Fresher.")
#     elif pages == 2:
#         st.markdown("You are at intermediate level!")
#     elif pages >= 3:
#         st.markdown("You are at experience level!")


# # ---------------------------------------------------
# # Resume Analysis Function (langgraph/gemini) — kept original signature
# # ---------------------------------------------------
# def analyze_resume_langgraph(resume_text: str, role: str):
#     """
#     Calls the langgraph agent to analyze the resume and return a parsed JSON dict.
#     Raises RuntimeError if agent wasn't initialized (missing deps or API key).
#     """
#     if resume_agent is None:
#         raise RuntimeError(
#             "Resume analysis agent is not available. Ensure langchain/langgraph/gemini are installed "
#             "and GEMINI_API_KEY is set."
#         )

#     MAX_CHARS = 10000
#     if len(resume_text) > MAX_CHARS:
#         resume_text = resume_text[:MAX_CHARS]

#     system_prompt = """
#     You are an expert resume reviewer. Analyze the resume strictly and return clean JSON.

#     Rules:
#     - Follow the exact JSON schema.
#     - Do NOT add explanations.
#     - Do NOT write outside JSON.
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
#         {"messages": [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=human_prompt)
#         ]},
#         {"configurable": {"thread_id": THREAD_ID}}
#     )

#     # Get response message
#     final_message = None
#     for chunk in stream:
#         if "agent" in chunk:
#             final_message = chunk["agent"]["messages"][0].content

#     if final_message is None:
#         return {"error": "No response from model."}

#     # Clean JSON formatting (remove fenced code markers if present)
#     cleaned = re.sub(r"```json|```", "", final_message).strip()

#     # Convert to Python dict
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         return {
#             "error": "JSON parsing failed",
#             "raw_output": final_message
#         }


# # Exported symbols
# __all__ = [
#     "pdf_reader",
#     "extract_basic_info_from_resume",
#     "display_basic_info_from_resume",
#     "analyze_resume_langgraph",
# ]

# -----------working one ----------
# import os
# import json
# import re
# from dotenv import load_dotenv

# # Defensive Streamlit import (display function will require it)
# try:
#     import streamlit as st
# except Exception:
#     st = None

# # Use pdfplumber for robust PDF extraction (Home.py uses it too)
# try:
#     import pdfplumber
# except Exception:
#     pdfplumber = None

# # Optional resume parser
# try:
#     from pyresparser import ResumeParser
# except Exception:
#     ResumeParser = None

# # LangChain / LangGraph / Gemini imports (kept as in your original)
# try:
#     from langchain_google_genai import ChatGoogleGenerativeAI
#     from langgraph.checkpoint.memory import MemorySaver
#     from langgraph.prebuilt import create_react_agent
#     from langchain_core.messages import SystemMessage, HumanMessage
# except Exception:
#     ChatGoogleGenerativeAI = None
#     MemorySaver = None
#     create_react_agent = None
#     SystemMessage = None
#     HumanMessage = None

# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")

# # ---------------------------------------------------
# # Setup LLM (optional — only if all deps + key present)
# # ---------------------------------------------------
# llm = None
# memory = None
# resume_agent = None
# THREAD_ID = "resume-analysis-001"

# if ChatGoogleGenerativeAI and create_react_agent and MemorySaver and api_key:
#     try:
#         llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash-lite",
#             google_api_key=api_key,
#             temperature=0.2,
#             convert_system_message_to_human=True
#         )
#         memory = MemorySaver()
#         resume_agent = create_react_agent(model=llm, tools=[], checkpointer=memory)
#     except Exception:
#         llm = None
#         memory = None
#         resume_agent = None

# # -------------------------
# # PDF reader (pdfplumber)
# # -------------------------
# def pdf_reader(path: str) -> str:
#     """
#     Extract text from a PDF path using pdfplumber.
#     Raises ImportError if pdfplumber not installed.
#     """
#     if pdfplumber is None:
#         raise ImportError("pdfplumber required for pdf_reader. Install: pip install pdfplumber")

#     text = ""
#     try:
#         with pdfplumber.open(path) as pdf:
#             for page in pdf.pages:
#                 page_text = page.extract_text() or ""
#                 text += page_text + "\n"
#     except Exception as e:
#         raise RuntimeError(f"Failed to read PDF '{path}': {e}")
#     return text

# # -------------------------
# # Basic info extraction
# # -------------------------
# def extract_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None) -> dict:
#     """
#     Returns dict: {name, email, mobile_number, no_of_pages}
#     Uses resume_data (pyresparser) if provided, otherwise falls back to pdf text heuristics.
#     """
#     basic = {
#         "name": "Not Found",
#         "email": "Not Found",
#         "mobile_number": "Not Found",
#         "no_of_pages": 0
#     }

#     if resume_data and isinstance(resume_data, dict):
#         basic["name"] = resume_data.get("name") or basic["name"]
#         basic["email"] = resume_data.get("email") or basic["email"]
#         basic["mobile_number"] = resume_data.get("mobile_number") or resume_data.get("mobile") or basic["mobile_number"]
#         basic["no_of_pages"] = resume_data.get("no_of_pages") or basic["no_of_pages"]

#     text = ""
#     if pdf_path:
#         try:
#             text = pdf_reader(pdf_path)
#         except Exception:
#             text = ""

#     if text:
#         if basic["email"] == "Not Found":
#             m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
#             if m:
#                 basic["email"] = m.group()

#         if basic["mobile_number"] == "Not Found":
#             m = re.search(r"\+?\d[\d\s\-]{8,15}", text)
#             if m:
#                 basic["mobile_number"] = m.group().strip()

#         if basic["name"] == "Not Found":
#             for line in text.splitlines():
#                 s = line.strip()
#                 if s and not re.match(r"^(resume|curriculum vitae|cv)$", s, flags=re.I):
#                     if len(s.split()) <= 6:
#                         basic["name"] = s
#                         break

#         if basic["no_of_pages"] == 0:
#             if pdfplumber is not None and pdf_path:
#                 try:
#                     with pdfplumber.open(pdf_path) as pdf:
#                         basic["no_of_pages"] = len(pdf.pages) or 1
#                 except Exception:
#                     basic["no_of_pages"] = text.count("\f") + 1 if text else 1
#             else:
#                 basic["no_of_pages"] = text.count("\f") + 1 if text else 1

#     return basic

# # -------------------------
# # Streamlit display helper
# # -------------------------
# def display_basic_info_from_resume(resume_data: dict = None, pdf_path: str = None):
#     """
#     Display basic info block in Streamlit (header + name/email/contact/pages + level message).
#     """
#     if st is None:
#         raise ImportError("Streamlit is required to use display_basic_info_from_resume().")

#     if resume_data is None and pdf_path and ResumeParser:
#         try:
#             resume_data = ResumeParser(pdf_path).get_extracted_data()
#         except Exception:
#             resume_data = None

#     basic = extract_basic_info_from_resume(resume_data=resume_data, pdf_path=pdf_path)

#     st.header("**Resume Analysis**")
#     st.success("Hello " + str(basic.get("name", "Not Found")))

#     st.subheader("**Your Basic info**")
#     try:
#         st.text("Name: " + str(basic.get("name", "Not Found")))
#         st.text("Email: " + str(basic.get("email", "Not Found")))
#         st.text("Contact: " + str(basic.get("mobile_number", "Not Found")))
#         st.text("Resume pages: " + str(basic.get("no_of_pages", "Not Found")))
#     except Exception:
#         pass

#     try:
#         pages = int(basic.get("no_of_pages", 0) or 0)
#     except Exception:
#         pages = 0

#     if pages == 1:
#         st.markdown("You are looking Fresher.")
#     elif pages == 2:
#         st.markdown("You are at intermediate level!")
#     elif pages >= 3:
#         st.markdown("You are at experience level!")

# # -------------------------
# # Skill extraction & matching helpers
# # -------------------------
# # Curated skill vocab (extend as needed)
# _SKILL_VOCAB = {
#     "data_science": [
#         "tensorflow", "keras", "pytorch", "machine learning", "deep learning",
#         "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "sql"
#     ],
#     "web": [
#         "react", "reactjs", "django", "node", "nodejs", "javascript", "html", "css",
#         "flask", "express", "angular", "vue"
#     ],
#     "android": ["android", "flutter", "kotlin", "java"],
#     "ios": ["ios", "swift", "objective-c", "xcode"],
#     "uiux": ["figma", "adobe xd", "photoshop", "illustrator", "ux", "ui", "prototyping"]
# }

# # flattened skills set
# _FLATTENED_SKILLS = set()
# for group in _SKILL_VOCAB.values():
#     for s in group:
#         _FLATTENED_SKILLS.add(s.lower())


# def extract_skills_from_text(text: str) -> set:
#     """
#     Best-effort: parse skills section (if present) and also phrase-match vocabulary across document.
#     Returns set of normalized skills (lowercase strings).
#     """
#     if not text:
#         return set()
#     txt = text.lower()
#     found = set()

#     # skills section heuristic
#     m = re.search(r"(skills|technical skills|core skills|key skills)\s*[:\-\n]\s*(.+?)(\n\n|\r\r|\n\s*\w+?:|\Z)", txt, flags=re.S)
#     if m:
#         skills_blob = m.group(2)
#         tokens = re.split(r"[,;\n•\u2022]", skills_blob)
#         for t in tokens:
#             s = t.strip()
#             if s:
#                 found.add(s.lower())

#     # vocabulary phrase matching
#     for skill in _FLATTENED_SKILLS:
#         if " " in skill:
#             if skill in txt:
#                 found.add(skill)
#         else:
#             if re.search(r"\b" + re.escape(skill) + r"\b", txt):
#                 found.add(skill)

#     return found


# def extract_required_skills_from_jd(job_role: str, job_description: str = "") -> set:
#     """
#     Extract required skills from job_role + job_description using flattened vocab.
#     Prefers explicit matches in the job description.
#     """
#     combined = ((job_role or "") + "\n" + (job_description or "")).lower()
#     required = set()

#     if job_description:
#         jd_text = job_description.lower()
#         for skill in _FLATTENED_SKILLS:
#             if " " in skill:
#                 if skill in jd_text:
#                     required.add(skill)
#             else:
#                 if re.search(r"\b" + re.escape(skill) + r"\b", jd_text):
#                     required.add(skill)

#     # fallback to job_role if none found in JD
#     if not required and job_role:
#         jr = job_role.lower()
#         for skill in _FLATTENED_SKILLS:
#             if " " in skill:
#                 if skill in jr:
#                     required.add(skill)
#             else:
#                 if re.search(r"\b" + re.escape(skill) + r"\b", jr):
#                     required.add(skill)

#     return required


# def recommend_courses_for_required_skills(required_skills: set, courses_mapping: dict = None):
#     """
#     Return list of (title,url) pairs recommended for the best-matching field.
#     If courses_mapping provided (e.g. Courses.py lists), it is used to return course pairs.
#     """
#     field_scores = {}
#     for field, vocab in _SKILL_VOCAB.items():
#         field_skills = set([v.lower() for v in vocab])
#         field_scores[field] = len(required_skills & field_skills)

#     # choose best field
#     best_field = max(field_scores, key=field_scores.get)
#     if field_scores.get(best_field, 0) == 0:
#         best_field = None

#     if courses_mapping and best_field and best_field in courses_mapping:
#         # courses in Courses.py are lists of [title,url]; return up to 6
#         return [(t, u) for (t, u) in courses_mapping[best_field][:6]]

#     # fallback: combine first courses from available mapping
#     if courses_mapping:
#         fallback = []
#         for k in courses_mapping:
#             fallback.extend([(t, u) for (t, u) in courses_mapping[k][:2]])
#         return fallback[:6]

#     # simple fallback list
#     return [
#         ("Intro to Machine Learning (Coursera)", "https://www.coursera.org/learn/machine-learning"),
#         ("The Web Developer Bootcamp (Udemy)", "https://www.udemy.com/course/the-web-developer-bootcamp")
#     ]

# # -------------------------
# # LangGraph/Gemini resume analysis (original signature preserved)
# # -------------------------
# def analyze_resume_langgraph(resume_text: str, role: str):
#     """
#     Calls the LangGraph agent (resume_agent) and returns parsed JSON (schema defined).
#     Raises RuntimeError if agent is not initialized.
#     """
#     if resume_agent is None:
#         raise RuntimeError("Resume analysis agent is not available. Ensure GEMINI_API_KEY and required packages are present.")

#     MAX_CHARS = 10000
#     if len(resume_text) > MAX_CHARS:
#         resume_text = resume_text[:MAX_CHARS]

#     system_prompt = """
#     You are an expert resume reviewer. Analyze the resume strictly and return clean JSON.

#     Rules:
#     - Follow the exact JSON schema.
#     - Do NOT add explanations.
#     - Do NOT write outside JSON.
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

#     # remove code fences if present
#     cleaned = re.sub(r"```json|```", "", final_message).strip()

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         return {"error": "JSON parsing failed", "raw_output": final_message}

# # Exports
# __all__ = [
#     "pdf_reader",
#     "extract_basic_info_from_resume",
#     "display_basic_info_from_resume",
#     "extract_skills_from_text",
#     "extract_required_skills_from_jd",
#     "recommend_courses_for_required_skills",
#     "analyze_resume_langgraph",
#     "_FLATTENED_SKILLS",
# ]

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
def analyze_resume_langgraph(resume_text: str, role: str):
    if resume_agent is None:
        raise RuntimeError("Resume analysis agent unavailable. Check GEMINI_API_KEY & dependencies.")

    MAX_CHARS = 10000
    if len(resume_text) > MAX_CHARS:
        resume_text = resume_text[:MAX_CHARS]

    system_prompt = """
    You are an expert resume reviewer. Analyze the resume strictly and return clean JSON.
    Follow EXACT schema. No explanations outside JSON.
    """

    human_prompt = f"""
    Target Role: {role}
    Resume:
    {resume_text}

    Return JSON in the exact format:
    {{
        "Overall_Score": <score out of 100>,
        "Category_Scores": {{
            "Presentation & Format": <score>,
            "Skills": <score>,
            "Projects": <score>,
            "Education": <score>,
            "Experience": <score>,
            "Certifications": <score>,
            "Achievements": <score>
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
        }}
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
