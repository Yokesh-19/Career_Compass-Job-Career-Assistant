# 🎯 AI Resume Analyzer & Career Assistant

This is an AI-powered career assistant application built with **Streamlit**. It analyzes your resume, provides personalized feedback, generates interview questions, conducts mock interviews with voice interaction, and offers career guidance through an intelligent chatbot.

---

## ✅ Prerequisites

- Python 3.8 or higher installed on your machine
- A valid Google Gemini API key
- Microphone access (for mock interview feature)

---

## ⚡ Setup Instructions

### 1️⃣ Install Python

Download and install Python from the official site:  
https://www.python.org/downloads/

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/ai-resume-analyzer.git
cd ai-resume-analyzer
```

---

### 3️⃣ Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:

- On Windows:  
  ```bash
  .venv\Scripts\activate
  ```
- On macOS / Linux:  
  ```bash
  source .venv/bin/activate
  ```

---

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

**Note for Windows users (Mock Interview feature):**
```bash
pip install pipwin
pipwin install pyaudio
```

---

### 5️⃣ Configure API Key

Create a `.env` file in the project root directory and add your API key:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

**How to get your API key:**
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy and paste it in the `.env` file

---

## 🚀 Run the App

```bash
streamlit run Home.py
```

The app will open in your browser at `http://localhost:8501`

---

## ⚙️ Features

### 📊 **Resume Analysis**
- Comprehensive scoring across 7 categories
- Skill gap identification
- Job match compatibility score
- Visual analytics with interactive charts

### 🎤 **AI Mock Interview**
- Voice-based interview interaction
- AI-generated role-specific questions
- Real-time speech-to-text conversion
- Text-to-speech responses
- Interview performance feedback

### 🔧 **Resume Fixer**
- Automatic grammar and formatting improvements
- ATS optimization
- Before/after comparison
- Export as PDF or TXT

### 📘 **Interview Q&A Generator**
- Personalized technical questions
- Data structures & algorithms problems
- Behavioral and scenario-based questions
- Model answers for each question
- Export as PDF

### 💬 **AI Career Chatbot**
- Ask anything about resumes, skills, or career advice
- Context-aware responses based on your resume
- Conversation history tracking

### 🎓 **Course Recommendations**
- Curated learning paths for skill gaps
- Direct links to Coursera, Udemy, and more

---

## 🔧 Troubleshooting

**Microphone not working (Mock Interview):**
1. Check browser microphone permissions
2. Close other apps using the microphone (Zoom, Teams, etc.)
3. Use Chrome browser for best compatibility

**"Module not found" error:**
```bash
pip install -r requirements.txt --force-reinstall
```

**API rate limit exceeded:**
- Wait a few minutes before retrying
- The app has built-in rate limiting (10 calls/minute)

---

## 📁 Project Structure

```
ai-resume-analyzer/
│
├── Home.py                    # Main application
├── pages/
│   ├── ChatBot.py            # Career chatbot
│   ├── QnA.py                # Q&A generator
│   ├── MockInterview.py      # Mock interview
│   └── FixResume.py          # Resume fixer
│
├── services/                  # AI logic modules
├── assets/style.css          # Custom styling
├── courses.py                # Course recommendations
├── requirements.txt          # Dependencies
└── .env                      # API key (create this)
```

---

## 📦 Dependencies

- `streamlit` - Web interface
- `langchain` & `langchain-google-genai` - AI orchestration
- `google-generativeai` - Google Gemini AI
- `pdfplumber` - PDF text extraction
- `plotly` - Interactive visualizations
- `edge-tts` - Text-to-speech
- `SpeechRecognition` - Voice input
- `reportlab` - PDF generation
- `pandas` - Data handling
- `python-dotenv` - Environment variables

---

## 📄 License

This project is open-source and free to use.

---

✨ **Happy Career Building!**
