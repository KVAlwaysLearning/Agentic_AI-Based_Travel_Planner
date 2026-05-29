import sqlite3
import json
import pandas as pd
import collections
from datetime import datetime, timedelta

# --- 1. Global State & Data Loading ---
global_trip_state = {
    "origin": None, "cities": [], "durations": [], "hotel_tiers": [], "attractions": []
}

def initialize_database():
    conn = sqlite3.connect('travel_itinerary.db')
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS flights (flight_id TEXT PRIMARY KEY, airline TEXT, origin TEXT, destination TEXT, price INTEGER);
        CREATE TABLE IF NOT EXISTS hotels (hotel_id TEXT PRIMARY KEY, name TEXT, city TEXT, price_per_night INTEGER);
        CREATE TABLE IF NOT EXISTS places (place_id TEXT PRIMARY KEY, name TEXT, city TEXT, rating REAL);
    ''')
    conn.commit()
    return conn

# --- 2. Data Processing & Constraint Engine ---
def prepare_data(conn):
    df_flights = pd.read_sql_query("SELECT * FROM flights", conn)
    df_hotels = pd.read_sql_query("SELECT * FROM hotels", conn)
    df_places = pd.read_sql_query("SELECT * FROM places", conn)
    
    df_flights['price'] = pd.to_numeric(df_flights['price'], errors='coerce').fillna(0).astype(int)
    df_hotels['price_per_night'] = pd.to_numeric(df_hotels['price_per_night'], errors='coerce').fillna(0).astype(int)
    df_hotels = df_hotels.sort_values(by=['city', 'price_per_night']).reset_index(drop=True)
    df_hotels['category'] = 'budget'
    
    def label_hotels(group):
        group.iloc[0, group.columns.get_loc('category')] = 'cheapest'
        if len(group) > 1: group.iloc[-1, group.columns.get_loc('category')] = 'luxurious'
        if len(group) > 5:
            group.loc[group.index[1:-1], 'category'] = 'mid-range'
            mid = len(group) // 2
            group.iloc[mid-1 : mid+2, group.columns.get_loc('category')] = 'budget'
        return group
    df_hotels = df_hotels.groupby('city', group_keys=False).apply(label_hotels)
    return df_flights, df_hotels, df_places

# --- 3. Core Logic Functions ---
def analyze_flight_itinerary(df_flights, origin, destination, max_hops=3):
    df_sorted = df_flights.sort_values(by=['origin', 'destination', 'airline'])
    flights_by_route = {r: g[['flight_id', 'airline', 'price']] for r, g in df_sorted.groupby(['origin', 'destination'])}
    queue = collections.deque([(origin, [origin], [])])
    all_possible = []
    while queue:
        curr, path, p_data = queue.popleft()
        if curr == destination:
            all_possible.append({"path": path, "legs": p_data})
            continue
        if len(path) > max_hops + 1: continue
        for (start, end), data in flights_by_route.items():
            if start == curr and end not in path:
                queue.append((end, path + [end], p_data + [{"route": (start, end), "options": data}]))
    
    if not all_possible: return "No paths found."
    for p in all_possible:
        p['total_min_price'] = sum(leg['options']['price'].min() for leg in p['legs'])
        p['num_hops'] = len(p['path']) - 1
    return {"cheapest": min(all_possible, key=lambda x: x['total_min_price'])}

def calculate_itinerary_costs(df_flights, df_hotels, cities, durations, hotel_tiers, origin):
    total_hotel_cost, total_misc_cost, detailed_itinerary = 0, 0, []
    for i, city in enumerate(cities):
        h_type = hotel_tiers[i]
        city_hotels = df_hotels[df_hotels['city'] == city]
        avg_h = city_hotels['price_per_night'].mean()
        misc_per_day = 1000 + (0.4 * avg_h)
        
        # Selection logic
        if h_type == 'cheapest': sel = city_hotels[city_hotels['category'] == 'cheapest']
        elif h_type == 'luxurious': sel = city_hotels[city_hotels['category'] == 'luxurious']
        else: sel = city_hotels[city_hotels['category'] == 'budget']
        
        price = sel.iloc[0]['price_per_night']
        total_hotel_cost += (price * durations[i])
        total_misc_cost += (misc_per_day * durations[i])
        detailed_itinerary.append({"city": city, "hotel": sel.iloc[0]['name'], "nights": durations[i], "hotel_cost": price*durations[i], "misc_cost": misc_per_day * durations[i]})
    
    # Flight Cost Logic
    full_route = [origin] + cities + [origin]
    total_f, f_legs = 0, []
    for i in range(len(full_route) - 1):
        cost = analyze_flight_itinerary(df_flights, full_route[i], full_route[i+1])['cheapest']['total_min_price']
        total_f += cost
        f_legs.append({"leg": f"{full_route[i]}->{full_route[i+1]}", "cost": cost})
        
    return {"itinerary": detailed_itinerary, "flight_legs": f_legs, "summary": {"total_hotel": total_hotel_cost, "total_flight": total_f, "total_misc": total_misc_cost, "grand_total": total_hotel_cost + total_f + total_misc_cost}}

def build_cost_breakdown_table(itinerary_data, flight_legs, hotel_details, start_date):
    table_rows = []
    for city_info in hotel_details:
        for day in range(city_info['nights']):
            flight_cost = next((f['cost'] for f in flight_legs if city_info['city'] in f['leg']), 0) if day == 0 else 0
            table_rows.append({
                "day_of_trip": f"Day {len(table_rows) + 1}",
                "date": start_date + timedelta(days=len(table_rows)),
                "city": city_info['city'],
                "flight_cost": flight_cost,
                "hotel_cost": city_info['hotel_cost'] / city_info['nights'],
                "misc_expense": city_info['misc_cost'] / city_info['nights']
            })
    return table_rows
