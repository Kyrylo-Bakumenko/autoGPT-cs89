import re
import logging
from bs4 import BeautifulSoup
from browser.browser_manager import ensure_browser, get_driver

def detect_page_type():
    """Analyze current page and detect what type of content it is"""
    if not ensure_browser():
        return "unknown"
        
    print("🔍 Analyzing current page type...")
    driver = get_driver()
    
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Enhanced quiz detection - check for multiple structures
        quiz_elements = soup.find_all([
            # Old style
            lambda tag: tag.name == "div" and tag.has_attr("class") and 
                       any(c for c in tag.get("class", []) if "rc-QuestionView" in c or "QuizSubmission" in c),
            # New style
            lambda tag: tag.name == "div" and tag.has_attr("data-testid") and 
                       "part-Submission_MultipleChoiceQuestion" in tag.get("data-testid", "")
        ])
        
        # Also check for quiz by role attribute
        quiz_groups = soup.find_all("div", role="group")
        quiz_legends = soup.find_all("div", attrs={"data-testid": "legend"})
        
        if quiz_elements or quiz_groups or quiz_legends:
            return "quiz"
        
        # Check for video elements
        video_elements = soup.find_all(["video", "iframe"]) or soup.find_all(class_=re.compile(r"video-player|rc-Video", re.I))
        if video_elements:
            return "video"
        
        # Check for reading content (most common fallback)
        reading_elements = soup.find_all(class_=re.compile(r"rc-ReadingItem|reading-item", re.I))
        if reading_elements:
            return "reading"
        
        # Check title for hints
        title = soup.find("h1")
        if (title):
            title_text = title.get_text().lower()
            if any(word in title_text for word in ["quiz", "exam", "test", "assessment"]):
                return "quiz"
            elif any(word in title_text for word in ["video", "lecture"]):
                return "video"
            elif any(word in title_text for word in ["reading", "article", "notes"]):
                return "reading"
        
        # Default fallback
        return "unknown"
    
    except Exception as e:
        print(f"❌ Error detecting page type: {str(e)}")
        return "unknown"
