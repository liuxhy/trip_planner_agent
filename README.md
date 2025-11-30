# ✈️ AI Trip Planner Agent

An intelligent trip planning application powered by Google's ADK (Agent Development Kit) with multiple specialized AI agents working together to create personalized travel itineraries.

## 🌟 Features

- **Smart Route Planning** - Optimized routes to minimize backtracking
- **Flight Search** - Finds the most reasonable flights (best value, not extremes)
- **Hotel Recommendations** - Mid-range hotels with good location and amenities
- **Activity Suggestions** - Top-rated attractions and hidden gems
- **Weather Integration** - Real-time weather forecasts with indoor alternatives
- **Budget Management** - Stays within your specified budget
- **Excel Export** - Download detailed day-by-day itinerary

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/liuxhy/trip_planner_agent.git
cd trip_planner_agent
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your Google API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

**⚠️ Important:** The free tier gives you 250 requests/day - enough for 2-3 trip plans daily.

### 5. Set up your API key

**For Web UI (Streamlit):**
- No setup needed! Just enter your API key in the sidebar when you run the app
- Your key is never stored or committed

**For CLI usage:**
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your API key:
```
GOOGLE_API_KEY=AIzaSyC-YourActualAPIKeyHere
```

**🔒 Security:** Never commit your `.env` file to GitHub!

### 6. Run the app

**Web Interface (Recommended):**
```bash
python run.py
```
Or directly:
```bash
streamlit run frontend/app.py
```

**Command Line:**
```bash
python run.py "Travel to Hawaii from Seattle, Jan 10-20, $3000 budget"
```

Open your browser at `http://localhost:8501`

## 📖 How to Use

1. **Enter trip details:**
   - Starting point: "San Francisco"
   - Destinations: "Lake Tahoe, Las Vegas, Grand Canyon"
   - Dates, budget, preferences

2. **Generate plan** (takes 1-3 minutes)

3. **View & download:**
   - Interactive table with day-by-day itinerary
   - Download as Excel or text

## 💡 What You Get

Your plan includes:
- ✅ Specific hotel names (e.g., "Holiday Inn Express Downtown")
- ✅ Flight details (numbers, times) or drive times
- ✅ Daily activities and attractions
- ✅ Weather forecasts
- ✅ Cost breakdown per day
- ✅ Travel tips

## 🤖 How It Works

8 specialized AI agents work together:
1. 🗺️ **Route Agent** - Plans optimal routes
2. ✈️ **Flight Agent** - Finds best-value flights
3. 🏨 **Hotel Agent** - Recommends reasonable hotels
4. 🎯 **Activity Agent** - Discovers attractions
5. 🌤️ **Weather Agent** - Checks forecasts
6. 👨‍⚖️ **Critic Agent** - Reviews plans
7. 🔧 **Refiner Agent** - Improves plans
8. 📊 **Export Agent** - Creates Excel file

## ⚠️ Troubleshooting

### API Quota Exceeded
**Error:** `429 RESOURCE_EXHAUSTED`

**Solution:**
- Wait for daily reset
- Or upgrade at [Google AI Pricing](https://ai.google.dev/pricing)

### No Excel File
Check terminal output for errors. Excel generation requires valid JSON from agents.

## 🛠️ Tech Stack

- Google ADK & Gemini 2.0 Flash Lite
- Streamlit
- Pandas & OpenPyxl
- Python 3.10+

## 🤝 Contributing

Contributions welcome! Open issues or submit PRs.

## 📄 License

MIT License

---

**Note:** Each user must get their own free Google API key. Never share your key publicly!
