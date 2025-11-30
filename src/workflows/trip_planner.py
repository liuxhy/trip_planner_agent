"""
Main workflow for the trip planner.
"""

import warnings
from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Suppress ADK warnings
warnings.filterwarnings('ignore', message='.*non-text parts.*')
warnings.filterwarnings('ignore', message='.*function_call.*')

from src.config.settings import APP_NAME, MAX_LOOP_ITERATIONS
from src.agents.route_agent import create_route_agent
from src.agents.flight_agent import create_flight_agent
from src.agents.hotel_agent import create_hotel_agent
from src.agents.activity_agent import create_activity_agent
from src.agents.plan_agent import create_plan_agent
from src.agents.critic_agent import create_critic_agent
from src.agents.refiner_agent import create_refiner_agent
from src.agents.export_agent import create_export_agent


def create_workflow():
    """
    Create and configure the complete trip planning workflow.

    Returns:
        tuple: (root_agent, runner) - The configured agent workflow and runner
    """
    print("🤖 Building agent architecture...")

    # Create individual agents
    route_agent = create_route_agent()
    print("✅ route_agent created.")

    flight_agent = create_flight_agent()
    print("✅ flight_agent created.")

    hotel_agent = create_hotel_agent()
    print("✅ hotel_agent created.")

    activity_agent = create_activity_agent()
    print("✅ activity_agent created.")

    # Create planning agent (coordinates other agents)
    initial_plan_agent = create_plan_agent(flight_agent, hotel_agent, activity_agent)
    print("✅ initial_plan_agent created.")

    # Create review agents
    critic_agent = create_critic_agent()
    print("✅ critic_agent created.")

    refiner_agent = create_refiner_agent(flight_agent, hotel_agent)
    print("✅ refiner_agent created.")

    # Create refinement loop
    plan_refinement_loop = LoopAgent(
        name="PlanRefinementLoop",
        sub_agents=[critic_agent, refiner_agent],
        max_iterations=MAX_LOOP_ITERATIONS,
    )
    print("✅ plan_refinement_loop created.")

    # Create export agent
    final_export_agent = create_export_agent()
    print("✅ final_export_agent created.")

    # Create root agent (sequential workflow)
    root_agent = SequentialAgent(
        name="PlanPipeline",
        sub_agents=[
            route_agent,
            initial_plan_agent,
            plan_refinement_loop,
            final_export_agent
        ],
    )
    print("✅ root_agent (PlanPipeline) created.")

    # Create runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    print("✅ Runner initialized.")

    return root_agent, runner


async def plan_trip(query: str):
    """
    Plan a trip based on the user query.

    Args:
        query: User's trip planning request including dates, locations, and budget

    Returns:
        Response from the trip coordinator agent
    """
    import os

    # Validate API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            "❌ GOOGLE_API_KEY is not set.\n"
            "For web UI: Enter your API key in the sidebar.\n"
            "For CLI: Set GOOGLE_API_KEY in your .env file or environment."
        )

    print(f"\n📋 Planning trip with query: {query}\n")

    # Create workflow
    _, runner = create_workflow()

    # Run the agent and get the response
    result = await runner.run_debug(query)

    # Extract text response (handle function_call parts)
    if hasattr(result, 'text'):
        return result.text
    elif isinstance(result, str):
        return result
    else:
        # If result has parts, extract text from them
        try:
            return str(result)
        except:
            return "Response received but couldn't extract text. Check logs above for details."
