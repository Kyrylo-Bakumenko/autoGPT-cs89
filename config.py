import os
import logging
import openai
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"coursera_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add console handler for warnings and errors
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    logging.getLogger('').addHandler(console)
    
    # Log startup
    logging.info("Starting Coursera automation script")
    
    return log_filename, log_dir

# Load environment variables
load_dotenv()

# OpenAI setup
def setup_openai():
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Coursera credentials
EMAIL = os.getenv("COURSERA_EMAIL")
PASSWORD = os.getenv("COURSERA_PASSWORD")
COURSE_URL = os.getenv("COURSERA_COURSE_URL")

MODEL = os.getenv("MODEL")

# System role for OpenAI
SYSTEM_ROLE = """You are an AI assistant helping complete Coursera coursework.
For multiple choice questions, only respond with the letter of the correct answer (e.g., 'A', 'B').
For free response questions, provide a concise, accurate answer.
When analyzing course content, extract key points and summarize information."""

# Initialize shared resources
log_filename, log_dir = setup_logging()
client = setup_openai()
