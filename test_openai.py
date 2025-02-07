import openai
import os

# Ensure the OpenAI API key is set
if not api_key:
    print("⚠️ OpenAI API key is not set. Please check your environment variables.")
else:
    # Test query to check API connection
    try:
        client = openai.OpenAI(api_key=api_key)  # ✅ NEW SYNTAX

        response = client.chat.completions.create(  # ✅ NEW API CALL
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            max_tokens=10
        )
        print("✅ OpenAI API connection successful!")
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ OpenAI API connection failed:", str(e))

