import streamlit as st
import pandas as pd
from services.QnAGeneratorModel import generate_qna_from_resume
from services.PdfGenerator import generate_qna_pdf

st.set_page_config(page_title="AI Q&A Generator", page_icon="📘", layout="wide")
st.title("📘 AI-Generated Interview Q&A")
st.caption("Get tailored interview questions & answers based on your resume and job role.")

if "resume" not in st.session_state or "role" not in st.session_state:
    st.warning("⚠️ Please analyze your resume first before generating Q&A.")
    st.stop()

if "qa_set" not in st.session_state:
    st.session_state.qa_set = None

col1, col2 = st.columns([3, 1])
with col1:
    role = st.text_input("Job Role", value=st.session_state.role)
with col2:
    num_questions = st.number_input("Number of Q&A", min_value=5, max_value=20, value=10, step=1)

generate_btn = st.button("⚙️ Generate Q&A")

if generate_btn:
    with st.spinner("Generating interview questions & answers..."):
        qna_list = generate_qna_from_resume(st.session_state.resume, role, num_questions)
        st.session_state.qa_set = qna_list
        st.success(f"✅ Generated {len(qna_list)} questions successfully!")

if st.session_state.qa_set:
    st.subheader("🧩 Generated Q&A Set")

    df = pd.DataFrame(st.session_state.qa_set)
    for i, row in df.iterrows():
        with st.expander(f"Q{i+1}. {row['Question'][:80]}..."):
            st.markdown(f"**Category:** {row['Category']}")
            st.markdown(f"**Q:** {row['Question']}")
            st.markdown(f"**A:** {row['Answer']}")

    # Optional: Export section
    pdf_data = generate_qna_pdf(df, role)
    st.download_button(
        label="📄 Download Q&A as PDF",
        data=pdf_data,
        file_name=f"{role.replace(' ', '_')}_QnA.pdf",
        mime="application/pdf",
    )

    if st.button("🔁 Regenerate"):
        st.session_state.qa_set = None
        st.rerun()