"""
Configuration settings for the Trip Planner Agent.
"""

import os
from dotenv import load_dotenv
from google.genai import types

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY environment variable is not set.\n"
        "Please ensure your .env file contains GOOGLE_API_KEY=your_actual_key"
    )

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Model Configuration
DEFAULT_MODEL = "gemini-2.5-flash-lite"

# Retry Configuration
RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Application Configuration
APP_NAME = "agents"
USER_ID = "default"
SESSION = "default"

# Output Configuration
OUTPUT_DIR = "./output"
DEFAULT_EXCEL_FILENAME = "travel_plan.xlsx"

# Agent Configuration
MAX_LOOP_ITERATIONS = 2
