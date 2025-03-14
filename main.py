import os
import logging
import sys
import time
from selenium.webdriver.common.by import By

# Import our modules using consistent relative paths
from browser.browser_manager import init_browser, ensure_browser, get_driver
from handlers.auth_handler import login_to_coursera
from handlers.page_analyzer import detect_page_type
from content.content_processor import process_reading_content, process_video_content
from quiz.quiz_handler import process_quiz_content, extract_quiz_questions
from config import EMAIL, PASSWORD, COURSE_URL, log_filename

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
    print("5. Type 'navigate' to explore course modules and grades")
    print("6. Type 'quit' to exit")
    print("="*60 + "\n")
    print(f"Log file: {log_filename}")
    
    # Initialize human-like browser once, and get the driver reference
    if not init_browser():
        print("❌ Could not initialize browser. Exiting.")
        return
    
    driver = get_driver()
    
    # Check if already logged in using the persistent profile
    print("🔍 Checking login status with persistent profile...")
    already_logged_in = False
    
    try:
        # Always go to Coursera homepage first, rather than directly to a course
        driver.get("https://www.coursera.org/")
        time.sleep(3)
        
        # Check for elements that indicate user is logged in
        profile_indicators = [
            "//button[contains(@aria-label, 'Your profile')]",  # Profile button
            "//div[contains(@class, 'c-ph-avatar')]",           # Avatar image
            "//a[contains(@href, '/user/')]"                    # User profile link
        ]
        
        for indicator in profile_indicators:
            try:
                element = driver.find_element(By.XPATH, indicator)
                already_logged_in = True
                print("✅ Already logged in from previous session!")
                logging.info("User already logged in via persistent profile")
                break
            except:
                pass
    except:
        pass
    
    # Try to login only if not already logged in and credentials are provided
    if not already_logged_in and EMAIL and PASSWORD:
        print("🔑 Not logged in. Attempting automatic login...")
        login_success = login_to_coursera()
        if not login_success:
            print("❌ Could not log in automatically.")
            # Ask if user wants to try manual login
            manual_login = input("Would you like to try logging in manually? (y/n): ")
            if manual_login.lower() == 'y':
                # Open Coursera login page if not already there
                if driver:
                    current_url = driver.current_url
                    if "login" not in current_url:
                        driver.get("https://www.coursera.org/login")
                    print("🔐 Please log in manually in the browser window.")
                    print("⚠️ NOTE: This login will be saved in your persistent profile.")
                    print("⚠️ You should only need to complete verification once.")
                    input("Press Enter once you've logged in manually...")
    elif not already_logged_in:
        print("⚠️ No login credentials provided. Please log in manually.")
        # Open Coursera login page
        if driver:
            driver.get("https://www.coursera.org/login")
            print("🔐 Please log in manually in the browser window.")
            print("⚠️ NOTE: This login will be saved in your persistent profile.")
            print("⚠️ You should only need to complete verification once.")
            input("Press Enter once you've logged in manually...")
    
    # NEW: Add a flag to track if user has already navigated to a URL
    has_navigated_to_url = False
    
    # NEW: Ask user for course URL
    print("\n🌐 Navigation Options:")
    print("1. Enter a Coursera course URL")
    print("2. Browse Coursera homepage (current)")
    
    course_url_choice = input("Your choice (1-2): ")
    
    if course_url_choice == "1":
        # Suggest default URL if we have it from config
        default_prompt = f" [default: {COURSE_URL}]" if COURSE_URL else ""
        course_url_input = input(f"Enter Coursera course URL{default_prompt}: ")
        
        # Use default if user just pressed enter
        if not course_url_input.strip() and COURSE_URL:
            course_url_input = COURSE_URL
        
        if course_url_input:
            # Process URL to ensure proper format with /home/module/1
            processed_url = format_course_url(course_url_input)
            print(f"Navigating to: {processed_url}")
            driver.get(processed_url)
            time.sleep(3)
            has_navigated_to_url = True  # ADDED: Mark that we've navigated to a URL
    
    # MODIFIED: Only navigate to default course URL if user hasn't already navigated somewhere
    if not has_navigated_to_url and COURSE_URL and driver:
        print(f"Opening course URL: {COURSE_URL}")
        driver.get(COURSE_URL)
    
    # Main command loop
    while True:
        command = input("\n📌 Enter command (process, status, questions, navigate, restart, quit): ").strip().lower()
        
        if command == "quit":
            print("Exiting...")
            break
            
        elif command == "restart":
            print("🔄 Restarting browser...")
            
            # Save current URL before restarting
            current_url = None
            if driver:
                try:
                    current_url = driver.current_url
                    # Don't save "data:" URLs or about:blank
                    if current_url and (current_url.startswith("data:") or current_url == "about:blank"):
                        current_url = None
                except:
                    pass
            
            # Restart browser
            init_browser()
            
            # Navigate back to the saved URL or to course URL if available
            if current_url and driver:
                print(f"Navigating back to: {current_url}")
                driver.get(current_url)
            elif COURSE_URL and driver:
                print(f"Navigating to course URL: {COURSE_URL}")
                driver.get(COURSE_URL)
                
            print("✅ Browser restarted. Please log in again if needed.")
            continue
        
        elif command == "process":
            if not driver:
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
            if not driver:
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
            if not driver:
                print("❌ Browser is not running. Type 'restart' to restart.")
                continue
                
            # Just display questions without processing answers
            page_type = detect_page_type()
            if page_type == "quiz":
                print("📋 Extracting quiz questions...")
                extract_quiz_questions(driver)
            else:
                print("⚠️ Not a quiz page. Please navigate to a quiz page to list questions.")
        
        elif command == "navigate":
            if not driver:
                print("❌ Browser is not running. Type 'restart' to restart.")
                continue
                
            print("🧭 Starting navigation...")
            from handlers.navigation_handler import navigate_course_modules, navigate_to_grades
            
            # Ask user what to navigate to
            nav_choice = input("Navigate to: (1) Course modules, (2) Grades, (3) Both: ")
            
            if nav_choice == "1":
                navigate_course_modules()
            elif nav_choice == "2":
                navigate_to_grades()
            else:
                navigate_course_modules()
                navigate_to_grades()
        
        else:
            print("Unknown command. Available commands: process, status, questions, navigate, restart, quit")
    
    # Close browser when done
    if driver:
        try:
            driver.quit()
        except:
            pass

def format_course_url(url):
    """Format a Coursera course URL to include /home/module/1 if needed"""
    # Clean up URL - remove trailing slashes
    url = url.rstrip('/')
    
    # Check if URL matches pattern /learn/xyz but doesn't have /home/module/
    if '/learn/' in url and not ('/home/module/' in url):
        return f"{url}/home/module/1"
    
    # URL already has the proper structure or is something else
    return url

if __name__ == "__main__":
    try:
        hybrid_mode()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
    finally:
        driver = get_driver()
        if driver:
            try:
                driver.quit()
            except:
                pass
