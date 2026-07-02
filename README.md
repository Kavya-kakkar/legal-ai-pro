# Legal AI Assistant

An advanced, full-stack, AI-powered document generation and management suite tailored for legal practitioners, advocates, and corporate counsel. It automates the generation of formal, jurisdiction-specific Indian legal notices from chronological client inputs and dispute summaries, supports real-time editing, and compiles professional PDF documents using standard advocate layouts.

---

## 🚀 Key Features

- **Intellectual Legal Notice Generation**: Adapts prompts using specialized context models trained on diverse legal fields (Criminal Law, Company Law, Labour Law, GST/Tax, and Family Court covenants).
- **Interactive Draft Editor**: Edit drafts directly in-browser using a standardized advocate paper format. Updates are automatically synced with the database.
- **Instant PDF Compilation**: Renders professional legal letters with letterhead formats, page numbers, date stamps, and signature fields using custom ReportLab flowables.
- **Robust Database Fallback**: Dynamically routes connections to a local SQLite fallback database if a connection to PostgreSQL is unavailable or driver modules (`psycopg2`) are missing.
- **Responsive Premium Theme**: A sleek, Inter-font based dashboard supporting custom primary color branding, dark mode elements, and visual state transitions.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Uvicorn, SQLAlchemy (ORM), Pydantic (data validation), python-dotenv.
- **AI Core**: OpenRouter API (`openai/gpt-4o-mini`), custom retry mechanisms, and exponential backoff wrappers for robust network requests.
- **PDF Generation**: ReportLab PDF library (canvas-based page routing, automated word-wrapping, and multi-page calculations).
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (CDN-based custom extend configuration), Google Material Icons.
- **Database**: PostgreSQL (Production) / SQLite3 (Local fallback).

---

## 📁 Repository Structure

```
Legal_ai_assitant/
│
├── backend/
│   ├── app.py                # Main FastAPI entry point (routes, auth, CORS, database sessioning)
│   ├── database.py           # DB connection builder with SQLite fallback routing
│   ├── models.py             # SQLAlchemy schemas (User and Notice tables)
│   ├── legal_ai.py           # OpenRouter API wrapper & connection verification
│   ├── pdf_generator.py      # Custom ReportLab PDF builder with flowable word-wrapping
│   ├── prompt_builder.py     # Prompt compiler formatting inputs for the AI agent
│   │
│   ├── templates/            # HTML templates (index, dashboard, create, drafts, templates, etc.)
│   └── static/               # Client-side custom scripts and stylesheets
│
├── requirements.txt          # Python dependency specifications
└── README.md                 # Project documentation
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Legal_ai_assitant
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```ini
OPENROUTER_API_KEY=your_openrouter_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/db_name

# Optional Email Services
GMAIL_EMAIL=example@gmail.com
GMAIL_PASSWORD=your_app_password
RESEND_API_KEY=your_resend_api_key
```
*Note: If `DATABASE_URL` is omitted, psycopg2 fails, or the target database is unreachable, the system falls back automatically to creating a local SQLite `notices.db`.*

### 3. Setup Virtual Environment & Install Dependencies
It is highly recommended to use the local virtual environment to execute commands.
```bash
# Navigate to backend and setup venv
cd backend
python -m venv venv

# Activate Virtual Environment (Windows)
.\venv\Scripts\activate

# Install Dependencies
pip install -r ../requirements.txt
```

---

## 💻 Running the Application

To start the local Uvicorn development server:

```bash
# Make sure you are inside the backend directory and the venv is active
python app.py
```
The server will start at **`http://127.0.0.1:8000`** with auto-reload enabled.

---

## 🧪 Integration Tests

The repository contains an automated integration test script that runs a complete E2E scenario (creating user, logging in, generating a notice draft, fetching notice details, checking database history, and compiling a PDF).

To run the integration tests on Windows:
```bash
# Set console encoding to UTF-8 to support emoji logs
$env:PYTHONIOENCODING="utf-8"

# Execute the test script using the venv python
..\venv\Scripts\python.exe <path-to-test-script>\test_backend.py
```

---

## 🔒 Security & Compliance Disclaimer

Legal AI is an automated drafting assistant and **does not constitute legal advice**. All generated documents should be reviewed by qualified legal counsel before filing, mailing, or serving. User data, API tokens, and drafts are fully encrypted at rest and in transit.
