# Coursera Automation Assistant

An AI-powered tool that helps automate interactions with Coursera coursework, including summarizing readings, processing videos, and answering quiz questions.

## Features

- **Content Processing**: Automatically summarizes readings and video transcripts
- **Quiz Automation**: Uses AI to answer multiple-choice, checkbox, and text input questions
- **Human-like Browsing**: Uses stealth techniques to avoid detection as an automation tool
- **Modular Design**: Clean, maintainable code structure

## Setup

1. Install required dependencies:
   ```
   pip install selenium openai beautifulsoup4 python-dotenv webdriver-manager
   ```

2. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY="your_openai_api_key"
   COURSERA_EMAIL="your_coursera_email"
   COURSERA_PASSWORD="your_coursera_password"
   COURSERA_COURSE_URL="https://www.coursera.org/learn/your-course-url"
   ```

3. Make sure you have the `selenium_stealth_helper.py` file in your `/Users/kyrylobakumenko/vscode/` directory

## Modular Architecture

The application follows a modular design pattern for better maintainability and separation of concerns:

### config.py
**Purpose**: Centralizes configuration, environment variables, and shared resources
- **Key Features**:
  - Logging setup (`setup_logging`)
  - OpenAI client configuration (`setup_openai`)
  - Environment variable management for credentials
  - System role definitions for AI prompts

### browser_manager.py
**Purpose**: Handles all browser-related functionality
- **Key Methods**:
  - `init_browser()`: Creates a stealth browser instance
  - `ensure_browser()`: Checks if browser is alive and restarts if needed
  - `is_browser_alive()`: Verifies browser session is still active
  - `get_driver()`: Provides access to the browser driver instance

### auth_handler.py
**Purpose**: Manages Coursera authentication processes
- **Key Methods**:
  - `login_to_coursera()`: Automates login with human-like behavior
  - Support for CAPTCHA handling and fallback to manual login

### page_analyzer.py
**Purpose**: Analyzes and identifies page content types
- **Key Methods**:
  - `detect_page_type()`: Determines if a page contains quiz, reading, or video content

### content_processor.py
**Purpose**: Processes reading and video content
- **Key Methods**:
  - `process_reading_content()`: Extracts and summarizes reading material
  - `process_video_content()`: Handles videos and extracts/summarizes transcripts

### quiz_handler.py
**Purpose**: Manages quiz questions and answers
- **Key Methods**:
  - `extract_quiz_questions()`: Identifies all quiz questions
  - `process_quiz_content()`: Main quiz processing workflow
  - `process_modern_radiogroup()`: Handles multiple-choice questions
  - `process_checkbox_question()`: Handles multi-select questions
  - `process_text_input()`: Handles free response questions
  - Various helper methods to handle different question formats

### main.py
**Purpose**: Entry point and command interface
- **Key Methods**:
  - `hybrid_mode()`: Main operation mode with interactive commands
  - Command processing for user interactions

## Usage

Run the main script:

   ```
   python main.py
   ```

### Commands

- `process`: Analyze and process current page (quiz, reading, or video)
- `status`: Show information about the current page
- `questions`: Extract and display quiz questions without processing
- `restart`: Restart browser if it crashes
- `quit`: Exit the application

## Implementation Details

### Quiz Question Types Supported
- Multiple choice (radio buttons)
- Multiple select (checkboxes)
- Text input questions
- Both traditional and modern Coursera UI elements

### Content Processing
- Reading material extraction and summarization
- Video transcript extraction and summarization
- Human-like browser interaction to avoid detection

## Note

This tool is for educational purposes only. Please use responsibly and in accordance with Coursera's terms of service.