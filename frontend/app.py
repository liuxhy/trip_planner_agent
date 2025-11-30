"""
Trip Planner Agent - Streamlit Frontend
A simple web interface for the trip planning agent system.
"""

import streamlit as st
import asyncio
import os
import sys
from datetime import date
from pathlib import Path
import contextlib
from io import StringIO
import importlib

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Save the original stdout/stderr (the actual terminal)
_original_stdout = sys.__stdout__
_original_stderr = sys.__stderr__

@contextlib.contextmanager
def redirect_to_terminal():
    """Redirect all output to the actual terminal, bypassing Streamlit"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        # Redirect to the original terminal streams
        sys.stdout = _original_stdout
        sys.stderr = _original_stderr
        yield
    finally:
        # Restore Streamlit's streams
        sys.stdout = old_stdout
        sys.stderr = old_stderr

# Page configuration
st.set_page_config(
    page_title="Trip Planner Agent",
    page_icon="✈️",
    layout="wide"
)

# Title and description
st.title("✈️ AI Trip Planner")
st.markdown("Plan your perfect trip with AI-powered agents!")

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Google API Key",
        type="password",
        help="Enter your Google AI API key. Get one at https://aistudio.google.com/apikey"
    )

    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API Key configured")

    st.divider()
    st.markdown("### 📝 About")
    st.markdown("""
    This app uses Google's ADK (Agent Development Kit) with multiple specialized agents:
    - 🗺️ Route Planner
    - ✈️ Flight Finder
    - 🏨 Hotel Finder
    - 🎯 Activity Recommender
    - 🌤️ Weather Checker
    """)

# Main form
st.header("🎯 Plan Your Trip")

col1, col2 = st.columns(2)

with col1:
    starting_point = st.text_input("📍 Starting Point", placeholder="e.g., San Jose")
    destinations = st.text_input("🌍 Destinations (comma-separated)",
                                 placeholder="e.g., Lake Tahoe, Las Vegas, Grand Canyon")

    start_date = st.date_input("📅 Start Date", value=date.today())
    end_date = st.date_input("📅 End Date", value=date.today())

with col2:
    budget = st.number_input("💰 Budget ($)", min_value=100, max_value=50000, value=2000, step=100)

    transport = st.selectbox("🚗 Preferred Transport",
                            ["Mix of driving and flights", "Driving only", "Flights only"])

    travel_style = st.selectbox("🎨 Travel Style",
                               ["Relaxed", "Adventure", "Luxury", "Budget-friendly"])

# Advanced options
with st.expander("⚙️ Advanced Options"):
    show_debug = st.checkbox("Show debug output", value=False)
    save_excel = st.checkbox("Save results to Excel", value=True)

# Generate button
if st.button("🚀 Generate Trip Plan", type="primary", use_container_width=True):

    # Validation
    if not api_key:
        st.error("❌ Please provide a Google API Key in the sidebar")
        st.stop()

    if not starting_point or not destinations:
        st.error("❌ Please fill in starting point and destinations")
        st.stop()

    # Construct query
    query = f"""I want to travel to {destinations} starting from {starting_point}.
    Dates: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}.
    Budget: ${budget}.
    I prefer {transport.lower()}.
    My travel style is {travel_style.lower()}."""

    st.info(f"📋 Query: {query}")

    # Create a placeholder for progress
    progress_placeholder = st.empty()
    result_placeholder = st.empty()

    try:
        # Clear old Excel file to ensure fresh results
        excel_path = "./output/travel_plan.xlsx"
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
            except:
                pass

        with progress_placeholder.container():
            st.write("🔄 Initializing agents...")

            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Loading trip planner agents...")
            progress_bar.progress(10)

            # Import the workflow module with terminal output
            with redirect_to_terminal():
                # Force reload to avoid cached imports
                import src.workflows.trip_planner
                importlib.reload(src.workflows.trip_planner)
                from src.workflows.trip_planner import plan_trip

            status_text.text("Agents loaded! Planning your trip...")
            progress_bar.progress(30)

            # Run the async function
            async def run_planner():
                return await plan_trip(query)

            status_text.text("🤖 Agents working on your trip plan...")
            progress_bar.progress(50)

            # Execute the planning with all output redirected to terminal
            with redirect_to_terminal():
                _original_stdout.write("\n" + "="*80 + "\n")
                _original_stdout.write("🚀 Starting trip planning agents...\n")
                _original_stdout.write(f"📋 Query: {query}\n")
                _original_stdout.write("="*80 + "\n\n")
                _original_stdout.flush()

                response = asyncio.run(run_planner())

            progress_bar.progress(100)
            status_text.text("✅ Trip plan generated!")

        # Clear progress and show results
        progress_placeholder.empty()

        with result_placeholder.container():
            # Display the Excel table if available
            excel_path = "./output/travel_plan.xlsx"
            if os.path.exists(excel_path):
                try:
                    import pandas as pd
                    df = pd.read_excel(excel_path)

                    # Display as a nice table
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
                except Exception as e:
                    # Fallback to text if Excel reading fails
                    st.markdown(response)
            else:
                # Fallback to text response if no Excel file
                st.markdown(response)

            # Download section
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="📄 Download as Text",
                    data=response,
                    file_name=f"trip_plan_{start_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with col2:
                if os.path.exists(excel_path):
                    with open(excel_path, "rb") as file:
                        st.download_button(
                            label="📊 Download as Excel",
                            data=file,
                            file_name=f"trip_plan_{start_date.strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                else:
                    st.download_button(
                        label="📊 Download as Excel",
                        data=response,
                        file_name=f"trip_plan_{start_date.strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        disabled=True,
                        help="Excel file not available"
                    )

    except Exception as e:
        progress_placeholder.empty()
        st.error(f"❌ Error: {str(e)}")

        if show_debug:
            st.exception(e)

        # Check for common errors
        if "RESOURCE_EXHAUSTED" in str(e):
            st.warning("""
            ⚠️ **Quota Exceeded**

            You've hit the Google API free tier limit. Options:
            1. Wait for quota to reset (usually daily)
            2. Upgrade your Google AI plan
            3. Try again in a few hours
            """)
        elif "API key" in str(e).lower():
            st.warning("⚠️ Please check your API key is valid")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Built with Google ADK | Powered by Gemini AI</p>
</div>
""", unsafe_allow_html=True)
