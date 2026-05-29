import streamlit as st
import os
import agent
import tools
from datetime import datetime, date, timedelta

# Set Streamlit Page Config
st.set_page_config(page_title="Indica Odyssey Planner", layout="wide")
st.title("🧳 Indica Odyssey Planner v3.0")

# Clear State Memory Sidebar controller
with st.sidebar:
    st.header("⚙️ State Engine status")
    if st.button("🔄 Clear State Memory", type="secondary"):
        tools.reset_memory()
        st.success("State memory cleared!")
    
    st.info(f"Stored cost logs count: {len(tools.city_data_memory)} records")

# Primary Tab Navigation 
tab1, tab2 = st.tabs(["💬 AI Prompt Planner", "🎛️ Constraint Control Panel (Form Inputs)"])

# Define actual master lists from database
available_cities = ["Delhi", "Mumbai", "Hyderabad", "Bangalore", "Chennai", "Goa", "Kolkata", "Jaipur"]
available_attractions = ["lake", "temple", "museum", "park", "fort", "beach", "market", "monument"]

# Helper to extract origin and dest cities from prompt for custom solved table
def extract_trip_details_from_prompt(prompt, logged_cities=None):
    prompt_lower = prompt.lower()
    cities_in_prompt = []
    for c in available_cities:
        idx = prompt_lower.find(c.lower())
        if idx != -1:
            cities_in_prompt.append((idx, c))
    # Sort by appearance in the prompt
    cities_in_prompt.sort(key=lambda x: x[0])
    
    if not cities_in_prompt:
        return "Hyderabad", ["Delhi", "Mumbai"]
        
    # Determine origin
    origin = None
    origin_words = ["from", "starting in", "starting at", "originating in", "departure", "out of"]
    
    for idx, c in cities_in_prompt:
        # Get context preceding this city
        start_idx = max(0, idx - 15)
        context = prompt_lower[start_idx:idx]
        if any(ow in context for ow in origin_words):
            origin = c
            break
            
    # Fallback for origin if no "from" matched
    if not origin:
        if any(c == "Hyderabad" for _, c in cities_in_prompt):
            origin = "Hyderabad"
        else:
            origin = cities_in_prompt[0][1]
            
    # Destinations are all other mentioned cities in they order they were mentioned
    dest_cities = [c for _, c in cities_in_prompt if c != origin]
    
    # Fallback destinations if empty
    if not dest_cities:
        dest_cities = ["Delhi", "Mumbai"] if origin != "Delhi" else ["Mumbai"]
        
    return origin, dest_cities

with tab1:
    st.subheader("🖊️ AI Freeform Prompt Planner")
    st.markdown("Let our Indica Specialist AI Agent plan your trip dynamically based on raw requirements!")
    
    user_query = st.text_area(
        "Where do you want to go? Include dates, cities, and budget.",
        placeholder="Example: I want a 5-day trip starting from Delhi. Visit Bangalore and Goa. Use budget hotels.",
        height=120,
        key="prompt_input"
    )

    button_clicked = st.button("🚀 Compose Travel Plan with Agent", type="primary")

    if button_clicked:
        if not user_query.strip():
            st.warning("Please type a planning query first!")
        else:
            st.subheader("🕵️‍♂️ Agent Reasoning Traces")
            trace_area = st.empty()
            log_messages = []

            def streamlit_logger(log_type, message, metadata):
                icon = "⚙️" if log_type == "tool_call_start" else "✅"
                log_messages.append(f"{icon} {message}")
                trace_area.markdown("\n\n".join(log_messages))
            
            with st.spinner("Agent is planning your multi-city trip..."):
                result = agent.run_travel_agent(user_query, callback_log=streamlit_logger)
                
            if result.get("success"):
                st.success("✨ Travel Plan generated successfully!")
                st.markdown(result["itinerary"])
                
                # Render the Solved tables
                if tools.latest_agent_itinerary:
                    st.markdown("---")
                    
                    # Estimate the cities visited and origin to recalculate exact legs
                    logged_cities = list(tools.city_data_memory.keys())
                    origin, dest_cities = extract_trip_details_from_prompt(user_query, logged_cities)
                    
                    # Get exact flight segments and costs
                    durations = []
                    hotel_tiers = []
                    # Guess durations and hotel types from logged data if available or default/from prompt
                    hotel_tier_guess = "budget"
                    if "cheap" in user_query.lower():
                        hotel_tier_guess = "cheapest"
                    elif "luxur" in user_query.lower():
                        hotel_tier_guess = "luxurious"
                        
                    for city_name in dest_cities:
                        days_count = sum(1 for d in tools.latest_agent_itinerary if city_name.lower() in d.get("activity", "").lower() or city_name.lower() in d.get("city", "").lower())
                        durations.append(max(1, days_count))
                        hotel_tiers.append(hotel_tier_guess)
                        
                    costs_data = tools.calculate_itinerary_costs(
                        tools.df_flights, tools.df_hotels,
                        dest_cities, durations, hotel_tiers, origin
                    )
                    
                    summary = costs_data.get("summary", {})
                    
                    st.subheader("📊 Solved Package Cost Summary")
                    # Use bento visual grids
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("Flight Expense Log", f"₹{summary.get('total_flight', 0):,}")
                    sc2.metric("Hotels & Lodging", f"₹{summary.get('total_hotel', 0):,}")
                    sc3.metric("Daily Buffer Expense", f"₹{summary.get('total_misc', 0):,}")
                    sc4.metric("Grand Total Cost", f"₹{summary.get('grand_total', 0):,}")
                    
                    st.subheader("📅 Solved Day-by-Day Comprehensive Cost Schedule")
                    
                    # Match day-by-day table rows to flight legs & hotels
                    flight_legs = costs_data.get("flight_legs", [])
                    hotel_details = costs_data.get("itinerary", [])
                    
                    rows = tools.build_cost_breakdown_table(
                        costs_data.get("itinerary", []),
                        costs_data.get("flight_legs", []),
                        costs_data.get("itinerary", []),
                        datetime.now().strftime("%Y-%m-%d")
                    )
                    
                    # Display the day-by-day table
                    st.table(rows)
                    
                    # Print warning if there are no direct flights
                    no_direct_warnings = []
                    for leg in flight_legs:
                        if not leg.get("is_direct", True):
                            start_c, end_c = leg["leg"].split("->")
                            no_direct_warnings.append(f"⚠️ Note: There are no direct flights between {start_c} and {end_c}. Showing connecting flight route.")
                    
                    for warn in no_direct_warnings:
                        st.warning(warn)
                        
                    # Flight Summary Table listing flight no, airline, from, to, cost
                    st.subheader("✈️ Selected Flights Summary Table")
                    flight_rows = []
                    for leg in flight_legs:
                        for segment in leg.get("segments", []):
                            flight_rows.append({
                                "Flight No": segment.get("flight_id"),
                                "Airline": segment.get("airline"),
                                "From": segment.get("from"),
                                "To": segment.get("to"),
                                "Cost": f"₹{segment.get('price'):,}"
                            })
                    if flight_rows:
                        st.table(flight_rows)
                    else:
                        st.info("No flight segment details available.")
                        
                    # Decision logic reasons
                    st.subheader("💡 Selection Intelligence & Decision Logic")
                    st.markdown("""
                    - **Flight Routing Selection**: 
                      - Cheaper and direct flight paths were prioritized.
                      - If direct flights do not exist, a custom BFS (Breadth-First Search) routing algorithm traversed alternative paths (e.g., through Kolkata) to resolve the absolute cheapest segment-by-segment chain of connections seamlessly.
                    - **Hotel Selection**: 
                      - Hotels of the requested class (e.g. Budget, Cheapest, or Luxury) with the highest verified rating scores (stars) were picked.
                    """)
            else:
                st.error("Failed to compile itinerary.")
                st.text(result.get("itinerary"))

with tab2:
    st.subheader("🎯 Flexible Constraint Selection Form")
    st.markdown("Customize precise input limits. Choose **Flexible** for any parameters you aren't certain on to auto-solve optimal allocations.")

    col1, col2 = st.columns(2)

    with col1:
        origin_input = st.selectbox(
            "1. Journey Origin City",
            options=["Flexible"] + available_cities,
            index=1 # Delhi default
        )
        
        dest_cities = st.multiselect(
            "2. Dest/Intermediate Cities to Visit (Multiple Select)",
            options=["Flexible"] + available_cities,
            default=["Mumbai"]
        )

        hotel_category = st.selectbox(
            "3. Lodging Luxury Class Budget",
            options=["Flexible", "cheapest", "budget", "luxurious"],
            index=2 # budget default
        )

    with col2:
        attraction_interest = st.selectbox(
            "4. Tourist Attraction Interest Type",
            options=["Flexible"] + available_attractions,
            index=0 # Flexible default
        )

        trip_days = st.selectbox(
            "5. Number of Days Duration limit",
            options=["Flexible"] + list(range(1, 15)),
            index=5 # 5 days standard default
        )

        date_range_selection = st.date_input(
            "6. Select Target Travel Departure Date Range (Calendar)",
            value=[date(2026, 6, 1), date(2026, 6, 6)]
        )

    st.markdown("---")
    
    if st.button("⛓️ Map Constraints & Build Structured Itinerary", type="primary"):
        start_date_str = "2026-06-01"
        formatted_dates = "2026-06-01 to 2026-06-06"
        
        if isinstance(date_range_selection, (list, tuple)) and len(date_range_selection) == 2:
            formatted_dates = " to ".join([d.strftime("%Y-%m-%d") for d in date_range_selection])
            start_date_str = date_range_selection[0].strftime("%Y-%m-%d")
        elif isinstance(date_range_selection, date):
            start_date_str = date_range_selection.strftime("%Y-%m-%d")
            formatted_dates = start_date_str
            
        # Build user inputs payload structured like resolve_and_save_state expected
        payload = {
            "origin": origin_input,
            "cities": dest_cities if len(dest_cities) > 0 else "Flexible",
            "days": trip_days,
            "hotel_types": hotel_category,
            "attractions": [attraction_interest] if attraction_interest != "Flexible" else []
        }
        
        with st.spinner("Resolving constraint domains & propagating matrices..."):
            status_msg = tools.resolve_and_save_state(payload, date_range=formatted_dates)
            st.toast(f"⚡ Constraints updated in state database: {status_msg}")
            
            # Now run full packaging itinerary matching tools.py logic
            res_itinerary = tools.run_full_itinerary_generation(tools.df_flights, tools.df_hotels)
            
            if isinstance(res_itinerary, str) or ("error" in res_itinerary and res_itinerary["error"]):
                st.error("Routing resolution error: " + (res_itinerary if isinstance(res_itinerary, str) else res_itinerary.get("message", "Impossible route mapping.")))
            else:
                st.success("✅ Itinerary calculations completed successfully!")
                
                # Fetch resolved state variables
                resolved_origin = tools.global_trip_state.get('origin', origin_input)
                resolved_cities = tools.global_trip_state.get('cities', dest_cities)
                resolved_category = tools.global_trip_state.get('hotel_types', hotel_category)
                
                # Display the complete beautiful plan details matching AI layout
                itinerary_md = tools.build_itinerary_markdown_report_from_state(
                    res_itinerary, resolved_origin, resolved_cities, formatted_dates, resolved_category
                )
                st.markdown(itinerary_md)
                
                st.markdown("---")
                
                # Display Summary Report
                summary = res_itinerary.get("summary", {})
                
                # Use bento visual grids
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Flight Expense Log", f"₹{summary.get('total_flight', 0):,}")
                sc2.metric("Hotels & Lodging", f"₹{summary.get('total_hotel', 0):,}")
                sc3.metric("Daily Buffer Expense", f"₹{summary.get('total_misc', 0):,}")
                sc4.metric("Grand Total Cost", f"₹{summary.get('grand_total', 0):,}")
                
                # Show itinerary tabular output
                st.subheader("📅 Solved Day-by-Day Comprehensive Cost Schedule")
                
                rows = tools.build_cost_breakdown_table(
                    res_itinerary.get("itinerary", []),
                    res_itinerary.get("flight_legs", []),
                    res_itinerary.get("itinerary", []), # hotel_details same as itinerary structure in tools.py
                    start_date_str
                )
                
                # Render beautifully as a table
                st.table(rows)
                
                # Print warning if there are no direct flights
                no_direct_warnings = []
                flight_legs = res_itinerary.get("flight_legs", [])
                for leg in flight_legs:
                    if not leg.get("is_direct", True):
                        start_c, end_c = leg["leg"].split("->")
                        no_direct_warnings.append(f"⚠️ Note: There are no direct flights between {start_c} and {end_c}. Showing connecting flight route.")
                
                for warn in no_direct_warnings:
                    st.warning(warn)
                    
                # Flight Summary Table listing flight no, airline, from, to, cost
                st.subheader("✈️ Selected Flights Summary Table")
                flight_rows = []
                for leg in flight_legs:
                    for segment in leg.get("segments", []):
                        flight_rows.append({
                            "Flight No": segment.get("flight_id"),
                            "Airline": segment.get("airline"),
                            "From": segment.get("from"),
                            "To": segment.get("to"),
                            "Cost": f"₹{segment.get('price'):,}"
                        })
                if flight_rows:
                    st.table(flight_rows)
                else:
                    st.info("No flight segment details available.")
                    
                # Decision logic reasons
                st.subheader("💡 Selection Intelligence & Decision Logic")
                st.markdown("""
                - **Flight Routing Selection**: 
                  - Cheaper and direct flight paths were prioritized.
                  - If direct flights do not exist, a custom BFS (Breadth-First Search) routing algorithm traversed alternative paths (e.g., through Kolkata) to resolve the absolute cheapest segment-by-segment chain of connections seamlessly.
                - **Hotel Selection**: 
                  - Hotels of the requested class (e.g. Budget, Cheapest, or Luxury) with the highest verified rating scores (stars) were picked.
                """)
