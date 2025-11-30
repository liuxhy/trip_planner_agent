"""
Entry point for running the Trip Planner Agent.
"""

import sys
import asyncio


def run_streamlit():
    """Run the Streamlit web interface."""
    import subprocess
    print("🚀 Starting Streamlit app...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])


async def run_cli(query: str):
    """
    Run the trip planner from command line.

    Args:
        query: Trip planning query string
    """
    from src.workflows.trip_planner import plan_trip

    print("\n" + "="*80)
    print("🤖 AI Trip Planner - Command Line")
    print("="*80 + "\n")

    response = await plan_trip(query)

    print("\n" + "="*80)
    print("🎉 TRIP PLANNING COMPLETE")
    print("="*80)
    print(f"\n{response}\n")
    print("="*80 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # CLI mode with query
        query = " ".join(sys.argv[1:])
        asyncio.run(run_cli(query))
    else:
        # Launch Streamlit UI
        run_streamlit()


if __name__ == "__main__":
    main()
