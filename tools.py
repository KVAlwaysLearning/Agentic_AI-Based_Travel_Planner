import json
import os
import requests
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
    matches = []
    for f in flights:
        if src in f.get("from", "").lower() and dest in f.get("to", "").lower():
            dep = datetime.fromisoformat(f['departure_time'])
            arr = datetime.fromisoformat(f['arrival_time'])
            duration_mins = (arr - dep).total_seconds() / 60
            f['duration_minutes'] = duration_mins
            f['duration'] = f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m"
            matches.append(f)
    if not matches: return {"success": False, "message": "No flights found."}
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])
    return {"success": True, "cheapest_option": cheapest, "fastest_option": fastest, "summary": f"Found {len(matches)} flights."}

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    hotels = load_json_data("hotels.json")
    matches = [h for h in hotels if city.strip().lower() in h.get("city", "").lower() and h.get("stars", 0) >= min_rating and h.get("price_per_night", 0) <= max_price]
    if not matches: return {"success": False, "message": "No hotels found."}
    sorted_by_rating = sorted(matches, key=lambda x: x.get("stars", 0), reverse=True)
    return {"success": True, "top_rated": sorted_by_rating[0], "summary": f"Top rated: {sorted_by_rating[0]['name']}"}

def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    places = load_json_data("places.json")
    matches = [p for p in places if city.strip().lower() in p.get("city", "").lower() and p.get("rating", 0) >= min_rating and (not place_type or place_type.lower() in p.get("type", "").lower())]
    if not matches: return {"success": False, "message": "No attractions found."}
    sorted_places = sorted(matches, key=lambda x: x.get("rating", 0), reverse=True)
    return {"success": True, "attractions": sorted_places[:5]}

def lookup_weather(city: str, start_date: str = None, end_date: str = None) -> dict:
    # Basic implementation
    return {"success": True, "summary": f"Weather for {city} is generally pleasant.", "daily_forecast": []}

def estimate_budget(flight_cost: float, hotel_price_per_night: float, daily_expense: float, num_days: int) -> dict:
    total = flight_cost + (hotel_price_per_night * num_days) + (daily_expense * num_days)
    return {"success": True, "total_budget": total, "summary": f"Estimated total budget: ${total}"}