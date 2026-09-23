# Mithra — Man Ka Mitra AI 💙

**Mithra** is an empathetic, voice-first mental wellbeing companion designed for youth and students. Built with natural conversational code-mixing (**Tanglish** & **Hinglish**), local offline AI intelligence via **Qwen3-4B**, an instant deterministic safety guardrail, and personal diary journaling.

---

## 📁 Repository Structure

```text
mithra/
├── .gitignore              # Pre-configured ignore rules (ignores node_modules, .venv, .db, .env)
├── package.json            # Root project metadata & run scripts
├── README.md               # Architecture documentation & setup guide
│
├── frontend/               # User Interface (HTML5, Vanilla CSS, JS)
│   ├── index.html          # Landing screen
│   ├── chat.html           # Mithra Home, Pick My Hobby & Voice Chat screen
│   ├── diary.html          # Diary (Write / Audio Record / Upload entries)
│   ├── emergency.html      # SOS support & emergency contacts
│   ├── profile.html        # Profile & language selection settings
│   ├── login.html          # User authentication (Login)
│   ├── signup.html         # User registration with password visibility toggle
│   ├── focus.html          # Mithra Focus Mode quiet study timer
│   ├── forgot.html         # Password recovery
│   ├── reset.html          # Password reset
│   ├── css/                # Aesthetic glassmorphism design tokens & styles
│   └── js/                 # API client & local session storage
│
└── backend/                # Application & AI Services
    ├── server.js           # Express API gateway & static file server (Port 4000)
    ├── ai.js               # Conversational brain, sentiment analysis, language detection
    ├── db.js               # SQLite database setup & migrations
    ├── voice_session.js    # Emotional tone detection & TTS speech formatter
    ├── routes/             # API routes (auth, chat, diary, misc)
    └── ai_service/         # Local AI Inference Microservice (FastAPI + llama-server)
        ├── app/
        │   ├── main.py     # FastAPI application lifecycle & endpoints (Port 8000)
        │   ├── model.py    # llama-server manager & Qwen3-4B streaming inference
        │   └── prompts.py  # Strict Tanglish, Hinglish, Tamil, Hindi, & English contracts
        └── requirements.txt # Python dependencies (fastapi, uvicorn, httpx)
```

---

## 🚀 Quick Setup & Run

### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)

### 2. Backend Gateway (Express)
```bash
cd backend
npm install
npm start
```
*The Express server runs on `http://localhost:4000` and serves the frontend automatically.*

### 3. AI Service (FastAPI + Qwen3-4B)
```bash
cd backend/ai_service
python -m venv .venv
.\.venv\Scripts\activate   # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 🌟 Key Features

1. **Natural Tanglish & Hinglish Code-Mixing**:
   - Responds in natural Latin-script Tamil (Tanglish) and Hindi (Hinglish) without English counseling clichés.
   - Example Tanglish: *"Puriyudhu bro, romba stress ah feel aagudhu pola. Enna aachu nu sollunga, naan kekkuren."*
   - Example Hinglish: *"Samajh sakta hoon bro, kaafi stress ho raha hai na. Kya hua? Batao, main sun raha hoon."*

2. **Deterministic Crisis Safety Guardrail**:
   - Immediate safety bypass (< 15ms) for self-harm or suicidal intent (`"naa saava poren"`, `"want to die"`).
   - Instant Tele-MANAS (14416 / 1800-891-4416) and National Emergency (112) helpline referral.

3. **Voice-First Companion Architecture**:
   - Speech Recognition via Web Speech API (`en-IN` for Latin-script mixed speech).
   - Real-time language classification before dispatching to the LLM.
   - Speech Synthesis (TTS) optimized with Indian English voices for natural Latin transliterations.

4. **Pick My Hobby on Home Screen**:
   - Interactive multi-select hobby chips (Music, Gaming, Art, Reading, Fitness, Photography).
   - Persisted across user sessions.

---

## 📤 Push to GitHub

To publish this unified repository to GitHub:

```bash
# 1. Navigate to the root directory
cd mithra

# 2. Stage all files (node_modules, .venv, and databases are automatically excluded by .gitignore)
git add .

# 3. Create your first commit
git commit -m "feat: complete Mithra AI companion with Tanglish & Hinglish voice architecture"

# 4. Link your GitHub repository (replace with your repo URL)
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 5. Push to GitHub
git push -u origin main
```
