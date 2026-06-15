import os
import base64
import pymongo
from datetime import datetime
from google import genai
from google.genai import types

# ── CONNECTIONS ──
mongo_client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["accounting"]

gemini = genai.Client(
    vertexai=True,
    project="project-73b31b23-b6f9-4055-889",
    location="global"
)

def parse_receipt(image_path: str) -> dict:
    # read image and convert to base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
        
    # figure out file type
    ext = image_path.split(".")[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    
    # ask gemini to extract receipt data
    response = gemini.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            types.Part.from_bytes(data=base64.b64decode(image_data), mime_type=mime_type),
            types.Part.from_text(text="""
                Extract the following from this receipt and respond ONLY in this exact JSON format, nothing else:
                {
                    "vendor": "store or restaurant name",
                    "amount": 0.00,
                    "currency": "USD",
                    "date": "YYYY-MM-DD",
                    "category": "one of: Food, Transport, Office, Software, Utilities, Marketing, Other",
                    "items": ["list", "of", "items", "purchased"],
                    "confidence": "high/medium/low"
                }
                If you cannot read something clearly, make your best guess and set confidence to low.
            """)
        ]
    )
    
    # parse the json response
    import json
    raw = response.text.strip()
    # remove markdown code blocks if gemini adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    extracted = json.loads(raw.strip())
    return extracted

def save_receipt(image_path: str) -> dict:
    print(f"Parsing receipt: {image_path}")
    
    # extract data from image
    extracted = parse_receipt(image_path)
    print(f"Extracted: {extracted}")
    
    # build the document
    doc = {
        "type": "expense",
        "vendor": extracted["vendor"],
        "amount": extracted["amount"],
        "currency": extracted.get("currency", "USD"),
        "category": extracted["category"],
        "date": datetime.strptime(extracted["date"], "%Y-%m-%d") if extracted["date"] != "unknown" else datetime.now(),
        "status": "pending_review",
        "receipt_image_path": image_path,
        "items": extracted.get("items", []),
        "extraction_confidence": extracted.get("confidence", "medium"),
        "source": "receipt_parser",
        # audit trail
        "audit_log": [
            {
                "action": "created",
                "by": "receipt_parser",
                "at": datetime.now(),
                "note": f"Auto-extracted by Gemini with {extracted.get('confidence', 'medium')} confidence"
            }
        ]
    }
    
    # save to mongodb
    result = db.transactions.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    
    print(f"Saved to MongoDB with id: {result.inserted_id}")
    return doc

# ── TEST IT ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 receipt_parser.py path/to/receipt.jpg")
    else:
        result = save_receipt(sys.argv[1])
        print(f"\nDone! Saved: {result['vendor']} - ${result['amount']}")