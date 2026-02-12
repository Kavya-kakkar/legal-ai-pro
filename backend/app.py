from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import io
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
import traceback
logging.basicConfig(level=logging.DEBUG)


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = openai.OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ✅ TEMPLATES
TEMPLATES = {
    "divorce-cruelty": "DIVORCE NOTICE - Cruelty & Desertion\n\nYou have deserted the matrimonial home without any reasonable cause. You have filed false 498A IPC case causing mental cruelty. Demand divorce under Hindu Marriage Act 1955 Section 13(1)(ia)(ib). Respond within 15 days or face court petition.",
    
    "rent-default": "RENT DEFAULT NOTICE\n\nYou failed to pay rent due since specified date. Vacate premises within 15 days per Rent Control Act. Pay arrears and damages or face eviction suit.",
    
    "498a-false": "FALSE 498A COMPLAINT NOTICE\n\nYour false 498A IPC complaint lacks evidence. Dowry demands proven false. Withdraw complaint within 7 days or face defamation suit under Section 182 IPC.",
    
    "cheque-bounce": "CHEQUE BOUNCE NOTICE\n\nCheque No. issued by you dated has bounced due to insufficient funds. Pay amount with interest within 15 days or face Section 138 NI Act proceedings.",
}

# ✅ INIT DATABASE
def init_db():
    conn = sqlite3.connect('notices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices 
                 (id INTEGER PRIMARY KEY, party1_name TEXT, party2_name TEXT, 
                  issue TEXT, draft_text TEXT, timestamp TEXT, template TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ✅ MODELS
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

class EmailRequest(BaseModel):
    draft_text: str
    party1_name: str
    party1_address: str
    party2_name: str
    party2_address: str
    issue: str
    recipient_email: str

# ✅ FEATURE 1: GET TEMPLATES
@app.get("/templates")
async def get_templates():
    return {"templates": list(TEMPLATES.keys())}

# ✅ FEATURE 2: GET SINGLE TEMPLATE
@app.get("/template/{template_name}")
async def get_template(template_name: str):
    if template_name not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": TEMPLATES[template_name]}

# ✅ MAIN: GENERATE LEGAL NOTICE
@app.post("/generate-legal-notice")
async def generate_legal_notice(request: NoticeRequest):
    try:
        # If template selected, use it
        if request.template and request.template in TEMPLATES:
            template_text = TEMPLATES[request.template]
            draft_text = f"{template_text}\n\nParty 1: {request.party1_name}\nParty 2: {request.party2_name}\nIssue: {request.issue}"
            return {"draft_text": draft_text}
        
        # Otherwise use AI
        prompt = f"""Legal notice (Indian format):

Claimant: {request.party1_name}
Address: {request.party1_address}

Respondent: {request.party2_name}
Address: {request.party2_address}

Issue: {request.issue}

Draft formal notice with 15-day demand."""

        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        return {"draft_text": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ PDF DOWNLOAD
@app.post("/download-pdf")
async def download_pdf(request: PDFRequest):
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=14, alignment=TA_CENTER, spaceAfter=12)
        body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], 
                                  fontSize=10, alignment=TA_JUSTIFY, spaceAfter=10)
        
        story = []
        story.append(Paragraph("LEGAL NOTICE", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph(f"<b>Claimant:</b> {request.party1_name}", body_style))
        story.append(Paragraph(f"<b>Address:</b> {request.party1_address}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        story.append(Paragraph(f"<b>Respondent:</b> {request.party2_name}", body_style))
        story.append(Paragraph(f"<b>Address:</b> {request.party2_address}", body_style))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("<b>Notice Details:</b>", body_style))
        for para in request.draft_text.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip().replace('\n', '<br/>'), body_style))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Legal_Notice.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF failed: {str(e)}")

# ✅ FEATURE 3: SAVE NOTICE
@app.post("/save-notice")
async def save_notice(request: NoticeRequest):
    try:
        conn = sqlite3.connect('notices.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO notices (party1_name, party2_name, issue, draft_text, timestamp, template) VALUES (?, ?, ?, ?, ?, ?)",
            (request.party1_name, request.party2_name, request.issue, "", datetime.now().isoformat(), request.template)
        )
        notice_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": notice_id, "status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ FEATURE 4: GET HISTORY
@app.get("/history")
async def get_history(limit: int = Query(10)):
    try:
        conn = sqlite3.connect('notices.db')
        c = conn.cursor()
        c.execute("SELECT id, party1_name, party2_name, issue, timestamp FROM notices ORDER BY timestamp DESC LIMIT ?", (limit,))
        history = [
            {"id": row[0], "party1": row[1], "party2": row[2], "issue": row[3], "date": row[4]} 
            for row in c.fetchall()
        ]
        conn.close()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ FEATURE 5: EMAIL PDF
@app.post("/email-pdf")
async def email_pdf(request: EmailRequest):
    print("🔍 EMAIL DEBUG START")
    
    try:
        sender_email = os.getenv("GMAIL_EMAIL")
        sender_password = os.getenv("GMAIL_PASSWORD")
        
        if not sender_email or not sender_password:
            raise HTTPException(status_code=500, detail="Missing .env credentials")
        
        print(f"🔍 FROM: {sender_email} → TO: {request.recipient_email}")
        
        # ✅ GENERATE FULL PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("LEGAL NOTICE", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Claimant: {request.party1_name}", styles['Normal']))
        story.append(Paragraph(f"Address: {request.party1_address}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Respondent: {request.party2_name}", styles['Normal']))
        story.append(Paragraph(f"Address: {request.party2_address}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(request.draft_text, styles['Normal']))
        
        doc.build(story)
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.getvalue()
        
        print(f"🔍 PDF SIZE: {len(pdf_data)} bytes")
        
        # ✅ CREATE EMAIL
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = request.recipient_email
        msg['Subject'] = f"Legal Notice - {request.party1_name} vs {request.party2_name}"
        
        msg.attach(MIMEText(f"""
        Legal Notice Document
        Party 1: {request.party1_name}
        Party 2: {request.party2_name}
        Issue: {request.issue}
        PDF attached above.
        """, 'plain'))
        
        # ✅ ATTACH PDF
        pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename='Legal_Notice.pdf')
        msg.attach(pdf_attachment)
        
        # ✅ SEND EMAIL (THIS WAS MISSING!)
        print("🔍 SENDING EMAIL...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, request.recipient_email, msg.as_string())
        server.quit()
        
        print("✅ EMAIL SENT SUCCESS!")
        return {"status": "Email sent successfully", "recipient": request.recipient_email}
        
    except Exception as e:
        print(f"❌ EMAIL FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email failed: {str(e)}")




@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
