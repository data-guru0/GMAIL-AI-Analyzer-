# How to Teach MailMind AI: A Codebase Walkthrough Guide

When explaining this project to others, it is easiest to tackle the files sequentially, starting from how the app boots up and ending with how the AI executes its complex background tasks. 

Here is the exact sequence you should follow to teach this codebase effectively.

---

## 1. The Entry Point and Configuration
*Start by showing how the app starts, where secrets live, and how environments are managed.*

1. **[.env](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/.env) (The Secrets):** Explain that this is where the sensitive keys (Google, OpenAI, secret key) live. Emphasize why this file is NEVER uploaded to GitHub.
2. **[config.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/config.py) (The Configuration Bridge):** Show how Flask reads the variables from the [.env](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/.env) file into Python dictionaries. Briefly touch on [DevelopmentConfig](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/config.py#44-46) vs. [ProductionConfig](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/config.py#48-50).
3. **[run.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/run.py) (The Engine Starter):** Explain that this is the main entry point to run the app. It imports the app factory, initializes it, and runs the local server.

---

## 2. The Core Setup & Database
*Next, explain how the app brings all the puzzle pieces together and what data it stores.*

4. **[app/__init__.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/__init__.py) (The Factory):** Explain the "Application Factory" pattern. Show how it initializes the SQLite Database (`db`), the Background Scheduler ([scheduler](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/scheduler.py#70-86)), Flask Sessions, and registers all the "Blueprints" (auth, main, api).
5. **[app/models.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py) (The Schema):** Walk through the database tables.
   - [User](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py#4-27): Stores Google ID, tokens, and profile info.
   - [UserRequirement](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py#28-49): Stores the JSON criteria extracted from uploaded documents.
   - [EmailLog](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py#50-73): Records every action the AI takes (kept, deleted, labeled).

---

## 3. The Front Door (Authentication)
*Now show how a user actually gets into the system.*

6. **[app/auth.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/auth.py) (The Google Login):** This is a critical file.
   - Explain the OAuth 2.0 flow: Clicking "Login" redirects to Google.
   - The `/callback` route receives the token, gets the user's email/name/picture, and either creates a new [User](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py#4-27) in the database or updates the existing one.
   - Show how the session tracks the logged-in user.

---

## 4. The User Interface (Views & Templates)
*Shift from the backend to what the user sees on their screen.*

7. **[app/main.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/main.py) (The HTML Routes):** Show how simple this file is. It just checks if the user is logged in via `@login_required` and renders HTML templates.
8. **[templates/base.html](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/templates/base.html) (The Shell):** Explain template inheritance. Show the sidebar, navigation, and where the `{% block content %}` fits in.
9. **[templates/index.html](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/templates/index.html) (The Landing Page):** The public face of the app.
10. **[templates/dashboard.html](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/templates/dashboard.html) & [templates/requirements.html](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/templates/requirements.html):** Show where the stats, activity logs, and drag-and-drop file upload UI live. Explain how the JavaScript in [requirements.html](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/templates/requirements.html) sends files to the backend.

---

## 5. The API & File Uploads
*Explain how the UI sends data back to the server without refreshing the page.*

11. **[app/api.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/api.py) (The JSON Routes):** Walk through the API endpoints.
    - `/api/stats` and `/api/activity`: Fetching data for the dashboard charts and tables.
    - `/api/upload-requirements`: This is the crucial bridge connecting the UI to the AI. It takes the uploaded file and passes it to the generic [document_parser.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/document_parser.py).

---

## 6. The "Brain" (AI and Processing)
*This is the core value of the application—parsing rules and analyzing emails.*

12. **[app/document_parser.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/document_parser.py) (The Reader):** 
    - Explain how it extracts raw text from PDF, DOCX, or TXT.
    - Show the [parse_requirements_with_ai](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/document_parser.py#49-92) function: How it uses OpenAI `gpt-4o` to turn messy human text (e.g., "I don't want spam from stores") into structured JSON rules (categories, keywords).
13. **[app/ai_agent/prompts.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/ai_agent/prompts.py) (The Instructions):** Show the exact system prompt instructing the AI on how to act like a strict inbox manager.
14. **[app/ai_agent/agent.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/ai_agent/agent.py) (The LangGraph Engine):** This is the most complex file. Break it down into the "Graph" structure:
    - **State:** It holds the email details, user requirements, and ultimate decision.
    - **Step 1 (Analyze):** Feeds the email to GPT-4o with the user's strict rules. It returns a decision (KEEP, DELETE, LABEL).
    - **Step 2 (Execute Action):** Based on the decision, it prepares to call Gmail.

---

## 7. The Execution and Automation
*Finally, show how the AI's decisions actually affect the real world.*

15. **[app/gmail_service.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/gmail_service.py) (The Hands):** Show how the backend physically interacts with Google Servers on behalf of the user.
    - Fetching unread emails.
    - Trashing emails.
    - Applying specific labels.
    - Marking emails as read so they aren't processed twice.
16. **[app/scheduler.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/scheduler.py) (The Heartbeat):** Bring it all together.
    - Explain the [process_all_users](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/scheduler.py#11-69) function.
    - It runs on an infinite loop every 1 minute.
    - It iterates through every user in the database, fetches their unread emails, passes them through the LangGraph AI agent, executes the decision via the Gmail service, and saves a record in the database [EmailLog](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/models.py#50-73). 

---

**Summary for teaching:** By starting at the [.env](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/.env) and ending at the [scheduler.py](file:///d:/TESTING%20EVOLVUE/Email%20analyzer/app/scheduler.py), you trace the complete lifecycle of the app: Configuration -> Setup -> Login -> UI -> Document Upload -> AI Analysis -> Background Execution.
