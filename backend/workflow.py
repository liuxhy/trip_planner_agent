#!/usr/bin/env python3
"""
Trip Planner Agent - Local Docker Version
Uses Google ADK to coordinate flight search and trip planning.
"""

# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import json
import requests
import asyncio
import sys
import os
import warnings
from dotenv import load_dotenv

# Suppress Google ADK warnings about function calls in responses
warnings.filterwarnings('ignore', message='.*non-text parts.*')
warnings.filterwarnings('ignore', message='.*function_call.*')

# Setup API keys for local environment
#########################
print("🔧 Setting up local environment...")

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY environment variable is not set.\n"
        "Please ensure your .env file contains GOOGLE_API_KEY=your_actual_key"
    )

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
print("✅ Setup and authentication complete.")
# Import Google ADK tools
from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent, LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.genai import types
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext

print("✅ ADK components imported successfully.")

# config retry options
###########################
retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

# Helper Functions
def export_plan_to_excel(plan_data: str, filename: str = "travel_plan.xlsx"):
    """
    Exports structured travel plan data to an Excel file in the output directory.

    Args:
        plan_data (str): The travel plan content. ideally in JSON format or structured text.
        filename (str): The name of the file to save (default: travel_plan.xlsx).
    """
    try:
        print(f"\n📊 Starting Excel export...")
        print(f"📝 Data to export (first 200 chars): {plan_data[:200]}...")

        # Ensure filename ends with .xlsx
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        # Create output directory if it doesn't exist
        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        print(f"📂 Output directory created: {output_dir}")

        # Create a simple DataFrame to save the text
        # If the agent is smart, it will pass JSON string which we can parse
        try:
            # Try parsing as JSON first for better formatting
            print("🔍 Attempting to parse as JSON...")
            data = json.loads(plan_data)
            df = pd.json_normalize(data)
            print(f"✅ Successfully parsed JSON with {len(df)} rows")
        except Exception as json_error:
            # Fallback: Just save the raw text in one cell or row
            print(f"⚠️ JSON parse failed: {json_error}. Using fallback text format.")
            df = pd.DataFrame({'Travel Plan Details': [plan_data]})

        # Save to Excel
        df.to_excel(filepath, index=False)
        abs_path = os.path.abspath(filepath)
        success_msg = f"✅ Success: Plan saved to {abs_path}"
        print(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"❌ Error saving Excel file: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

# Wrap it as a Tool
file_tool = FunctionTool(export_plan_to_excel)

print("✅ FileTool (export_to_excel) created.")

def get_weather_forecast(city: str, start_date: str, end_date: str):
    """
    Retrieves the daily weather forecast (Max Temp and Precip) for a specific city and date range.
    Uses the free Open-Meteo API.
    
    Args:
        city (str): Name of the city (e.g., "Las Vegas").
        start_date (str): Format YYYY-MM-DD.
        end_date (str): Format YYYY-MM-DD.
    """
    try:
        # Step 1: Geocode the city to get Lat/Lon
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_res = requests.get(geo_url, params=geo_params).json()
        
        if not geo_res.get("results"):
            return f"Error: Could not find coordinates for city: {city}"
            
        location = geo_res["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        
        # Step 2: Get Weather Forecast
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "precipitation_sum", "precipitation_probability_max"],
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }
        
        w_res = requests.get(weather_url, params=weather_params).json()
        
        if "error" in w_res:
            return f"Error from Weather API: {w_res['reason']}"
            
        # Format the output nicely for the Agent
        daily = w_res.get("daily", {})
        times = daily.get("time", [])
        temps = daily.get("temperature_2m_max", [])
        precips = daily.get("precipitation_sum", [])
        probs = daily.get("precipitation_probability_max", [])
        
        summary = [f"Weather Forecast for {city}:"]
        for i, date in enumerate(times):
            summary.append(
                f"- {date}: Max {temps[i]}°C, Rain: {precips[i]}mm ({probs[i]}% chance)"
            )
            
        return "\n".join(summary)

    except Exception as e:
        return f"Tool Error: {str(e)}"

# Wrap as an Agent Tool
weather_tool = FunctionTool(get_weather_forecast)
print("✅ Free weather_tool created.")

# This is the function that the RefinerAgent will call to exit the loop.
def exit_loop():
    """Call this function ONLY when the critique is 'APPROVED', indicating the travel plan is finished and no more changes are needed."""
    return {"status": "approved", "message": "Travel plan approved. Exiting refinement loop."}


print("✅ exit_loop function created.")

# Agent architecture
###########################

# Route agent: with input starting point and destinations, give optimized routes for the travel plan
route_agent = Agent(
    name="route_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
    ),
    # Instruction is key here: We force it to SEARCH for times, not guess.
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
print("✅ route_agent created.")

# Flight Agent: with input date and destination, search for the flight options and price
###########################
flight_agent = Agent(
    name="flight_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
    ),
    instruction="""You are a specialized flight search agent. Find the MOST REASONABLE flight option based on the user's needs.

    Search Strategy:
    1. Use google_search to find available flights for the given route and dates
    2. Evaluate flights based on these criteria:
       - Price (avoid extremely cheap flights with bad times/long layovers, but also avoid unnecessarily expensive ones)
       - Timing (prefer convenient departure/arrival times - avoid red-eyes unless budget is very tight)
       - Duration (prefer non-stop or minimal layovers)
       - Airline reliability (prefer major carriers when price difference is reasonable)

    What is "MOST REASONABLE":
    - NOT the absolute cheapest (often has terrible times or long connections)
    - NOT the most expensive (unnecessary premium)
    - The BEST VALUE: good timing + acceptable price + reasonable duration

    Return Format:
    Provide ONE recommended flight with:
    - Flight number(s)
    - Airline
    - Departure and arrival times (with timezone)
    - Duration and layover info (if applicable)
    - Price
    - Brief reason why this is the best choice (e.g., "Direct flight at reasonable midday time for $180")
    """,
    tools=[google_search],
    output_key="flight_options",
)
print("✅ flight_agent created.")


# Hotel Agent: Based on the travel plan, find the proper hotel information and feedback to root agent.
#########################
hotel_agent = Agent(
    name="hotel_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
    ),
    instruction="""You are a specialized hotel search agent. Find the MOST REASONABLE hotel option for each destination.

    Search Strategy:
    1. Use google_search to find hotels in the destination area
    2. Consider the user's total budget and number of nights
    3. Evaluate hotels based on these criteria:
       - Price (look for good value, not necessarily cheapest)
       - Location (walking distance or short drive to main attractions)
       - Quality (minimum 3-star rating, good reviews)
       - Amenities (free breakfast, parking, WiFi are valuable)

    What is "MOST REASONABLE":
    - NOT the cheapest motel (poor location/quality)
    - NOT luxury hotels (unnecessary expense)
    - BEST VALUE: Good location + clean & safe + fair price + positive reviews

    Examples of reasonable choices:
    - Holiday Inn Express (reliable, often includes breakfast)
    - Hampton Inn (good quality-to-price ratio)
    - Courtyard by Marriott (solid mid-range option)
    - Best Western Plus (dependable budget-friendly)

    Return Format:
    Provide ONE recommended hotel with:
    - SPECIFIC hotel name (e.g., "Holiday Inn Express Downtown")
    - Exact address or neighborhood
    - Nightly rate
    - Number of nights
    - Total cost for the stay
    - Key amenities (e.g., "Free breakfast, parking, pool")
    - Brief reason why this is the best choice (e.g., "Central location, good reviews, includes breakfast - best value for $120/night")

    DO NOT recommend luxury hotels unless the budget clearly allows for it.
    """,
    tools=[google_search],
    output_key="hotel_options",
)
print("✅ hotel_agent created.")

# activity Agent: Handles the general "Things to do" searches
activity_agent = Agent(
    name="activity_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),  # Using lighter model
    instruction="""
    You are a travel activity scout. 
    Your job is to find the top rated attractions, hidden gems, and must-see spots for specific locations.
    Use `Google Search` to find this information.
    """,
    tools=[google_search], # It's okay here because there are no other FunctionTools
    output_key="activity_options",
)
print("✅ activity_agent created.")

# Plan agent: generate travel plan.
#############################
initial_plan_agent = Agent(
    name="initial_plan_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
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
    # We still give it the flight tool, but the Prompt above tells it when to IGNORE it.
    tools=[AgentTool(flight_agent), AgentTool(hotel_agent), AgentTool(activity_agent), weather_tool],
    output_key="Day-by-Day_Plan",
)

# This agent's only job is to provide feedback or the approval signal. It has no tools.
critic_agent = Agent(
    name="CriticAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
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

print("✅ critic_agent created.")

# This agent refines the travel plan based on critique OR calls the exit_loop function.
refiner_agent = Agent(
    name="RefinerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a travel plan refiner. You have a travel plan draft and critique.
    
    Travel plan draft: {Day-by-Day_Plan}
    Critique: {critique}
    
    Your task is to analyze the critique.
    - IF the critique is EXACTLY "APPROVED", you MUST call the `exit_loop` function and nothing else.
    - OTHERWISE, rewrite the travel plan draft to fully incorporate the feedback from the critique.
    You can call flight_agent and hotel_agent to find relEvant flight and hotel info if necessary.""",
    output_key="Day-by-Day_Plan",  # It overwrites the plan with the new, refined version.
    tools=[AgentTool(flight_agent), AgentTool(hotel_agent),
        FunctionTool(exit_loop)
    ],  # The tool is now correctly initialized with the function reference.
)

print("✅ refiner_agent created.")

# The LoopAgent contains the agents that will run repeatedly: Critic -> Refiner.
plan_refinement_loop = LoopAgent(
    name="PlanRefinementLoop",
    sub_agents=[critic_agent, refiner_agent],
    max_iterations=2,  # Prevents infinite loops
)

# final_export_agent is to translate the text plan into the specific JSON format
final_export_agent = Agent(
    name="FinalExportAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Using lighter model to reduce quota usage
        retry_options=retry_config
    ),
    instruction="""
    You are the Data Formatter and Exporter.

    Your ONLY job is to take the travel plan and save it to Excel.

    Travel Plan: {Day-by-Day_Plan}

    **YOUR TASK:**
    1. Convert the travel plan above into a JSON array format
    2. Use these exact keys for each day:
       - "Day" (Number)
       - "Date" (String)
       - "City" (String)
       - "Hotel" (String: Extract the SPECIFIC hotel name from the plan, e.g., "Hilton Garden Inn", "Marriott Downtown". NOT generic like "downtown hotel")
       - "Main_Activity" (String)
       - "Transport_Method" (String: "Flight", "Drive", or "N/A")
       - "Flight_Details" (String: If Transport_Method is "Flight", include flight number, airline, departure/arrival times. Otherwise use "N/A")
       - "Drive_Time" (String: If Transport_Method is "Drive", include estimated driving hours (e.g., "4 hours 30 mins"). Otherwise use "N/A")
       - "Estimated_Cost" (Number)
       - "Travel_Tips" (String)
    3. IMMEDIATELY call export_plan_to_excel() with your JSON string as the plan_data parameter

    **CRITICAL:** You MUST call the export_plan_to_excel function. Do not just describe what to do - actually call the function!

    Example JSON format:
    [
      {"Day": 1, "Date": "12/12/2025", "City": "Lake Tahoe", "Hotel": "Hyatt Regency", "Main_Activity": "Travel from San Jose", "Transport_Method": "Drive", "Flight_Details": "N/A", "Drive_Time": "4 hours 30 mins", "Estimated_Cost": 250, "Travel_Tips": "Leave early to avoid traffic"},
      {"Day": 2, "Date": "12/13/2025", "City": "Las Vegas", "Hotel": "MGM Grand", "Main_Activity": "Travel to Las Vegas", "Transport_Method": "Flight", "Flight_Details": "UA 1234, United Airlines, 10:00 AM - 11:30 AM", "Drive_Time": "N/A", "Estimated_Cost": 180, "Travel_Tips": "Check-in online 24hrs before"},
      {"Day": 3, "Date": "12/14/2025", "City": "Las Vegas", "Hotel": "MGM Grand", "Main_Activity": "Explore the Strip", "Transport_Method": "N/A", "Flight_Details": "N/A", "Drive_Time": "N/A", "Estimated_Cost": 150, "Travel_Tips": "Wear comfortable shoes"}
    ]

    Call the function NOW with your formatted JSON!
    """,
    tools=[file_tool], 
    output_key="final_save_status",
)

# The root agent is a SequentialAgent that defines the overall workflow: Initial Write -> Refinement Loop.
root_agent = SequentialAgent(
    name="PlanPipeline",
    sub_agents=[route_agent, initial_plan_agent, plan_refinement_loop, final_export_agent],
)

print("✅ Loop and Sequential Agents created.")

session_service = InMemorySessionService()
APP_NAME = "agents"  # Match the expected app name to avoid warnings
USER_ID = "default"
SESSION = "default"

# Create the Runner with proper configuration
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

print("✅ root_agent created.")


async def plan_trip(query: str):
    """
    Plan a trip based on the user query.

    Args:
        query: User's trip planning request including dates, locations, and budget

    Returns:
        Response from the trip coordinator agent
    """
    print(f"\n📋 Planning trip with query: {query}\n")

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


async def main():
    """Main function to run the trip planner."""
    # Default example queries (you can choose one or provide via command line)
    default_query = (
        "I want to travel to Salt Lake City, Lake Tahoe, Las Vegas, and Grand Canyon "
        "starting from San Jose. Dates: 12/12/2025 to 12/23/2025. Budget: $2000. "
        "I prefer mix of driving and flights. My travel style is relaxed."
    )

    # Get query from command line arguments or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = default_query
        print(f"📝 Using default query. To use custom query, pass as command line argument.\n")

    try:
        # Run the trip planner
        response = await plan_trip(query)
    except Exception as e:
        print(f"\n❌ Error during trip planning: {e}")
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*80)
    print("🎉 TRIP PLANNING COMPLETE")
    print("="*80)
    print(f"\nResponse:\n{response}")
    print("\n" + "="*80)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
