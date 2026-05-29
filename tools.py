import json
import os
from datetime import datetime

# --- State Management for Costs ---
city_data_memory = {}

def reset_memory():
    global city_data_memory
    city_data_memory = {}

def log_city_data(city: str, category: str, amount: int):
    """
    Saves the cost of a flight or hotel for a specific city.
    category must be 'flight' or 'hotel'.
    """
    global city_data_memory
    if city not in city_data_memory:
        city_data_memory[city] = {"flight": 0, "hotel": 0}
    city_data_memory[city][category] = int(amount)
    return f"Successfully logged {category} for {city}: ₹{amount}"

def get_all_costs():
    # Helper to return the total sums
    total_flights = sum(data.get("flight", 0) for data in city_data_memory.values())
    total_hotels = sum(data.get("hotel", 0) for data in city_data_memory.values())
    return total_flights, total_hotels


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
    
    if not matches: 
        return {"success": False, "message": f"No flights found from {source} to {destination}."}
    
    for f in matches:
        dep = datetime.fromisoformat(f['departure_time'])
        arr = datetime.fromisoformat(f['arrival_time'])
        duration_mins = (arr - dep).total_seconds() / 60
        f['duration_minutes'] = duration_mins
        f['duration'] = f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m"
        f['price'] = int(f['price'])  # FIX: Convert EVERY flight in the list
        
    
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])

    price = int(cheapest['price'])
    # FIX: Use the new function with the city name
    log_city_data(city=destination, category="flight", amount=price)
    
    return {
        "success": True, 
        "cheapest_option": cheapest, 
        "fastest_option": fastest, 
        "summary": f"Found {len(matches)} flights from {source} to {destination}."
    }

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    hotels = load_json_data("hotels.json")
    matches = [h for h in hotels if city.strip().lower() in h.get("city", "").lower() and h.get("stars", 0) >= min_rating and h.get("price_per_night", 0) <= max_price]
    
    if not matches: return {"success": False, "message": f"No hotels found in {city} matching criteria."}
    
    # FIX: Convert all prices to int before sorting
    for h in matches:
        h['price_per_night'] = int(h['price_per_night'])
    log_cost("hotels", price_per_night) # SAVED!    
    sorted_by_rating = sorted(matches, key=lambda x: x.get("stars", 0), reverse=True)

    price = int(h['price_per_night'])
    # FIX: Use the new function with the city name
    log_city_data(city=destination, category="flight", amount=price)
    
    return {"success": True, "top_rated": sorted_by_rating[0], "summary": f"Top rated: {sorted_by_rating[0]['name']}"}


def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    places = load_json_data("places.json")
    matches = [p for p in places if city.strip().lower() in p.get("city", "").lower() and p.get("rating", 0) >= min_rating and (not place_type or place_type.lower() in p.get("type", "").lower())]
    if not matches: return {"success": False, "message": f"No attractions found in {city}."}
    sorted_places = sorted(matches, key=lambda x: x.get("rating", 0), reverse=True)
    return {"success": True, "attractions": sorted_places[:5]}

def lookup_weather(city: str, start_date: str = None, end_date: str = None) -> dict:
    return {"success": True, "summary": f"Weather for {city} during {start_date} to {end_date} is generally pleasant.", "daily_forecast": []}

def generate_itinerary_tables(daily_data: list) -> str:
    """
    daily_data: list of dicts: 
    [{'day': 1, 'date': '2025-07-15', 'activity': '...', 'flight': 3304, 'hotel': 2828, 'min': 20, 'max': 30}, ...]
    """
    daily_expense = 1750
    rows = []
    
    # Calculate totals
    total_f = sum(cost_memory["flights"])
    total_h = sum(cost_memory["hotels"])
    total_d = len(daily_data) * 1750
    grand_total = total_f + total_h + total_d
    
    # Build Expense Log Table
    log_table = "| Day | Date | Activity | Flight | Hotel | Daily Exp | Total | Weather |\n"
    log_table += "|---|---|---|---|---|---|---|---|\n"
    
    for d in daily_data:
        day_total = d['flight'] + d['hotel'] + daily_expense
        log_table += f"| {d['day']} | {d['date']} | {d['activity']} | ₹{d['flight']} | ₹{d['hotel']} | ₹{daily_expense} | ₹{day_total} | {d['min']}/{d['max']} |\n"
    
    # Build Budget Breakdown Table
    breakdown_table = "\n| Expense | Total |\n|---|---|\n"
    breakdown_table += f"| **Flights** | ₹{total_f} |\n"
    breakdown_table += f"| **Lodging** | ₹{total_h} |\n"
    breakdown_table += f"| **Daily Expenses** | ₹{total_d} |\n"
    breakdown_table += f"| **GRAND TOTAL** | **₹{grand_total}** |\n"
    
    return log_table + breakdown_table

def estimate_budget(itinerary_summary: str) -> dict:
    """
    Accepts the final aggregated cost summary from the agent.
    """
    return {"success": True, "summary": "Budget calculation logged.", "details": itinerary_summary}
