import requests

payload = {
    "party1_name": "ABC Pvt Ltd",
    "party1_address": "Delhi",
    "party2_name": "XYZ Pvt Ltd",
    "party2_address": "Mumbai",
    "issue": "Trademark infringement",
    "laws": ["Trademark Act 1999", "Class 25"]
}

res = requests.post("http://127.0.0.1:8000/generate-legal-notice", json=payload)
print("STATUS:",res.status_code)
print("TEXT RESPONSE:")
print(res.text)
