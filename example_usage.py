from autoGPTcs89.browser.selenium_stealth_helper import create_realistic_browser

def test_your_server():
    # Create a stealth browser
    driver = create_realistic_browser()
    
    try:
        # Visit your server
        driver.get("http://localhost:3000")
        print("Successfully connected to your server")
        
        # Test interactions with realistic behavior
        # For example, find a form and enter data
        username = driver.find_element(By.ID, "username")
        username.send_keys("testuser")  # Will type like a human
        
        # Smooth scroll to a button
        submit_button = driver.smooth_scroll_to("#submit-button")
        submit_button.click()  # Will click with natural timing
        
        # Test completed
        print("Test completed successfully")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_your_server()
