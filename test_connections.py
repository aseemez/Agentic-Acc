import os
import pymongo
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

# ── TEST MONGODB ──
try:
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    client.admin.command('ping')
    print("MongoDB connected")
except Exception as e:
    print(f"MongoDB failed: {e}")
# ── TEST GEMINI (via ADC) ──
try:
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True,
        project="project-73b31b23-b6f9-4055-889",
        location="global"
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Say hello in one word"
    )
    print(f"Gemini connected: {response.text}")
except Exception as e:
    print(f"Gemini failed: {e}")