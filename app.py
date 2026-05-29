import streamlit as st
import os
import agent
import tools
from datetime import datetime, date

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
