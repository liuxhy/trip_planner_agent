"""
Weather forecast functionality using Open-Meteo API.
"""

import requests


def get_weather_forecast(city: str, start_date: str, end_date: str):
    """
    Retrieves the daily weather forecast for a specific city and date range.
    Uses the free Open-Meteo API.

    Args:
        city (str): Name of the city (e.g., "Las Vegas").
        start_date (str): Format YYYY-MM-DD.
        end_date (str): Format YYYY-MM-DD.

    Returns:
        str: Formatted weather forecast or error message.
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
