import time
import random
import logging
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from webdriver_manager.chrome import ChromeDriverManager

# CHANGE: Add a lock file to ensure single browser instance across processes
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.browser_lock')

# NEW: Define a persistent profile directory path
PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chrome_profile")

# Global browser instance - implemented as a class for better singleton handling
class BrowserInstance:
    _instance = None
    driver = None
    is_initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserInstance()
        return cls._instance
    
    @classmethod
    def get_driver(cls):
        instance = cls.get_instance()
        if not instance.is_initialized or instance.driver is None:
            cls.init_browser(force_new=True)
        return instance.driver

# Create the singleton instance
browser = BrowserInstance.get_instance()

def init_browser(force_new=False):
    """Initialize or re-initialize the browser with human-like characteristics"""
    global browser
    
    # Check if browser already initialized and working
    if not force_new and browser.is_initialized and browser.driver:
        try:
            # Test if browser is actually responsive
            _ = browser.driver.current_url 
            logging.info("Browser already initialized and responsive, skipping initialization")
            return True
        except:
            logging.info("Browser initialized but not responsive, reinitializing")
    
    # Close existing driver if it exists
    if browser.driver:
        try:
            browser.driver.quit()
        except:
            pass
        browser.driver = None
        browser.is_initialized = False
    
    # Ensure we don't have stale lock files
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
            logging.info("Removed stale browser lock file")
        except:
            pass
    
    print("🌐 Initializing human-like browser with persistent profile...")
    logging.info(f"Using persistent Chrome profile directory: {PROFILE_DIR}")
    
    # Create profile directory if it doesn't exist
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    try:
        # Create a lock file to prevent multiple initializations
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # Import stealth helper only when needed
        sys.path.append('/Users/kyrylobakumenko/vscode')
        
        try:
            from browser.selenium_stealth_helper import create_stealth_driver, humanize_browser_interaction, add_natural_scrolling
            
            # NEW: Create Chrome options with user-data-dir
            chrome_options = Options()
            chrome_options.add_argument(f"user-data-dir={PROFILE_DIR}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Use stealth functions but with our custom options that include the profile directory
            service = Service(ChromeDriverManager().install())
            browser.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Apply stealth JavaScript modifications
            browser.driver.execute_script("""
                // Overwrite the 'webdriver' property to make it undefined
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Add human-like behaviors from selenium_stealth_helper
            browser.driver = humanize_browser_interaction(browser.driver)
            browser.driver = add_natural_scrolling(browser.driver)
            
        except Exception as stealth_error:
            logging.error(f"Stealth browser creation failed: {str(stealth_error)}")
            print("\nFalling back to standard browser initialization with persistent profile...")
            
            # Standard initialization but with persistent profile
            chrome_options = Options()
            chrome_options.add_argument(f"user-data-dir={PROFILE_DIR}")  # Use persistent profile
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            ]
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
            
            service = Service(ChromeDriverManager().install())
            browser.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            browser.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
        browser.is_initialized = True
        logging.info("Human-like browser initialized with persistent profile")
        print("✅ Human-like browser initialized with persistent profile!")
        return True
        
    except Exception as e:
        browser.is_initialized = False
        browser.driver = None
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
            except:
                pass
        logging.error(f"Browser initialization failed: {str(e)}")
        print(f"❌ Browser initialization failed: {str(e)}")
        return False

def is_browser_alive():
    """Check if browser is still running and responsive"""
    global browser
    
    if not browser.driver or not browser.is_initialized:
        return False
        
    try:
        _ = browser.driver.current_url
        return True
    except (WebDriverException, NoSuchWindowException):
        browser.is_initialized = False
        print("⚠️ Browser window has closed or crashed.")
        return False

def ensure_browser():
    """Ensure browser is running, restart if needed"""
    if not is_browser_alive():
        print("🔄 Restarting browser...")
        return init_browser(force_new=True)
    return True

def get_driver():
    """Get the current browser driver instance"""
    global browser
    return BrowserInstance.get_driver()  # Use the class method for consistency
