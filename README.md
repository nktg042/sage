# Sage 🌿 - AI-Powered Mental Health Companion

MindEase (Sage) is a professional, empathetic, and highly responsive AI mental health companion. Powered by **Google Gemini AI** and built on a high-performance **FastAPI** backend with **MongoDB Atlas** for secure cloud storage, Sage offers conversational support, mindfulness exercises, and compassionate guidance in both English and Hinglish.

## ✨ Features

- **Empathetic Conversational AI:** Driven by Google's Gemini LLM with a deeply crafted system prompt ensuring non-judgmental, evidence-based responses.
- **Secure User Accounts (JWT):** Full authentication system allowing users to securely track and access their personal conversation history across sessions.
- **Voice Support (Speech-to-Text):** Integrated Web Speech API allows you to talk directly to Sage using your microphone.
- **Crisis Detection System:** Robust word-boundary keyword filtering (with typo support) for immediate detection of severe distress. Instantly provides offline emergency helplines.
- **Export Chats to PDF:** Generate and download a clean PDF transcript of your counseling session for your personal records with a single click.
- **Progressive Web App (PWA):** MindEase is installable directly to your mobile or desktop device's home screen for app-like offline UI behavior.
- **Live Admin Dashboard:** Contains an analytics endpoint to view real-time platform statistics (total users, total messages, active sessions).

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, Uvicorn, PyJWT, Bcrypt
- **Database:** MongoDB Atlas (via `pymongo`)
- **AI Integration:** `google-generativeai` SDK
- **Frontend:** Vanilla HTML, CSS, JavaScript (Local Storage, Service Workers)
- **Data Visualization & Export:** Chart.js, html2pdf.js

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- A [Google Gemini API Key](https://aistudio.google.com/)
- A [MongoDB Atlas Cluster URI](https://cloud.mongodb.com/)

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
Create a `.env` file in the root directory and add your API Keys:
```env
GEMINI_API_KEY=your_actual_api_key_here
MONGO_URI=mongodb+srv://username:password@cluster0.mongodb.net/?appName=Cluster0
JWT_SECRET=your_super_secret_string # (Optional, defaults to a local key)
```

**Important:** You must add your computer's IP address to the "Network Access" section in your MongoDB Atlas dashboard, otherwise the server will fail to connect.

### 4. Run the Application

Start the FastAPI backend server:
```bash
python -m uvicorn main:app --reload
```
The server will run at `http://127.0.0.1:8000`.

To view the chatbot interface, simply open the `chatbot-ui/index.html` file in your web browser. To view the internal analytics dashboard, open `chatbot-ui/admin.html`.

## ⚠️ Disclaimer

Sage is an Artificial Intelligence companion intended purely for emotional support and wellness tracking. **It is NOT a licensed medical professional, therapist, or a substitute for medical advice.** If you are in crisis, please contact your local emergency services or mental health helplines immediately.
