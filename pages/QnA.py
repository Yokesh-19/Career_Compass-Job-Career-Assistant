import os
os.environ["GRPC_VERBOSITY"] = "ERROR"  # Reduce logging overhead

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)
import streamlit as st
import pandas as pd
from services.QnAGeneratorModel import generate_qna_from_resume
from services.PdfGenerator import generate_qna_pdf

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Q&A Generator",
    page_icon="📘",
    layout="wide",
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
        pass

load_css("assets/style.css")

# ============================================
# CUSTOM CSS FOR Q&A PAGE
# ============================================
st.markdown(
    """
    <style>
    /* Q&A specific styles */
    .qna-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .category-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .badge-technical {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-dsa {
        background: rgba(168, 85, 247, 0.2);
        color: #d8b4fe;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }
    
    .badge-behavioral {
        background: rgba(236, 72, 153, 0.2);
        color: #f9a8d4;
        border: 1px solid rgba(236, 72, 153, 0.3);
    }
    
    .badge-scenario {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 1.05rem;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Question and answer styling */
    .question-text {
        color: #c7d2fe;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .answer-text {
        color: #94a3b8;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================
# CHECK ACCESS
# ============================================
if "resume" not in st.session_state or "role" not in st.session_state:
    st.error("⚠️ Please analyze your resume first before generating Q&A.")
    st.markdown("---")
    if st.button("🏠 Go to Home Page", use_container_width=True):
        st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
        st.switch_page("Home.py")
    st.stop()

# ============================================
# SESSION STATE
# ============================================
if "qa_set" not in st.session_state:
    st.session_state.qa_set = None

# ============================================
# HEADER
# ============================================
st.markdown(
    """
    <div class='qna-header'>
        <h1 style='margin: 0; font-size: 2.5rem;'>📘 AI Interview Q&A Generator</h1>
        <p style='margin-top: 0.5rem; color: #94a3b8;'>
            Get personalized interview questions & model answers based on your resume and target role
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================
# INPUT SECTION
# ============================================
st.markdown("### ⚙️ Configuration")

col1, col2 = st.columns([3, 1])

with col1:
    role = st.text_input(
        "🎯 Target Job Role",
        value=st.session_state.role,
        help="The role you're preparing for"
    )

with col2:
    num_questions = st.number_input(
        "📊 Number of Q&A",
        min_value=5,
        max_value=20,
        value=10,
        step=1,
        help="How many questions to generate"
    )

st.markdown("---")

# Generate button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button("⚙️ Generate Q&A Set", use_container_width=True)

# ============================================
# GENERATE Q&A
# ============================================
if generate_btn:
    with st.spinner("🤖 AI is generating personalized questions & answers..."):
        try:
            qna_list = generate_qna_from_resume(
                st.session_state.resume,
                role,
                num_questions
            )
            
            # Check if error occurred
            if isinstance(qna_list, dict) and "error" in qna_list:
                st.error(f"❌ Error generating Q&A: {qna_list.get('error')}")
                if "raw_output" in qna_list:
                    with st.expander("🔍 Debug Info"):
                        st.code(qna_list["raw_output"])
            else:
                st.session_state.qa_set = qna_list
                st.success(f"✅ Generated {len(qna_list)} questions successfully!")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

# ============================================
# DISPLAY Q&A SET
# ============================================
if st.session_state.qa_set:
    st.markdown("---")
    st.markdown("## 🧩 Your Personalized Q&A Set")
    
    df = pd.DataFrame(st.session_state.qa_set)
    
    # Category distribution
    if 'Category' in df.columns:
        st.markdown("### 📊 Question Distribution")
        
        category_counts = df['Category'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        
        cols = [col1, col2, col3, col4]
        for idx, (category, count) in enumerate(category_counts.items()):
            with cols[idx % 4]:
                badge_class = {
                    'Technical': 'badge-technical',
                    'DSA': 'badge-dsa',
                    'Behavioral': 'badge-behavioral',
                    'Scenario': 'badge-scenario'
                }.get(category, 'badge-technical')
                
                st.markdown(
                    f"""
                    <div style='text-align: center; padding: 1rem; background: rgba(255,255,255,0.02); border-radius: 12px;'>
                        <div class='category-badge {badge_class}'>{category}</div>
                        <h2 style='margin: 0.5rem 0 0 0;'>{count}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
    
    # Display questions
    st.markdown("### 📝 Questions & Answers")
    
    for i, row in df.iterrows():
        category = row.get('Category', 'General')
        question = row.get('Question', '')
        answer = row.get('Answer', '')
        
        # Determine badge class
        badge_class = {
            'Technical': 'badge-technical',
            'DSA': 'badge-dsa',
            'Behavioral': 'badge-behavioral',
            'Scenario': 'badge-scenario'
        }.get(category, 'badge-technical')
        
        # Create expander with category badge
        with st.expander(f"**Q{i+1}.** {question[:80]}{'...' if len(question) > 80 else ''}"):
            st.markdown(
                f"""
                <div class='category-badge {badge_class}'>{category}</div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"<div class='question-text'>❓ Question:</div>", unsafe_allow_html=True)
            st.markdown(question)
            
            st.markdown("---")
            
            st.markdown(f"<div class='question-text'>✅ Model Answer:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='answer-text'>{answer}</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # ============================================
    # ACTION BUTTONS
    # ============================================
    st.markdown("### 📥 Export & Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download PDF
        try:
            pdf_data = generate_qna_pdf(df, role)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_data,
                file_name=f"{role.replace(' ', '_')}_QnA.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
    
    with col2:
        # Regenerate
        if st.button("🔄 Regenerate Q&A", use_container_width=True):
            st.session_state.qa_set = None
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.rerun()
    
    with col3:
        # Back to home
        if st.button("🏠 Back to Home", use_container_width=True):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("Home.py")

# ============================================
# TIPS SECTION
# ============================================
if not st.session_state.qa_set:
    st.markdown("---")
    st.markdown("### 💡 How to Use This Tool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class='skill-card'>
                <h4>📋 What You'll Get:</h4>
                <ul>
                    <li>Role-specific technical questions</li>
                    <li>Data structures & algorithms problems</li>
                    <li>Behavioral interview questions</li>
                    <li>Scenario-based questions</li>
                    <li>Model answers for each question</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class='skill-card'>
                <h4>🎯 Best Practices:</h4>
                <ul>
                    <li>Practice answering out loud</li>
                    <li>Time yourself (2-3 min per answer)</li>
                    <li>Adapt model answers to your style</li>
                    <li>Focus on storytelling with examples</li>
                    <li>Review before every interview</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; padding: 1rem 0;'>
        # <p style='font-size: 0.9rem;'>🤖 Powered by Google Gemini AI</p>
        <p style='font-size: 0.8rem;'>💡 Tip: Practice these questions regularly to build confidence!</p>
    </div>
    """,
    unsafe_allow_html=True
)