import json
import os
import requests
from datetime import datetime

# Path helper to make sure we find files relative to the script location if needed
def load_json_data(filename):
    paths_to_try = [
        filename,
        os.path.join(os.path.dirname(__file__), filename) if os.path.dirname(__file__) else filename
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    print(f"Warning: {filename} not found.")
    return []

def search_flights(source: str, destination: str) -> dict:
    """
    Search available flights from a source city to a destination city.
    """
    flights = load_json_data("flights.json")
    src = source.strip().lower()
    dest = destination.strip().lower()
    
    matches = []
    for f in flights:
        # Fixed: Using 'from' and 'to' keys
        if src in f.get("from", "").lower() and dest in f.get("to", "").lower():
            # Calculate duration on-the-fly
            dep = datetime.fromisoformat(f['departure_time'])
            arr = datetime.fromisoformat(f['arrival_time'])
            duration_mins = (arr - dep).total_seconds() / 60
            f['duration_minutes'] = duration_mins
            f['duration'] = f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m"
            matches.append(f)
            
    if not matches:
        return {"success": False, "message": f"No flights from {source} to {destination}."}
        
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])
    
    return {
        "success": True,
        "cheapest_option": cheapest,
        "fastest_option": fastest,
        "summary": f"Found {len(matches)} flights. Cheapest: {cheapest['airline']} (${cheapest['price']}). Fastest: {fastest['airline']} ({fastest['duration']})."
    }

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    """
    Search and recommend hotels in a given destination city.
    """
    hotels = load_json_data("hotels.json")
    target_city = city.strip().lower()
    
    matches = []
    for h in hotels:
        if target_city in h.get("city", "").lower():
            # Fixed: Using 'stars' instead of 'rating'
            stars = h.get("stars", 0)
            if stars >= min_rating and h.get("price_per_night", 0) <= max_price:
                matches.append(h)
                
    if not matches:
        return {"success": False, "message": f"No hotels found in {city}."}
        
    sorted_by_rating = sorted(matches, key=lambda x: x.get("stars", 0), reverse=True)
    sorted_by_price = sorted(matches, key=lambda x: x.get("price_per_night", 0))
    
    return {
        "success": True,
        "top_rated": sorted_by_rating[0],
        "best_value": sorted_by_price[0],
        "summary": f"Top rated: {sorted_by_rating[0]['name']} ({sorted_by_rating[0]['stars']} stars)."
    }

def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    """
    Search and discover attractions.
    """
    places = load_json_data("places.json")
    target_city = city.strip().lower()
    
    matches = []
    for p in places:
        if target_city in p.get("city", "").lower():
            if p.get("rating", 0) >= min_rating:
                if not place_type or place_type.lower() in p.get("type", "").lower():
                    matches.append(p)
                    
    if not matches:
        return {"success": False, "message": "No attractions found."}
        
    sorted_places = sorted(matches, key=lambda x: x.get("rating", 0), reverse=True)
    return {"success": True, "attractions": sorted_places[:5]}

# (lookup_weather and estimate_budget remain unchanged as they worked correctly)
