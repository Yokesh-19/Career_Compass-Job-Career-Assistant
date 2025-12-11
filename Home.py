# # -------- with all the features implemented -------
# # Last working code


# import streamlit as st
# import pdfplumber
# import pandas as pd
# import plotly.express as px
# import tempfile
# from services.ResumeModel import (
#     analyze_resume_langgraph,
#     display_basic_info_from_resume,
#     analyze_job_fit
# )

# from services.ChatBotModel import chatbot_reply

# st.set_page_config(
#     page_title="AI Resume Analyzer",
#     page_icon="📃",
#     layout="centered",
#     initial_sidebar_state="collapsed"
# )

# st.title("AI Resume Analyzer")
# st.markdown("Upload your resume and get AI-powered feedback tailored to your needs!")

# if "resume" not in st.session_state:
#     st.session_state.resume = None
# if "role" not in st.session_state:
#     st.session_state.role = None
# if "allow_mock" not in st.session_state:
#     st.session_state.allow_mock = False
# if "job_description" not in st.session_state:
#     st.session_state.job_description = None

# uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
# job_role = st.text_input("Enter the job role you're targeting")
# job_description = st.text_area("Paste the Job Description (JD)", height=180, placeholder="Paste the JD here")
# analyze = st.button("Analyze Resume")

# def extract_text_from_pdf_filelike(file_like):
#     text = ""
#     try:
#         if hasattr(file_like, "read") and hasattr(file_like, "name"):
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#                 tmp.write(file_like.getbuffer())
#                 tmp_path = tmp.name
#             with pdfplumber.open(tmp_path) as pdf:
#                 for page in pdf.pages:
#                     page_text = page.extract_text()
#                     if page_text:
#                         text += page_text + "\n"
#         else:
#             with pdfplumber.open(file_like) as pdf:
#                 for page in pdf.pages:
#                     page_text = page.extract_text()
#                     if page_text:
#                         text += page_text + "\n"
#     except Exception:
#         text = ""
#     return text

# def extract_text_from_file(uploaded_file):
#     if uploaded_file.type == "application/pdf":
#         return extract_text_from_pdf_filelike(uploaded_file)
#     else:
#         try:
#             return uploaded_file.read().decode("utf-8")
#         except Exception:
#             return ""

# if analyze:
#     if not uploaded_file:
#         st.error("⚠️ Please upload a resume file before analyzing.")
#         st.stop()

#     if not job_role.strip():
#         st.error("⚠️ Please enter the job role before analyzing your resume.")
#         st.stop()

#     try:
#         file_content = extract_text_from_file(uploaded_file)

#         if not file_content.strip():
#             st.error("⚠️ File doesn't contain any content.")
#             st.stop()

#         st.session_state.resume = file_content.strip()
#         st.session_state.role = job_role.strip()
#         st.session_state.job_description = job_description.strip()

#         if uploaded_file.type == "application/pdf":
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#                 tmp.write(uploaded_file.getbuffer())
#                 tmp_path = tmp.name
#             try:
#                 display_basic_info_from_resume(resume_data=None, pdf_path=tmp_path)
#             except Exception as e:
#                 st.warning(f"Could not show basic info block: {e}")
#         else:
#             txt = file_content
#             import re
#             email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", txt)
#             phone_match = re.search(r"\+?\d[\d\s\-]{8,15}", txt)
#             first_line = next((line.strip() for line in txt.splitlines() if line.strip()), "Not Found")
#             st.header("*Resume Analysis*")
#             st.success("Hello " + first_line)
#             st.subheader("*Your Basic info*")
#             try:
#                 st.text("Name: " + first_line)
#                 st.text("Email: " + (email_match.group() if email_match else "Not Found"))
#                 st.text("Contact: " + (phone_match.group() if phone_match else "Not Found"))
#                 st.text("Resume pages: 1")
#             except Exception:
#                 pass
#             st.markdown("You are looking Fresher.")

#         with st.spinner("Analyzing your resume using LangChain..."):
#             result = analyze_resume_langgraph(file_content, job_role)

#         if "error" in result:
#             st.error(f"Error: {result['error']}")
#             st.write(result.get("raw_output", "No raw output available"))
#         else:
#             st.session_state.allow_mock = True
#             overall_score = result.get("Overall_Score", 0)
#             st.subheader(f"🏆 Overall Score: {overall_score}/100")

#             category_scores = result.get("Category_Scores", {})
#             df_scores = pd.DataFrame({
#                 "Category": list(category_scores.keys()),
#                 "Score": list(category_scores.values())
#             })

#             fig_radar = px.line_polar(
#                 df_scores,
#                 r="Score",
#                 theta="Category",
#                 line_close=True,
#                 title="Radar View",
#                 color_discrete_sequence=["#0072B2"]
#             )
#             fig_radar.update_traces(fill="toself", hovertemplate="%{theta}: %{r}")
#             fig_radar.update_layout(
#                 polar=dict(
#                     radialaxis=dict(visible=True, range=[0, 100])
#                 ),
#                 showlegend=False,
#                 height=500
#             )
#             st.plotly_chart(fig_radar, use_container_width=True)

#             st.subheader("📈 Category-wise Scores")
#             st.table(df_scores)

#             # ---------------- SKILL GAP FEATURE ----------------
#             st.subheader("🧠 Skill Gap Analysis")
#             try:
#                 skill_gap_prompt = f"""
#                 From the resume and the job role below, extract ONLY the skills and compare them.
#                 Return in JSON format with keys:
#                 "resume_skills", "job_required_skills", "skills_to_improve"
#                 Resume:
#                 {file_content}
#                 Job Role:
#                 {job_role}
#                 """
#                 skill_gap_output = analyze_resume_langgraph(skill_gap_prompt, job_role)

#                 resume_skills = skill_gap_output.get("resume_skills", [])
#                 job_required_skills = skill_gap_output.get("job_required_skills", [])
#                 skills_to_improve = skill_gap_output.get("skills_to_improve", [])

#                 st.write("### 🔹 Skills in Resume")
#                 st.write(", ".join(resume_skills) if resume_skills else "Not detected")

#                 st.write("### 🔹 Skills Required for Role")
#                 st.write(", ".join(job_required_skills) if job_required_skills else "Not present in JD")

#                 st.write("### 🔥 Skills You Need to Improve")
#                 if skills_to_improve:
#                     for s in skills_to_improve:
#                         st.write(f"- {s}")
#                 else:
#                     st.success("🎉 No major skill gaps detected — you're a strong match!")
#             except Exception as e:
#                 st.warning(f"Skill-gap check unavailable: {e}")

#             # ---------------- JOB MATCH SCORE SECTION ----------------
#             st.markdown("---")
#             st.subheader("🎯 Job Match Score & Actionable Tip")

#             if st.session_state.job_description:
#                 job_match = analyze_job_fit(st.session_state.resume, st.session_state.job_description)
#                 if "error" not in job_match:
#                     st.success(f"⭐ Match Score: {job_match['match_score']} / 10")
#                     st.info(f"📌 Match Level: **{job_match['match_label']}**")
#                     st.warning("💡 Actionable Tip: " + job_match["actionable_tip"])

#                     # ---- Visual Job Match Bar ----
#                     score = job_match["match_score"]
#                     if score >= 8:
#                         bar_color = "🟢 Strong Match"
#                     elif score >= 5:
#                         bar_color = "🟠 Moderate Match"
#                     else:
#                         bar_color = "🔴 Weak Match"

#                     st.markdown(f"### {bar_color}")
#                     st.progress(min(score / 10, 1.0))
#                 else:
#                     st.error("Unable to calculate job match")

#             # ------------------------------------------------------------

#             st.subheader("✅ Strengths")
#             for p in result.get("Strengths", []):
#                 st.write(f"- {p}")

#             st.subheader("⚠️ Weaknesses")
#             weaknesses = result.get("Weaknesses", {})
#             for importance in ["Critical", "Medium", "Low"]:
#                 points = weaknesses.get(importance, [])
#                 if points:
#                     st.markdown(f"*{importance}*")
#                     for p in points:
#                         st.write(f"- {p}")

#             st.subheader("💡 Suggestions")
#             suggestions = result.get("Suggestions", {})
#             for importance in ["Critical", "Medium", "Low"]:
#                 points = suggestions.get(importance, [])
#                 if points:
#                     st.markdown(f"*{importance}*")
#                     for p in points:
#                         st.write(f"- {p}")

#     except Exception as e:
#         st.error(f"An error occurred: {e}")

# if st.button("Enter mock interview", disabled=not st.session_state.allow_mock):
#     st.switch_page("pages/MockInterview.py")

# # ------------ AI Chatbot (Career Assistant) ------------
# st.markdown("---")
# st.subheader("💬 Ask AI Your Doubts (Career Assistant)")

# if "bot_chat_history" not in st.session_state:
#     st.session_state.bot_chat_history = []

# user_msg = st.chat_input("Ask about resume, job role, interview tips, skills, projects...")

# if user_msg:
#     st.session_state.bot_chat_history.append(("You", user_msg))
#     bot_response = chatbot_reply(
#         user_question=user_msg,
#         resume=st.session_state.get("resume"),
#         role=st.session_state.get("role"),
#         job_description=st.session_state.get("job_description")
#     )
#     st.session_state.bot_chat_history.append(("AI Bot", bot_response))

# for sender, msg in st.session_state.bot_chat_history:
#     with st.chat_message("user" if sender == "You" else "assistant"):
#         st.write(msg)


import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import tempfile
from services.ResumeModel import (
    analyze_resume_langgraph,
    display_basic_info_from_resume,
    analyze_job_fit
)

from services.ChatBotModel import chatbot_reply

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📃",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("AI Resume Analyzer")
st.markdown("Upload your resume and get AI-powered feedback tailored to your needs!")

if "resume" not in st.session_state:
    st.session_state.resume = None
if "role" not in st.session_state:
    st.session_state.role = None
if "allow_mock" not in st.session_state:
    st.session_state.allow_mock = False
if "job_description" not in st.session_state:
    st.session_state.job_description = None

uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targeting")
job_description = st.text_area("Paste the Job Description (JD)", height=180, placeholder="Paste the JD here")
analyze = st.button("Analyze Resume")

def extract_text_from_pdf_filelike(file_like):
    text = ""
    try:
        # defensive: ensure the file pointer is at the start for repeated reads
        try:
            file_like.seek(0)
        except Exception:
            pass

        if hasattr(file_like, "read") and hasattr(file_like, "name"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_like.getbuffer())
                tmp_path = tmp.name
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            # if someone passed a path-like object
            with pdfplumber.open(file_like) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
    except Exception:
        text = ""
    return text

def extract_text_from_file(uploaded_file):
    # make extraction resilient to repeated reads
    try:
        if uploaded_file.type == "application/pdf":
            # pdf path uses the pdf helper that uses getbuffer() safely
            return extract_text_from_pdf_filelike(uploaded_file)
        else:
            # for text files, use getbuffer() and decode (does not advance a read pointer the same way)
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            try:
                return uploaded_file.getbuffer().tobytes().decode("utf-8", errors="ignore")
            except Exception:
                # fallback to read() if getbuffer fails
                try:
                    uploaded_file.seek(0)
                except Exception:
                    pass
                try:
                    return uploaded_file.read().decode("utf-8", errors="ignore")
                except Exception:
                    return ""
    except Exception:
        return ""

if analyze:
    if not uploaded_file:
        st.error("⚠️ Please upload a resume file before analyzing.")
        st.stop()

    if not job_role.strip():
        st.error("⚠️ Please enter the job role before analyzing your resume.")
        st.stop()

    try:
        # Ensure file pointer at start before extracting (defensive)
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("⚠️ File doesn't contain any content.")
            st.stop()

        st.session_state.resume = file_content.strip()
        st.session_state.role = job_role.strip()
        st.session_state.job_description = job_description.strip()

        if uploaded_file.type == "application/pdf":
            # ensure pointer at start before writing temp PDF
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                display_basic_info_from_resume(resume_data=None, pdf_path=tmp_path)
            except Exception as e:
                st.warning(f"Could not show basic info block: {e}")
        else:
            txt = file_content
            import re
            email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", txt)
            phone_match = re.search(r"\+?\d[\d\s\-]{8,15}", txt)
            first_line = next((line.strip() for line in txt.splitlines() if line.strip()), "Not Found")
            st.header("*Resume Analysis*")
            st.success("Hello " + first_line)
            st.subheader("*Your Basic info*")
            try:
                st.text("Name: " + first_line)
                st.text("Email: " + (email_match.group() if email_match else "Not Found"))
                st.text("Contact: " + (phone_match.group() if phone_match else "Not Found"))
                st.text("Resume pages: 1")
            except Exception:
                pass
            st.markdown("You are looking Fresher.")

        with st.spinner("Analyzing your resume using LangChain..."):
            result = analyze_resume_langgraph(file_content, job_role)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.write(result.get("raw_output", "No raw output available"))
        else:
            st.session_state.allow_mock = True
            overall_score = result.get("Overall_Score", 0)
            st.subheader(f"🏆 Overall Score: {overall_score}/100")

            category_scores = result.get("Category_Scores", {})
            df_scores = pd.DataFrame({
                "Category": list(category_scores.keys()),
                "Score": list(category_scores.values())
            })

            fig_radar = px.line_polar(
                df_scores,
                r="Score",
                theta="Category",
                line_close=True,
                title="Radar View",
                color_discrete_sequence=["#0072B2"]
            )
            fig_radar.update_traces(fill="toself", hovertemplate="%{theta}: %{r}")
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            st.subheader("📈 Category-wise Scores")
            st.table(df_scores)

            # ---------------- SKILL GAP FEATURE ----------------
            st.subheader("🧠 Skill Gap Analysis")
            try:
                skill_gap_prompt = f"""
                From the resume and the job role below, extract ONLY the skills and compare them.
                Return in JSON format with keys:
                "resume_skills", "job_required_skills", "skills_to_improve"
                Resume:
                {file_content}
                Job Role:
                {job_role}
                """
                skill_gap_output = analyze_resume_langgraph(skill_gap_prompt, job_role)

                resume_skills = skill_gap_output.get("resume_skills", [])
                job_required_skills = skill_gap_output.get("job_required_skills", [])
                skills_to_improve = skill_gap_output.get("skills_to_improve", [])

                st.write("### 🔹 Skills in Resume")
                st.write(", ".join(resume_skills) if resume_skills else "Not detected")

                st.write("### 🔹 Skills Required for Role")
                st.write(", ".join(job_required_skills) if job_required_skills else "Not present in JD")

                st.write("### 🔥 Skills You Need to Improve")
                if skills_to_improve:
                    for s in skills_to_improve:
                        st.write(f"- {s}")
                else:
                    st.success("🎉 No major skill gaps detected — you're a strong match!")
            except Exception as e:
                st.warning(f"Skill-gap check unavailable: {e}")

            # ---------------- JOB MATCH SCORE SECTION ----------------
            st.markdown("---")
            st.subheader("🎯 Job Match Score & Actionable Tip")

            if st.session_state.job_description:
                job_match = analyze_job_fit(st.session_state.resume, st.session_state.job_description)
                if "error" not in job_match:
                    st.success(f"⭐ Match Score: {job_match['match_score']} / 10")
                    st.info(f"📌 Match Level: **{job_match['match_label']}**")
                    st.warning("💡 Actionable Tip: " + job_match["actionable_tip"])

                    # ---- Visual Job Match Bar ----
                    score = job_match["match_score"]
                    if score >= 8:
                        bar_color = "🟢 Strong Match"
                    elif score >= 5:
                        bar_color = "🟠 Moderate Match"
                    else:
                        bar_color = "🔴 Weak Match"

                    st.markdown(f"### {bar_color}")
                    st.progress(min(score / 10, 1.0))
                else:
                    st.error("Unable to calculate job match")

            # ------------------------------------------------------------

            st.subheader("✅ Strengths")
            for p in result.get("Strengths", []):
                st.write(f"- {p}")

            st.subheader("⚠️ Weaknesses")
            weaknesses = result.get("Weaknesses", {})
            for importance in ["Critical", "Medium", "Low"]:
                points = weaknesses.get(importance, [])
                if points:
                    st.markdown(f"*{importance}*")
                    for p in points:
                        st.write(f"- {p}")

            st.subheader("💡 Suggestions")
            suggestions = result.get("Suggestions", {})
            for importance in ["Critical", "Medium", "Low"]:
                points = suggestions.get(importance, [])
                if points:
                    st.markdown(f"*{importance}*")
                    for p in points:
                        st.write(f"- {p}")

    except Exception as e:
        st.error(f"An error occurred: {e}")

if st.button("Enter mock interview", disabled=not st.session_state.allow_mock):
    st.switch_page("pages/MockInterview.py")

# ------------ AI Chatbot (Career Assistant) ------------
st.markdown("---")
st.subheader("💬 Ask AI Your Doubts (Career Assistant)")

if "bot_chat_history" not in st.session_state:
    st.session_state.bot_chat_history = []

user_msg = st.chat_input("Ask about resume, job role, interview tips, skills, projects...")

if user_msg:
    st.session_state.bot_chat_history.append(("You", user_msg))
    bot_response = chatbot_reply(
        user_question=user_msg,
        resume=st.session_state.get("resume"),
        role=st.session_state.get("role"),
        job_description=st.session_state.get("job_description")
    )
    st.session_state.bot_chat_history.append(("AI Bot", bot_response))

for sender, msg in st.session_state.bot_chat_history:
    with st.chat_message("user" if sender == "You" else "assistant"):
        st.write(msg)
