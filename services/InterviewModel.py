import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3
)

memory = MemorySaver()

agent = create_react_agent(
    model=llm,
    tools=[],
    checkpointer=memory
)

def start_interview_langchain(job_role, resume_text):
    system_prompt = """You are a professional interviewer for a tech company.
    Your goal is to conduct a structured mock interview.
    Follow these rules:
    - Ask questions from resume and self intro, behavioural and qualities about the candidate
    - Ask one question at a time.
    - End the interview after 5–7 questions with a conclusion message with "we will not be moving forward" phrase or "you are selected" phrase inside it.
    Use a sample name for yourself.
    """
    context_prompt = f"""Here is the candidate's information:
    **Job Role:** {job_role}
    **Resume:**
    {resume_text}

    Start the interview by introducing yourself and asking the first question.
    """

    response = list(agent.stream(
            {"messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_prompt)
                ]},
            {"configurable": {"thread_id": "123"}}
        ))
    output = response[0]["agent"]["messages"][0].content
    return output

def continue_interview(candidate_answer):
    response = list( agent.stream(
        {"messages": [HumanMessage(content=candidate_answer)]},
        {"configurable": {"thread_id": "123"}}
    ))
    output = response[0]["agent"]["messages"][0].content
    return output