#!/usr/bin/env python3
import os
import sys
import logging

# Configure environment first
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

# Set up directories
log_dir = os.path.join(parent_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(log_dir, 'coursera_assistant.log')
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    filename=log_file
)

# CHANGE: Clean up any lock files from previous runs
lock_file = os.path.join(parent_dir, 'browser', '.browser_lock')
if os.path.exists(lock_file):
    try:
        os.remove(lock_file)
        logging.info("Removed stale browser lock file")
    except Exception as e:
        logging.error(f"Could not remove lock file: {str(e)}")

# Import modules only when ready
if __name__ == "__main__":
    logging.info("Starting Coursera Assistant")
    print("📝 Starting Coursera Assistant - initializing...")
    print("\n📌 USING PERSISTENT BROWSER PROFILE")
    print("   Login sessions and cookies will be saved.")
    print("   You should only need to solve CAPTCHA once.")
    print("   Profile stored in: chrome_profile/\n")
    
    # Import the main function
    from main import hybrid_mode
    
    # Run the application
    try:
        hybrid_mode()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"❌ An error occurred: {str(e)}")
    finally:
        # Ensure clean shutdown of browser
        try:
            from browser.browser_manager import get_driver
            driver = get_driver()
            if driver:
                driver.quit()
                print("✅ Browser closed successfully")
        except:
            pass
