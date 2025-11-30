"""
Export agent that formats and saves travel plans to Excel.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from src.config.settings import DEFAULT_MODEL, RETRY_CONFIG
from src.tools.excel_export import export_plan_to_excel


def create_export_agent():
    """Create and return the export agent."""
    file_tool = FunctionTool(export_plan_to_excel)

    return Agent(
        name="FinalExportAgent",
        model=Gemini(
            model=DEFAULT_MODEL,
            retry_options=RETRY_CONFIG
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
