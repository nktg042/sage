# 🌿 Sage — AI-Powered Mental Health Companion

MindEase is a modern, professional mental health chatbot named **Sage**. It is designed to provide compassionate, evidence-based emotional support, safety-net crisis detection, and secure user-specific chat history tracking.

---

## ✨ Features

- **Professional Conversational AI:** Driven by the **Cohere Command R** LLM family with an advanced system prompt designed for "Pro" level empathy and counseling techniques.
- **Auto-Model Detective:** Sage intelligently chooses the latest, most stable Cohere model (released late 2024/2025) to ensure you always get high-quality support.
- **Secure JWT Authentication:** Full user registration and login system. Sage remembers your private conversations across sessions and devices.
- **PWA (Progressive Web App):** Install MindEase directly on your phone or desktop. Works like a native app with offline-ready UI.
- **Voice-to-Text Integration:** Speak naturally to Sage using the built-in Web Speech API microphone support.
- **Export to PDF:** Download clean, formatted transcripts of your counseling sessions with a single click.
- **Crisis Detection System:** Robust word-boundary regex filtering (with common typo support) for immediate detection of severe distress, providing offline emergency helplines.
- **Live Admin Dashboard:** Analytics dashboard protected by admin credentials to track global usage, session counts, and platform health.

## 🛠️ Technology Stack

- **Backend:** Python 3.9+, FastAPI, Uvicorn, PyJWT, Bcrypt
- **Database:** MongoDB Atlas (Cloud-native scalable storage)
- **AI Integration:** Cohere API (Command R family)
- **Frontend:** Vanilla HTML5, CSS3 (Modern Glassmorphism), JavaScript
- **Security:** JWT (JSON Web Tokens), BCrypt password hashing

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- [Cohere API Key](https://dashboard.cohere.com/)
- [MongoDB Atlas Cluster URI](https://cloud.mongodb.com/)

### 2. Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/nktg042/sage.git
   cd sage
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` file:
   ```env
   COHERE_API_KEY=your_key_here
   MONGO_URI=your_mongodb_cluster_uri
   ```

### 3. Running the App
1. Start the FastAPI backend:
   ```bash
   uvicorn main:app --reload
   ```
2. Open `chatbot-ui/index.html` in your web browser.

---

## 🔒 Security Note
This application is an AI-powered conversational companion, **NOT** a replacement for professional clinical therapy. Mental health data is stored securely in MongoDB Atlas using unique user IDs, but always ensure you use strong passwords.

## 👥 Contributors
- **MindEase Team** 🌿

---
*Sage is dedicated to ensuring that no one has to walk their journey alone.*
