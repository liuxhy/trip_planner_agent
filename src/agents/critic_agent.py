"""
Critic agent that reviews and validates travel plans.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG


def create_critic_agent():
    """Create and return the critic agent."""
    return Agent(
        name="CriticAgent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
        ),
        instruction="""
        You are a Travel Logic Critic. Review the plan below.

        Plan: {Day-by-Day_Plan}

        Validation Rules:
        1. **Drive Time Reality:** Does the plan suggest driving 15 hours in one day? If so, REJECT it.
        2. **Transport Consistency:** If the user asked to drive, are there flights in the plan? If so, REJECT it.
        3. **Pacing:** Is there enough time to actually do the activities listed?

        Response:
        - If valid, respond EXACTLY: "APPROVED"
        - If invalid, provide 3 specific corrections needed.
        """,
        output_key="critique",
    )
