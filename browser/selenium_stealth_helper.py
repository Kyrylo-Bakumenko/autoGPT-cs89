import random
import time
import json
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Collection of common user agents for variety
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
]

# Common screen resolutions
RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720)
]

def create_stealth_driver(
    headless: bool = False,
    user_agent: Optional[str] = None,
    resolution: Optional[tuple] = None,
    chrome_options: Options = None
) -> webdriver.Chrome:
    """
    Create a Selenium Chrome driver with anti-detection measures.
    
    Args:
        headless: Whether to run in headless mode
        user_agent: Specify a custom user agent, or None for random selection
        resolution: Specify a custom (width, height) resolution, or None for random
        chrome_options: Optional pre-configured Chrome options to use
        
    Returns:
        A configured Chrome WebDriver instance
    """
    # Use provided options or create new ones
    options = chrome_options or Options()
    
    # Select random user agent if not specified and not already set in options
    selected_user_agent = user_agent or random.choice(USER_AGENTS)
    
    # Only add user-agent if not already in the options
    user_agent_set = any("user-agent" in arg.lower() for arg in options.arguments)
    if not user_agent_set:
        options.add_argument(f"user-agent={selected_user_agent}")
    
    # Select random resolution if not specified
    if not resolution:
        resolution = random.choice(RESOLUTIONS)
    width, height = resolution
    
    # Configure general options to avoid detection (if not already set)
    if not any("disable-blink-features=AutomationControlled" in arg for arg in options.arguments):
        options.add_argument("--disable-blink-features=AutomationControlled")
        
    if not any("disable-features=IsolateOrigins" in arg for arg in options.arguments):
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    # Set window size using a common desktop resolution (if not already set)
    if not any("window-size" in arg.lower() for arg in options.arguments):
        options.add_argument(f"--window-size={width},{height}")
    
    # Configure headless mode if requested, with special anti-detection settings
    if headless and not any("headless" in arg.lower() for arg in options.arguments):
        options.add_argument("--headless=new")  # New headless implementation
        options.add_argument("--disable-gpu")
        # These can help with headless detection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    
    # Add excludeSwitches if not already set
    if not options.experimental_options.get("excludeSwitches"):
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Add useAutomationExtension if not already set
    if "useAutomationExtension" not in options.experimental_options:
        options.add_experimental_option("useAutomationExtension", False)
    
    # Create the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute JavaScript to modify navigator properties to avoid detection
    driver.execute_script("""
        // Overwrite the 'webdriver' property to make it undefined
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Add language if missing
        if (navigator.languages === undefined) {
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'es']
            });
        }
        
        // Add Chrome plugins to avoid headless detection
        if (navigator.plugins.length === 0) {
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5].map(() => ({
                    name: 'Chrome PDF Plugin'
                }))
            });
        }
        
        // Create a more realistic WebGL fingerprint if needed
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Replace the WebGL info with regular Chrome values
            if (parameter === 37445) {
                return 'Google Inc.';  // UNMASKED_VENDOR_WEBGL
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)';  // UNMASKED_RENDERER_WEBGL
            }
            return getParameter.apply(this, arguments);
        };
    """)
    
    # Set the viewport to match the window size
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'mobile': False,
        'width': width,
        'height': height,
        'deviceScaleFactor': 1,
        'screenWidth': width,
        'screenHeight': height,
        'positionX': 0,
        'positionY': 0
    })
    
    return driver

def humanize_browser_interaction(driver):
    """Add randomized human-like behavior to browser interactions"""
    
    # Store original methods to patch
    original_find_element = driver.find_element
    original_click = webdriver.remote.webelement.WebElement.click
    original_send_keys = webdriver.remote.webelement.WebElement.send_keys
    
    # Add random delay to simulate human thinking time
    def humanized_find_element(by, value):
        time.sleep(random.uniform(0.3, 1.2))  # Random delay before finding element
        return original_find_element(by, value)
    
    # Add human-like click behavior with slight hesitations
    def humanized_click(self):
        time.sleep(random.uniform(0.1, 0.5))  # Random delay before clicking
        original_click(self)
        time.sleep(random.uniform(0.2, 0.8))  # Random delay after clicking
    
    # Add human-like typing with variable speed
    def humanized_send_keys(self, *args):
        text = "".join(args)
        for char in text:
            original_send_keys(self, char)
            # Random typing speed between characters
            time.sleep(random.uniform(0.05, 0.15))
    
    # Patch methods
    driver.find_element = humanized_find_element
    webdriver.remote.webelement.WebElement.click = humanized_click
    webdriver.remote.webelement.WebElement.send_keys = humanized_send_keys
    
    return driver

def add_natural_scrolling(driver):
    """Add natural scrolling behavior instead of jumping to elements"""
    
    def smooth_scroll_to(element_selector):
        # Get the element we want to scroll to
        element = driver.find_element(By.CSS_SELECTOR, element_selector)
        
        # Get element position
        location = element.location
        
        # Current scroll position
        current_y = driver.execute_script("return window.pageYOffset")
        
        # Target position (slightly above element for natural view)
        target_y = location["y"] - 100
        
        # Calculate the number of steps for smooth scrolling
        distance = target_y - current_y
        steps = 10
        step_size = distance / steps
        
        # Perform smooth scrolling
        for i in range(steps):
            new_y = current_y + (step_size * (i + 1))
            scroll_script = f"window.scrollTo({{top: {new_y}, behavior: 'auto'}})"
            driver.execute_script(scroll_script)
            # Random small delay between scroll steps
            time.sleep(random.uniform(0.01, 0.05))
            
        return element
    
    # Add the method to the driver
    driver.smooth_scroll_to = smooth_scroll_to
    
    return driver

def create_realistic_browser():
    """Create a browser with all stealth and human-like behaviors applied"""
    
    driver = create_stealth_driver(headless=False)
    driver = humanize_browser_interaction(driver)
    driver = add_natural_scrolling(driver)
    
    return driver
