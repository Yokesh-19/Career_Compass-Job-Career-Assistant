# # services/ChatBotModel.py
# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.4
# )

# def chatbot_reply(user_question):
#     prompt = f"""
#     You are an AI assistant helping job seekers.
#     Provide clear, supportive, short answers.
#     Avoid bullet points unless required.
#     Question from user: "{user_question}"
#     """
#     response = llm.invoke(prompt)
#     return response.content

# # services/ChatBotModel.py
# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.4
# )

# def chatbot_reply(user_question):
#     prompt = f"""
#     You are an AI chatbot who ONLY answers questions related to:
#     - Resume improvement
#     - Job search & job roles
#     - Skill development & learning paths
#     - Interview preparation & career guidance

#     STRICT RULES:
#     - If the question is outside the above topics, DO NOT answer it.
#     - Instead reply: "I can help only with resume, jobs, skills and interview-related questions."
#     - Never answer questions about entertainment, sports, coding help, politics, personal advice, or anything illegal/unethical.

#     Examples of valid questions: resume format, skills to learn for a job role, best courses, mock interview tips, how to describe projects.
#     Examples of invalid questions: math problems, movie suggestions, hacking, gossip, medical advice, news, coding outputs.

#     User Question: "{user_question}"

#     Your response should always be short and supportive.
#     """

#     response = llm.invoke(prompt)
#     return response.content

# ---- new code of ai that only answers to queries related to resume, jobs, skills and interview ----
# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.4
# )

# def chatbot_reply(user_question):
#     prompt = f"""
#     You are a friendly AI career assistant.

#     Your allowed topics:
#     - Resume building
#     - Job roles & job search
#     - Skill development & learning paths
#     - Interview preparation & career guidance

#     Your behavior:
#     - If the user greets (hi, hello, hey etc.), greet them back warmly.
#     - If the user says thanks / thank you, reply politely (e.g., "Happy to help!").
#     - If the question is career-related, answer clearly and helpfully in 3–5 sentences.
#     - If the topic is unrelated to career topics (like movies, maths, gossip, hacking etc.):
#          ⛔ DO NOT answer
#          ✔ Respond only: "I can help only with resume, jobs, skills and interview-related questions."

#     User message: "{user_question}"

#     Now generate your reply following the rules.
#     """

#     response = llm.invoke(prompt)
#     return response.content


import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.55
)

def chatbot_reply(user_question, resume=None, role=None, job_description=None):
    """
    Friendly AI career assistant:
    - Answers ONLY questions related to jobs, careers, resume improvement, interview, skill learning.
    - Greets when users greet.
    - Rejects unrelated topics politely.
    """

    # ---------- polite rejection for unrelated topics ----------
    blocked_topics = [
        "love", "date", "relationship", "story", "joke", "song", "movie", "politics",
        "religion", "funny", "crush", "game", "matchmaking", "astrology"
    ]
    if any(word in user_question.lower() for word in blocked_topics):
        return (
            "I'm here to guide you about **careers, resumes, job roles, interviews, and skills** 😊\n"
            "Ask me anything related to your career and I’ll gladly help!"
        )

    # ---------- greeting / thank you replies ----------
    greeting_words = ["hi", "hello", "hey", "thank", "thanks", "good morning", "good evening"]
    if any(w in user_question.lower() for w in greeting_words):
        return (
            "Happy to help! ✨\n"
            "Feel free to ask anything about improving your resume, job readiness, skills, or interview preparation 😊"
        )

    # ---------- main AI prompt ----------
    prompt = f"""
    You are a **friendly AI career assistant** helping job seekers.

    Use the context below ONLY if needed:
    Resume (may be None): {resume}
    Target job role: {role}
    Job description: {job_description}

    Question from student:
    "{user_question}"

    Your response rules:
    - Tone must be **friendly, supportive, and encouraging**
    - Keep it **short, clear and practical** (4–7 lines)
    - Focus ONLY on these topics:
        ✔ career guidance
        ✔ resume improvement
        ✔ job role clarification
        ✔ skill learning roadmap
        ✔ interview preparation & tips
    - Give **specific suggestions**, not generic advice
    - If there is no context in resume/role to answer properly, ask a follow-up question politely
    - If the question is unrelated to careers, politely refuse
    """

    response = llm.invoke(prompt)
    return response.content
