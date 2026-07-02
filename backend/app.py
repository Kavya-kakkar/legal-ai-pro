from fastapi import FastAPI, HTTPException, Query, Request, Form, Depends
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import io
import hashlib
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Notice

# Helper modules
from legal_ai import generate_legal_draft
from pdf_generator import generate_pdf
from prompt_builder import build_legal_prompt

# ==============================
# Load Environment & DB Setup
# ==============================
load_dotenv()
app = FastAPI()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

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
# Database Dependency
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
# Pydantic Models
# ==============================
class NoticeRequest(BaseModel):
    party1_name: str
    party1_email: str = ""
    party1_phone: str = ""
    party1_address: str
    party2_name: str
    party2_email: str = ""
    party2_phone: str = ""
    party2_address: str
    issue: str
    template: str = ""
    custom_instructions: str = ""

class PDFRequest(BaseModel):
    notice_id: int = None
    draft_text: str = ""

class UpdateNoticeRequest(BaseModel):
    draft_text: str

# ==============================
# Authentication Helpers
# ==============================
def get_current_user_id(request: Request) -> int:
    # Read simple cookie-based session
    user_id_str = request.cookies.get("session_user_id")
    if user_id_str and user_id_str.isdigit():
        return int(user_id_str)
    return None

def get_current_user_name(request: Request) -> str:
    return request.cookies.get("session_user_name", "Julian Thorne, Esq.")

# ==============================
# Frontend Routes
# ==============================
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_name": get_current_user_name(request),
        "user_id": get_current_user_id(request)
    })

@app.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    return templates.TemplateResponse("features.html", {"request": request})

@app.get("/drafting", response_class=HTMLResponse)
async def drafting(request: Request):
    return templates.TemplateResponse("drafting.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # If not logged in, we let them view but they'll see demo data or we can prompt login
    # For a seamless experience, we won't strictly block, but we can display their name
    user_name = get_current_user_name(request)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_name": user_name
    })

@app.get("/create", response_class=HTMLResponse)
async def create(request: Request):
    return templates.TemplateResponse("create.html", {
        "request": request,
        "user_name": get_current_user_name(request)
    })

@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    return templates.TemplateResponse("templates.html", {
        "request": request,
        "user_name": get_current_user_name(request)
    })

@app.get("/drafts", response_class=HTMLResponse)
async def drafts(request: Request):
    return templates.TemplateResponse("drafts.html", {"request": request})

@app.get("/case-studies", response_class=HTMLResponse)
async def case_studies(request: Request):
    return templates.TemplateResponse("case_studies.html", {"request": request})

@app.get("/document-templates", response_class=HTMLResponse)
async def document_templates(request: Request):
    return templates.TemplateResponse("document_templates.html", {"request": request})

@app.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})

@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy_policy.html", {"request": request})

# Redirects for old routes to prevent 404s
@app.get("/landing")
async def landing_redirect():
    return RedirectResponse(url="/create", status_code=301)

@app.get("/templates-page")
async def templates_page_redirect():
    return RedirectResponse(url="/templates", status_code=301)

@app.get("/code5")
async def code5_redirect():
    return RedirectResponse(url="/dashboard", status_code=301)

# ==============================
# Authentication Routes
# ==============================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Hash password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Check user
    user = db.query(User).filter(User.email == email, User.password == hashed_password).first()
    if not user:
        return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)
    
    # Set cookies
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_user_id", value=str(user.id), path="/")
    response.set_cookie(key="session_user_name", value=user.name, path="/")
    return response

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return RedirectResponse(url="/signup?error=Email+already+registered", status_code=303)
    
    # Hash password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Create user
    new_user = User(name=name, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/login?success=Account+created", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session_user_id", path="/")
    response.delete_cookie(key="session_user_name", path="/")
    return response

# ==============================
# API Routes
# ==============================
@app.get("/api/templates")
async def get_templates_json():
    return {"templates": list(TEMPLATES.keys())}

@app.post("/generate-legal-notice")
async def api_generate_legal_notice(
    request: NoticeRequest,
    req_obj: Request,
    db: Session = Depends(get_db)
):
    try:
        # Build prompt using the prompt_builder
        issue_text = request.issue
        if request.custom_instructions:
            issue_text += f"\nCustom Instructions: {request.custom_instructions}"
            
        prompt_data = {
            "party1_name": request.party1_name,
            "party1_address": request.party1_address,
            "party2_name": request.party2_name,
            "party2_address": request.party2_address,
            "issue": issue_text
        }
        
        prompt = build_legal_prompt(prompt_data)
        
        # Generate legal notice using AI
        draft_text = generate_legal_draft(prompt)
        
        # Save to database
        user_id = get_current_user_id(req_obj)
        db_notice = Notice(
            party1_name=request.party1_name,
            party1_email=request.party1_email,
            party1_phone=request.party1_phone,
            party1_address=request.party1_address,
            party2_name=request.party2_name,
            party2_email=request.party2_email,
            party2_phone=request.party2_phone,
            party2_address=request.party2_address,
            issue=request.issue,
            template=request.template,
            draft_text=draft_text,
            user_id=user_id
        )
        db.add(db_notice)
        db.commit()
        db.refresh(db_notice)
        
        return {
            "id": db_notice.id,
            "draft_text": draft_text,
            "status": "generated_and_saved"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-pdf")
async def download_pdf_api(request: PDFRequest, db: Session = Depends(get_db)):
    try:
        text_to_print = ""
        if request.notice_id:
            db_notice = db.query(Notice).filter(Notice.id == request.notice_id).first()
            if db_notice:
                text_to_print = request.draft_text if request.draft_text else db_notice.draft_text
        
        if not text_to_print:
            text_to_print = request.draft_text

        if not text_to_print:
            raise HTTPException(status_code=400, detail="No draft text provided")

        # Generate PDF using the custom pdf_generator
        pdf_path = generate_pdf(text_to_print)
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="Legal_Notice.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-notice")
async def save_notice_api(request: NoticeRequest, req_obj: Request, db: Session = Depends(get_db)):
    try:
        user_id = get_current_user_id(req_obj)
        db_notice = Notice(
            party1_name=request.party1_name,
            party1_email=request.party1_email,
            party1_phone=request.party1_phone,
            party1_address=request.party1_address,
            party2_name=request.party2_name,
            party2_email=request.party2_email,
            party2_phone=request.party2_phone,
            party2_address=request.party2_address,
            issue=request.issue,
            template=request.template,
            draft_text="",
            user_id=user_id
        )
        db.add(db_notice)
        db.commit()
        db.refresh(db_notice)
        return {"status": "saved", "id": db_notice.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history_api(limit: int = Query(10), db: Session = Depends(get_db)):
    try:
        notices = db.query(Notice).order_by(Notice.timestamp.desc()).limit(limit).all()
        history = [
            {
                "id": n.id,
                "party1": n.party1_name,
                "party2": n.party2_name,
                "issue": n.issue,
                "date": n.timestamp.strftime("%Y-%m-%d %H:%M") if n.timestamp else ""
            }
            for n in notices
        ]
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notice/{id}")
async def get_notice_api(id: int, db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return {
        "id": notice.id,
        "party1_name": notice.party1_name,
        "party1_email": notice.party1_email or "",
        "party1_phone": notice.party1_phone or "",
        "party1_address": notice.party1_address,
        "party2_name": notice.party2_name,
        "party2_email": notice.party2_email or "",
        "party2_phone": notice.party2_phone or "",
        "party2_address": notice.party2_address,
        "issue": notice.issue,
        "template": notice.template or "",
        "draft_text": notice.draft_text or "",
        "date": notice.timestamp.strftime("%B %d, %Y") if notice.timestamp else ""
    }

@app.post("/api/notice/{id}/update")
async def update_notice_api(id: int, request: UpdateNoticeRequest, db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    notice.draft_text = request.draft_text
    db.commit()
    return {"status": "updated"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}

# ==============================
# Local Run
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
