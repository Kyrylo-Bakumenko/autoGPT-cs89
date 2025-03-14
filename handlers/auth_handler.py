import os
import time
import random
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# CHANGE: Import get_driver directly
from browser.browser_manager import get_driver
from config import EMAIL, PASSWORD, log_dir

def login_to_coursera():
    """Handle Coursera login with better error handling and human-like behavior"""
    # CHANGE: Only use get_driver() to ensure we're using the singleton instance
    driver = get_driver()
    if not driver:
        print("❌ Browser not available for login")
        return False
        
    print("🔑 Logging into Coursera with human-like behavior...")
    logging.info("Starting login process")
    
    try:
        # Go to login page directly to ensure we're on the right page
        driver.get("https://www.coursera.org/login")
        time.sleep(2)  # Short delay to allow redirects
        
        # ADDED: First check if we were redirected away from login page due to existing cookies
        current_url = driver.current_url
        logging.info(f"Current URL after navigation to login page: {current_url}")
        
        # If we're no longer on the login page, check if we're logged in
        if "/login" not in current_url:
            logging.info("Redirected away from login page - checking if already logged in")
            print("🔄 Redirected from login page - checking login status...")
            
            # Check for elements that indicate user is logged in
            login_indicators = [
                "//button[contains(@aria-label, 'Your profile')]",  # Profile button
                "//div[contains(@class, 'c-ph-avatar')]",           # Avatar image
                "//a[contains(@href, '/user/')]"                    # User profile link
            ]
            
            for indicator in login_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    logging.info(f"Found logged-in indicator: {indicator}")
                    print("✅ Already logged in via cookies!")
                    return True
                except:
                    pass
            
            # If we're redirected but no login indicators found, try to go back to login page
            logging.info("No login indicators found despite redirection, returning to login page")
            print("⚠️ Redirected but login status unclear - retrying login page...")
            driver.get("https://www.coursera.org/login")
            time.sleep(2)
        
        # Wait for the login form to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='email'][name='email']"))
            )
            logging.info("Login form loaded successfully")
        except TimeoutException:
            logging.warning("Timeout waiting for the standard login form")
            
            # ADDED: Check again if we've been redirected to a non-login page, might be logged in
            current_url = driver.current_url
            if "/login" not in current_url:
                logging.info("Redirected away from login page after timeout")
                print("🔄 Redirected from login page - checking login status...")
                
                # Check for elements that indicate user is logged in
                for indicator in login_indicators:
                    try:
                        element = driver.find_element(By.XPATH, indicator)
                        logging.info(f"Found logged-in indicator after timeout: {indicator}")
                        print("✅ Already logged in via cookies!")
                        return True
                    except:
                        pass
            
            # Alternative wait strategy
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "input[name='email']") or 
                            d.find_element(By.ID, "email")
                )
                logging.info("Found alternative login form elements")
            except:
                # ADDED: One more check if we're on a dashboard or course page instead of login
                if any(x in current_url for x in ["/home", "/learn/", "/specializations/", "/professional-certificates/"]):
                    logging.info("On a content page instead of login - likely already logged in")
                    print("✅ Already on a course page - likely logged in via cookies!")
                    return True
                
                print("❌ Login page failed to load properly")
                return False
        
        # Add some random delay before typing (like a human would)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Find email field
        email_input = None
        for selector in ["input[autocomplete='email'][name='email']", "input[name='email']", "#email"]:
            try:
                email_input = driver.find_element(By.CSS_SELECTOR, selector)
                logging.info(f"Found email input using: {selector}")
                break
            except:
                continue
        
        if not email_input:
            print("❌ Could not find email input field")
            return False
        
        # Enter email
        email_input.clear()
        email_input.send_keys(EMAIL)
        logging.info("Email entered successfully")
        
        # Pause between email and password
        time.sleep(random.uniform(0.8, 2.0))
        
        # Find password field
        password_input = None
        for selector in ["input[autocomplete='current-password'][name='password']", "input[name='password']", "#password"]:
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, selector)
                logging.info(f"Found password input using: {selector}")
                break
            except:
                continue
        
        if not password_input:
            print("❌ Could not find password input field")
            return False
        
        # Enter password
        password_input.clear()
        password_input.send_keys(PASSWORD)
        logging.info("Password entered successfully")
        
        # Pause before clicking login
        time.sleep(random.uniform(0.5, 1.5))
        
        # Find login button
        login_button = None
        for selector in ["button[data-e2e='login-form-submit-button']", "button[type='submit']", "//button[contains(text(), 'Login')]"]:
            try:
                if selector.startswith("//"):
                    login_button = driver.find_element(By.XPATH, selector)
                else:
                    login_button = driver.find_element(By.CSS_SELECTOR, selector)
                logging.info(f"Found login button using: {selector}")
                break
            except:
                continue
        
        if not login_button:
            print("❌ Could not find login button")
            return False
        
        # Take a screenshot before clicking login (useful for debugging)
        try:
            screenshot_path = os.path.join(log_dir, f"before_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
        except:
            pass
        
        # Click the login button
        login_button.click()
        logging.info("Login button clicked")
        
        # CHANGE: Show which window we are using for clarity
        print(f"\n⚠️ IMPORTANT: In the browser window at URL '{driver.current_url}', solve the CAPTCHA if it appears.")
        user_response = input("Press Enter when ready to continue (after solving CAPTCHA if needed), or type 'skip' to skip login: ")
        
        if user_response.strip().lower() == 'skip':
            print("Login process skipped. You can proceed manually.")
            return True
        
        # Check login success - multiple ways
        # 1. Check URL contains learn
        if "coursera.org/learn" in driver.current_url:
            print("✅ Successfully logged in!")
            
            # ADDED: Import and call the navigation function after successful login
            from handlers.navigation_handler import navigate_after_login
            navigate_after_login()
            
            return True
            
        # 2. Check if login form is gone
        try:
            driver.find_element(By.CSS_SELECTOR, "input[name='email']")
            print("⚠️ Still on login page. Login may have failed.")
            logging.warning("Still on login page after submit")
            
            # Take screenshot for debugging
            screenshot_path = os.path.join(log_dir, f"login_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved login status screenshot to {screenshot_path}")
            
            # Check if we want to proceed anyway
            proceed = input("Do you want to proceed anyway and navigate manually? (y/n): ")
            return proceed.lower() == 'y'
        except NoSuchElementException:
            # If login form is gone, we're probably logged in
            print("✅ Login form no longer visible - likely logged in successfully!")
            
            # ADDED: Import and call the navigation function after successful login
            from handlers.navigation_handler import navigate_after_login
            navigate_after_login()
            
            return True
    
    except Exception as e:
        print(f"❌ Login process encountered an error: {str(e)}")
        logging.error(f"Login error: {str(e)}")
        
        # Take screenshot for debugging
        try:
            screenshot_path = os.path.join(log_dir, f"login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved error screenshot to {screenshot_path}")
        except:
            pass
            
        # Ask about manual login
        proceed = input("Do you want to continue with manual login? (y/n): ")
        if proceed.lower() == 'y':
            input("Please log in manually in the browser. Press Enter once you're logged in...")
            return True
        return False
