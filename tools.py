import json
import os
from datetime import datetime

# Path helper
def load_json_data(filename):
    paths_to_try = [
        filename,
        os.path.join(os.path.dirname(__file__), filename) if os.path.dirname(__file__) else filename
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

def search_flights(source: str, destination: str) -> dict:
    flights = load_json_data("flights.json")
    src, dest = source.strip().lower(), destination.strip().lower()
    matches = [f for f in flights if src in f.get("from", "").lower() and dest in f.get("to", "").lower()]
    
    for f in matches:
        dep = datetime.fromisoformat(f['departure_time'])
        arr = datetime.fromisoformat(f['arrival_time'])
        duration_mins = (arr - dep).total_seconds() / 60
        f['duration_minutes'] = duration_mins
        f['duration'] = f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m"
        
    if not matches: return {"success": False, "message": f"No flights found from {source} to {destination}."}
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])
    return {"success": True, "cheapest_option": cheapest, "fastest_option": fastest, "summary": f"Found {len(matches)} flights from {source} to {destination}."}

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    hotels = load_json_data("hotels.json")
    matches = [h for h in hotels if city.strip().lower() in h.get("city", "").lower() and h.get("stars", 0) >= min_rating and h.get("price_per_night", 0) <= max_price]
    if not matches: return {"success": False, "message": f"No hotels found in {city} matching criteria."}
    sorted_by_rating = sorted(matches, key=lambda x: x.get("stars", 0), reverse=True)
    return {"success": True, "top_rated": sorted_by_rating[0], "summary": f"Top rated hotel in {city}: {sorted_by_rating[0]['name']}"}

def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    places = load_json_data("places.json")
    matches = [p for p in places if city.strip().lower() in p.get("city", "").lower() and p.get("rating", 0) >= min_rating and (not place_type or place_type.lower() in p.get("type", "").lower())]
    if not matches: return {"success": False, "message": f"No attractions found in {city}."}
    sorted_places = sorted(matches, key=lambda x: x.get("rating", 0), reverse=True)
    return {"success": True, "attractions": sorted_places[:5]}

def lookup_weather(city: str, start_date: str = None, end_date: str = None) -> dict:
    return {"success": True, "summary": f"Weather for {city} during {start_date} to {end_date} is generally pleasant.", "daily_forecast": []}

def estimate_budget(itinerary_summary: str) -> dict:
    """
    Accepts a descriptive summary of costs calculated by the agent.
    The agent should perform the math and pass the final summary here.
    """
    return {
        "success": True, 
        "summary": "Budget breakdown finalized.", 
        "details": itinerary_summary
    }
