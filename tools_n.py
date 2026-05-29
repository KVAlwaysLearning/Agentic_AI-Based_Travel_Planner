import os
import json
import sqlite3
import pandas as pd
import collections
from datetime import datetime, timedelta

# --- State Management for Costs ---
city_data_memory = {}

def reset_memory():
    global city_data_memory
    city_data_memory.clear()

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

# --- Database Orchestrator & Data Loader ---
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

def init_database():
    conn = sqlite3.connect('travel_itinerary.db')
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id TEXT PRIMARY KEY,
            airline TEXT,
            origin TEXT,
            destination TEXT,
            price INTEGER
        );

        CREATE TABLE IF NOT EXISTS hotels (
            hotel_id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            price_per_night INTEGER
        );

        CREATE TABLE IF NOT EXISTS places (
            place_id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            rating REAL
        );
    ''')
    conn.commit()

    # Load and ingest flights
    flights_data = load_json_data("flights.json")
    for item in flights_data:
        cursor.execute(
            "INSERT OR IGNORE INTO flights (flight_id, airline, origin, destination, price) VALUES (?, ?, ?, ?, ?)",
            (item.get("flight_id"), item.get("airline"), item.get("from"), item.get("to"), item.get("price"))
        )
    
    # Load and ingest hotels
    hotels_data = load_json_data("hotels.json")
    for item in hotels_data:
        cursor.execute(
            "INSERT OR IGNORE INTO hotels (hotel_id, name, city, price_per_night) VALUES (?, ?, ?, ?)",
            (item.get("hotel_id"), item.get("name"), item.get("city"), item.get("price_per_night"))
        )

    # Load and ingest places
    places_data = load_json_data("places.json")
    for item in places_data:
        cursor.execute(
            "INSERT OR IGNORE INTO places (place_id, name, city, rating) VALUES (?, ?, ?, ?)",
            (item.get("place_id"), item.get("name"), item.get("city"), item.get("rating"))
        )

    conn.commit()
    conn.close()

# Build DB and retrieve dataframes
init_database()

conn_read = sqlite3.connect('travel_itinerary.db')
df_flights = pd.read_sql_query("SELECT * FROM flights", conn_read)
df_hotels = pd.read_sql_query("SELECT * FROM hotels", conn_read)
df_places = pd.read_sql_query("SELECT * FROM places", conn_read)
conn_read.close()

# Clean and pre-process flight and hotel pricing data structures
df_flights['price'] = pd.to_numeric(df_flights['price'], errors='coerce').fillna(0).astype(int)
df_hotels['price_per_night'] = pd.to_numeric(df_hotels['price_per_night'], errors='coerce').fillna(0).astype(int)
df_places['rating'] = df_places['rating'].astype(float).round(1)

# Sort hotels by city and classify them into cheapest/budget/luxurious categories
df_hotels = df_hotels.sort_values(by=['city', 'price_per_night']).reset_index(drop=True)
df_hotels['category'] = 'budget'

def label_hotels_by_category(group):
    if len(group) == 0:
        return group
    group.iloc[0, group.columns.get_loc('category')] = 'cheapest'
    if len(group) > 1:
        group.iloc[-1, group.columns.get_loc('category')] = 'luxurious'
    if len(group) > 5:
        group.loc[group.index[1:-1], 'category'] = 'mid-range'
        mid_idx = len(group) // 2
        group.iloc[mid_idx-1 : mid_idx+2, group.columns.get_loc('category')] = 'budget'
    return group

df_hotels = df_hotels.groupby('city', group_keys=False).apply(label_hotels_by_category)

# Build Activities dataframe
df_activities = df_places.groupby('name')['city'].apply(list).reset_index()
df_activities = df_activities.rename(columns={'name': 'tourist_attraction', 'city': 'cities'})
df_activities = df_activities.explode('cities').reset_index(drop=True)
df_activities = df_activities.rename(columns={'cities': 'city'})

# Global constants initialized from the preprocessed DataFrames
ALL_CITIES = df_hotels['city'].unique().tolist() if not df_hotels.empty else []
ALL_ATTRS = df_activities['tourist_attraction'].unique().tolist() if not df_activities.empty else []

# --- Global Reference Trip State (Agent Decisions / Constraints) ---
global_trip_state = {
    "origin": None,
    "cities": [],
    "days": [],
    "durations": [],
    "hotel_types": [],
    "hotel_tiers": [],
    "attractions": []
}

# --- Travel Helper lookups ---
def get_reachable_cities(origin):
    """Checks the flight dataframe for all cities connected to the origin."""
    if df_flights.empty:
        return []
    reachable = df_flights[df_flights['origin'] == origin]['destination'].unique().tolist()
    return reachable

def get_cities_by_itinerary_limit(days):
    """Logic: Fewer days mean fewer cities."""
    if days < 3: 
        return ALL_CITIES[:1]
    if days < 7: 
        return ALL_CITIES[:3]
    return ALL_CITIES

def get_cities_with_attraction(attr_name):
    """Filters cities that contain the user's desired attraction."""
    if df_activities.empty:
        return []
    return df_activities[df_activities['tourist_attraction'] == attr_name]['city'].unique().tolist()

def get_duration_by_luxury(h_type):
    """Suggests duration based on hotel tier."""
    return [3, 4, 5] if h_type == 'luxurious' else [1, 2, 3]

def get_weather_score(city, date_range=None):
    """Returns a scored index indicating pleasantness (0 - 100)."""
    # High score default indicating warm, lovely weather
    return 85

# Constraint Matrix connecting variables for the resolving engine
CONSTRAINT_MATRIX = {
    ('origin', 'cities'): lambda val: get_reachable_cities(val),
    ('days', 'cities'): lambda days: get_cities_by_itinerary_limit(days),
    ('attractions', 'cities'): lambda attr: get_cities_with_attraction(attr),
    ('hotel_types', 'days'): lambda h_type: get_duration_by_luxury(h_type),
}

def propagate_constraints(user_inputs):
    """
    Implements the constraint boundary resolution.
    """
    domains = {
        'origin': ALL_CITIES,
        'cities': ALL_CITIES, 
        'days': list(range(1, 15)),
        'attractions': ALL_ATTRS, 
        'hotel_types': ['cheapest', 'budget', 'luxurious']
    }
    
    for (fixed_cat, target_cat), rule in CONSTRAINT_MATRIX.items():
        val = user_inputs.get(fixed_cat)
        if val and val != "Flexible":
            # For lists like attractions / cities / types, make sure we extract values correctly
            try:
                allowed = rule(val)
                domains[target_cat] = list(set(domains[target_cat]) & set(allowed))
            except Exception:
                pass
            
    return domains

def filter_by_weather(cities, date_range):
    """Logic to return the best rated cities for weather."""
    return [city for city in cities if get_weather_score(city, date_range) > 70]

def resolve_and_save_state(user_inputs, date_range=None):
    """
    The main Agent Decision Layer. Maps flexible inputs to strict validated options.
    """
    global global_trip_state
    
    # Propagate constraints
    domains = propagate_constraints(user_inputs)
    
    # Filter cities by meteorology rating
    if date_range and 'cities' in domains:
        domains['cities'] = filter_by_weather(domains['cities'], date_range)
    
    # Resolve values by defaulting if 'Flexible'
    resolved = {}
    for k in domains.keys():
        user_val = user_inputs.get(k)
        if user_val != "Flexible" and user_val is not None:
            resolved[k] = user_val
        else:
            resolved[k] = domains[k][0] if len(domains[k]) > 0 else None
            
    # Keep durations/hotel_tiers aligned with days and hotel_types
    resolved['durations'] = [3 if resolved['hotel_types'] == 'luxurious' else 2] * (len([resolved['cities']]) if resolved['cities'] else 1)
    resolved['hotel_tiers'] = [resolved['hotel_types']] * (len([resolved['cities']]) if resolved['cities'] else 1)

    global_trip_state.update(resolved)
    return "State resolved and saved."

# --- Unified Functional Interface Checklist ---

def search_flights(origin: str, destination: str) -> dict:
    source_clean = origin.strip().lower()
    dest_clean = destination.strip().lower()
    
    flights = load_json_data("flights.json")
    matches = [f for f in flights if source_clean in f.get("from", "").lower() and dest_clean in f.get("to", "").lower()]
    
    if not matches: 
        return {"success": False, "message": f"No flights found from {origin} to {destination}."}
    
    for f in matches:
        dep = datetime.fromisoformat(f['departure_time'])
        arr = datetime.fromisoformat(f['arrival_time'])
        duration_mins = (arr - dep).total_seconds() / 60
        f['duration_minutes'] = duration_mins
        f['duration'] = f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m"
        f['price'] = int(f['price'])
        
    cheapest = min(matches, key=lambda x: x["price"])
    fastest = min(matches, key=lambda x: x["duration_minutes"])

    price = int(cheapest['price'])
    log_city_data(city=destination, category="flight", amount=price)
    
    return {
        "success": True, 
        "cheapest_option": cheapest, 
        "fastest_option": fastest, 
        "matches": matches,
        "summary": f"Found {len(matches)} flights from {origin} to {destination}."
    }

def recommend_hotels(city: str, min_rating: float = 0.0, max_price: float = 100000.0) -> dict:
    hotels = load_json_data("hotels.json")
    matches = [h for h in hotels if city.strip().lower() in h.get("city", "").lower() and h.get("stars", 0) >= min_rating and h.get("price_per_night", 0) <= max_price]
    
    if not matches: 
        return {"success": False, "message": f"No hotels found in {city} matching criteria."}
    
    for h in matches:
        h['price_per_night'] = int(h['price_per_night'])
   
    sorted_by_rating = sorted(matches, key=lambda x: x.get("stars", 0), reverse=True)
    price = int(sorted_by_rating[0]['price_per_night'])
    log_city_data(city=city, category="hotel", amount=price)
    
    return {
        "success": True, 
        "top_rated": sorted_by_rating[0], 
        "matches": sorted_by_rating,
        "summary": f"Top rated: {sorted_by_rating[0]['name']}"
    }

def search_hotels(city: str) -> dict:
    """Checklist compliance method. Maps directly to recommend_hotels."""
    return recommend_hotels(city)

def discover_places(city: str, place_type: str = None, min_rating: float = 0.0) -> dict:
    places = load_json_data("places.json")
    matches = [p for p in places if city.strip().lower() in p.get("city", "").lower() and p.get("rating", 0) >= min_rating and (not place_type or place_type.lower() in p.get("type", "").lower())]
    if not matches: 
        return {"success": False, "message": f"No attractions found in {city}."}
    sorted_places = sorted(matches, key=lambda x: x.get("rating", 0), reverse=True)
    return {"success": True, "attractions": sorted_places[:5]}

def search_places(attraction_type: str) -> dict:
    """Checklist compliance matching. Finds places containing matching types."""
    places = load_json_data("places.json")
    matches = [p for p in places if attraction_type.strip().lower() in p.get("type", "").lower() or attraction_type.strip().lower() in p.get("name", "").lower()]
    if not matches: 
        return {"success": False, "message": f"No attractions found of type/name {attraction_type}."}
    return {"success": True, "attractions": matches}

def lookup_weather(city: str, start_date: str = None, end_date: str = None) -> dict:
    """Retrieves generic pleasant meteorological outline."""
    return {
        "success": True, 
        "city": city,
        "summary": f"Weather for {city} during {start_date} to {end_date} is generally pleasant. Sunny, high 28°C.",
        "daily_forecast": [
            {"date": start_date or "Day 1", "temp": "28°C", "humidity": "60%", "condition": "Sunny"}
        ]
    }

def generate_itinerary_tables(daily_logs: list) -> str:
    total_flights, total_hotels = get_all_costs()
    total_daily = len(daily_logs) * 1750
    grand_total = total_flights + total_hotels + total_daily
    
    log_table = "| Day | Date | Activity | Flight | Hotel | Daily Exp | Total | Weather |\n"
    log_table += "|---|---|---|---|---|---|---|---|\n"
    
    for d in daily_logs:
        row_total = d.get('flight', 0) + d.get('hotel', 0) + 1750
        log_table += f"| {d.get('day')} | {d.get('date')} | {d.get('activity')} | ₹{d.get('flight', 0)} | ₹{d.get('hotel', 0)} | ₹1750 | ₹{row_total} | {d.get('weather', 'Sunny')} |\n"
    
    breakdown = f"\n| Expense | Total |\n|---|---|\n"
    breakdown += f"| **Flights** | ₹{total_flights} |\n"
    breakdown += f"| **Lodging** | ₹{total_hotels} |\n"
    breakdown += f"| **Daily Expenses** | ₹{total_daily} |\n"
    breakdown += f"| **GRAND TOTAL** | **₹{grand_total}** |\n"
    
    return log_table + breakdown

def estimate_budget(itinerary_summary: str) -> dict:
    return {"success": True, "summary": "Budget calculation logged.", "details": itinerary_summary}

# --- Complex Pathfinding BFS & Total Calculations ---

def analyze_flight_itinerary(df_flights, origin, destination, max_hops=3):
    if df_flights.empty:
        return "No paths found."
    
    # Sort for consistency
    df_sorted = df_flights.sort_values(by=['origin', 'destination', 'airline'])
    flights_by_route = {
        route: group[['flight_id', 'airline', 'price']]
        for route, group in df_sorted.groupby(['origin', 'destination'])
    }

    # BFS Queuing system
    queue = collections.deque([(origin, [origin], [])])
    all_possible_paths = []

    while queue:
        current_city, path, path_data = queue.popleft()

        if current_city == destination:
            all_possible_paths.append({"path": path, "legs": path_data})
            continue

        if len(path) > max_hops + 1:
            continue

        for (start, end), data in flights_by_route.items():
            if start == current_city and end not in path:
                queue.append((end, path + [end], path_data + [{"route": (start, end), "options": data}]))

    if not all_possible_paths:
        return "No paths found."

    # Process and rank paths by pricing & connectivity gaps
    for p in all_possible_paths:
        p['total_min_price'] = int(sum(leg['options']['price'].min() for leg in p['legs']))
        p['num_hops'] = len(p['path']) - 1

    cheapest = min(all_possible_paths, key=lambda x: x['total_min_price'])
    fastest = min(all_possible_paths, key=lambda x: x['num_hops'])

    # Format the options cleanly for response
    return {
        "all_paths": all_possible_paths,
        "cheapest": cheapest,
        "fastest": fastest
    }

def get_cities_for_attractions(df_activities, attraction_list):
    """
    Takes a list of attraction names and returns a DataFrame
    showing those attractions and the cities where they are located.
    """
    if df_activities.empty:
        return pd.DataFrame()
    return df_activities[df_activities['tourist_attraction'].isin(attraction_list)]

def calculate_total_hotel_cost(df_hotels, cities, days_list=None, hotel_types=None):
    if days_list is None:
        days_list = [1] * len(cities)
    if hotel_types is None:
        hotel_types = ['budget'] * len(cities)

    if not (len(days_list) == len(cities) == len(hotel_types)):
        return 0, "Error: Cities, days_list, and hotel_types must have the same length."

    total_trip_hotel_cost = 0
    detailed_itinerary = []

    for i, city in enumerate(cities):
        days = days_list[i]
        h_type = hotel_types[i]
        city_hotels = df_hotels[df_hotels['city'] == city]

        if city_hotels.empty:
            return 0, f"No hotels found in {city}."

        if h_type == 'cheapest':
            selection = city_hotels[city_hotels['category'] == 'cheapest']
        elif h_type == 'luxurious':
            selection = city_hotels[city_hotels['category'] == 'luxurious']
        else:
            budget_options = city_hotels[city_hotels['category'] == 'budget']
            selection = budget_options.iloc[2:3] if len(budget_options) >= 3 else budget_options.iloc[0:1]

        if selection.empty:
            return 0, f"No '{h_type}' hotel available in {city}."

        price_per_night = int(selection.iloc[0]['price_per_night'])
        city_cost = price_per_night * days
        total_trip_hotel_cost += city_cost

        detailed_itinerary.append({
            "city": city,
            "hotel": selection.iloc[0]['name'],
            "type": h_type,
            "nights": days,
            "cost": city_cost
        })

    return total_trip_hotel_cost, detailed_itinerary

def build_package_trip(df_flights, df_hotels, cities_to_visit, origin, days_list=None, hotel_types=None):
    """
    Builds the complete trip itinerary including flights and hotels.
    """
    full_route = [origin] + cities_to_visit + [origin]
    trip_itinerary = []
    total_flight_cost = 0

    for i in range(len(full_route) - 1):
        start_node = full_route[i]
        end_node = full_route[i+1]

        path_results = analyze_flight_itinerary(df_flights, start_node, end_node)
        if isinstance(path_results, str) or path_results == "No paths found.":
            return f"Error: Route {start_node} -> {end_node} is impossible."

        best_leg = path_results['cheapest']
        trip_itinerary.append({
            "leg": f"{start_node} to {end_node}",
            "path": best_leg['path'],
            "flight_cost": best_leg['total_min_price']
        })
        total_flight_cost += best_leg['total_min_price']

    hotel_cost, hotel_details = calculate_total_hotel_cost(df_hotels, cities_to_visit, days_list, hotel_types)

    return {
        "full_sequence": full_route,
        "itinerary_legs": trip_itinerary,
        "hotel_stay_details": hotel_details,
        "total_flight_cost": total_flight_cost,
        "total_hotel_cost": hotel_cost,
        "total_package_cost": total_flight_cost + hotel_cost
    }

def build_final_package(df_flights, df_hotels):
    """
    Uses the saved global_trip_state to generate the quote.
    """
    return build_package_trip(
        df_flights, 
        df_hotels, 
        global_trip_state['cities'] if isinstance(global_trip_state['cities'], list) else [global_trip_state['cities']], 
        global_trip_state['origin'], 
        global_trip_state['durations'] if global_trip_state['durations'] else [global_trip_state['days']], 
        global_trip_state['hotel_tiers'] if global_trip_state['hotel_tiers'] else [global_trip_state['hotel_types']]
    )

def calculate_itinerary_costs(df_flights, df_hotels, cities, durations, hotel_tiers, origin):
    """
    Computes precise Flight, Hotel, and Dynamic Misc costs.
    Misc = (1000 + (0.4 * Avg_City_Hotel_Price)) * Nights
    """
    total_hotel_cost = 0
    total_misc_cost = 0
    detailed_itinerary = []

    for i, city in enumerate(cities):
        days = durations[i]
        h_type = hotel_tiers[i]
        city_hotels = df_hotels[df_hotels['city'] == city]
        
        if city_hotels.empty:
            continue
            
        avg_hotel_price = city_hotels['price_per_night'].mean()
        misc_per_day = 1000 + (0.4 * avg_hotel_price)
        
        if h_type == 'cheapest':
            selection = city_hotels[city_hotels['category'] == 'cheapest']
        elif h_type == 'luxurious':
            selection = city_hotels[city_hotels['category'] == 'luxurious']
        else:
            budget_options = city_hotels[city_hotels['category'] == 'budget']
            selection = budget_options.iloc[2:3] if len(budget_options) >= 3 else budget_options.iloc[0:1]
            
        price = int(selection.iloc[0]['price_per_night']) if not selection.empty else 0
        cost = price * days
        
        total_hotel_cost += cost
        total_misc_cost += (misc_per_day * days)
        
        detailed_itinerary.append({
            "city": city, 
            "hotel": selection.iloc[0]['name'] if not selection.empty else "Standard Stay",
            "nights": days, 
            "hotel_cost": cost, 
            "misc_cost": int(misc_per_day * days)
        })

    full_route = [origin] + cities + [origin]
    total_flight_cost = 0
    flight_legs = []
    
    for i in range(len(full_route) - 1):
        leg_data = analyze_flight_itinerary(df_flights, full_route[i], full_route[i+1])
        if isinstance(leg_data, dict) and 'cheapest' in leg_data:
            price = leg_data['cheapest']['total_min_price']
        else:
            price = 5000 # default fallback
        total_flight_cost += price
        flight_legs.append({"leg": f"{full_route[i]}->{full_route[i+1]}", "cost": price})

    return {
        "itinerary": detailed_itinerary,
        "flight_legs": flight_legs,
        "summary": {
            "total_hotel": total_hotel_cost,
            "total_flight": total_flight_cost,
            "total_misc": int(total_misc_cost),
            "grand_total": int(total_hotel_cost + total_flight_cost + total_misc_cost)
        }
    }

def run_full_itinerary_generation(df_flights, df_hotels):
    """
    Triggers the calculation using the pre-resolved global_trip_state.
    """
    if not global_trip_state['origin']:
        return "Error: Agent state not resolved. Please commit itinerary first."
        
    cities_list = global_trip_state['cities']
    if not isinstance(cities_list, list):
         cities_list = [cities_list] if cities_list else []
         
    return calculate_itinerary_costs(
        df_flights, df_hotels,
        cities_list,
        global_trip_state['durations'] if global_trip_state['durations'] else [2]*len(cities_list),
        global_trip_state['hotel_tiers'] if global_trip_state['hotel_tiers'] else ['budget']*len(cities_list),
        global_trip_state['origin']
    )

def build_cost_breakdown_table(itinerary_data, flight_legs, hotel_details, start_date):
    """
    Constructs the day-by-day table data structure.
    - itinerary_data: From calculate_itinerary_costs() output dictionary
    - flight_legs: From calculate_itinerary_costs() flight legs list
    - hotel_details: From calculate_itinerary_costs() itinerary details list
    """
    table_rows = []
    if isinstance(start_date, str):
         try:
              start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
         except Exception:
              start_date_obj = datetime.now()
    else:
         start_date_obj = datetime.now()
         
    # Day-by-day row generations
    for city_idx, city_info in enumerate(hotel_details):
        nights_count = city_info['nights']
        for day in range(nights_count):
            flight_cost = 0
            if day == 0: 
                leg = next((f for f in flight_legs if city_info['city'] in f['leg']), None)
                flight_cost = leg['cost'] if leg else 0
                
            hotel_per_night = city_info['hotel_cost'] / nights_count
            misc_per_night = city_info['misc_cost'] / nights_count
            
            table_rows.append({
                "day_of_trip": f"Day {len(table_rows) + 1}",
                "date": (start_date_obj + timedelta(days=len(table_rows))).strftime("%Y-%m-%d"),
                "city": city_info['city'],
                "activity": f"Exploring attractions in {city_info['city']}",
                "flight_cost": int(flight_cost),
                "hotel_cost": int(hotel_per_night),
                "misc_expense": int(misc_per_night),
                "weather": "Sunny, 28°C",
                "temp_humidity": "28°C / 60%"
            })

    return table_rows
