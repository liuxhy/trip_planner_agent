"""
Excel export functionality for trip plans.
"""

import os
import json
import pandas as pd
from src.config.settings import OUTPUT_DIR, DEFAULT_EXCEL_FILENAME


def export_plan_to_excel(plan_data: str, filename: str = DEFAULT_EXCEL_FILENAME):
    """
    Exports structured travel plan data to an Excel file in the output directory.

    Args:
        plan_data (str): The travel plan content. Ideally in JSON format or structured text.
        filename (str): The name of the file to save.

    Returns:
        str: Success or error message.
    """
    try:
        print(f"\n📊 Starting Excel export...")
        print(f"📝 Data to export (first 200 chars): {plan_data[:200]}...")

        # Ensure filename ends with .xlsx
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"📂 Output directory created: {OUTPUT_DIR}")

        # Create a simple DataFrame to save the text
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
