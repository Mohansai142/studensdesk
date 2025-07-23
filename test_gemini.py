import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

# Use this model (proven to work from your available models)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Generate response
response = model.generate_content("List three programming languages.")
print(response.text)