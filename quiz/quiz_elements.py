import time
import logging
import re
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException
from selenium import webdriver

from dotenv import load_dotenv
from browser.browser_manager import ensure_browser, get_driver
from quiz.quiz_utils import extract_question_from_radiogroup
from config import client, SYSTEM_ROLE, log_dir

load_dotenv()
MODEL=os.getenv("MODEL", "gpt-4o-mini")

def process_modern_radiogroup(radiogroup_element):
    """Process a modern Coursera radiogroup question with enhanced error handling"""
    question_text, options = extract_question_from_radiogroup(radiogroup_element)
    driver = get_driver()
    
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
            model=MODEL,
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

def process_checkbox_question(question, question_text):
    """
    Process a question with checkboxes (multiple answers possible)
    Works for both standard and SVG-based checkboxes
    """
    print("Processing checkbox question (multiple answers possible)")
    logging.info(f"Processing checkbox question: {question_text[:100]}...")
    driver = get_driver()
    
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
                    model=MODEL,
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
                model=MODEL,
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

def process_text_input(driver, question_text, input_field):
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
            # Find parent container of the input field
            parent_container = input_field
            for _ in range(5):  # Look up to 5 levels up
                if parent_container:
                    parent_container = parent_container.find_element(By.XPATH, "./..")
                    heading_elems = parent_container.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
                    for elem in heading_elems:
                        if elem.text:
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
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.05
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"ChatGPT generated answer: {answer}")
        
        # Enter the answer
        input_field.clear()
        input_field.send_keys(answer)
    
    except Exception as e:
        print(f"❌ Error processing text input question: {str(e)}")

def process_multiple_choice(question, question_text, choices):
    """Enhanced handler for multiple choice questions"""
    if not ensure_browser():
        return
    
    driver = get_driver()
        
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
            model=MODEL,
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

def process_svg_radio_buttons(question, question_text, option_labels):
    """Handle modern Coursera UI with SVG-based radio buttons"""
    print("Processing SVG-based multiple choice question")
    logging.info(f"Processing SVG radio button question: {question_text[:100]}...")
    driver = get_driver()
    
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
            model=MODEL,
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

def process_svg_checkboxes(question, question_text, option_labels):
    """Handle the SVG-based checkboxes in Coursera's new UI"""
    print("Processing SVG-based checkbox question (multiple answers possible)")
    driver = get_driver()
    
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
            model=MODEL,
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
                try:
                    # Use JavaScript click which is more reliable for SVG elements
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option_labels[answer_index])
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", option_labels[answer_index])
                    print(f"Selected option {answer}")
                except Exception as click_error:
                    logging.error(f"Error clicking SVG checkbox: {str(click_error)}")
                    print(f"⚠️ Could not select option {answer}")
            else:
                print(f"Invalid answer '{answer}', skipping")
    
    except Exception as e:
        print(f"❌ Error processing SVG checkboxes: {str(e)}")
