import re
import logging
from selenium.webdriver.common.by import By

from browser.browser_manager import ensure_browser, get_driver

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
                            
                            # Skip if this container contains radio buttons or checkboxes (likely an answer option)
                            radio_inputs = parent_container.find_elements(By.CSS_SELECTOR, 'input[type="radio"], input[type="checkbox"]')
                            if radio_inputs:
                                continue
                                
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
            # Find all cml-viewers which likely contain question text, but filter out ones that are in answer options
            cml_viewers = driver.find_elements(By.CSS_SELECTOR, '[data-testid="cml-viewer"]')
            processed_viewers = []
            
            for i, viewer in enumerate(cml_viewers):
                # Skip viewers that are inside radio/checkbox option containers
                try:
                    # Check if this viewer is within a radio or checkbox option
                    parent = viewer
                    is_answer_option = False
                    
                    # Check up to 3 parent levels
                    for _ in range(3):
                        parent = parent.find_element(By.XPATH, "./..")
                        radio_inputs = parent.find_elements(By.CSS_SELECTOR, 'input[type="radio"], input[type="checkbox"]')
                        radio_labels = parent.find_elements(By.CSS_