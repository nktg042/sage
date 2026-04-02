# Sage 🌿 - AI-Powered Mental Health Companion

MindEase (Sage) is a professional, empathetic, and responsive AI mental health companion. Powered by **Google Gemini API** and built on a high-performance **FastAPI** backend, Sage offers conversational support, mindfulness exercises, and compassionate guidance in both English and Hinglish.

## ✨ Features

- **Empathetic Conversational AI:** Completely driven by Google's Gemini LLM with a deeply crafted system prompt ensuring non-judgmental, evidence-based responses.
- **Crisis Detection System:** Robust word-boundary keyword filtering (with typo support) for immediate detection of severe distress. Instantly provides global mental health helpline numbers.
- **Markdown & Interactive UI:** A stunning locally-hosted vanilla JS/CSS frontend interface rendering bold text, lists, and embedded links.
- **Bilingual Capabilities:** Conversations naturally flow in both English and Hinglish depending on user input.
- **Rich User Experience:** Includes dynamic suggestion chips, typing indicators, animated "breathing" exercises, and an integrated mood tracker with a data chart.
- **Chat Memory:** Context retention across conversations within a session using SQLite.

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, Uvicorn, SQLite
- **AI Integration:** `google-generativeai` SDK (Gemini 2.0 Flash)
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Data Visualization:** Chart.js (for Mood Tracker)

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- A Google Gemini API Key. You can get one from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation

Clone the repository:
```bash
git clone https://github.com/nktg042/sage.git
cd sage
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate
# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory and add your Google Gemini API Key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

Start the FastAPI backend server:
```bash
python -m uvicorn main:app --reload
```
The server will run at `http://127.0.0.1:8000`.

To view the chatbot interface, simply open the `chatbot-ui/index.html` file in your web browser.

## ⚠️ Disclaimer

Sage is an Artificial Intelligence companion intended purely for emotional support and wellness tracking. **It is NOT a licensed medical professional, therapist, or a substitute for medical advice.** If you are in crisis, please contact your local emergency services or mental health helplines immediately.
