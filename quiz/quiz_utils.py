import json
import logging
import os
from datetime import datetime

from config import log_dir

def extract_question_from_radiogroup(radiogroup_element):
    """
    Extract question text and answer options from a radiogroup element
    using the specific Coursera HTML structure
    """
    from browser.browser_manager import get_driver  # Changed from autoGPTcs89.browser.browser_manager
    from selenium.webdriver.common.by import By
    
    driver = get_driver()
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
        logging.error(f"Error extracting from radiogroup: {str(e)}")
        return None, None

def process_agreement_checkbox(driver):
    """
    Find and process the agreement checkbox and input field at the end of the quiz form
    """
    from selenium.webdriver.common.by import By
    import time
    
    try:
        # First scroll to bottom of page to ensure agreement elements are loaded
        logging.info("TASK: Scrolling to bottom of page to find honor code agreement section")
        print("🔍 Scrolling to bottom of page to find honor code agreement section...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for scroll to complete
        
        # Log the current URL
        current_url = driver.current_url
        logging.info(f"CURRENT URL: {current_url}")
        
        # IMPROVED: Using exact selectors the user found in DOM inspection
        print("\n=== HONOR CODE AGREEMENT SECTION ===")
        
        # First check for the parent containers
        logging.info("LOOKING FOR: Parent container with selector 'div[data-e2e='AttemptSubmitControls']'")
        attempt_submit_controls = driver.find_elements(By.CSS_SELECTOR, "div[data-e2e='AttemptSubmitControls']")
        if attempt_submit_controls:
            logging.info("Found AttemptSubmitControls container")
            print("✅ Found AttemptSubmitControls container")
        else:
            logging.warning("Could not find AttemptSubmitControls container")
            print("❌ Could not find AttemptSubmitControls container")
        
        logging.info("LOOKING FOR: Honor code container with selector 'div[data-testid='HonorCodeAgreement']'")
        honor_code_container = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='HonorCodeAgreement']")
        if honor_code_container:
            logging.info("Found HonorCodeAgreement container")
            print("✅ Found HonorCodeAgreement container")
        else:
            logging.warning("Could not find HonorCodeAgreement container - will try alternative lookups")
            print("❌ Could not find HonorCodeAgreement container - will try alternative lookups")
            
        # STEP 1: Find and handle the agreement checkbox using the exact selector
        logging.info("TASK: Finding and handling honor code agreement checkbox")
        agreement_checkbox = None
        try:
            # Direct lookup by data-testid as specified by user
            logging.info("LOOKING FOR: Agreement checkbox div with selector 'div[data-testid='agreement-checkbox']'")
            agreement_checkbox_div = driver.find_element(By.CSS_SELECTOR, "div[data-testid='agreement-checkbox']")
            logging.info("Found agreement checkbox div using exact selector")
            print("✅ Found agreement checkbox div using exact selector")
            
            # Find the checkbox input within this div
            logging.info("LOOKING FOR: Checkbox input within agreement-checkbox div")
            agreement_checkbox = agreement_checkbox_div.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            logging.info("Found checkbox input within agreement-checkbox div")
            print("✅ Found checkbox input within agreement-checkbox div")
        except Exception as e:
            logging.warning(f"Could not find agreement checkbox with exact selector: {str(e)}")
            print(f"❌ Could not find agreement checkbox with exact selector: {str(e)}")
            
            # Fall back to more generic searches if exact selector fails
            logging.info("Trying alternative methods to find agreement checkbox...")
            print("Trying alternative methods to find agreement checkbox...")
            
            # Try multiple selectors with detailed logging
            checkbox_selectors = [
                "#agreement-checkbox-base",
                "input[id*='agreement-checkbox']",
                "input[id*='honor-code']",
                "input[id*='honourCode']",
                "input[id*='honorCode']"
            ]
            
            for selector in checkbox_selectors:
                try:
                    agreement_checkbox = driver.find_element(By.CSS_SELECTOR, selector)
                    logging.info(f"Found agreement checkbox using fallback selector: {selector}")
                    print(f"✅ Found agreement checkbox using fallback selector: {selector}")
                    break
                except:
                    pass
                    
            # Last resort - look for any checkbox in a div containing "honor" text
            if not agreement_checkbox:
                try:
                    honor_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'honor') or contains(text(), 'Honor')]")
                    for elem in honor_elements:
                        try:
                            parent = elem
                            for _ in range(3):  # Look up to 3 levels up
                                parent = parent.find_element(By.XPATH, "./..")
                                checkboxes = parent.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                                if checkboxes:
                                    agreement_checkbox = checkboxes[0]
                                    logging.info("Found checkbox near honor code text")
                                    print("✅ Found checkbox near honor code text")
                                    break
                            if agreement_checkbox:
                                break
                        except:
                            continue
                except:
                    pass
        
        # Check the checkbox if found
        if agreement_checkbox:
            logging.info("Found honor code agreement checkbox")
            print("📝 Found honor code agreement checkbox")
            
            # Check if already selected
            checkbox_selected = agreement_checkbox.is_selected()
            logging.info(f"Agreement checkbox already checked: {checkbox_selected}")
            
            if not checkbox_selected:
                try:
                    # Scroll to ensure visibility
                    logging.info("Scrolling agreement checkbox into view")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agreement_checkbox)
                    time.sleep(0.5)
                    
                    # Try to click using JavaScript
                    logging.info("CLICKING: Honor code agreement checkbox using JavaScript")
                    driver.execute_script("arguments[0].click();", agreement_checkbox)
                    logging.info("Successfully checked honor code agreement checkbox")
                    print("✅ Successfully checked honor code agreement checkbox")
                    
                    # Verify if the click worked
                    try:
                        checkbox_checked = agreement_checkbox.is_selected()
                        logging.info(f"Checkbox checked after click: {checkbox_checked}")
                    except:
                        pass
                    
                except Exception as e:
                    logging.error(f"Could not check agreement checkbox: {str(e)}")
                    print(f"⚠️ Could not check agreement checkbox: {str(e)}")
            else:
                logging.info("Agreement checkbox already checked, no action needed")
                print("✅ Agreement checkbox already checked")
        else:
            logging.warning("No agreement checkbox found on this page")
            print("❓ No agreement checkbox found on this page")
        
        # STEP 2: Find and fill the legal name input field with correct selectors
        logging.info("TASK: Finding and handling legal name input field")
        agreement_input = None
        
        try:
            # NEW: Look for the legal name div using the correct data-testid attribute
            logging.info("LOOKING FOR: Legal name input with selector 'div[data-testid=\"legal-name\"]'")
            legal_name_div = driver.find_element(By.CSS_SELECTOR, "div[data-testid='legal-name']")
            logging.info("✅ Found legal name div using exact selector")
            print("✅ Found legal name div using exact selector")
            
            # Find the input within this div
            logging.info("LOOKING FOR: Input field within legal name div")
            agreement_input = legal_name_div.find_element(By.TAG_NAME, "input")
            logging.info("✅ Found legal name input field")
            print("✅ Found legal name input field")
        except Exception as e:
            logging.warning(f"Could not find legal name input with exact selector: {str(e)}")
            print(f"❌ Could not find legal name input with exact selector")
            
            # Try alternative methods to find the field
            try:
                # Try by placeholder attribute
                logging.info("LOOKING FOR: Input with placeholder 'Enter your legal name'")
                agreement_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter your legal name']")
                logging.info("✅ Found legal name input by placeholder attribute")
                print("✅ Found legal name input by placeholder attribute")
            except:
                # Try by aria-label attribute
                try:
                    logging.info("LOOKING FOR: Input with aria-label 'Enter your legal name'")
                    agreement_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Enter your legal name']")
                    logging.info("✅ Found legal name input by aria-label attribute")
                    print("✅ Found legal name input by aria-label attribute")
                except:
                    # Try looking within the honor code agreement container
                    if honor_code_container and len(honor_code_container) > 0:
                        try:
                            agreement_input = honor_code_container[0].find_element(By.TAG_NAME, "input")
                            logging.info("✅ Found text input within honor code container")
                            print("✅ Found input field within honor code container")
                        except:
                            pass
        
        # Fill the input if found
        if agreement_input:
            # Use "Kyrylo Bakumenko" for the legal name field (not "DONE")
            input_text = "Kyrylo Bakumenko"
            
            # Enter the text
            try:
                # Scroll to ensure visibility
                logging.info("Scrolling legal name input into view")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agreement_input)
                time.sleep(0.5)
                
                # Check the current value before clearing
                current_value = agreement_input.get_attribute("value") or ""
                logging.info(f"Current input value before clearing: '{current_value}'")
                
                # Clear and enter text
                logging.info("Clearing legal name field")
                agreement_input.clear()
                
                logging.info(f"ENTERING TEXT: '{input_text}' into legal name field")
                agreement_input.send_keys(input_text)
                logging.info(f"Successfully entered '{input_text}' in legal name field")
                print(f"✅ Entered '{input_text}' in legal name field")
                
                # Verify the text was entered correctly
                try:
                    entered_value = agreement_input.get_attribute("value") or ""
                    logging.info(f"Value after entering text: '{entered_value}'")
                except:
                    pass
                
            except Exception as e:
                logging.error(f"Could not enter text in legal name field: {str(e)}")
                print(f"⚠️ Could not enter text in legal name field: {str(e)}")
        else:
            logging.warning("No legal name input found on this page")
            print("❓ No legal name input found on this page")
        
        # Take a screenshot to help debug any issues
        try:
            import os
            from datetime import datetime
            from config import log_dir
            
            screenshot_path = os.path.join(log_dir, f"honor_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved screenshot of honor code section to {screenshot_path}")
            print(f"📷 Saved screenshot of honor code section to {screenshot_path}")
        except Exception as screenshot_error:
            logging.error(f"Could not save honor code screenshot: {str(screenshot_error)}")
        
        print("=================================\n")
        
        # Return True if we found at least one of the elements
        return agreement_checkbox is not None or agreement_input is not None
    
    except Exception as e:
        logging.error(f"Error processing agreement section: {str(e)}")
        logging.error(f"CURRENT URL WHEN ERROR OCCURRED: {driver.current_url}")
        print(f"❌ Error processing agreement section: {str(e)}")
        return False

def log_question_for_review(question_text, options_text, answer):
    """
    Log failed or problematic questions for later review
    """
    try:
        with open(os.path.join(log_dir, "failed_questions.txt"), "a") as fail_file:
            fail_file.write(f"\n--- {datetime.now()} ---\n")
            fail_file.write(f"QUESTION: {question_text}\n")
            fail_file.write(f"OPTIONS: {options_text}\n")
            fail_file.write(f"SELECTED: {answer}\n")
            fail_file.write("---\n")
        return True
    except Exception as e:
        logging.error(f"Failed to log question for review: {str(e)}")
        return False
