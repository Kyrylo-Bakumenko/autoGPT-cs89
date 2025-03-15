import re
import os
import time
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv
from browser.browser_manager import ensure_browser, get_driver
from config import client, SYSTEM_ROLE

load_dotenv()
MODEL=os.getenv("MODEL", "gpt-4o-mini")

def process_reading_content():
    """Process reading content but don't auto-navigate"""
    if not ensure_browser():
        return False
        
    print("📚 Processing reading content...")
    driver = get_driver()
    
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract the reading content text to summarize it
        reading_content = soup.find("div", class_=re.compile(r"rc-ReadingItem|reading-item", re.I))
        content_text = ""
        
        if not reading_content:
            reading_content = soup.find("main", class_="item-page-content")
            
        if reading_content:
            # Get h1 title
            title = reading_content.find("h1")
            if title:
                content_text += f"Title: {title.get_text(strip=True)}\n\n"
            
            # Get paragraph content
            paragraphs = reading_content.find_all(["p", "li"])
            for p in paragraphs:
                content_text += f"{p.get_text(strip=True)}\n"
        
        # Summarize the content using ChatGPT
        if content_text:
            print("📝 Summarizing content with ChatGPT...")
            response = client.chat.completions.create(
                model=MODEL, 
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE},
                    {"role": "user", "content": f"Summarize this content in 3-5 bullet points:\n\n{content_text[:4000]}"}
                ],
                temperature=0.3
            )
            summary = response.choices[0].message.content.strip()
            print("\n--- Content Summary ---")
            print(summary)
            print("----------------------\n")
        else:
            print("⚠️ No content found to summarize")
            
        # Check if there's a mark complete button and notify user
        try:
            complete_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='mark-complete']")
            print("✅ TASK COMPLETE: Reading has been summarized.")
            print("👉 Manual action needed: You can click 'Mark as completed' when ready.")
        except:
            print("✅ TASK COMPLETE: Reading has been summarized.")
            print("👉 No 'Mark as complete' button found - you may need to navigate manually.")
            
        return True
        
    except Exception as e:
        print(f"❌ Error processing reading content: {str(e)}")
        return False

def process_video_content():
    """Process video content but don't auto-navigate"""
    if not ensure_browser():
        return False
        
    print("🎬 Processing video content...")
    driver = get_driver()
    
    try:
        # Get video title
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text
            print(f"Video Title: {video_title}")
        except:
            print("Could not find video title")
        
        # Try to find and access transcript
        transcript_text = ""
        try:
            # Try to find and click the transcript tab
            transcript_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Transcript')]"))
            )
            transcript_tab.click()
            time.sleep(2)
            
            # Extract transcript
            transcript_container = driver.find_element(By.CSS_SELECTOR, ".rc-Transcript")
            transcript_text = transcript_container.text
            print("📄 Found video transcript")
            
            # Summarize the transcript
            if transcript_text:
                print("📝 Summarizing video transcript with ChatGPT...")
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_ROLE},
                        {"role": "user", "content": f"Summarize this video transcript in 3-5 bullet points:\n\n{transcript_text[:4000]}"}
                    ],
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
                print("\n--- Video Summary ---")
                print(summary)
                print("--------------------\n")
        except Exception as e:
            print(f"No transcript found or accessible: {str(e)}")
        
        print("✅ TASK COMPLETE: Video has been processed.")
        print("👉 Manual action needed: You may want to watch key parts of the video before continuing.")
        return True
        
    except Exception as e:
        print(f"❌ Error processing video content: {str(e)}")
        return False
