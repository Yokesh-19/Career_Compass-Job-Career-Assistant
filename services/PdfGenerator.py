from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
import pandas as pd
from datetime import datetime

def generate_qna_pdf(df: pd.DataFrame, role: str) -> bytes:
    """
    Generate a formatted PDF containing Q&A pairs for a given job role.

    Args:
        df (pd.DataFrame): DataFrame with columns ['Category', 'Question', 'Answer']
        role (str): The job role name

    Returns:
        bytes: PDF binary data
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    # --- Custom Styles ---
    title_style = ParagraphStyle(
        "title_style",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#1E88E5"),
        spaceAfter=12,
    )
    q_style = ParagraphStyle(
        "q_style",
        parent=styles["Heading4"],
        textColor=colors.HexColor("#0D47A1"),
        spaceAfter=6,
    )
    a_style = ParagraphStyle(
        "a_style",
        parent=styles["BodyText"],
        spaceAfter=12,
        leading=14,
    )
    meta_style = ParagraphStyle(
        "meta_style",
        parent=styles["Normal"],
        textColor=colors.gray,
        fontSize=9,
        spaceAfter=12,
    )

    # --- Header Section ---
    content.append(Paragraph(f"Interview Q&A Set for {role.title()}", title_style))
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    content.append(Paragraph(f"Generated on {timestamp}", meta_style))
    content.append(Spacer(1, 10))

    # --- Add Questions and Answers ---
    for i, row in df.iterrows():
        category = row.get("Category", "General")
        question = row.get("Question", "")
        answer = row.get("Answer", "")

        content.append(Paragraph(f"Q{i+1}. ({category})", q_style))
        content.append(Paragraph(f"<b>Question:</b> {question}", styles["BodyText"]))
        content.append(Paragraph(f"<b>Answer:</b> {answer}", a_style))
        content.append(Spacer(1, 6))

    # --- Build PDF ---
    doc.build(content)
    return pdf_buffer.getvalue()
