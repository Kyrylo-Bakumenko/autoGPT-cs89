import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the OpenAI API key is set

if os.getenv("OPENAI_API_KEY"):
    # Test query to check API connection
    try:
        client = openai.OpenAI(api_key=str(os.getenv("OPENAI_API_KEY")))
        prompt = "What is the capital of France?"
        response = client.chat.completions.create(  # NEW API CALL
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "system", "content": "Answer with the answer and nothing more."},
                      {"role": "user", "content": prompt}],
            max_tokens=10
        )
        print("✅ OpenAI API connection successful!\n")
        print("Prompt:", prompt)
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ OpenAI API connection failed:", str(e))
else:
    print("⚠️ OpenAI API key is not set. Please check your environment variables.")



