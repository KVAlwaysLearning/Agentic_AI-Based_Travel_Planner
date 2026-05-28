import json
import os
import requests
from datetime import datetime

# Path helper to make sure we find files relative to the script location if needed
def load_json_data(filename):
    # Try current directory or parent directory
    paths_to_try = [
        filename,
        os.path.join(os.path.dirname(__file__), filename) if os.path.dirname(__file__) else filename
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    # Return empty list if not found
    print(f"Warning: {filename} not found.")
    return []

def search_flights(source: str, destination: str) -> dict:
    """
    Search available flights from a source city to a destination city.
    Suggests the cheapest flight, the fastest flight, and lists all matching flights.
    """
    flights = load_json_data("flights.json")
    
    # Clean inputs
    src = source.strip().lower()
    dest = destination.strip().lower()
    
    matches = []
    for f in flights:
        if src in f["source"].lower() and dest in f["destination"].lower():
            matches.append(f)
            
    if not matches:
        return {
            "success": False,
            "message": f"No flights found from '{source}' to '{destination}' in dataset."
        }
        
    # Find cheapest and fastest
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])
    
    return {
        "success": True,
        "all_options": matches,
        "cheapest_option": cheapest,
        "fastest_option": fastest,
        "summary": f"Found {len(matches)} flights from {source} to {destination}. "
                   f"Cheapest is {cheapest['airline']} for ${cheapest['price']} ({cheapest['duration']}). "
                   f"Fastest is {fastest['airline']} taking {fastest['duration']} (${fastest['price']})."
    }

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    """
    Search and recommend hotels in a given destination city.
    Allows filtering by minimum rating (e.g., 4.0) and maximum budget per night.
    """
    hotels = load_json_data("hotels.json")
    
    target_city = city.strip().lower()
    
    matches = []
    for h in hotels:
        if target_city in h["city"].lower():
            # Apply filters
            if h["rating"] >= min_rating and h["price_per_night"] <= max_price:
                matches.append(h)
                
    if not matches:
        return {
            "success": False,
            "message": f"No hotels found in '{city}' matching filters (min_rating: {min_rating}, max_price: ${max_price})."
        }
        
    # Sort matches by rating (descending) and price (ascending) as suggestions
    sorted_by_rating = sorted(matches, key=lambda x: x["rating"], reverse=True)
    sorted_by_price = sorted(matches, key=lambda x: x["price_per_night"])
    
    return {
        "success": True,
        "all_options": matches,
        "top_rated": sorted_by_rating[0] if sorted_by_rating else None,
        "best_value": sorted_by_price[0] if sorted_by_price else None,
        "summary": f"Found {len(matches)} hotels in {city}. "
                   f"Top rated is {sorted_by_rating[0]['name']} at ${sorted_by_rating[0]['price_per_night']}/night (Rating: {sorted_by_rating[0]['rating']}). "
                   f"Best value is {sorted_by_price[0]['name']} at ${sorted_by_price[0]['price_per_night']}/night (Rating: {sorted_by_price[0]['rating']})."
    }

def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    """
    Search and discover attractions, museums, parks, or sights in a given city.
    Filters by place_type (e.g. 'Museum', 'Park', 'Sightseeing') or minimum rating.
    """
    places = load_json_data("places.json")
    
    target_city = city.strip().lower()
    target_type = place_type.strip().lower() if place_type else None
    
    matches = []
    for p in places:
        if target_city in p["city"].lower():
            # Apply filters
            if p["rating"] >= min_rating:
                if not target_type or target_type in p["type"].lower():
                    matches.append(p)
                    
    if not matches:
        return {
            "success": False,
            "message": f"No attractions found in '{city}' matching filters (type: {place_type}, min_rating: {min_rating})."
        }
        
    # Sort by rating descending
    sorted_places = sorted(matches, key=lambda x: x["rating"], reverse=True)
    
    return {
        "success": True,
        "attractions": sorted_places,
        "summary": f"Found {len(sorted_places)} attractions in {city} matching type {place_type or 'any'}."
    }

def lookup_weather(city: str, start_date: str = None, end_date: str = None) -> dict:
    """
    Lookup weather forecast or historical averages for a destination city.
    Uses public Open-Meteo API. start_date and end_date should be in YYYY-MM-DD format.
    """
    # Quick fallback coordinates map
    fallbacks = {
        "new york": (40.7128, -74.0060),
        "paris": (48.8566, 2.3522),
        "tokyo": (35.6762, 139.6503),
        "london": (51.5074, -0.1278),
        "rome": (41.9028, 12.4964),
    }
    
    cleaned_city = city.strip().lower()
    lat, lon = None, None
    
    # 1. Geocoding search from Open-Meteo
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        if geo_res.status_code == 200:
            data = geo_res.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]
                city = result.get("name", city) # update to formal name if found
    except Exception as e:
        print(f"Geocoding API failed: {e}")
        
    # 2. Fall back to hardcoded coordinates if geocoding failed
    if lat is None or lon is None:
        for name, coords in fallbacks.items():
            if name in cleaned_city:
                lat, lon = coords
                break
                
    if lat is None or lon is None:
        # Defaults to Paris coordinates if completely unknown
        lat, lon = 48.8566, 2.3522
        print(f"Unknown city location '{city}'. Defaulting to Paris coordinates (48.8566, 2.3522).")
        
    # 3. Call Open-Meteo Weather Forecast API
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum&"
            f"timezone=auto"
        )
        weather_res = requests.get(weather_url, timeout=5)
        if weather_res.status_code == 200:
            w_data = weather_res.json()
            daily = w_data.get("daily", {})
            
            # Formulate the response dates & forecasts
            times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            codes = daily.get("weathercode", [])
            precips = daily.get("precipitation_sum", [])
            
            # Weather code translator helper
            code_meanings = {
                0: "Clear Sky",
                1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing Rime Fog",
                51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
                61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
                71: "Slight Snowfall", 73: "Moderate Snowfall", 75: "Heavy Snowfall",
                77: "Snow Grains",
                80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
                85: "Slight Snow Showers", 86: "Heavy Snow Showers",
                95: "Slight Thunderstorm", 96: "Thunderstorm with Hail", 99: "Heavy Thunderstorm"
            }
            
            forecast_list = []
            for i in range(len(times)):
                code = codes[i] if i < len(codes) else 0
                condition = code_meanings.get(code, "Clear / Breezy")
                
                forecast_list.append({
                    "date": times[i],
                    "max_temp_c": max_temps[i] if i < len(max_temps) else 25.0,
                    "min_temp_c": min_temps[i] if i < len(min_temps) else 15.0,
                    "condition": condition,
                    "precipitation_mm": precips[i] if i < len(precips) else 0.0
                })
                
            # Filter by travel dates if provided
            filtered_forecast = forecast_list
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    filtered_forecast = []
                    for day in forecast_list:
                        day_dt = datetime.strptime(day["date"], "%Y-%m-%d").date()
                        if start_dt <= day_dt <= end_dt:
                            filtered_forecast.append(day)
                except Exception as ex:
                    print(f"Date filtering error: {ex}. Returning full 7-day forecast.")
            
            # Take up to 7 days if no dates or filtering was too wide
            if not filtered_forecast:
                filtered_forecast = forecast_list[:7]
            else:
                filtered_forecast = filtered_forecast[:7] # limit to 7 days forecast
                
            return {
                "success": True,
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "timezone": w_data.get("timezone", "UTC"),
                "daily_forecast": filtered_forecast,
                "summary": f"Weather for {city}: Max temperatures are around "
                           f"{round(sum([d['max_temp_c'] for d in filtered_forecast])/len(filtered_forecast), 1)}°C. "
                           f"Primary conditions: {', '.join(set([d['condition'] for d in filtered_forecast]))}."
            }
    except Exception as e:
        print(f"Weather lookup error: {e}")
        
    # Return placeholder if call fails
    return {
        "success": False,
        "message": f"Could not gather real-time forecast for {city}. Returning average seasonal forecast.",
        "daily_forecast": [
            {"date": start_date or "Day 1", "max_temp_c": 22.0, "min_temp_c": 14.0, "condition": "Partly Cloudy", "precipitation_mm": 0.0},
            {"date": "Day 2", "max_temp_c": 23.0, "min_temp_c": 15.0, "condition": "Clear Sky", "precipitation_mm": 0.0},
            {"date": "Day 3", "max_temp_c": 21.0, "min_temp_c": 13.0, "condition": "Slight Rain Showers", "precipitation_mm": 1.2}
        ]
    }

def estimate_budget(flight_cost: float, hotel_price_per_night: float, daily_expense: float, num_days: int) -> dict:
    """
    Calculate and break down the estimated travel budget.
    """
    total_hotel_cost = hotel_price_per_night * num_days
    total_local_cost = daily_expense * num_days
    total_grand = flight_cost + total_hotel_cost + total_local_cost
    
    return {
        "success": True,
        "breakdown": {
            "flight_cost": flight_cost,
            "hotel_cost_per_night": hotel_price_per_night,
            "total_hotel_cost": total_hotel_cost,
            "daily_local_expense": daily_expense,
            "total_local_expenses": total_local_cost,
            "duration_days": num_days
        },
        "total_budget": total_grand,
        "summary": f"Your total estimated budget for a {num_days}-day trip is ${total_grand:,.2f}. "
                   f"This includes ${flight_cost:,.2f} for flights, "
                   f"${total_hotel_cost:,.2f} for hotel lodging (${hotel_price_per_night}/night), "
                   f"and ${total_local_cost:,.2f} for local daily meals, travel and shopping (${daily_expense}/day)."
    }
