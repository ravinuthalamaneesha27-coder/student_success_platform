from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("ERROR: .env file lo API key dorakaledu.")
else:
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input="Reply with only: API connection successful"
        )
        print(response.output_text)
    except Exception as e:
        print("API test failed:", e)
        