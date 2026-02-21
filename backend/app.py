from fastapi import FastAPI, HTTPException, Query, Request , Form
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import io
import sqlite3
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# ==============================
# Load Environment
# ==============================
load_dotenv()

app = FastAPI()

# ==============================
# Static & Templates Setup
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# OpenRouter Client
# ==============================
client = openai.OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ==============================
# Default Templates
# ==============================
TEMPLATES = {
    "divorce-cruelty": "DIVORCE NOTICE - Cruelty & Desertion...",
    "rent-default": "RENT DEFAULT NOTICE...",
    "498a-false": "FALSE 498A COMPLAINT NOTICE...",
    "cheque-bounce": "CHEQUE BOUNCE NOTICE..."
}

# ==============================
# Database Init
# ==============================
def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "notices.db"))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices 
                 (id INTEGER PRIMARY KEY, party1_name TEXT, 
                  party2_name TEXT, issue TEXT, 
                  draft_text TEXT, timestamp TEXT, template TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==============================
# MODELS
# ==============================
class NoticeRequest(BaseModel):
    party1_name: str
    party1_address: str
    party2_name: str
    party2_address: str
    issue: str
    template: str = ""

class PDFRequest(BaseModel):
    draft_text: str
    party1_name: str
    party1_address: str
    party2_name: str
    party2_address: str
    issue: str

class EmailRequest(PDFRequest):
    recipient_email: str


# ==============================
# Frontend Routes (Stitch UI)
# ==============================
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    return templates.TemplateResponse("features.html", {"request": request})

@app.get("/drafting", response_class=HTMLResponse)
async def drafting(request: Request):
    return templates.TemplateResponse("drafting.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request:Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/about",response_class=HTMLResponse)
async def about(request:Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/preview", response_class=HTMLResponse)
async def preview(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/landing", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/create", response_class=HTMLResponse)
async def create(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/code5", response_class=HTMLResponse)
async def code5(request: Request):
    return templates.TemplateResponse("code5.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    # For now simple demo login
    return RedirectResponse(url="/landing", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    # Later we connect database
    return RedirectResponse(url="/login", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/templates-page", response_class=HTMLResponse)
async def templates_page(request: Request):
    return templates.TemplateResponse("templates.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/create")
async def create(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/drafts", response_class=HTMLResponse)
async def drafts(request: Request):
    return templates.TemplateResponse("drafts.html", {"request": request})


# ==============================
# API Routes
# ==============================
@app.get("/templates")
async def get_templates():
    return {"templates": list(TEMPLATES.keys())}


@app.post("/generate-legal-notice")
async def generate_legal_notice(request: NoticeRequest):
    try:
        if request.template and request.template in TEMPLATES:
            template_text = TEMPLATES[request.template]
            draft_text = f"""{template_text}

Claimant: {request.party1_name}
Respondent: {request.party2_name}
Issue: {request.issue}"""
            return {"draft_text": draft_text}

        prompt = f"""Legal notice (Indian format):

Claimant: {request.party1_name}
Address: {request.party1_address}

Respondent: {request.party2_name}
Address: {request.party2_address}

Issue: {request.issue}

Draft formal notice with 15-day demand.
"""

        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )

        return {"draft_text": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download-pdf")
async def download_pdf(request: PDFRequest):
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            alignment=TA_CENTER
        )

        story = []
        story.append(Paragraph("LEGAL NOTICE", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(request.draft_text, styles['Normal']))

        doc.build(story)
        pdf_buffer.seek(0)

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Legal_Notice.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-notice")
async def save_notice(request: NoticeRequest):
    try:
        conn = sqlite3.connect(os.path.join(BASE_DIR, "notices.db"))
        c = conn.cursor()
        c.execute(
            "INSERT INTO notices (party1_name, party2_name, issue, draft_text, timestamp, template) VALUES (?, ?, ?, ?, ?, ?)",
            (request.party1_name, request.party2_name, request.issue, "", datetime.now().isoformat(), request.template)
        )
        conn.commit()
        conn.close()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(limit: int = Query(10)):
    conn = sqlite3.connect(os.path.join(BASE_DIR, "notices.db"))
    c = conn.cursor()
    c.execute(
        "SELECT id, party1_name, party2_name, issue, timestamp FROM notices ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()

    history = [
        {"id": r[0], "party1": r[1], "party2": r[2], "issue": r[3], "date": r[4]}
        for r in rows
    ]

    return {"history": history}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}


# ==============================
# Local Run
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
