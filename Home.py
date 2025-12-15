
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)

import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import courses
import re

from services.ResumeModel import (
    analyze_resume_langgraph,
    display_basic_info_from_resume,
    analyze_job_fit
)

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📃",
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
        st.warning("⚠️ CSS file not found. Using default styles.")

load_css("assets/style.css")

# Add custom CSS for animations and scroll behavior
st.markdown("""
<style>
/* Spinning pie chart animation */
@keyframes spin-pie {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.spinning-chart {
    animation: spin-pie 20s linear infinite;
    transform-origin: center center;
}

/* Smooth scroll behavior */
html {
    scroll-behavior: smooth;
}

/* Scroll to top anchor */
.scroll-anchor {
    position: relative;
    top: -80px;
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION (PERSISTENT)
# ============================================
if "resume" not in st.session_state:
    st.session_state.resume = None
if "role" not in st.session_state:
    st.session_state.role = None
if "allow_mock" not in st.session_state:
    st.session_state.allow_mock = False
if "job_description" not in st.session_state:
    st.session_state.job_description = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "basic_info" not in st.session_state:
    st.session_state.basic_info = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "fixed_resume_used" not in st.session_state:
    st.session_state.fixed_resume_used = False
if "job_match_result" not in st.session_state:
    st.session_state.job_match_result = None
if "file_type" not in st.session_state:
    st.session_state.file_type = None
# NEW: Cache key to prevent duplicate API calls
if "analysis_cache_key" not in st.session_state:
    st.session_state.analysis_cache_key = None

# ============================================
# HEADER SECTION
# ============================================
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
st.title("🎯 AI Resume Analyzer")
st.markdown(
    """
    <div style='text-align: center; color: #94a3b8; margin-bottom: 2rem;'>
        Upload your resume and get AI-powered feedback tailored to your career goals!
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================
# HELPER FUNCTIONS
# ============================================
def extract_text_from_pdf_filelike(file_like):
    """Extract text from PDF file-like object"""
    text = ""
    try:
        file_like.seek(0)
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
            with pdfplumber.open(file_like) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        text = ""
    return text


def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file (PDF or TXT)"""
    try:
        if uploaded_file.type == "application/pdf":
            return extract_text_from_pdf_filelike(uploaded_file)
        else:
            uploaded_file.seek(0)
            return uploaded_file.getbuffer().tobytes().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""


def extract_and_save_basic_info(file_content, file_type, pdf_path=None):
    """Extract and save basic info to session state WITHOUT API calls"""
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", file_content)
    phone_match = re.search(r"\+?\d[\d\s\-]{8,15}", file_content)
    first_line = next((l.strip() for l in file_content.splitlines() if l.strip()), "Not Found")
    
    # Calculate actual page count
    pages = 1
    if file_type == "application/pdf" and pdf_path:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = len(pdf.pages)
        except:
            pages = 1
    
    basic_info = {
        "name": first_line,
        "email": email_match.group() if email_match else "Not Found",
        "phone": phone_match.group() if phone_match else "Not Found",
        "pages": pages
    }
    
    st.session_state.basic_info = basic_info
    return basic_info


def display_basic_info():
    """Display basic info from session state matching the original design"""
    if st.session_state.basic_info:
        info = st.session_state.basic_info
        
        # Header with dark background
        st.markdown("## Resume Analysis")
        
        # Green greeting box
        st.success(f"Hello {info['name']}")
        
        # Basic info section
        st.subheader("**Your Basic info**")
        
        # Display info in text format (not in a card)
        st.text(f"Name: {info['name']}")
        st.text(f"Email: {info['email']}")
        st.text(f"Contact: {info['phone']}")
        st.text(f"Resume pages: {info['pages']}")
        
        # Experience level message
        st.markdown("You are at intermediate level!")


def create_gauge_chart(score, title):
    """Create a beautiful gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': '#c7d2fe'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#667eea"},
            'bar': {'color': "#667eea"},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 2,
            'bordercolor': "rgba(102, 126, 234, 0.3)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [50, 75], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#c7d2fe", 'family': "Inter"},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_animated_pie_chart(df_scores):
    """Create an animated spinning pie chart"""
    fig = px.pie(
        df_scores,
        values='Score',
        names='Category',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#c7d2fe", 'family': "Inter"},
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [{
                'label': 'Spin',
                'method': 'animate',
                'args': [None, {
                    'frame': {'duration': 50, 'redraw': True},
                    'fromcurrent': True,
                    'mode': 'immediate',
                    'transition': {'duration': 50}
                }]
            }]
        }]
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label', rotation=0)
    
    frames = []
    for angle in range(0, 360, 10):
        frames.append(go.Frame(
            data=[go.Pie(
                values=df_scores['Score'],
                labels=df_scores['Category'],
                hole=0.4,
                rotation=angle
            )]
        ))
    
    fig.frames = frames
    
    return fig


def generate_cache_key(resume, role, job_description):
    """Generate unique cache key for API results"""
    import hashlib
    content = f"{resume[:500]}{role}{job_description[:200]}"
    return hashlib.md5(content.encode()).hexdigest()


# ============================================
# CHECK FOR FIXED RESUME
# ============================================
if st.session_state.get("fixed_resume_used") and "fixed_resume" in st.session_state:
    st.session_state.analysis_result = None
    st.session_state.job_match_result = None
    st.session_state.analysis_cache_key = None  # Reset cache
    
    with st.spinner("🤖 Analyzing your fixed resume..."):
        try:
            result = analyze_resume_langgraph(
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description or ""
            )
            st.session_state.analysis_result = result
            st.session_state.analysis_cache_key = generate_cache_key(
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description or ""
            )
            st.success("✅ Fixed resume analyzed successfully!")
            st.balloons()
            
            st.session_state.fixed_resume_used = False
            st.rerun()
        except Exception as e:
            st.error(f"Error analyzing fixed resume: {e}")
            st.session_state.fixed_resume_used = False

# ============================================
# SHOW PREVIOUS ANALYSIS IF EXISTS
# ============================================
if st.session_state.analysis_result and st.session_state.resume:
    st.info(f"📄 **Previous Analysis Loaded:** {st.session_state.uploaded_filename or 'Resume'}")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Upload New Resume"):
            st.session_state.resume = None
            st.session_state.role = None
            st.session_state.job_description = None
            st.session_state.analysis_result = None
            st.session_state.basic_info = None
            st.session_state.uploaded_filename = None
            st.session_state.allow_mock = False
            st.session_state.fixed_resume_used = False
            st.session_state.job_match_result = None
            st.session_state.file_type = None
            st.session_state.analysis_cache_key = None  # Clear cache
            if "fixed_resume" in st.session_state:
                del st.session_state.fixed_resume
            st.rerun()

# ============================================
# INPUT SECTION (Only if no previous analysis)
# ============================================
if not st.session_state.analysis_result:
    st.markdown("### 📄 Upload Resume & Job Details")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "🔎 Upload your resume",
            type=["pdf", "txt"],
            help="Supported formats: PDF, TXT"
        )

    with col2:
        job_role = st.text_input(
            "💼 Target Job Role",
            placeholder="e.g., Software Engineer, Data Analyst",
            help="Enter the job title you're applying for"
        )

    job_description = st.text_area(
        "📋 Job Description (Optional but Recommended)",
        height=150,
        placeholder="Paste the complete job description here for better analysis...",
        help="Including the JD helps us provide more accurate skill gap analysis"
    )

    st.markdown("---")

    analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
    with analyze_col2:
        analyze = st.button("🚀 Analyze Resume", use_container_width=True)

    if analyze:
        if not uploaded_file:
            st.error("⚠️ Please upload a resume file before analyzing.")
            st.stop()

        if not job_role.strip():
            st.error("⚠️ Please enter the target job role before analyzing.")
            st.stop()

        try:
            uploaded_file.seek(0)
            file_content = extract_text_from_file(uploaded_file)

            if not file_content.strip():
                st.error("⚠️ The uploaded file doesn't contain any readable content.")
                st.stop()

            # Store data in session state
            st.session_state.resume = file_content.strip()
            st.session_state.role = job_role.strip()
            st.session_state.job_description = job_description.strip()
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.file_type = uploaded_file.type
            st.session_state.fixed_resume_used = False

            # Generate cache key for this analysis
            cache_key = generate_cache_key(
                st.session_state.resume,
                st.session_state.role,
                st.session_state.job_description
            )

            # OPTIMIZATION: Check if we already analyzed this exact combination
            if st.session_state.analysis_cache_key == cache_key:
                st.info("✅ Using cached analysis results to save API quota!")
            else:
                # Extract basic info WITHOUT API call
                st.markdown("<div id='candidate-profile' class='scroll-anchor'></div>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("## 👤 Candidate Profile")
                
                if uploaded_file.type == "application/pdf":
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    extract_and_save_basic_info(file_content, uploaded_file.type, tmp_path)
                else:
                    extract_and_save_basic_info(file_content, uploaded_file.type)
                
                display_basic_info()

                st.markdown("---")
                
                # SINGLE API CALL for main analysis
                with st.spinner("🤖 AI is analyzing your resume... This may take a moment."):
                    result = analyze_resume_langgraph(file_content, job_role, job_description)
                    st.session_state.analysis_result = result
                    st.session_state.analysis_cache_key = cache_key
                    
                    # OPTIMIZATION: Only call job fit IF job description provided
                    # AND if not already included in main analysis
                    if job_description.strip():
                        if "match_score" not in result:  # Only if not already computed
                            job_match = analyze_job_fit(file_content, job_description)
                            st.session_state.job_match_result = job_match
                        else:
                            st.session_state.job_match_result = {
                                "match_score": result.get("match_score", 0),
                                "match_label": result.get("match_label", "Unknown"),
                                "actionable_tip": result.get("actionable_tip", "")
                            }
                    
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ An error occurred during analysis: {str(e)}")

# ============================================
# DISPLAY SAVED ANALYSIS WITH BASIC INFO
# ============================================
if st.session_state.analysis_result:
    # DISPLAY BASIC INFO FIRST
    st.markdown("<div id='candidate-profile' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 👤 Candidate Profile")
    display_basic_info()
    
    result = st.session_state.analysis_result
    
    overall_score = result.get("Overall_Score", 0)
    
    st.markdown("<div id='analysis-results' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 📊 Resume Analysis Results")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        fig_gauge = create_gauge_chart(overall_score, "Overall Resume Score")
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<div id='category-scores' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("### 📈 Category-wise Performance")
    
    category_scores = result.get("Category_Scores", {})
    
    if category_scores:
        score_col1, score_col2 = st.columns(2)
        
        categories = list(category_scores.keys())
        scores = list(category_scores.values())
        
        df_scores = pd.DataFrame({
            "Category": categories,
            "Score": scores
        })
        
        fig_bar = go.Figure(data=[
            go.Bar(
                x=scores,
                y=categories,
                orientation='h',
                marker=dict(
                    color=scores,
                    colorscale='Viridis',
                    line=dict(color='rgba(102, 126, 234, 0.5)', width=1)
                ),
                text=scores,
                textposition='auto',
            )
        ])
        
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "#c7d2fe", 'family': "Inter"},
            height=400,
            xaxis=dict(title="Score", range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(title="", gridcolor='rgba(255,255,255,0.1)'),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        with score_col1:
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with score_col2:
            fig_pie = create_animated_pie_chart(df_scores)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<div id='skill-gap' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 🧠 Skill Gap Analysis")

    resume_skills = result.get("resume_skills", []) or []
    job_required_skills = result.get("job_required_skills", []) or []
    skills_to_improve = result.get("skills_to_improve", []) or []

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            f"""
            <div class='skill-card'>
                <div class='card-title'>
                    <span>✅</span>
                    <strong>Skills in Your Resume</strong>
                    <span class='count-bubble'>{len(resume_skills)}</span>
                </div>
                <div class='tags-flow'>
                    {''.join(f"<div class='skill-tag skill-resume'>{s}</div>" for s in resume_skills) if resume_skills else "<p>No skills detected</p>"}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class='skill-card'>
                <div class='card-title'>
                    <span>🎯</span>
                    <strong>Skills Required for Role</strong>
                    <span class='count-bubble'>{len(job_required_skills)}</span>
                </div>
                <div class='tags-flow'>
                    {''.join(f"<div class='skill-tag skill-required'>{s}</div>" for s in job_required_skills) if job_required_skills else "<p>No specific skills detected in JD</p>"}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if skills_to_improve:
        st.markdown("### 🔥 Skills You Need to Develop")
        st.markdown(
            """
            <div class='skill-card' style='background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));'>
            """,
            unsafe_allow_html=True
        )
        for skill in skills_to_improve:
            st.markdown(f"- **{skill}**")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("🎉 Excellent! No major skill gaps detected. You're a strong match!")

    if skills_to_improve:
        st.markdown("<div id='courses' class='scroll-anchor'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## 🎓 Recommended Learning Path")
        
        for idx, skill in enumerate(skills_to_improve, 1):
            with st.expander(f"📚 Courses for: **{skill}**", expanded=(idx == 1)):
                suggested_courses = courses.get_courses_for_skill(skill)[:3]
                
                if suggested_courses:
                    for course in suggested_courses:
                        title = course.get("title", "Course")
                        url = course.get("url", "#")
                        st.markdown(f"- 🔗 [{title}]({url})")
                else:
                    st.info(f"💡 Search for '{skill}' courses on:")
                    links = courses.platform_search_links(skill)
                    for platform, url in list(links.items())[:3]:
                        st.markdown(f"  - [{platform}]({url})")

    st.markdown("<div id='job-match' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 🎯 Job Compatibility Analysis")

    # OPTIMIZATION: Use cached job match result
    if st.session_state.job_description:
        if st.session_state.job_match_result is None:
            # Only call if we don't have it cached
            with st.spinner("Analyzing job compatibility..."):
                job_match = analyze_job_fit(
                    st.session_state.resume,
                    st.session_state.job_description
                )
                st.session_state.job_match_result = job_match
        else:
            job_match = st.session_state.job_match_result

        if "error" not in job_match:
            st.session_state.allow_mock = True
            
            match_score = job_match.get("match_score", 0)
            match_label = job_match.get("match_label", "Unknown")
            actionable_tip = job_match.get("actionable_tip", "")

            col1, col2 = st.columns([1, 2])
            
            with col1:
                fig_match = create_gauge_chart(match_score * 10, "Job Match Score")
                st.plotly_chart(fig_match, use_container_width=True)
            
            with col2:
                st.markdown(
                    f"""
                    <div class='skill-card'>
                        <h3>📊 Match Assessment</h3>
                        <p><strong>Score:</strong> {round(match_score, 1)}/10</p>
                        <p><strong>Level:</strong> {match_label}</p>
                        <p><strong>💡 Pro Tip:</strong> {actionable_tip}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            score_normalized = min(match_score / 10, 1.0)
            st.progress(score_normalized)

    st.markdown("<div id='strengths-weaknesses' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 💪 Strengths & Areas for Improvement")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Strengths")
        strengths = result.get("Strengths", [])
        if strengths:
            for strength in strengths:
                st.success(f"✓ {strength}")
        else:
            st.info("No specific strengths highlighted")

    with col2:
        st.markdown("### ⚠️ Weaknesses")
        weaknesses = result.get("Weaknesses", {})
        
        for level in ["Critical", "Medium", "Low"]:
            items = weaknesses.get(level, [])
            if items:
                emoji = "🔴" if level == "Critical" else "🟡" if level == "Medium" else "🟢"
                st.markdown(f"**{emoji} {level}**")
                for item in items:
                    st.warning(f"• {item}")

    st.markdown("<div id='suggestions' class='scroll-anchor'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 💡 Improvement Suggestions")
    
    suggestions = result.get("Suggestions", {})
    
    for level in ["Critical", "Medium", "Low"]:
        items = suggestions.get(level, [])
        if items:
            emoji = "🔥" if level == "Critical" else "⚡" if level == "Medium" else "💫"
            with st.expander(f"{emoji} {level} Priority Suggestions", expanded=(level == "Critical")):
                for suggestion in items:
                    st.info(f"💡 {suggestion}")

# ============================================
# ACTION BUTTONS
# ============================================
if st.session_state.analysis_result:
    st.markdown("---")
    st.markdown("## 🚀 Next Steps")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔧 Fix My Resume", use_container_width=True):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("pages/FixResume.py")
    
    with col2:
        if st.button("🎤 Mock Interview", use_container_width=True, disabled=not st.session_state.allow_mock):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("pages/MockInterview.py")
    
    with col3:
        if st.button("📘 Generate Q&A", use_container_width=True):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("pages/QnA.py")
    
    with col4:
        if st.button("💬 Chat Assistant", use_container_width=True):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("pages/ChatBot.py")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; padding: 2rem 0;'>
        <p style='font-size: 0.85rem;'>💡 Tip: Your analysis is saved until you upload a new resume!</p>
    </div>
    """,
    unsafe_allow_html=True
)