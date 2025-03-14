import openai
import time
import os
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from .env file
load_dotenv()

# OpenAI API Setup
client = openai.OpenAI(api_key=str(os.getenv("OPENAI_API_KEY")))

# Selenium Chrome Setup
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

# Automatically install the correct ChromeDriver version
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the quiz webpage
QUIZ_URL = "https://jackgrodnick.github.io/quiz-CS89/"
driver.get(QUIZ_URL)

# Function to ask OpenAI for correct answers
def get_correct_answer(question, options):
    system_role = os.getenv("SYSTEM_ROLE") # instructions hidden for security
    prompt = f"""
    Question: {question}.
    Choices: {options}.
    """

    print("\n🔹 Asking OpenAI:")
    print(f"  Question: {question}")
    print(f"  Choices: {options}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_role},
                      {"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )

        openai_response = response.choices[0].message.content.strip().lower()
        print(f"  ✅ OpenAI Response: {openai_response}")

        # Validate response (should be a, b, c, or d)
        if openai_response in ["a", "b", "c", "d"]:
            return openai_response
        else:
            print("  ⚠️ OpenAI gave an invalid response, defaulting to 'a'")
            return "a"

    except openai.RateLimitError:
        print("⚠️ OpenAI Rate Limit Exceeded. Waiting before retrying...")
        time.sleep(10)
        return "a"  # Default answer if API quota is exceeded

# Extract all questions and options
questions = driver.find_elements(By.CLASS_NAME, "question")
correct_answers = {}

for i, question in enumerate(questions):
    question_text = question.find_element(By.TAG_NAME, "p").text
    options = question.find_elements(By.TAG_NAME, "input")
    time.sleep(2)

    # Extract option text
    option_texts = []
    for option in options:
        try:
            # Extract text after radio button
            label = driver.execute_script("return arguments[0].nextSibling.textContent;", option).strip()
        except Exception as e:
            print(f"  ⚠️ Error extracting choice text: {e}")
            label = "UNKNOWN"

        option_texts.append(f"{option.get_attribute('value')}) {label}")

    print(f"  Extracted Choices: {option_texts}")  # ✅ Debugging print

    # Get correct answer from OpenAI
    correct_choice = get_correct_answer(question_text, "\n".join(option_texts))
    correct_answers[f"q{i+1}"] = correct_choice

    # Print debug info
    print(f"\n🔹 Selecting Answer for Question {i+1}")
    print(f"  Question: {question_text}")
    print(f"  Answer Chosen: {correct_choice}")

    # Select the correct option
    for option in options:
        if option.get_attribute("value") == correct_choice:
            option.click()
            break

# Submit the quiz
submit_button = driver.find_element(By.TAG_NAME, "button")
submit_button.click()

# Wait for results to load
time.sleep(2)

# Extract and print results
result_text = driver.find_element(By.ID, "result").text
print("\n✅ Test Result:", result_text)

# Close the browser
driver.quit()

