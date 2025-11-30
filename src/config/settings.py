"""
Configuration settings for the Trip Planner Agent.
"""

import os
import sys
from pathlib import Path
from google.genai import types

# Add project root to Python path (for imports)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file if available (for local development)
from dotenv import load_dotenv
load_dotenv()

# API Configuration
# Note: For web UI, the API key is set by user input in the frontend
# For CLI, it should be in .env file or environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
