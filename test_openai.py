import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env")
else:
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o-mini",
            input="Say hello in one short sentence."
        )
        print("OpenAI API connection successful!")
        print(response.output_text)

    except Exception as e:
        print("API test failed:", type(e).__name__)
        print(str(e))
        