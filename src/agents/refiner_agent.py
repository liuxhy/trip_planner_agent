"""
Refiner agent that improves travel plans based on feedback.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool, FunctionTool
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG
from src.tools.helpers import exit_loop


def create_refiner_agent(flight_agent, hotel_agent):
    """
    Create and return the refiner agent.

    Args:
        flight_agent: The flight search agent
        hotel_agent: The hotel search agent

    Returns:
        Agent: The configured refiner agent
    """
    return Agent(
        name="RefinerAgent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
        ),
        instruction="""You are a travel plan refiner.

        Travel plan draft: {Day-by-Day_Plan}
        Critique: {critique}

        CRITICAL INSTRUCTIONS:
        1. Check if the critique contains the word "APPROVED"
        2. IF IT DOES: Immediately call the exit_loop() function. DO NOT respond with text. ONLY call exit_loop().
        3. IF IT DOES NOT contain "APPROVED": Rewrite the travel plan to fix the issues mentioned in the critique.

        Remember: When you see "APPROVED", you MUST call the exit_loop function, not write a response.""",
        output_key="Day-by-Day_Plan",
        tools=[
            FunctionTool(exit_loop),
            AgentTool(flight_agent),
            AgentTool(hotel_agent)
        ],
    )
