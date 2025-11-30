"""
Main travel plan agent that coordinates other agents.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool, FunctionTool
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG
from src.tools.weather import get_weather_forecast


def create_plan_agent(flight_agent, hotel_agent, activity_agent):
    """
    Create and return the main travel planning agent.

    Args:
        flight_agent: The flight search agent
        hotel_agent: The hotel search agent
        activity_agent: The activity recommendation agent

    Returns:
        Agent: The configured planning agent
    """
    weather_tool = FunctionTool(get_weather_forecast)

    return Agent(
        name="initial_plan_agent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
        ),
        instruction="""
        You are the Lead Travel Planner. You have access to the optimized route: {optimized_routes}

        Your Tasks:
        1. **Transport Check:** - READ the user request.
           - IF the user says "driving", DO NOT use the `flight_agent`. Instead, rely on the driving times in {optimized_routes}.
           - IF the user says "flying" or "mix", use the `flight_agent` to find the MOST REASONABLE flight (not cheapest, not most expensive, but best value).

        2. **Accommodation:**
           - Use `hotel_agent` to find the MOST REASONABLE hotel for each destination.
           - The agent will return ONE recommended hotel per location - use that recommendation in your plan.
           - For EACH night, specify the EXACT hotel name (e.g., "Holiday Inn Express Downtown")
           - Ensure total accommodation costs fit within the user's budget.
           - If the recommended hotel exceeds budget, ask hotel_agent to search again with a lower price range.

        3. **Activity Planning:**
           - Use `activity_agent` to find top-rated attractions and activities.
           - Use `get_weather_forecast` for each city to check conditions. If rain is forecast, suggest indoor alternatives.

        4. **Budget Management:**
           - Keep track of cumulative costs (transport + hotels + activities)
           - Ensure the total stays within the user's stated budget
           - Prioritize value over luxury

        Output:
        Create a Day-by-Day itinerary that is REASONABLE and within budget.
        For EACH day, include:
        - Specific hotel name (e.g., "Hampton Inn & Suites Downtown")
        - Transportation details (specific flight numbers with times, or drive times)
        - Main activities for the day
        - Daily cost breakdown
        - Helpful travel tips
        """,
        tools=[
            AgentTool(flight_agent),
            AgentTool(hotel_agent),
            AgentTool(activity_agent),
            weather_tool
        ],
        output_key="Day-by-Day_Plan",
    )
