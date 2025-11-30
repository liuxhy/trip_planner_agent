"""
Helper functions for the trip planner.
"""


def exit_loop():
    """
    Called by RefinerAgent to exit the refinement loop when plan is approved.

    Returns:
        dict: Status message indicating approval.
    """
    return {
        "status": "approved",
        "message": "Travel plan approved. Exiting refinement loop."
    }
