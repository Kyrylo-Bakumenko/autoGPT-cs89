import os  # Add import for screenshot paths
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from browser.browser_manager import get_driver
from config import log_dir  # Add import for log directory

def navigate_course_modules():
    """Navigate through all course modules to explore the content"""
    driver = get_driver()
    if not driver:
        print("❌ Browser not available for navigation")
        return False
        
    # Enhanced logging: current task and URL
    current_url = driver.current_url
    logging.info(f"TASK: Exploring course modules | CURRENT URL: {current_url}")
    print("🧭 Exploring course modules...")
    
    try:
        # Log the selector being used
        logging.info("LOOKING FOR: Course navigation container with selector 'div[data-e2e='courseNavigation']'")
        # Wait for course navigation to be available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-e2e='courseNavigation']"))
        )
        
        # CHANGED: Try direct approach first - find all module links regardless of collection structure
        logging.info("LOOKING FOR: All module navigation links with selector 'a[data-test=\"rc-WeekNavigationItem\"]'")
        all_module_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-test="rc-WeekNavigationItem"]')
        
        if all_module_links:
            logging.info(f"Found {len(all_module_links)} total module links directly")
            print(f"📚 Found {len(all_module_links)} total modules")
            
            # Process all modules with improved handling for stale elements
            process_all_module_links(driver, current_url)
            return True
        
        # Original collection-based approach as fallback
        logging.info("No direct module links found, trying collection-based approach")
        logging.info("LOOKING FOR: Module collections with selector 'li[data-test='rc-WeekCollectionNavigationItem']'")
        module_collections = driver.find_elements(By.CSS_SELECTOR, "li[data-test='rc-WeekCollectionNavigationItem']")
        
        if not module_collections:
            logging.info("No module collections found either, navigation may not be possible")
            print("ℹ️ No course module collections found in navigation")
            return False
            
        logging.info(f"Found {len(module_collections)} module collections")
        print(f"📚 Found {len(module_collections)} module collections")
        
        # Process each module collection
        for i, collection in enumerate(module_collections, 1):
            try:
                logging.info(f"TASK: Exploring module collection {i} of {len(module_collections)}")
                print(f"📘 Exploring module collection {i} of {len(module_collections)}")
                
                # Scroll element into view before clicking
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", collection)
                time.sleep(0.5)
                
                # Since we can't reliably find modules within collections due to styling divs,
                # expand the collection if it has an expander button
                try:
                    expander = collection.find_element(By.CSS_SELECTOR, "button[aria-expanded='false']")
                    if expander:
                        logging.info("Found collapsed collection, expanding it")
                        driver.execute_script("arguments[0].click();", expander)
                        time.sleep(1)  # Wait for expansion animation
                except:
                    logging.info("Collection already expanded or no expander found")
                
                # After expanding, find all module links on the page again
                logging.info("Re-fetching all module links after potential collection expansion")
                process_all_module_links(driver, current_url)
                    
            except Exception as e:
                logging.error(f"Error navigating module collection {i}: {str(e)}")
                print(f"⚠️ Could not navigate module collection {i}: {str(e)}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error during module navigation: {str(e)}")
        print(f"❌ Failed to navigate course modules: {str(e)}")
        return False

def process_all_module_links(driver, course_page_url):
    """Process all module links on the page without relying on stale collections"""
    logging.info("TASK: Processing all module links with stale element protection")
    
    # Get the total number of modules to process
    all_modules = driver.find_elements(By.CSS_SELECTOR, 'a[data-test="rc-WeekNavigationItem"]')
    total_modules = len(all_modules)
    logging.info(f"Found {total_modules} total modules to process")
    print(f"Found {total_modules} modules to process")
    
    # Process each module one-by-one, returning to the course page after each
    for module_num in range(1, total_modules + 1):
        try:
            # Always start from the course page to avoid stale element issues
            if driver.current_url != course_page_url:
                logging.info(f"Navigating back to course page: {course_page_url}")
                driver.get(course_page_url)
                time.sleep(2)
                
                # Wait for navigation to be available again
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-e2e='courseNavigation']"))
                )
            
            # Fetch the module link fresh each time
            # We'll use index+1 in the XPath to target modules by position rather than relying on collection structure
            module_xpath = f"(//a[@data-test='rc-WeekNavigationItem'])[{module_num}]"
            logging.info(f"Looking for module {module_num} with XPath: {module_xpath}")
            
            try:
                module_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, module_xpath))
                )
                
                # Get module name for logging
                module_name = module_link.text.strip() or f"Module {module_num}"
                logging.info(f"Found module {module_num}: {module_name}")
                print(f"🔍 Processing module {module_num}/{total_modules}: {module_name}")
                
                # Scroll to the element to ensure it's visible
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", module_link)
                time.sleep(1)
                
                # Get the destination URL if available
                href = module_link.get_attribute('href')
                if href:
                    logging.info(f"Module link destination: {href}")
                
                # Click the link using JavaScript for better reliability
                logging.info(f"CLICKING: Module {module_num} link")
                driver.execute_script("arguments[0].click();", module_link)
                time.sleep(2)
                
                # Log the new URL after navigation
                new_url = driver.current_url
                logging.info(f"NAVIGATED TO: {new_url}")
                
                # Extract module title if available
                try:
                    module_title = driver.find_element(By.CSS_SELECTOR, "h1").text
                    logging.info(f"Module title: {module_title}")
                    print(f"  📝 Title: {module_title}")
                except:
                    logging.info("Could not find module title")
                
                # Return to course page using direct navigation
                logging.info(f"Returning to course page: {course_page_url}")
                print("  🔙 Returning to course page...")
                driver.get(course_page_url)
                time.sleep(2)
                
                # Verify we're back at the course page
                if driver.current_url == "https://www.coursera.org/":
                    logging.warning("Ended up at Coursera homepage instead of course page")
                    print("  ⚠️ Redirected to homepage, navigating back to course...")
                    driver.get(course_page_url)
                    time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error processing module {module_num}: {str(e)}")
                print(f"  ⚠️ Could not process module {module_num}: {str(e)}")
                
                # Try to get back to the course page
                driver.get(course_page_url)
                time.sleep(2)
        
        except Exception as e:
            logging.error(f"Fatal error processing module {module_num}: {str(e)}")
            print(f"❌ Fatal error processing module {module_num}: {str(e)}")
            return

# Keep the original click_module_links for compatibility but don't use it in the main flow
def click_module_links(driver, module_links):
    """Helper function to click through a list of module links - DEPRECATED"""
    # Store the original course page URL before clicking any links
    course_page_url = driver.current_url
    logging.info(f"STORED COURSE PAGE URL: {course_page_url}")
    
    for j, link in enumerate(module_links, 1):
        try:
            # Get module name before clicking
            module_name = link.text.strip() or f"Module {j}"
            current_url = driver.current_url
            
            # Enhanced logging of current action and URL
            logging.info(f"TASK: Navigating to module {j} ({module_name}) | CURRENT URL: {current_url}")
            print(f"    🔗 Navigating to {module_name}")
            
            # Capture destination URL if available
            href = link.get_attribute('href')
            if href:
                logging.info(f"DESTINATION URL: {href}")
            
            # Scroll link into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            time.sleep(0.5)
            
            # Log the action of clicking
            logging.info(f"CLICKING: Module link {j} ({module_name})")
            # Click the link
            driver.execute_script("arguments[0].click();", link)
            
            # Wait for page to load
            time.sleep(2)
            
            # Log the new URL after navigation
            new_url = driver.current_url
            logging.info(f"NAVIGATED TO: {new_url}")
            
            # Extract module title for better logging
            try:
                # Log the selector being used
                logging.info("LOOKING FOR: Module title using selector 'h1'")
                module_title = driver.find_element(By.CSS_SELECTOR, "h1").text
                logging.info(f"Found module title: {module_title}")
                print(f"      📝 Title: {module_title}")
            except Exception as title_error:
                logging.warning(f"Could not find module title: {str(title_error)}")
            
            # CHANGED: Instead of using browser history, navigate directly back to course page
            logging.info(f"TASK: Returning to course navigation | NAVIGATING DIRECTLY TO: {course_page_url}")
            print(f"    🔙 Returning to course page...")
            driver.get(course_page_url)
            
            # Wait for navigation to be available again
            logging.info("LOOKING FOR: Course navigation container to confirm return to course page")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-e2e='courseNavigation']"))
            )
            
            # Log the URL after going back and verify we're not at the homepage
            back_url = driver.current_url
            logging.info(f"RETURNED TO: {back_url}")
            
            # ADDED: Verify we didn't end up at the homepage
            if back_url == "https://www.coursera.org/":
                logging.warning("Ended up at Coursera homepage, navigating back to course page")
                print("    ⚠️ Redirected to homepage, navigating back to course...")
                driver.get(course_page_url)
                time.sleep(2)
            
            # Give the page a moment to fully load
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error navigating to module {j}: {str(e)}")
            print(f"    ⚠️ Could not navigate to module {j}: {str(e)}")
            
            # ADDED: If there's an error, try to return to the course page
            try:
                driver.get(course_page_url)
                logging.info(f"Returned to course page after error: {course_page_url}")
                time.sleep(2)
            except:
                logging.error("Failed to return to course page after error")

def navigate_to_grades():
    """Navigate to the grades section of the course"""
    driver = get_driver()
    if not driver:
        print("❌ Browser not available for navigation")
        return False
    
    # Enhanced logging with current task and URL
    current_url = driver.current_url
    logging.info(f"TASK: Navigating to grades page | CURRENT URL: {current_url}")
    print("🧭 Navigating to grades page...")
    
    try:
        # Log the selector being searched for
        logging.info("LOOKING FOR: Grades navigation item with selector 'li[data-e2e='gradesNavigationItem']'")
        # First find the grades navigation item
        grades_item = WebDriverWait(driver, 15).until(  # Increased timeout
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-e2e='gradesNavigationItem']"))
        )
        
        # Find the anchor element within the list item
        try:
            logging.info("LOOKING FOR: Anchor tag within grades navigation item")
            grades_link = grades_item.find_element(By.TAG_NAME, "a")
            logging.info("Found grades link in navigation")
            print("✅ Found grades link in navigation")
            
            # Get destination URL if available
            href = grades_link.get_attribute('href')
            if href:
                logging.info(f"DESTINATION URL: {href}")
        except NoSuchElementException:
            # If no anchor found, try clicking the list item itself
            logging.warning("No anchor tag found in grades navigation, using list item instead")
            grades_link = grades_item
            print("⚠️ No anchor tag found in grades navigation, using list item instead")
        
        # Scroll element into view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", grades_link)
        time.sleep(1)  # Increased delay
        
        # Log the click action
        logging.info("CLICKING: Grades navigation link")
        # Click the grades link
        driver.execute_script("arguments[0].click();", grades_link)
        print("✅ Clicked grades link")
        
        # Wait for grades page to load - with expanded selectors
        logging.info("LOOKING FOR: Grades page elements with selectors '.rc-GradeSummaryWidget, .gradebook, div[role='grid'][aria-label='Assignments Table'], .rc-AssignmentsTableRowCds'")
        try:
            WebDriverWait(driver, 15).until(  # Increased timeout
                lambda d: d.find_elements(By.CSS_SELECTOR, ".rc-GradeSummaryWidget, .gradebook, div[role='grid'][aria-label='Assignments Table'], .rc-AssignmentsTableRowCds")
            )
            
            # Log new URL after navigation
            new_url = driver.current_url
            logging.info(f"NAVIGATED TO GRADES PAGE: {new_url}")
            print("✅ Successfully navigated to grades page")
            
            # Now that we're on the grades page, explore assignments
            navigate_assignments_from_grades()
            
            return True
        except TimeoutException:
            logging.warning("Timeout waiting for grades page elements")
            print("⚠️ Clicked grades link but grades page did not load as expected")
            
            # Try to proceed anyway - sometimes the expected elements aren't found but we're still on the grades page
            current_url = driver.current_url
            logging.info(f"Current URL after grades link click: {current_url}")
            
            if "grades" in current_url:
                logging.info("URL contains 'grades', continuing despite missing expected elements")
                print("📝 URL contains 'grades', attempting to continue...")
                navigate_assignments_from_grades()
                return True
            return False
        
    except Exception as e:
        logging.error(f"Error navigating to grades: {str(e)}")
        print(f"❌ Failed to navigate to grades: {str(e)}")
        return False

def navigate_assignments_from_grades():
    """Navigate to assignments from the grades page"""
    driver = get_driver()
    if not driver:
        print("❌ Browser not available for navigation")
        return False
        
    print("📝 Exploring assignments from grades page...")
    logging.info("Starting assignments exploration")
    
    try:
        # Wait a bit for page to fully load
        time.sleep(2)
        
        # Try multiple ways to find the assignment rows
        assignment_rows = []
        
        # Method 1: Look for rows by class
        assignment_rows = driver.find_elements(By.CSS_SELECTOR, ".rc-AssignmentsTableRowCds")
        
        # Method 2: If that fails, try more generic row elements
        if not assignment_rows:
            assignment_rows = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
            print(f"Using fallback method to find rows, found {len(assignment_rows)} potential assignment rows")
        
        if not assignment_rows:
            print("ℹ️ No assignments found in the grades table")
            return False
            
        print(f"📚 Found {len(assignment_rows)} assignments")
        
        # PRINT ALL ASSIGNMENTS: First print all available assignments before proceeding
        print("\n=== AVAILABLE ASSIGNMENTS IN GRADES VIEW ===")
        for idx, row in enumerate(assignment_rows, 1):
            # Extract assignment name
            try:
                # IMPROVED: Look specifically for the data-e2e="item-title-text" element for name
                assignment_name = "Unknown Assignment"
                try:
                    title_elem = row.find_element(By.CSS_SELECTOR, "div[data-e2e='item-title-text'] a")
                    assignment_name = title_elem.text.strip()
                    logging.info(f"Found assignment name using title element: {assignment_name}")
                except:
                    # Fall back to previous method if specific element not found
                    name_cell = None
                    for selector in [".css-1lqc678", ".rc-AssignmentCell", "div[role='cell']"]:
                        cells = row.find_elements(By.CSS_SELECTOR, selector)
                        if cells and len(cells) > 0:
                            name_cell = cells[0]
                            break
                    
                    if name_cell:
                        assignment_name = name_cell.text.strip()
                
                # ADDED: Extract completion status
                status = "Status unknown"
                completion_status = "⬜ Incomplete"  # Default to incomplete
                
                try:
                    # Look specifically for the status column text
                    status_elem = row.find_element(By.CSS_SELECTOR, "div.status-column-text p")
                    status = status_elem.text.strip()
                    
                    # Check if it's completed (anything other than "--" or empty)
                    if status and status != "--":
                        completion_status = "✅ Completed"
                        logging.info(f"Assignment '{assignment_name}' marked as completed with status: {status}")
                except:
                    # Fall back to previous method
                    try:
                        status_cells = row.find_elements(By.CSS_SELECTOR, "div[role='cell']")
                        if len(status_cells) >= 3:
                            status = status_cells[2].text.strip() or status_cells[3].text.strip()
                            if status and status != "--":
                                completion_status = "✅ Completed"
                    except:
                        pass
                
                # Try to extract due date if available
                due_date = ""
                try:
                    due_elements = row.find_elements(By.CSS_SELECTOR, ".due-column-text-date")
                    if due_elements:
                        due_date = f" (Due: {due_elements[0].text})"
                except:
                    pass
                
                # Extract weight/percentage if available
                weight = ""
                try:
                    weight_elem = row.find_element(By.CSS_SELECTOR, "div.weight-column p span")
                    if weight_elem:
                        weight = f" | Weight: {weight_elem.text}"
                except:
                    pass
                
                print(f"  {idx}. {assignment_name} - {completion_status}{weight}{due_date}")
            except Exception as e:
                print(f"  {idx}. [Assignment info unavailable: {str(e)}]")
        print("=========================================\n")
        
        # NEW: Prompt user to select an assignment by number
        selection_prompt = input("Enter an assignment number to navigate to (or press Enter to skip): ")
        
        if selection_prompt.strip():
            try:
                # Convert input to integer and validate
                selection = int(selection_prompt.strip())
                
                # Check if selection is within valid range
                if 1 <= selection <= len(assignment_rows):
                    print(f"🔍 Navigating to assignment #{selection}...")
                    logging.info(f"User selected assignment #{selection} for navigation")
                    
                    # Get the selected row and navigate to it
                    selected_row = assignment_rows[selection-1]
                    
                    # Use the existing function to click on the row
                    if click_assignment_row(selected_row):
                        return True
                    else:
                        print(f"⚠️ Could not navigate to assignment #{selection}")
                else:
                    print(f"⚠️ Invalid selection: Please enter a number between 1 and {len(assignment_rows)}")
            except ValueError:
                print("⚠️ Invalid input: Please enter a valid number")
        else:
            # Show informative message if user skips selection
            print("📝 To process an assignment later, navigate to it and use the 'process' command")
            print("   or use the 'navigate' command to return to this grades view.\n")
        
        return True
        
    except Exception as e:
        logging.error(f"Error exploring assignments: {str(e)}")
        print(f"❌ Failed to explore assignments: {str(e)}")
        return False

def click_assignment_row(row):
    """Click on an assignment row with improved link finding"""
    driver = get_driver()
    
    try:
        # Store the grades page URL for direct navigation back
        grades_page_url = driver.current_url
        logging.info(f"STORED GRADES PAGE URL: {grades_page_url}")
        
        # Try to extract the assignment name for better user experience
        assignment_name = "Unknown Assignment"
        try:
            cells = row.find_elements(By.CSS_SELECTOR, ".css-1lqc678, .rc-AssignmentCell")
            if cells and len(cells) > 0:
                assignment_name = cells[0].text.strip()
        except:
            pass
            
        print(f"  📝 Navigating to assignment: {assignment_name}")
        
        # Find the anchor tag within this row
        link_element = None
        
        try:
            # First try: Find link with specific data-click-key attribute 
            link_element = row.find_element(By.CSS_SELECTOR, 
                "a[data-click-key='open_course_home.grades_page.click.grades_page_item_link']")
            print("  ✅ Found assignment link by data-click-key attribute")
        except:
            # Second try: Find any anchor tag within this row
            try:
                link_element = row.find_element(By.TAG_NAME, "a")
                print("  ✅ Found assignment link by tag name")
            except:
                # Third try: Find anything clickable
                print("  ⚠️ No direct link found - attempting to click the row itself")
                link_element = row
        
        # Scroll into view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
        time.sleep(1)  # Increased delay
        
        # Click the link element
        driver.execute_script("arguments[0].click();", link_element)
        print("  ✅ Clicked assignment link")
        
        # Wait for page to load
        time.sleep(3)
        
        # NEW: Check for cover page with Resume/Start button
        try:
            # Try to find the Resume/Start button
            button_selectors = [
                "button[data-testid='CoverPageActionButton']", 
                "button.cds-button-primary span.cds-button-label",
                "//button[.//span[contains(text(), 'Resume') or contains(text(), 'Start')]]"
            ]
            
            resume_button = None
            for selector in button_selectors:
                try:
                    if selector.startswith("//"):
                        resume_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        resume_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if resume_button:
                        break
                except:
                    pass
            
            if resume_button:
                button_text = resume_button.text.strip() if hasattr(resume_button, "text") else "Resume/Start"
                print(f"  🔄 Found '{button_text}' button on cover page - clicking to proceed to quiz...")
                logging.info(f"Clicking '{button_text}' button on assignment cover page")
                
                # Scroll the button into view and click it
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", resume_button)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", resume_button)
                
                # Wait for quiz content to load
                time.sleep(3)
                print("  ✅ Navigated to quiz content")
        except Exception as e:
            logging.info(f"No cover page or resume button found, might be directly in quiz: {str(e)}")
        
        # Ask user for confirmation before continuing
        user_choice = input("\n✋ Found the quiz. What would you like to do?\n"
                           "1. Process this quiz now\n"
                           "2. Return to grades page\n"
                           "3. Continue exploring all assignments\n"
                           "Your choice (1-3): ")
        
        if user_choice == '1':
            print("👉 Processing quiz now...")
            from quiz.quiz_handler import process_quiz_content
            process_quiz_content()
            # CHANGED: Navigate directly back to grades page instead of using browser history
            print("🔙 Returning to grades page...")
            driver.get(grades_page_url)
            time.sleep(2)
            return True
            
        elif user_choice == '2':
            # CHANGED: Go directly back to grades page instead of using browser history
            print("🔙 Returning to grades page...")
            driver.get(grades_page_url)
            time.sleep(2)
            return True
            
        elif user_choice == '3':
            # CHANGED: Go directly back to grades page instead of using browser history
            driver.get(grades_page_url)
            time.sleep(2)
            
            # Now find assignments again as the page may have reloaded
            try:
                time.sleep(2)  # Wait for page to reload
                assignment_rows = driver.find_elements(By.CSS_SELECTOR, ".rc-AssignmentsTableRowCds")
                if not assignment_rows:
                    assignment_rows = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
                
                if len(assignment_rows) > 1:
                    # Skip the first one since we already processed it
                    print("👉 Continuing with remaining assignments...")
                    for i, next_row in enumerate(assignment_rows[1:], 2):
                        process_next_assignment(next_row, i, grades_page_url)  # Pass the grades URL
                else:
                    print("⚠️ No additional assignments found")
            except Exception as e:
                print(f"⚠️ Error finding remaining assignments: {str(e)}")
            return True
        else:
            # CHANGED: Go directly back to grades page instead of using browser history
            print("🔙 Invalid choice, returning to grades page...")
            driver.get(grades_page_url)
            time.sleep(2)
            return True
            
    except Exception as e:
        logging.error(f"Error clicking assignment: {str(e)}")
        print(f"  ⚠️ Could not click assignment: {str(e)}")
        
        # Try to take screenshot for debugging
        try:
            from datetime import datetime
            screenshot_path = os.path.join(log_dir, f"assignment_click_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Saved error screenshot to {screenshot_path}")
        except:
            pass
        return False

def process_next_assignment(row, index, grades_page_url=None):
    """Process a single assignment row"""
    driver = get_driver()
    
    try:
        # Store grades page URL if not provided
        if not grades_page_url:
            grades_page_url = driver.current_url
            logging.info(f"STORED GRADES PAGE URL: {grades_page_url}")
        
        # Try to extract the assignment name
        assignment_name = "Unknown Assignment"
        try:
            cells = row.find_elements(By.CSS_SELECTOR, ".css-1lqc678, .rc-AssignmentCell")
            if cells and len(cells) > 0:
                assignment_name = cells[0].text.strip()
        except:
            pass
            
        print(f"  📝 Navigating to assignment {index}: {assignment_name}")
        
        # Find the anchor tag within this row
        link_element = None
        try:
            link_element = row.find_element(By.CSS_SELECTOR, 
                "a[data-click-key='open_course_home.grades_page.click.grades_page_item_link']")
        except:
            try:
                link_element = row.find_element(By.TAG_NAME, "a")
            except:
                link_element = row
        
        # Scroll into view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
        time.sleep(1)
        
        # Click the assignment
        driver.execute_script("arguments[0].click();", link_element)
        
        # Wait for page to load
        time.sleep(3)
        
        # NEW: Check for cover page with Resume/Start button
        try:
            # Try to find the Resume/Start button
            button_selectors = [
                "button[data-testid='CoverPageActionButton']", 
                "button.cds-button-primary span.cds-button-label",
                "//button[.//span[contains(text(), 'Resume') or contains(text(), 'Start')]]"
            ]
            
            resume_button = None
            for selector in button_selectors:
                try:
                    if selector.startswith("//"):
                        resume_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        resume_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if resume_button:
                        break
                except:
                    pass
            
            if resume_button:
                button_text = resume_button.text.strip() if hasattr(resume_button, "text") else "Resume/Start"
                print(f"  🔄 Found '{button_text}' button on cover page - clicking to proceed to quiz...")
                logging.info(f"Clicking '{button_text}' button on assignment cover page")
                
                # Scroll the button into view and click it
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", resume_button)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", resume_button)
                
                # Wait for quiz content to load
                time.sleep(3)
                print("  ✅ Navigated to quiz content")
        except Exception as e:
            logging.info(f"No cover page or resume button found, might be directly in quiz: {str(e)}")
        
        # Ask user what to do with this quiz
        user_choice = input(f"\n✋ Quiz {index}: {assignment_name}\n"
                          "1. Process this quiz\n"
                          "2. Skip this quiz\n"
                          "3. Stop exploration\n"
                          "Your choice (1-3): ")
        
        if user_choice == '1':
            print("👉 Processing quiz...")
            from quiz.quiz_handler import process_quiz_content
            process_quiz_content()
            
        if user_choice == '3':
            print("🛑 Stopping assignment exploration as requested.")
            driver.get(grades_page_url)  # Return directly to grades page
            time.sleep(2)
            return False
        
        # CHANGED: Go directly back to grades page instead of using browser history
        driver.get(grades_page_url)
        time.sleep(2)
        return True
        
    except Exception as e:
        logging.error(f"Error processing assignment {index}: {str(e)}")
        print(f"  ⚠️ Could not process assignment {index}: {str(e)}")
        
        # Try to return to grades page if we have the URL
        if grades_page_url:
            try:
                driver.get(grades_page_url)
                time.sleep(2)
            except:
                pass
        return False

def navigate_after_login():
    """Perform navigation sequence after successful login"""
    print("🧭 Starting post-login navigation sequence...")
    
    # First navigate through all course modules
    navigate_course_modules()
    
    # Then navigate to the grades page which will also explore assignments
    navigate_to_grades()
    
    print("✅ Navigation sequence complete")
    return True
