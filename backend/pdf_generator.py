from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
from datetime import datetime
import tempfile
from fastapi import HTTPException

def generate_pdf(text: str, filename: str = "legal_notice.pdf") -> str:
    """
    Generate professional legal notice PDF
    
    Args:
        text: Legal notice content (draft text)
        filename: Output filename
        
    Returns:
        Temporary file path
    """
    try:
        # ✅ Create temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="legal_")
        os.close(temp_fd)
        
        c = canvas.Canvas(temp_path, pagesize=A4)
        width, height = A4
        
        # Margins
        margin_x = 40
        margin_y = 40
        text_width = width - (2 * margin_x)
        
        # Starting position
        x = margin_x
        y = height - 50
        
        # ✅ Header (Advocate details)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "ADVOCATE & SOLICITOR")
        y -= 18
        
        c.setFont("Helvetica", 10)
        c.drawString(x, y, "High Court of Madhya Pradesh, Bhopal")
        y -= 14
        c.drawString(x, y, "Email: advocate@legal.com | Mobile: +91-XXXXXXXXXX")
        y -= 28
        
        # ✅ Title
        c.setFont("Helvetica-Bold", 14)
        title = "LEGAL NOTICE"
        title_width = c.stringWidth(title, "Helvetica-Bold", 14)
        c.drawString((width - title_width) / 2, y, title)
        y -= 28
        
        # ✅ Body text with word wrapping
        c.setFont("Helvetica", 11)
        line_height = 14
        page_num = 1
        
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                y -= line_height
                continue
            
            wrapped_lines = wrap_text(paragraph, text_width, c, "Helvetica", 11)
            
            for wrapped_line in wrapped_lines:
                # Check if new page needed
                if y < margin_y + line_height:
                    c.setFont("Helvetica", 9)
                    c.drawRightString(width - margin_x, margin_y, f"Page {page_num}")
                    c.showPage()
                    page_num += 1
                    y = height - 50
                    c.setFont("Helvetica", 11)
                
                c.drawString(x, y, wrapped_line)
                y -= line_height
        
        # ✅ Footer
        c.setFont("Helvetica", 10)
        y -= 14
        c.drawString(x, y, f"Place: Bhopal")
        y -= 14
        c.drawString(x, y, f"Date: {datetime.now().strftime('%d %B, %Y')}")
        y -= 28
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "Advocate")
        y -= 14
        c.setFont("Helvetica", 9)
        c.drawString(x, y, "Enrollment No: MP/XXXX/XXXX")
        
        # Page number on last page
        c.setFont("Helvetica", 9)
        c.drawRightString(width - margin_x, margin_y, f"Page {page_num}")
        
        c.save()
        print(f"✅ PDF saved: {temp_path}")
        return temp_path
    
    except Exception as e:
        print(f"❌ PDF Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

def wrap_text(text: str, max_width: float, canvas_obj, font_name: str, font_size: int) -> list:
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        line_width = canvas_obj.stringWidth(test_line, font_name, font_size)
        
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines
