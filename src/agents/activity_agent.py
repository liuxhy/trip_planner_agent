"""
Activity recommendation agent for trip planner.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG


def create_activity_agent():
    """Create and return the activity recommendation agent."""
    return Agent(
        name="activity_agent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
        ),
        instruction="""
        You are a travel activity scout.
        Your job is to find the top rated attractions, hidden gems, and must-see spots for specific locations.
        Use `Google Search` to find this information.
        """,
        tools=[google_search],
        output_key="activity_options",
    )
