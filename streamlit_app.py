"""
Streamlit Cloud entry point.
This file should be at the root for Streamlit Cloud deployment.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main app
from frontend.app import *
