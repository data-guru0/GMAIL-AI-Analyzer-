# 📬 MailMind AI — Gmail AI Analyzer

A production-grade web app that uses GPT-4o + LangGraph to monitor your Gmail inbox, filter unwanted emails, and automatically organize the ones you want into custom labels — all based on your requirements document.

---

## ✨ Features

- 🔐 **Google OAuth 2.0** — Secure sign-in, Gmail access only
- 📄 **Requirements Upload** — PDF, DOCX, or TXT describing your email preferences
- 🤖 **LangGraph AI Agent** — GPT-4o analyzes each email and decides: keep, delete, spam, or label
- 🏷️ **Auto Labeling** — Creates Gmail labels and applies them automatically
- ⏰ **Background Monitoring** — Checks your inbox every N minutes (configurable)
- 📊 **Dashboard** — Real-time stats and activity feed
- 🎨 **Premium Dark UI** — Glassmorphism, animations, fully responsive

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd "d:\TESTING EVOLVUE\Email analyzer"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` and fill in the following template:

```env
SECRET_KEY=a8f3b2c1d9e4f7a6b5c8d2e1f0a3b9c4d7e8f2a1b6c5d4e3f2a1b0c9d8e7f6

GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

OPENAI_API_KEY=your_openai_api_key

FLASK_ENV=development
FLASK_DEBUG=True

APP_URL=http://localhost:5000
DATABASE_URL=sqlite:///gmail_analyzer.db
DEFAULT_CHECK_INTERVAL=5
OPENAI_MODEL=gpt-4o
```

### 3. Set up Google Cloud

**Step 1 — Go to Google Cloud Console**
👉 [console.cloud.google.com](https://console.cloud.google.com/)
Sign in with your Google account.

**Step 2 — Create a New Project**
- Click the project dropdown (top-left, next to the Google Cloud logo)
- Click "New Project"
- Name it (e.g. Gmail AI Agent) → Click Create

**Step 3 — Enable Gmail API**
- Go to APIs & Services → Library
- Search for "Gmail API"
- Click it → Click "Enable"

**Step 4 — Create OAuth Credentials**
1. Go to APIs & Services → Credentials
2. Click "+ Create Credentials" → "OAuth client ID"
3. If prompted, click "Configure Consent Screen" first:
   - Choose **External**
   - Fill in **App name**, **support email**
   - Add your email under **Test Users** (important during dev)
   - Save

**Back in Create OAuth Client ID:**
1. Application type → **Web application**
2. Name it anything (e.g. `Gmail Client`)
3. Under **Authorized redirect URIs**, add:
   `http://localhost:5000/callback`
4. Click **Create**

**Step 5 — Copy Your Credentials**
You'll get:
- **Client ID** → looks like `xxxxxxx.apps.googleusercontent.com`
- **Client Secret** → a random string

Put them in your `.env` file.

## Generate the Flask Secret key

```bash
python -c 'import secrets; print(secrets.token_hex(16))'
```

### 4. Run

```bash
python run.py
```

Visit `http://localhost:5000`

---

## 📁 Project Structure

```
Email analyzer/
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── auth.py             # Google OAuth routes
│   ├── main.py             # Page routes
│   ├── api.py              # REST API endpoints
│   ├── models.py           # Database models
│   ├── gmail_service.py    # Gmail API wrapper
│   ├── document_parser.py  # PDF/DOCX/TXT parser + AI extraction
│   ├── scheduler.py        # Background email monitoring
│   └── ai_agent/
│       ├── agent.py        # LangGraph email analysis pipeline
│       └── prompts.py      # GPT-4o prompts
├── static/css/styles.css   # Premium dark theme
├── templates/              # HTML pages
├── config.py               # Configuration
├── run.py                  # Entry point
├── requirements.txt
└── .env.example
```

---

## 🧠 How the AI Agent Works

```
New Email → Fetch Details → Prepare Context
                ↓
         [LangGraph Agent]
                ↓
    GPT-4o Analysis (keep/delete/spam/label)
                ↓
         Gmail API Action
                ↓
         Log to Database
```

The AI agent reads your requirements document and uses it as the source of truth for every email decision.

---

