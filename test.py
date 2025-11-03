from google import generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Write a motivational quote for students learning AI.")
    print(response.text)
except Exception as e:
    print("❌ Error:", e)
