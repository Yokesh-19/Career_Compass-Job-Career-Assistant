
# 🤖 AI Mock Interview App

This is an AI-powered mock interview application built with **Streamlit**. It allows you to get interviewed by an AI for your desired job role using voice input and provides interactive interview sessions.

---

## ✅ Prerequisites

- Python 3.8 or higher installed on your machine
- A valid API key for your backend service

---

## ⚡ Setup Instructions

### 1️⃣ Install Python

Download and install Python from the official site:  
https://www.python.org/downloads/

---

### 2️⃣ Create a Virtual Environment

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

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure API Key

Create a `.env` file in the project root directory and add your API key:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Make sure to replace `YOUR_API_KEY` with your actual API key.

---

## 🚀 Run the App

```bash
streamlit run Home.py
```

---

## ⚙️ Features

- Voice-based interview interaction
- AI-generated interview questions
- Real-time speech-to-text conversion
- Text-to-speech responses
- Clean interactive UI using Streamlit

---

## 📄 License

This project is open-source and free to use.

---

✨ Happy Interviewing!