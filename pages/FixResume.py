import os
os.environ["GRPC_VERBOSITY"] = "ERROR"

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(func, *args, **kwargs):
    return func(*args, **kwargs)

import streamlit as st
import os
import json
import re
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Fix My Resume",
    page_icon="🔧",
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
# CUSTOM CSS
# ============================================
st.markdown(
    """
    <style>
    .fix-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .comparison-box {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .old-resume {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
        border-left: 4px solid #ef4444;
    }
    
    .new-resume {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
        border-left: 4px solid #10b981;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================
# CHECK ACCESS
# ============================================
if "resume" not in st.session_state or not st.session_state.resume:
    st.error("⚠️ Please analyze a resume first before using Resume Fixer.")
    if st.button("🏠 Go to Home Page", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# ============================================
# SESSION STATE
# ============================================
if "fixed_resume" not in st.session_state:
    st.session_state.fixed_resume = None
if "fix_changes" not in st.session_state:
    st.session_state.fix_changes = None

# ============================================
# AI RESUME FIXER FUNCTION
# ============================================
def fix_resume_with_ai(resume_text, role, job_description=""):
    """Optimized resume fixer"""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.4,
            max_tokens=4000
        )
        
        # CRITICAL: Truncate input to save tokens
        MAX_CHARS = 3000
        if len(resume_text) > MAX_CHARS:
            resume_text = resume_text[:MAX_CHARS]
        
        # Shorter, more focused prompt
        prompt = f"""Fix this resume for {role}. Be concise.

Resume:
{resume_text}

JD: {job_description[:500] if job_description else "None"}

Return JSON:
{{
    "fixed_resume": "improved version (keep same length)",
    "key_changes": ["list 5-8 specific improvements"]
}}

Focus on: grammar, action verbs, quantification, ATS optimization."""
        
        response = llm.invoke(prompt)
        content = response.content
        
        cleaned = re.sub(r"^```json\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)
        result = json.loads(cleaned)
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

# ============================================
# PDF GENERATOR FUNCTION
# ============================================
def generate_resume_pdf(resume_text, filename="Fixed_Resume.pdf"):
    """Generate a professional PDF from resume text"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#e5e7eb'),
        borderPadding=4,
        backColor=colors.HexColor('#f3f4f6')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#374151'),
        spaceAfter=6,
        leading=14,
        fontName='Helvetica'
    )
    
    # Content
    content = []
    
    # Parse resume text into sections
    lines = resume_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            content.append(Spacer(1, 6))
            continue
        
        # Detect headings (ALL CAPS or ends with :)
        if line.isupper() or line.endswith(':'):
            content.append(Paragraph(line, heading_style))
        # Detect name (first non-empty line, typically)
        elif len(content) < 3 and len(line.split()) <= 4:
            content.append(Paragraph(line, title_style))
        else:
            # Regular text
            content.append(Paragraph(line, body_style))
    
    # Footer
    content.append(Spacer(1, 12))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    content.append(Paragraph(
        f"Generated by AI Resume Analyzer on {datetime.now().strftime('%B %d, %Y')}",
        footer_style
    ))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================
# HEADER
# ============================================
st.markdown(
    """
    <div class='fix-header'>
        <h1 style='margin: 0; font-size: 2.5rem;'>🔧 AI Resume Fixer</h1>
        <p style='margin-top: 0.5rem; color: #94a3b8;'>
            Let AI fix errors, improve content, and optimize your resume for ATS
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================
# MAIN CONTENT
# ============================================
if not st.session_state.fixed_resume:
    st.markdown("### 🎯 What Will Be Fixed?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class='skill-card'>
                <h4>✅ Improvements Include:</h4>
                <ul>
                    <li>✏️ Fix grammar & spelling errors</li>
                    <li>📊 Add quantifiable achievements</li>
                    <li>💪 Strengthen action verbs</li>
                    <li>🎯 Tailor to target role</li>
                    <li>🤖 Optimize for ATS systems</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class='skill-card'>
                <h4>🛡️ What's Preserved:</h4>
                <ul>
                    <li>📋 Same structure & sections</li>
                    <li>✅ All your real achievements</li>
                    <li>📝 Your actual experience</li>
                    <li>🎓 Education & certifications</li>
                    <li>👤 Personal information</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    st.markdown("### 📄 Current Resume Preview")
    with st.expander("Click to view your current resume", expanded=False):
        st.text_area(
            "Your Resume",
            value=st.session_state.resume[:2000] + "..." if len(st.session_state.resume) > 2000 else st.session_state.resume,
            height=300,
            disabled=True
        )
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Fix My Resume with AI", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is analyzing and improving your resume... This may take 30-60 seconds."):
                result = fix_resume_with_ai(
                    st.session_state.resume,
                    st.session_state.role,
                    st.session_state.get("job_description", "")
                )
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.session_state.fixed_resume = result.get("fixed_resume", "")
                    st.session_state.fix_changes = result.get("key_changes", [])
                    st.success("✅ Resume has been improved successfully!")
                    st.balloons()
                    st.rerun()

else:
    # Display fixed resume
    st.markdown("### ✅ Your Resume Has Been Improved!")
    
    # Key changes
    st.markdown("### 📝 Key Improvements Made:")
    
    if st.session_state.fix_changes:
        for idx, change in enumerate(st.session_state.fix_changes, 1):
            st.success(f"**{idx}.** {change}")
    
    st.markdown("---")
    
    # Side by side comparison
    st.markdown("### 📊 Before & After Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ❌ Original Resume")
        st.markdown('<div class="comparison-box old-resume">', unsafe_allow_html=True)
        st.text_area(
            "Original",
            value=st.session_state.resume[:1500] + "..." if len(st.session_state.resume) > 1500 else st.session_state.resume,
            height=400,
            disabled=True,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ✅ Improved Resume")
        st.markdown('<div class="comparison-box new-resume">', unsafe_allow_html=True)
        st.text_area(
            "Fixed",
            value=st.session_state.fixed_resume[:1500] + "..." if len(st.session_state.fixed_resume) > 1500 else st.session_state.fixed_resume,
            height=400,
            disabled=True,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Full improved resume
    st.markdown("### 📄 Full Improved Resume")
    st.text_area(
        "Complete Fixed Resume",
        value=st.session_state.fixed_resume,
        height=400,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Action buttons
    st.markdown("### 📥 Download Your Improved Resume")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download as PDF
        try:
            pdf_data = generate_resume_pdf(st.session_state.fixed_resume)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_data,
                file_name=f"Fixed_Resume_{st.session_state.role.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
    
    with col2:
        # Download as TXT
        st.download_button(
            label="📝 Download as TXT",
            data=st.session_state.fixed_resume,
            file_name=f"Fixed_Resume_{st.session_state.role.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        # Copy to clipboard (using text area + instruction)
        if st.button("📋 Show Copy Instructions", use_container_width=True):
            st.info("💡 Select all text above and press Ctrl+C (Windows) or Cmd+C (Mac) to copy!")
    
    st.markdown("---")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Fix Again", use_container_width=True):
            st.session_state.fixed_resume = None
            st.session_state.fix_changes = None
            st.rerun()
    
    with col2:
        if st.button("✅ Use Fixed Resume", use_container_width=True, type="primary"):
            # Update the main resume in session state
            st.session_state.resume = st.session_state.fixed_resume
            st.session_state.fixed_resume_used = True
            st.session_state.analysis_result = None  # Clear old analysis
            
            # Show success message
            st.success("✅ Fixed resume is now your active resume!")
            st.info("📄 Redirecting to Home page to analyze the fixed resume...")
            
            # Wait a moment then redirect
            time.sleep(1)
            st.switch_page("Home.py")
    
    with col3:
        if st.button("📊 View Analysis", use_container_width=True):
            st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
            st.switch_page("Home.py")

# ============================================
# TIPS SECTION
# ============================================
st.markdown("---")
with st.expander("💡 Tips for Using Your Fixed Resume"):
    st.markdown("""
    ### Next Steps:
    1. **Review Carefully** - Read through all changes and ensure accuracy
    2. **Customize Further** - Tailor specific sections for each job application
    3. **Update Regularly** - Keep adding new achievements and skills
    4. **Use Keywords** - Ensure job-specific keywords are present
    5. **Get Feedback** - Have a friend or mentor review it
    
    ### Best Practices:
    - ✅ Save multiple versions for different roles
    - ✅ Update your LinkedIn profile to match
    - ✅ Use the same keywords in your cover letter
    - ✅ Keep it to 1-2 pages maximum
    - ✅ Use a clean, ATS-friendly format
    
    ### What to Do with This Resume:
    - 📧 Use it for online job applications
    - 💼 Update your LinkedIn profile
    - 📨 Attach to email applications
    - 🖨️ Print for in-person interviews
    - 📱 Save PDF on your phone for quick access
    """)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; padding: 1rem 0;'>
        # <p style='font-size: 0.9rem;'>🤖 Powered by Google Gemini AI</p>
        <p style='font-size: 0.8rem;'>💡 Always review AI-generated content before using!</p>
    </div>
    """,
    unsafe_allow_html=True
)