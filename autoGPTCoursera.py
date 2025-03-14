import os
import openai
import time
import json
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, NoSuchWindowException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

# Import the stealth helper
import sys
import random
# Add the directory containing selenium_stealth_helper to Python's path
sys.path.append('/Users/kyrylobakumenko/vscode')
from autoGPTcs89.browser.selenium_stealth_helper import create_stealth_driver, humanize_browser_interaction, add_natural_scrolling

# Configure logging
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

load_dotenv()

# Configure OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_ROLE = """You are an AI assistant helping complete Coursera coursework.
For multiple choice questions, only respond with the letter of the correct answer (e.g., 'A', 'B').
For free response questions, provide a concise, accurate answer.
When analyzing course content, extract key points and summarize information."""

# Your Coursera credentials
EMAIL = os.getenv("COURSERA_EMAIL")
PASSWORD = os.getenv("COURSERA_PASSWORD")
COURSE_URL = os.getenv("COURSERA_COURSE_URL")

# Global browser instance
# import undetected_chromedriver as uc
# driver = uc.Chrome(headless=True,use_subprocess=False)
driver = None

def init_browser():
    """Initialize or re-initialize the browser with human-like characteristics"""
    global driver
    
    # Close existing driver if it exists
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    print("🌐 Initializing human-like browser...")
    
    try:
        # Use the stealth driver with randomized user agent and resolution
        # We specifically avoid headless mode to appear more human-like
        driver = create_stealth_driver(
            headless=False,  # Visible browser is less likely to trigger detection
            user_agent=None,  # Random user agent will be selected
            resolution=None   # Random resolution will be selected
        )
        
        # Add human-like interaction behaviors
        driver = humanize_browser_interaction(driver)
        
        # Add natural scrolling capability
        driver = add_natural_scrolling(driver)
        
        print("✅ Human-like browser initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Browser initialization failed: {str(e)}")
        print("\nFalling back to standard browser initialization...")
        
        # Fallback to standard initialization if stealth methods fail
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Add a random user agent as basic stealth
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            ]
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Basic stealth modifications with JavaScript
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            print("✅ Browser initialized with basic stealth features!")
            return True
        except Exception as e:
            print(f"❌ All browser initialization methods failed: {str(e)}")
            return False

def is_browser_alive():
    """Check if browser is still running"""
    global driver
    
    if not driver:
        return False
        
    try:
        # Simple operation to check if browser is responsive
        current_url = driver.current_url
        return True
    except (WebDriverException, NoSuchWindowException):
        print("⚠️ Browser window has closed or crashed.")
        return False

def ensure_browser():
    """Ensure browser is running, restart if needed"""
    if not is_browser_alive():
        print("🔄 Restarting browser...")
        return init_browser()
    return True

def login_to_coursera():
    """Handle Coursera login with better error handling and human-like behavior"""
    if not ensure_browser():
        return False
        
    print("🔑 Logging into Coursera with human-like behavior...")
    logging.info("Starting login process")
    
    try:
        # Go to login page
        driver.get("https://www.coursera.org/login")
        
        # Wait for the login form to load - use more specific selectors based on attributes
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='email'][name='email']"))
            )
            logging.info("Login form loaded successfully")
        except TimeoutException:
            logging.warning("Timeout waiting for the standard login form, checking for alternative elements")
            # Try alternative wait strategy
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "input[name='email']") or 
                          d.find_element(By.ID, "email")
            )
            logging.info("Found alternative login form elements")
        
        # Add some random delay before typing (like a human would)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Find email field using the exact attributes
        try:
            email_input = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='email'][name='email']")
            logging.info("Found email input by autocomplete and name attributes")
        except NoSuchElementException:
            # Fallback to alternative selectors
            try:
                email_input = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
                logging.info("Found email input by name attribute")
            except NoSuchElementException:
                email_input = driver.find_element(By.ID, "email")
                logging.info("Found email input by ID")
        
        # Enter email with clear first to ensure field is empty
        email_input.clear()
        email_input.send_keys(EMAIL)
        logging.info("Email entered successfully")
        
        # Pause between email and password like a human would
        time.sleep(random.uniform(0.8, 2.0))
        
        # Find password field using the exact attributes
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='current-password'][name='password']")
            logging.info("Found password input by autocomplete and name attributes")
        except NoSuchElementException:
            # Fallback to alternative selectors
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
                logging.info("Found password input by name attribute")
            except NoSuchElementException:
                password_input = driver.find_element(By.ID, "password")
                logging.info("Found password input by ID")
        
        # Enter password
        password_input.clear()
        password_input.send_keys(PASSWORD)
        logging.info("Password entered successfully")
        
        # Brief pause before clicking login button (like a human deciding they're done)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Find login button with the specific attributes
        try:
            login_button = driver.find_element(By.CSS_SELECTOR, "button[data-e2e='login-form-submit-button']")
            logging.info("Found login button by data-e2e attribute")
        except NoSuchElementException:
            # Fallback to more generic selectors
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                logging.info("Found login button by type attribute")
            except NoSuchElementException:
                # Last resort selector
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
                logging.info("Found login button by text content")
        
        # Click the login button
        login_button.click()
        logging.info("Login button clicked")
        
        # NEW: Pause for manual CAPTCHA solving if needed
        print("\n⚠️ IMPORTANT: If a CAPTCHA appears, please solve it now.")
        user_response = input("Press Enter when ready to continue (after solving CAPTCHA if needed), or type 'skip' to skip login: ")
        
        if user_response.strip().lower() == 'skip':
            print("Login process skipped. You can proceed manually.")
            return True
            
        # Check if we successfully navigated to a course page
        # But don't fail if we're not on a course page yet
        try:
            WebDriverWait(driver, 5).until(
                EC.url_contains("coursera.org/learn")
            )
            print("✅ Successfully logged in!")
            logging.info("Login successful")
            return True
        except TimeoutException:
            # We might still be logged in, just not on a course page
            # Let's check if the login form is no longer visible
            try:
                # If email input is still visible, we failed to log in
                driver.find_element(By.CSS_SELECTOR, "input[name='email']")
                print("⚠️ Still on login page. Login may have failed.")
                logging.warning("Still on login page after submit")
                
                # Take screenshot for debugging
                screenshot_path = os.path.join(log_dir, f"login_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                driver.save_screenshot(screenshot_path)
                logging.info(f"Saved login status screenshot to {screenshot_path}")
                
                # Ask user if they want to continue manually
                proceed = input("Do you want to proceed anyway and navigate manually? (y/n): ")
                if proceed.lower() == 'y':
                    return True
                return False
            except NoSuchElementException:
                # If login form is gone, we're probably logged in
                print("✅ Login form no longer visible - likely logged in successfully!")
                logging.info("Login form no longer visible - assuming success")
                return True
    
    except Exception as e:
        print(f"❌ Login process encountered an error: {str(e)}")
        logging.error(f"Login error: {str(e)}")
        # Take screenshot for debugging
        try:
            screenshot_path = os.path.join(log_dir, f"login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved error screenshot to {screenshot_path}")
            print(f"Screenshot saved to {screenshot_path}")
        except:
            logging.error("Failed to save screenshot")
            
        # Ask user how to proceed instead of automatically failing
        proceed = input("Do you want to continue with manual login? (y/n): ")
        if proceed.lower() == 'y':
            # Wait for user to complete login manually
            input("Please log in manually in the browser. Press Enter once you're logged in...")
            return True
        return False

def detect_page_type():
    """Analyze current page and detect what type of content it is"""
    if not ensure_browser():
        return "unknown"
        
    print("🔍 Analyzing current page type...")
    
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Enhanced quiz detection - check for multiple structures
        quiz_elements = soup.find_all([
            # Old style
            lambda tag: tag.name == "div" and tag.has_attr("class") and 
                       any(c for c in tag.get("class", []) if "rc-QuestionView" in c or "QuizSubmission" in c),
            # New style
            lambda tag: tag.name == "div" and tag.has_attr("data-testid") and 
                       "part-Submission_MultipleChoiceQuestion" in tag.get("data-testid", "")
        ])
        
        # Also check for quiz by role attribute
        quiz_groups = soup.find_all("div", role="group")
        quiz_legends = soup.find_all("div", attrs={"data-testid": "legend"})
        
        if quiz_elements or quiz_groups or quiz_legends:
            return "quiz"
        
        # Rest of the detection code remains the same...
        
        # Check for video elements
        video_elements = soup.find_all(["video", "iframe"]) or soup.find_all(class_=re.compile(r"video-player|rc-Video", re.I))
        if video_elements:
            return "video"
        
        # Check for reading content (most common fallback)
        reading_elements = soup.find_all(class_=re.compile(r"rc-ReadingItem|reading-item", re.I))
        if reading_elements:
            return "reading"
        
        # Check title for hints
        title = soup.find("h1")
        if (title):
            title_text = title.get_text().lower()
            if any(word in title_text for word in ["quiz", "exam", "test", "assessment"]):
                return "quiz"
            elif any(word in title_text for word in ["video", "lecture"]):
                return "video"
            elif any(word in title_text for word in ["reading", "article", "notes"]):
                return "reading"
        
        # Default fallback
        return "unknown"
    
    except Exception as e:
        print(f"❌ Error detecting page type: {str(e)}")
        return "unknown"

def process_reading_content():
    """Process reading content but don't auto-navigate"""
    if not ensure_browser():
        return False
        
    print("📚 Processing reading content...")
    
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract the reading content text to summarize it
        reading_content = soup.find("div", class_=re.compile(r"rc-ReadingItem|reading-item", re.I))
        content_text = ""
        
        if not reading_content:
            reading_content = soup.find("main", class_="item-page-content")
            
        if reading_content:
            # Get h1 title
            title = reading_content.find("h1")
            if title:
                content_text += f"Title: {title.get_text(strip=True)}\n\n"
            
            # Get paragraph content
            paragraphs = reading_content.find_all(["p", "li"])
            for p in paragraphs:
                content_text += f"{p.get_text(strip=True)}\n"
        
        # Summarize the content using ChatGPT
        if content_text:
            print("📝 Summarizing content with ChatGPT...")
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18", 
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE},
                    {"role": "user", "content": f"Summarize this content in 3-5 bullet points:\n\n{content_text[:4000]}"}
                ],
                temperature=0.3
            )
            summary = response.choices[0].message.content.strip()
            print("\n--- Content Summary ---")
            print(summary)
            print("----------------------\n")
        else:
            print("⚠️ No content found to summarize")
            
        # Check if there's a mark complete button and notify user
        try:
            complete_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='mark-complete']")
            print("✅ TASK COMPLETE: Reading has been summarized.")
            print("👉 Manual action needed: You can click 'Mark as completed' when ready.")
        except:
            print("✅ TASK COMPLETE: Reading has been summarized.")
            print("👉 No 'Mark as complete' button found - you may need to navigate manually.")
            
        return True
        
    except Exception as e:
        print(f"❌ Error processing reading content: {str(e)}")
        return False

def process_video_content():
    """Process video content but don't auto-navigate"""
    if not ensure_browser():
        return False
        
    print("🎬 Processing video content...")
    
    try:
        # Get video title
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text
            print(f"Video Title: {video_title}")
        except:
            print("Could not find video title")
        
        # Try to find and access transcript
        transcript_text = ""
        try:
            # Try to find and click the transcript tab
            transcript_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Transcript')]"))
            )
            transcript_tab.click()
            time.sleep(2)
            
            # Extract transcript
            transcript_container = driver.find_element(By.CSS_SELECTOR, ".rc-Transcript")
            transcript_text = transcript_container.text
            print("📄 Found video transcript")
            
            # Summarize the transcript
            if transcript_text:
                print("📝 Summarizing video transcript with ChatGPT...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                        {"role": "system", "content": SYSTEM_ROLE},
                        {"role": "user", "content": f"Summarize this video transcript in 3-5 bullet points:\n\n{transcript_text[:4000]}"}
                    ],
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
                print("\n--- Video Summary ---")
                print(summary)
                print("--------------------\n")
        except Exception as e:
            print(f"No transcript found or accessible: {str(e)}")
        
        print("✅ TASK COMPLETE: Video has been processed.")
        print("👉 Manual action needed: You may want to watch key parts of the video before continuing.")
        return True
        
    except Exception as e:
        print(f"❌ Error processing video content: {str(e)}")
        return False

def extract_question_from_radiogroup(radiogroup_element):
    """
    Extract question text and answer options from a radiogroup element
    using the specific Coursera HTML structure
    """
    try:
        # Get the question prompt ID from the aria-labelledby attribute
        aria_labelledby = radiogroup_element.get_attribute("aria-labelledby")
        if not aria_labelledby or not aria_labelledby.startswith("prompt-autoGradableResponseId"):
            return None, None
            
        # The ID is used to find the question prompt element
        prompt_id = aria_labelledby
        question_text = ""
        
        # Try to find the prompt element directly
        try:
            prompt_element = driver.find_element(By.ID, prompt_id)
            if (prompt_element):
                # Look for cml-viewer within the prompt which contains the actual question text
                cml_viewers = prompt_element.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
                if cml_viewers:
                    question_text = cml_viewers[0].text
                else:
                    question_text = prompt_element.text
        except:
            # If direct approach fails, try alternative method
            try:
                # Some Coursera questions have the prompt directly in an element with the aria-labelledby as ID
                base_id = aria_labelledby.replace("prompt-", "")
                prompt_element = driver.find_element(By.ID, base_id)
                if prompt_element:
                    question_text = prompt_element.text
            except:
                pass
        
        if not question_text:
            # Last resort - find any cml-viewer near the radiogroup
            cml_viewers = radiogroup_element.find_elements(By.XPATH, 
                "./preceding::div[@data-testid='cml-viewer'][1]")
            if cml_viewers:
                question_text = cml_viewers[0].text
            
        # Extract the answer options - find all radio inputs within the radiogroup
        answer_inputs = radiogroup_element.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        if not answer_inputs:
            return question_text, None
        
        # Extract option labels using data-testid="cml-viewer" near each radio button
        options = []
        for i, radio_input in enumerate(answer_inputs):
            # Get the name which should match autoGradableResponseId~[random string]
            input_name = radio_input.get_attribute("name")
            if not input_name or not input_name.startswith("autoGradableResponseId"):
                continue
            
            # Find the label by looking for the nearest cml-viewer
            option_text = ""
            try:
                # Find parent label or surrounding element that might contain the text
                parent_label = radio_input.find_element(By.XPATH, "./ancestor::label")
                cml_viewers = parent_label.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
                if cml_viewers:
                    option_text = cml_viewers[0].text
                else:
                    # Fallback to just the label text
                    option_text = parent_label.text
            except:
                # If we can't find the parent label, look for any nearby cml-viewer
                try:
                    # Find closest cml-viewer to this radio button
                    cml_viewers = driver.find_elements(By.XPATH, 
                        f"//input[@name='{input_name}']/following::div[@data-testid='cml-viewer'][1]")
                    if cml_viewers:
                        option_text = cml_viewers[0].text
                    else:
                        option_text = f"Option {chr(65+i)}"
                except:
                    option_text = f"Option {chr(65+i)}"
            
            options.append({
                "text": option_text,
                "element": radio_input,
                "letter": chr(65+i)
            })
        
        return question_text, options
    
    except Exception as e:
        print(f"Error extracting from radiogroup: {str(e)}")
        return None, None

def process_modern_radiogroup(radiogroup_element):
    """Process a modern Coursera radiogroup question with enhanced error handling"""
    question_text, options = extract_question_from_radiogroup(radiogroup_element)
    
    if not question_text or not options:
        logging.error("Couldn't extract question or options from radiogroup")
        print("❌ Couldn't extract question or options from radiogroup")
        return False
    
    print(f"Question: {question_text[:100]}...")
    logging.info(f"Processing question: {question_text[:100]}...")
    
    # Format options for ChatGPT
    options_text = "\n".join([f"{opt['letter']}. {opt['text']}" for opt in options])
    logging.info(f"Options extracted: {len(options)} options found")
    
    # Use ChatGPT to determine the answer
    prompt = f"Question: {question_text}\n\nOptions:\n{options_text}\n\nWhat is the correct answer? Reply with just the letter."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().upper()
        print(f"ChatGPT selected answer: {answer}")
        logging.info(f"ChatGPT selected answer: {answer}")
        
        # Find the option with the matching letter
        selected_option = next((opt for opt in options if opt["letter"] == answer), None)
        
        if selected_option:
            # Try to click with enhanced error handling
            try:
                # First, try to scroll the element into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selected_option["element"])
                time.sleep(0.5)  # Wait for scroll to complete
                
                # Try multiple clicking strategies
                try_methods = [
                    # Method 1: JavaScript click
                    lambda: driver.execute_script("arguments[0].click();", selected_option["element"]),
                    
                    # Method 2: Regular click
                    lambda: selected_option["element"].click(),
                    
                    # Method 3: ActionChains click
                    lambda: webdriver.ActionChains(driver).move_to_element(selected_option["element"]).click().perform(),
                    
                    # Method 4: Find parent label and click it
                    lambda: driver.execute_script(
                        "arguments[0].click();", 
                        selected_option["element"].find_element(By.XPATH, "./ancestor::label")
                    ),
                    
                    # Method 5: JavaScript to check the radio button directly
                    lambda: driver.execute_script(
                        "arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change', { 'bubbles': true }));", 
                        selected_option["element"]
                    )
                ]
                
                success = False
                for i, method in enumerate(try_methods):
                    try:
                        method()
                        print(f"Selected option {answer}: {selected_option['text'][:50]}... (method {i+1})")
                        logging.info(f"Successfully clicked option {answer} using method {i+1}")
                        success = True
                        break
                    except Exception as method_error:
                        logging.warning(f"Click method {i+1} failed: {str(method_error)}")
                        continue
                
                if not success:
                    # Log detailed diagnostics about the element
                    elem_diagnose = {
                        "element_type": selected_option["element"].get_attribute("type"),
                        "element_id": selected_option["element"].get_attribute("id"),
                        "element_class": selected_option["element"].get_attribute("class"),
                        "element_name": selected_option["element"].get_attribute("name"),
                        "is_displayed": selected_option["element"].is_displayed(),
                        "is_enabled": selected_option["element"].is_enabled(),
                        "answer_letter": answer,
                        "option_text": selected_option["text"][:100]
                    }
                    
                    logging.error(f"All click methods failed. Element diagnostic: {json.dumps(elem_diagnose)}")
                    print(f"⚠️ Could not click option {answer}. See log for details.")
                    
                    # Log question and answer for manual review
                    with open(os.path.join(log_dir, "failed_questions.txt"), "a") as fail_file:
                        fail_file.write(f"\n--- {datetime.now()} ---\n")
                        fail_file.write(f"QUESTION: {question_text}\n")
                        fail_file.write(f"OPTIONS: {options_text}\n")
                        fail_file.write(f"SELECTED: {answer}\n")
                        fail_file.write("---\n")
                    
                    print("Question details saved to failed_questions.txt for manual review")
                    return False
                
                return True
                
            except Exception as e:
                logging.error(f"Error interacting with radio option: {str(e)}")
                print("⚠️ Error selecting answer. Details saved to log.")
                return False
        else:
            logging.warning(f"Invalid answer '{answer}', defaulting to first option")
            print(f"Invalid answer '{answer}', defaulting to first option")
            
            # Try clicking the first option as fallback
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", options[0]["element"])
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", options[0]["element"])
                print(f"Selected option A: {options[0]['text'][:50]}...")
                return True
            except Exception as fallback_error:
                logging.error(f"Failed to click fallback option: {str(fallback_error)}")
                print("⚠️ Could not select fallback option either.")
                return False
            
    except Exception as e:
        logging.error(f"Error processing radiogroup: {str(e)}")
        print(f"⚠️ Error analyzing question. See log file for details.")
        return False

def extract_quiz_questions(driver):
    """
    Extract all questions from the quiz page and display them line by line
    before processing any answers
    """
    print("\n📋 QUIZ QUESTIONS OVERVIEW:")
    print("===========================")
    
    try:
        questions = []
        
        # Find all question numbers using data-testid="visually-hidden"
        question_numbers = driver.find_elements(By.CSS_SELECTOR, '[data-testid="visually-hidden"]')
        question_texts = {}
        
        # Extract question numbers and find matching question texts
        for num_elem in question_numbers:
            num_text = num_elem.text
            if "Question" in num_text:
                try:
                    # Extract the question number
                    q_num = int(re.search(r'Question\s+(\d+)', num_text).group(1))
                    logging.info(f"Found question number: {q_num}")
                    
                    # Find the closest cml-viewer which contains the question text
                    # Start by getting the parent container that has the question number
                    parent_container = num_elem
                    for _ in range(5):  # Look up to 5 levels up
                        if parent_container:
                            parent_container = parent_container.find_element(By.XPATH, "./..")
                            
                            # Look for cml-viewer within this container
                            cml_viewers = parent_container.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
                            if cml_viewers:
                                # Get the question text from the cml-viewer
                                question_texts[q_num] = cml_viewers[0].text
                                logging.info(f"Found question text for Q{q_num}")
                                break
                                
                            # Alternative: look for rc-CML divs
                            rc_cmls = parent_container.find_elements(By.CSS_SELECTOR, '.rc-CML')
                            if rc_cmls:
                                question_texts[q_num] = rc_cmls[0].text
                                logging.info(f"Found question text for Q{q_num} in rc-CML")
                                break
                except Exception as e:
                    logging.warning(f"Error extracting question number: {str(e)}")
        
        # If we found numbered questions, add them to our list
        if question_texts:
            for q_num in sorted(question_texts.keys()):
                questions.append(f"Question {q_num}: {question_texts[q_num]}")
        
        # If we didn't find any questions via numbers, try direct approach
        if not questions:
            # Find all cml-viewers which likely contain question text
            cml_viewers = driver.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
            for i, viewer in enumerate(cml_viewers, 1):
                # Check if this seems like a question (not an answer option)
                if len(viewer.text) > 20:  # Questions typically longer than options
                    questions.append(f"Question {i}: {viewer.text}")
            
            # Try alternative rc-CML class if needed
            if not questions:
                rc_cmls = driver.find_elements(By.CSS_SELECTOR, '.rc-CML')
                for i, cml in enumerate(rc_cmls, 1):
                    if len(cml.text) > 20:
                        questions.append(f"Question {i}: {cml.text}")
            
            # Try finding questions under radiogroups
            if not questions:
                radiogroups = driver.find_elements(By.CSS_SELECTOR, 
                    'div[aria-labelledby^="prompt-autoGradableResponseId"]')
                for i, group in enumerate(radiogroups, 1):
                    prompt_id = group.get_attribute("aria-labelledby")
                    if prompt_id:
                        try:
                            prompt_elem = driver.find_element(By.ID, prompt_id)
                            if prompt_elem:
                                questions.append(f"Question {i}: {prompt_elem.text}")
                        except:
                            pass
        
        # Display questions
        if questions:
            for question in questions:
                print(question)
        else:
            print("❌ Could not identify individual questions for display")
            
        print("===========================\n")
        return questions
    except Exception as e:
        print(f"❌ Error extracting questions: {str(e)}")
        print("===========================\n")
        return []

def process_checkbox_question(question, question_text):
    """
    Process a question with checkboxes (multiple answers possible)
    Works for both standard and SVG-based checkboxes
    """
    print("Processing checkbox question (multiple answers possible)")
    logging.info(f"Processing checkbox question: {question_text[:100]}...")
    
    try:
        # First try to find standard checkboxes
        checkbox_inputs = question.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        
        # If no standard checkboxes, try SVG-based ones
        if not checkbox_inputs:
            svg_checkboxes = question.find_elements(By.CSS_SELECTOR, 
                "svg[aria-labelledby*='OutlinedBlankCheckbox'], svg[path*='M19 5v14H5V5h14m0-2H5c-1.1']")
            
            if svg_checkboxes:
                # Get the parent labels for these SVG checkboxes
                checkbox_labels = [svg.find_element(By.XPATH, "./ancestor::label") for svg in svg_checkboxes]
                
                # Extract option texts from labels
                options = []
                for i, label in enumerate(checkbox_labels):
                    # Try different ways to get the text
                    option_texts = []
                    
                    # Check for cml-viewer within the label
                    cml_viewers = label.find_elements(By.CSS_SELECTOR, "[data-testid='cml-viewer']")
                    if cml_viewers:
                        for viewer in cml_viewers:
                            option_texts.append(viewer.text)
                    else:
                        # Try paragraphs or spans
                        text_elems = label.find_elements(By.CSS_SELECTOR, "p, span.rc-Option__content")
                        for elem in text_elems:
                            option_texts.append(elem.text)
                    
                    # If still no text, use the whole label text
                    if not option_texts:
                        option_texts.append(label.text)
                    
                    option_text = " ".join([t for t in option_texts if t])
                    options.append(f"{chr(65+i)}. {option_text}")
                
                # Use ChatGPT to determine the answers
                options_text = "\n".join(options)
                prompt = f"""Question: {question_text}\n\nOptions:\n{options_text}\n\n
                What are the correct answers? This is a multiple-answer checkbox question.
                Reply with just the letters of all correct answers, separated by commas (e.g., 'A,C,D')."""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                        {"role": "system", "content": SYSTEM_ROLE},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
                
                answers = response.choices[0].message.content.strip().upper().split(',')
                print(f"ChatGPT selected answers: {answers}")
                
                # Click the selected options
                for answer in answers:
                    answer = answer.strip()
                    answer_index = ord(answer) - ord('A')
                    if 0 <= answer_index < len(checkbox_labels):
                        try:
                            # Try JavaScript click which is more reliable for SVG elements
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox_labels[answer_index])
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", checkbox_labels[answer_index])
                            print(f"Selected option {answer}")
                        except Exception as click_error:
                            logging.error(f"Error clicking SVG checkbox: {str(click_error)}")
                            print(f"⚠️ Could not select option {answer}")
                
                return True
        
        # Process standard checkboxes if we found them
        if checkbox_inputs:
            # Extract option texts from labels or nearby elements
            options = []
            for i, checkbox in enumerate(checkbox_inputs):
                # Try to find the associated label
                label_text = ""
                
                # Method 1: by ID
                input_id = checkbox.get_attribute("id")
                if input_id:
                    try:
                        label = question.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        label_text = label.text
                    except:
                        pass
                
                # Method 2: parent label
                if not label_text:
                    try:
                        parent_label = checkbox.find_element(By.XPATH, "./ancestor::label")
                        label_text = parent_label.text
                    except:
                        pass
                
                # Method 3: nearby text div
                if not label_text:
                    try:
                        # Find closest text element
                        text_div = driver.find_element(By.XPATH, 
                            f"//input[@id='{input_id}']/following::div[contains(@class, 'Option__content')][1]")
                        label_text = text_div.text
                    except:
                        label_text = f"Option {chr(65+i)}"
                
                options.append(f"{chr(65+i)}. {label_text}")
            
            # Use ChatGPT to determine the answers
            options_text = "\n".join(options)
            prompt = f"""Question: {question_text}\n\nOptions:\n{options_text}\n\n
            What are the correct answers? This is a multiple-answer checkbox question.
            Reply with just the letters of all correct answers, separated by commas (e.g., 'A,C,D')."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            answers = response.choices[0].message.content.strip().upper().split(',')
            print(f"ChatGPT selected answers: {answers}")
            
            # Click the selected options
            for answer in answers:
                answer = answer.strip()
                answer_index = ord(answer) - ord('A')
                if 0 <= answer_index < len(checkbox_inputs):
                    try:
                        checkbox_inputs[answer_index].click()
                        print(f"Selected option {answer}")
                    except Exception as click_error:
                        logging.error(f"Error clicking checkbox: {str(click_error)}")
                        print(f"⚠️ Could not select option {answer}")
            
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error processing checkbox question: {str(e)}")
        print(f"❌ Error processing checkbox question: {str(e)}")
        return False

def process_quiz_content():
    """Process and complete quiz content with enhanced detection for modern Coursera UI"""
    if not ensure_browser():
        return False
        
    print("❓ Processing quiz content...")
    logging.info("Starting quiz processing")
    
    try:
        # Wait for any quiz element to load
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".rc-QuestionView") or 
                      d.find_elements(By.CSS_SELECTOR, "div[data-testid*='part-Submission_']") or
                      d.find_elements(By.CSS_SELECTOR, "div[role='group']") or
                      d.find_elements(By.CSS_SELECTOR, "div[aria-labelledby*='prompt-autoGradableResponseId']") or
                      d.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'][aria-labelledby^='prompt-autoGradableResponseId']")
        )
        
        # Extract and display all questions before processing
        quiz_questions = extract_quiz_questions(driver)
        
        # NEW: Try to find modern radiogroup questions first
        radiogroups = driver.find_elements(By.CSS_SELECTOR, 'div[role="radiogroup"][aria-labelledby^="prompt-autoGradableResponseId"]')
        if radiogroups:
            print(f"Processing {len(radiogroups)} modern radiogroup questions")
            logging.info(f"Found {len(radiogroups)} modern radiogroup questions")
            processed_count = 0
            
            for i, radiogroup in enumerate(radiogroups):
                logging.info(f"Processing radiogroup {i+1}/{len(radiogroups)}")
                if process_modern_radiogroup(radiogroup):
                    processed_count += 1
            
            if processed_count > 0:
                print(f"✅ Successfully processed {processed_count} modern radiogroup questions")
                
                # Now look for checkbox questions
                checkboxes_containers = driver.find_elements(By.CSS_SELECTOR, 'div[role="group"][aria-labelledby^="prompt-autoGradableResponseId"]')
                if checkboxes_containers:
                    print(f"Found {len(checkboxes_containers)} checkbox question groups")
                    checkbox_count = 0
                    
                    for i, container in enumerate(checkboxes_containers):
                        # Extract question text
                        prompt_id = container.get_attribute("aria-labelledby")
                        question_text = ""
                        
                        if prompt_id:
                            try:
                                prompt_elem = driver.find_element(By.ID, prompt_id)
                                if prompt_elem:
                                    question_text = prompt_elem.text
                            except:
                                pass
                        
                        # If no question text found, try finding nearby cml-viewer
                        if not question_text:
                            try:
                                cml_viewers = container.find_elements(By.XPATH, 
                                    "./preceding::div[@data-testid='cml-viewer'][1]")
                                if cml_viewers:
                                    question_text = cml_viewers[0].text
                            except:
                                question_text = f"Question {i+1}"
                                
                        print(f"\nProcessing checkbox question {i+1}: {question_text[:100]}...")
                        if process_checkbox_question(container, question_text):
                            checkbox_count += 1
                    
                    if checkbox_count > 0:
                        print(f"✅ Successfully processed {checkbox_count} checkbox questions")
                
                # Look for text input questions
                input_containers = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
                if input_containers:
                    print(f"Found {len(input_containers)} text input fields")
                    input_count = 0
                    
                    for i, input_field in enumerate(input_containers):
                        # Try to find the question text
                        question_text = ""
                        
                        # Look for label with for attribute
                        input_id = input_field.get_attribute("id")
                        if input_id:
                            try:
                                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                                question_text = label.text
                            except:
                                pass
                        
                        # If no question found, look for nearest cml-viewer
                        if not question_text:
                            try:
                                # Find parent container
                                parent = input_field
                                for _ in range(5):  # Look up to 5 levels up
                                    parent = parent.find_element(By.XPATH, "./..")
                                    cml_viewers = parent.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
                                    if cml_viewers:
                                        question_text = cml_viewers[0].text
                                        break
                            except:
                                question_text = f"Text Input {i+1}"
                        
                        print(f"\nProcessing text input {i+1}: {question_text[:100]}...")
                        process_text_input(driver, question_text, input_field)
                        input_count += 1
                    
                    if input_count > 0:
                        print(f"✅ Successfully processed {input_count} text input questions")
                
                # Check for submit button
                submit_selectors = [
                    "button[data-testid='submit-button']",
                    "button[data-e2e='quiz-next-button']",
                    "button[type='submit']",
                    "button.primary",
                    "button:contains('Submit')",
                    "button.submit"
                ]
                
                submit_found = False
                for selector in submit_selectors:
                    try:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"👉 Manual action needed: Review answers and click '{submit_button.text}' when ready.")
                        submit_found = True
                        break
                    except:
                        continue
                        
                if not submit_found:
                    print("⚠️ Could not find submit button - answers selected but manual submission required.")
                
                return True

    except Exception as e:
        logging.error(f"Failed to process quiz: {str(e)}")
        print(f"❌ Failed to process quiz. See log file for details.")
        return False

def process_svg_checkboxes(question, question_text, option_labels):
    """Handle the SVG-based checkboxes in Coursera's new UI"""
    print("Processing SVG-based checkbox question (multiple answers possible)")
    
    try:
        # Extract option texts
        options = []
        for i, label in enumerate(option_labels):
            # Extract text from the label, handling potential math expressions
            option_texts = []
            
            # Try different potential text containers
            text_elements = label.find_elements(By.CSS_SELECTOR, 
                "p, span._bc4egv, div.css-g2bbpm, div[data-testid='cml-viewer']")
            
            for elem in text_elements:
                # Check for math expressions
                math_elements = elem.find_elements(By.CSS_SELECTOR, "span[data-pendo='math-block']")
                if math_elements:
                    option_texts.append("[Math Expression]")
                else:
                    option_texts.append(elem.text)
            
            # Join all found text segments
            option_text = " ".join([t for t in option_texts if t])
            if not option_text:
                option_text = label.text
                
            # Clean up the text
            option_text = option_text.replace("\n", " ").strip()
            if not option_text:
                option_text = f"Option {i+1}"
                
            options.append(f"{chr(65+i)}. {option_text}")
        
        # Use ChatGPT to determine the answer
        options_text = "\n".join(options)
        prompt = f"""Question: {question_text}\n\nOptions:\n{options_text}\n\n
        What are the correct answers? This is a multiple-answer checkbox question where multiple options can be correct.
        Reply with just the letters of all correct answers, separated by commas (e.g., 'A,C,D')."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answers = response.choices[0].message.content.strip().upper().split(',')
        print(f"ChatGPT selected answers: {answers}")
        
        # Click the selected options
        for answer in answers:
            answer = answer.strip()
            answer_index = ord(answer) - ord('A')
            if 0 <= answer_index < len(option_labels):
                option_labels[answer_index].click()
            else:
                print(f"Invalid answer '{answer}', skipping")
    
    except Exception as e:
        print(f"❌ Error processing SVG checkboxes: {str(e)}")

def process_checkboxes(question, question_text, checkboxes):
    """Handle checkbox (multiple answer) questions"""
    if not ensure_browser():
        return
        
    print("Processing checkbox question")
    
    try:
        # Extract all option texts
        options = []
        for i, checkbox in enumerate(checkboxes):
            # Find the associated label
            label_id = checkbox.get_attribute("id")
            label = question.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
            option_text = label.text
            options.append(f"{chr(65+i)}. {option_text}")
        
        # Use ChatGPT to determine the answer
        options_text = "\n".join(options)
        prompt = f"""Question: {question_text}\n\nOptions:\n{options_text}\n\n
        What are the correct answers? This is a multiple-answer question where multiple options can be correct.
        Reply with just the letters of all correct answers, separated by commas (e.g., 'A,C,D')."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answers = response.choices[0].message.content.strip().upper().split(',')
        print(f"ChatGPT selected answers: {answers}")
        
        # Click the selected options
        for answer in answers:
            answer = answer.strip()
            answer_index = ord(answer) - ord('A')
            if 0 <= answer_index < len(checkboxes):
                checkboxes[answer_index].click()
            else:
                print(f"Invalid answer '{answer}', skipping")
    
    except Exception as e:
        print(f"❌ Error processing checkbox question: {str(e)}")

def process_text_input(question, question_text, input_field):
    """Handle free response text input questions with enhanced extraction"""
    if not ensure_browser():
        return
        
    print("Processing text input question")
    
    try:
        # Get the question using both the provided text and looking for context
        full_question_text = question_text
        
        # Look for labels that might provide context
        labels = []
        
        # Method 1: Direct label element
        try:
            input_id = input_field.get_attribute("id")
            if input_id:
                label_elem = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                if label_elem and label_elem.text and label_elem.text.strip() != "Enter answer here":
                    labels.append(label_elem.text)
        except:
            pass
            
        # Method 2: Look for nearby heading elements
        try:
            heading_elems = question.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            for elem in heading_elems:
                if elem.text:
                    labels.append(elem.text)
        except:
            pass
            
        # Method 3: Look up in parent elements for context
        try:
            parent_elems = question.find_elements(By.XPATH, "./ancestor::div[contains(@class, 'rc-QuestionView') or contains(@class, 'css-')]")
            for elem in parent_elems[:2]:  # Just check the first couple of parents
                if elem.text and len(elem.text) < 300:  # Only use reasonably sized text
                    labels.append(elem.text)
        except:
            pass
            
        # Add found labels to question text
        if labels:
            additional_context = " | ".join(labels)
            full_question_text = f"{full_question_text}\n\nAdditional context: {additional_context}"
        
        # Use ChatGPT to generate an answer
        prompt = f"Question: {full_question_text}\n\nPlease provide a concise, accurate answer (1-2 sentences)."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"ChatGPT generated answer: {answer}")
        
        # Enter the answer
        input_field.clear()
        input_field.send_keys(answer)
    
    except Exception as e:
        print(f"❌ Error processing text input question: {str(e)}")

def process_svg_radio_buttons(question, question_text, option_labels):
    """Handle modern Coursera UI with SVG-based radio buttons"""
    print("Processing SVG-based multiple choice question")
    logging.info(f"Processing SVG radio button question: {question_text[:100]}...")
    
    try:
        # Extract option texts
        options = []
        for i, label in enumerate(option_labels):
            # Extract text from the label
            option_spans = label.find_elements(By.CSS_SELECTOR, "p, span.p-x-1s, div.css-g2bbpm")
            
            if option_spans:
                option_text = option_spans[0].text
                options.append(f"{chr(65+i)}. {option_text}")
            else:
                # Fallback to label text
                option_text = label.text
                options.append(f"{chr(65+i)}. {option_text}")
        
        # Use ChatGPT to determine the answer
        options_text = "\n".join(options)
        prompt = f"Question: {question_text}\n\nOptions:\n{options_text}\n\nWhat is the correct answer? Reply with just the letter."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().upper()
        print(f"ChatGPT selected answer: {answer}")
        logging.info(f"ChatGPT selected answer: {answer}")
        
        # Click the selected option
        answer_index = ord(answer) - ord('A')
        if 0 <= answer_index < len(option_labels):
            # Add enhanced clicking logic with error handling
            try:
                # First attempt - try JavaScript click which is more reliable
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option_labels[answer_index])
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", option_labels[answer_index])
                logging.info(f"Selected option {answer} using JavaScript click")
            except Exception as js_error:
                logging.warning(f"JavaScript click failed: {str(js_error)}")
                
                try:
                    # Second attempt - standard click
                    option_labels[answer_index].click()
                    logging.info(f"Selected option {answer} using standard click")
                except ElementNotInteractableException as click_error:
                    # Log detailed error information
                    logging.error(f"Element not interactable: {str(click_error)}")
                    logging.error(f"Question: {question_text[:200]}")
                    logging.error(f"Selected answer: {answer}")
                    
                    # Try to find if there's a wrapper element we can click instead
                    try:
                        # Look for parent div that might be clickable
                        parent = option_labels[answer_index].find_element(By.XPATH, "./ancestor::div[contains(@class, 'option') or contains(@class, 'answer')]")
                        driver.execute_script("arguments[0].click();", parent)
                        logging.info("Clicked parent container as alternative")
                        print(f"Selected option {answer} (alternative method)")
                    except Exception as alt_error:
                        logging.error(f"All click attempts failed: {str(alt_error)}")
                        print("⚠️ Could not select option - element not interactable")
        else:
            print(f"Invalid answer '{answer}', defaulting to first choice")
            option_labels[0].click()
    
    except Exception as e:
        logging.error(f"Error processing SVG radio buttons: {str(e)}")
        print("⚠️ Error processing question. See log for details.")

def process_multiple_choice_new(question, question_text, choices):
    """Enhanced handler for multiple choice questions"""
    if not ensure_browser():
        return
        
    print("Processing multiple choice question")
    
    try:
        # Extract all option texts
        options = []
        for i, choice in enumerate(choices):
            # First try to find the label associated with this input
            label_id = choice.get_attribute("id")
            option_text = ""
            
            try:
                # Try to find by for attribute
                label = question.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                option_text = label.text
            except:
                try:
                    # Try to find parent label
                    label = choice.find_element(By.XPATH, "./ancestor::label")
                    option_text = label.text
                except:
                    # Last resort: get the value attribute
                    option_text = choice.get_attribute("value") or f"Option {i+1}"
            
            options.append(f"{chr(65+i)}. {option_text}")
        
        # Use ChatGPT to determine the answer
        options_text = "\n".join(options)
        prompt = f"Question: {question_text}\n\nOptions:\n{options_text}\n\nWhat is the correct answer? Reply with just the letter."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().upper()
        print(f"ChatGPT selected answer: {answer}")
        
        # Click the selected option
        answer_index = ord(answer) - ord('A')
        if 0 <= answer_index < len(choices):
            choices[answer_index].click()
        else:
            print(f"Invalid answer '{answer}', defaulting to first choice")
            choices[0].click()
    
    except Exception as e:
        print(f"❌ Error processing multiple choice question: {str(e)}")

def hybrid_mode():
    """Main function for hybrid mode operation"""
    print("\n" + "="*60)
    print("🤖 COURSERA HYBRID ASSISTANT MODE")
    print("="*60)
    print("Instructions:")
    print("1. Navigate manually to Coursera content pages")
    print("2. When on a quiz/reading/video page, type 'process' to analyze and complete")
    print("3. After completion, manually navigate to next item")
    print("4. Type 'restart' to restart the browser if it crashes")
    print("5. Type 'quit' to exit")
    print("="*60 + "\n")
    print(f"Log file: {log_filename}")
    
    # Initialize human-like browser
    if not init_browser():
        print("❌ Could not initialize browser. Exiting.")
        return
    
    # Try to login if credentials provided
    if EMAIL and PASSWORD:
        login_success = login_to_coursera()
        if not login_success:
            print("❌ Could not log in automatically.")
            # Ask if user wants to try manual login instead of automatically showing login page
            manual_login = input("Would you like to try logging in manually? (y/n): ")
            if manual_login.lower() == 'y':
                # Open Coursera login page if not already there
                if ensure_browser():
                    current_url = driver.current_url
                    if "login" not in current_url:
                        driver.get("https://www.coursera.org/login")
                    input("Press Enter once you've logged in manually...")
    else:
        print("⚠️ No login credentials provided. Please log in manually.")
        # Open Coursera login page
        if ensure_browser():
            driver.get("https://www.coursera.org/login")
            input("Press Enter once you've logged in manually...")
    
    # If we have a course URL, go there
    if COURSE_URL and ensure_browser():
        print(f"Opening course URL: {COURSE_URL}")
        driver.get(COURSE_URL)
    
    # Main command loop
    while True:
        command = input("\n📌 Enter command (process, status, questions, restart, quit): ").strip().lower()
        
        if command == "quit":
            print("Exiting...")
            break
            
        elif command == "restart":
            print("Restarting browser...")
            init_browser()
            print("Browser restarted. Please log in again if needed.")
            continue
        
        elif command == "process":
            if not ensure_browser():
                print("❌ Browser is not running. Type 'restart' to restart.")
                continue
                
            # Detect page type and process accordingly
            page_type = detect_page_type()
            print(f"Detected page type: {page_type}")
            
            if (page_type == "quiz"):
                process_quiz_content()
            elif (page_type == "video"):
                process_video_content()
            elif (page_type == "reading"):
                process_reading_content()
            else:
                print("⚠️ Unknown page type. Please navigate to a quiz, video, or reading page.")
        
        elif command == "status":
            if not ensure_browser():
                print("❌ Browser is not running. Type 'restart' to restart.")
                continue
                
            try:
                # Get current URL and page title
                current_url = driver.current_url
                page_title = driver.title
                page_type = detect_page_type()
                
                print("\n--- Page Status ---")
                print(f"Title: {page_title}")
                print(f"URL: {current_url}")
                print(f"Type: {page_type}")
                print("------------------\n")
            except Exception as e:
                print(f"❌ Error getting status: {str(e)}")
        
        elif command == "questions":
            if not ensure_browser():
                print("❌ Browser is not running. Type 'restart' to restart.")
                continue
                
            # Just display questions without processing answers
            page_type = detect_page_type()
            if page_type == "quiz":
                print("📋 Extracting quiz questions...")
                extract_quiz_questions(driver)
            else:
                print("⚠️ Not a quiz page. Please navigate to a quiz page to list questions.")
        
        else:
            print("Unknown command. Available commands: process, status, restart, quit")
    
    # Close browser when done
    if driver:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    try:
        hybrid_mode()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
