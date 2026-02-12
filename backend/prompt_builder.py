from datetime import datetime

def build_legal_prompt(data: dict) -> str:
    """
    Build comprehensive legal notice prompt for Indian advocate AI
    """
    # ✅ Get current date
    current_date = datetime.now().strftime("%d %B, %Y")
    
    # Extract safely
    party1 = f"{data['party1_name']}, {data['party1_address']}"
    party2 = f"{data['party2_name']}, {data['party2_address']}"
    issue = data['issue']
    
    return f"""
=== INDIAN LEGAL NOTICE DRAFTING INSTRUCTIONS ===

**CLIENT (SENDER - Party 1):** {party1}
**RECIPIENT (Party 2):** {party2}
**DISPUTE DETAILS:** {issue}

**FORMAT REQUIREMENTS (STANDARD INDIAN LEGAL NOTICE):**
1. Advocate letterhead format (High Court of Madhya Pradesh)
2. "LEGAL NOTICE" title (bold, centered, 16pt)
3. "To," + recipient complete address
4. "Subject:" + dispute summary (Payment recovery/Breach of contract)
5. "Sir/Madam," salutation
6. Background facts (numbered 1,2,3 paragraphs)
7. Legal violations (IPC 420/406, Contract Act 73, etc.)
8. DEMAND: 15/30 days payment/compliance + exact amount
9. Consequences: Suit filing + costs + interest
10. "Place: Bhopal" | "Date: {current_date}"
11. "Advocate" signature + Enrollment No: MP/1234/2020

**STYLE GUIDELINES:**
- Formal legal language (senior advocate tone)
- Precise section references 
- Jurisdiction: Courts at Bhopal, Madhya Pradesh
- Notice period: 15 days (urgent) OR 30 days (standard)

**Generate COMPLETE notice in proper sequence above.**
"""
