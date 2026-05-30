import streamlit as st
import os
import agent
import tools
from datetime import datetime, date, timedelta

# --- Page Setup ---
st.set_page_config(page_title="Indica Odyssey Planner", layout="wide")

# Custom CSS for the "Modern/Clean" look from your screenshots
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    .stApp { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/map-marker.png", width=60) # Placeholder logo
    st.title("Odyssey Engine")
    st.header("⚙️ State Engine")
    if st.button("🔄 Clear State Memory", type="primary"):
        tools.reset_memory()
        st.success("State memory cleared!")
    
    st.metric("Records in Memory", len(tools.city_data_memory))
    st.info("Version 3.0 | Indica Specialist AI")

# --- Main Title ---
st.title("🧳 Indica Odyssey Planner v3.0")
st.markdown("---")

# --- Tabs ---
tab1, tab2 = st.tabs(["💬 AI Prompt Planner", "🎛️ Constraint Control Panel"])

# --- Logic Definitions ---
available_cities = ["Delhi", "Mumbai", "Hyderabad", "Bangalore", "Chennai", "Goa", "Kolkata", "Jaipur"]

with tab1:
    st.subheader("🖊️ AI Freeform Prompt Planner")
    user_query = st.text_area(
        "Describe your dream trip:",
        placeholder="Example: I want a 5-day trip starting from Delhi. Visit Bangalore and Goa. Use budget hotels.",
        height=150,
        key="prompt_input"
    )
    
    start_date = st.date_input("Start Date", date.today())
    
    if st.button("🚀 Generate Optimized Itinerary"):
        if not user_query:
            st.warning("Please enter a trip prompt.")
        else:
            with st.spinner("Agent is reasoning..."):
                res_itinerary = agent.run_agent(user_query)
                
                if isinstance(res_itinerary, str) or ("error" in res_itinerary and res_itinerary["error"]):
                    st.error("Routing error: " + (res_itinerary if isinstance(res_itinerary, str) else "Impossible route."))
                else:
                    st.success("✅ Itinerary calculations completed!")
                    
                    # Summary Metrics (Bento Style)
                    summary = res_itinerary.get("summary", {})
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Flights", f"₹{summary.get('total_flight', 0):,}")
                    c2.metric("Hotels", f"₹{summary.get('total_hotel', 0):,}")
                    c3.metric("Misc", f"₹{summary.get('total_misc', 0):,}")
                    c4.metric("Grand Total", f"₹{summary.get('grand_total', 0):,}")
                    
                    # Table Output
                    st.subheader("📅 Comprehensive Schedule")
                    rows = tools.build_cost_breakdown_table(
                        res_itinerary.get("itinerary", []),
                        res_itinerary.get("flight_legs", []),
                        res_itinerary.get("itinerary", []),
                        start_date.strftime("%Y-%m-%d")
                    )
                    st.table(rows)
                    
                    # Flight Details Section
                    flight_legs = res_itinerary.get("flight_legs", [])
                    if flight_legs:
                        st.subheader("✈️ Flight Segment Details")
                        flight_rows = []
                        for leg in flight_legs:
                            for segment in leg.get("segments", []):
                                flight_rows.append({
                                    "Flight": segment.get("flight_id"),
                                    "Airline": segment.get("airline"),
                                    "From": segment.get("from"),
                                    "To": segment.get("to"),
                                    "Cost": f"₹{segment.get('price'):,}"
                                })
                        st.table(flight_rows)

                    # Decision Logic
                    with st.expander("💡 Selection Intelligence & Decision Logic"):
                        st.markdown("""
                        - **Flight Routing**: Prioritized direct paths; custom BFS algorithm used for cost-optimized segments.
                        - **Hotel Selection**: Ranked by verified star ratings and cost efficiency for requested class.
                        """)

with tab2:
    st.subheader("🎛️ Constraints")
    st.info("Configure your specific budget and preferences here.")
    # Your existing constraint form logic stays here...
