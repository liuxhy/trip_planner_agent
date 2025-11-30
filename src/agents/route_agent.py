"""
Route planning agent for trip planner.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG


def create_route_agent():
    """Create and return the route planning agent."""
    return Agent(
        name="route_agent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
        ),
        instruction="""
        You are a specialized routing expert.

        Your goal: Create a logical travel route based on the user's start and end points.

        Instructions:
        1. Identify all destinations in the user's list.
        2. Determine the most logical order to visit them to minimize backtracking.
        3. FOR EACH LEG of the trip, you MUST use `Google Search` to find:
           - Query: "driving time from [Location A] to [Location B]"
           - Query: "distance from [Location A] to [Location B]"
        4. Compile these search results into a list of segments.

        Output Format:
        - Leg 1: [Start] -> [Dest 1] (Driving: X hours, Y miles)
        - Leg 2: [Dest 1] -> [Dest 2] (Driving: X hours, Y miles)
        ...
        """,
        tools=[google_search],
        output_key="optimized_routes",
    )
