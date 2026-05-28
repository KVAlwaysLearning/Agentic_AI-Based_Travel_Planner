import streamlit as st
import os
import json
import pandas as pd
import agent
import tools

# Set Streamlit Page Config
st.set_page_config(
    page_title="Elite AI Travel Agent Playground",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom css for a polished interface
st.markdown("""
<style>
    .reportview-container {
        background: #f8f9fa;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #eaeaea;
    }
    .trace-card {
        background: #111;
        color: #00ff66;
        padding: 12px;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        margin-bottom: 8px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("✈️ Elite AI Travel Specialist Playground")
st.caption("A multi-tool ReAct / ToolCalling AI Agent to plan, optimize, and estimate budgets for custom holidays using Google Gemini.")

# Sidebar Configuration
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    st.header("🔑 Credentials & Config")
    
    # API Key Handling
    gemini_key = st.text_input(
        "Google Gemini API Key",
        value=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Provide your Gemini API key to run the live Agent planner."
    )
    
    # Save Key to Env
    if gemini_key:
        os.environ["GOOGLE_API_KEY"] = gemini_key
        os.environ["GEMINI_API_KEY"] = gemini_key
        
    st.divider()
    
    # Dataset Explorer
    st.header("🗄️ Dataset Inspector")
    dataset_option = st.selectbox(
        "Select Dataset to View",
        ["Flights Database", "Hotels Database", "Attractions Database"]
    )
    
    if dataset_option == "Flights Database":
        data = tools.load_json_data("flights.json")
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    elif dataset_option == "Hotels Database":
        data = tools.load_json_data("hotels.json")
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        data = tools.load_json_data("places.json")
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        
    st.caption("The datasets are loaded locally from `flights.json`, `hotels.json`, and `places.json`.")

# Main Layout
tab1, tab2, tab3 = st.tabs(["🗺️ Trip Planner Agent", "🛠️ Test Python Tools Directly", "💻 Download Python Code"])

with tab1:
    col_input, col_presets = st.columns([2, 1])
    
    with col_presets:
        st.subheader("💡 Presets Examples")
        preset_queries = [
            "3-day trip from New York to Paris starting June 15th",
            "Budget trip from Los Angeles to Tokyo under $1800 for 5 days",
            "Weekend getaway in Rome starting next Friday. Max 4-star hotels.",
            "Family trip from London to Paris. Looking for top landmarks & museums"
        ]
        selected_preset = st.radio("Select a quick preset query:", preset_queries)
        
    with col_input:
        st.subheader("🔮 Your Travel Requirements")
        user_query = st.text_area(
            "What criteria do you have? (Include dates, budget limits, destination preference)",
            value=selected_preset,
            height=120
        )
        
        button_clicked = st.button("🚀 Compose Travel Plan with Agent", type="primary")

    # Agent Execution Section
    if button_clicked:
        if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
            st.error("⚠️ Please specify your Google Gemini API Key in the sidebar to authenticate the agent.")
        else:
            status_container = st.empty()
            logs_container = st.container()
            
            with logs_container:
                st.subheader("🕵️ Agent Action & ReAct Reasoning Traces")
                trace_area = st.empty()
                
            # Logger context to render real-time UI stream
            log_messages = []
            
            def streamlit_logger(log_type, message, metadata):
                if log_type == "agent_thinking":
                    emoji = "🧠"
                    color_prefix = "#### 🧠"
                elif log_type == "tool_call_start":
                    emoji = "🤖"
                    color_prefix = "##### 🛠️"
                elif log_type == "tool_call_result":
                    emoji = "✅"
                    color_prefix = "> 💡"
                elif log_type == "agent_complete":
                    emoji = "✨"
                    color_prefix = "### ✨"
                else:
                    emoji = "⚙️"
                    color_prefix = ""
                
                log_messages.append(f"{color_prefix} {message}")
                trace_area.markdown("\n\n".join(log_messages))
            
            with st.spinner("Analyzing criteria and executing tools on Google Gemini..."):
                result = agent.run_travel_agent(user_query, callback_log=streamlit_logger)
                
            if result.get("success"):
                st.success("🎉 Travel Plan generated successfully!")
                
                st.divider()
                st.subheader("🗺️ Your Finished Travel Itinerary")
                st.markdown(result["itinerary"])
                
                # Render specific visual summary breakdown
                st.divider()
                st.subheader("📊 Execution Statistics")
                traces = result.get("traces", [])
                st.metric("Total Tool Invocations", len(traces))
                
                # Show an expandable JSON trace for debugging
                with st.expander("🔍 View Raw Agent JSON Traces"):
                    st.json(traces)
            else:
                st.error("Failed to compile trip itinerary.")
                st.text(result.get("itinerary"))

with tab2:
    st.subheader("🛠️ Verify and Test Custom Python Planning Tools")
    st.caption("Inspect individual tool outputs to verify search filters, coordinate mapping, and weather forecasts.")
    
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        st.markdown("### ✈️ Search Flights")
        f_source = st.selectbox("Departure City", ["New York", "London", "Los Angeles", "Paris", "Tokyo"])
        f_dest = st.selectbox("Arrival City", ["Paris", "Tokyo", "London", "Rome", "New York"])
        if st.button("Run Flight Search Tool"):
            res = tools.search_flights(f_source, f_dest)
            st.json(res)
            
        st.divider()
        st.markdown("### 🏨 Hotel Recommendations")
        h_city = st.selectbox("Hotel City", ["Paris", "Tokyo", "London", "New York", "Rome"], key="hotel_city")
        h_rating = st.slider("Minimum Rating", 3.0, 5.0, 4.0, 0.1)
        h_budget = st.number_input("Maximum Price per Night ($)", 50, 1500, 300)
        if st.button("Run Hotel Tool"):
            res = tools.recommend_hotels(h_city, min_rating=h_rating, max_price=h_budget)
            st.json(res)
            
    with t_col2:
        st.markdown("### ☀️ Weather Lookup (Real API)")
        w_city = st.text_input("Weather City", "Paris")
        w_start = st.date_input("Start Date")
        w_end = st.date_input("End Date")
        if st.button("Run Weather Forecast API"):
            res = tools.lookup_weather(w_city, start_date=str(w_start), end_date=str(w_end))
            st.json(res)
            
        st.divider()
        st.markdown("### 📍 Places Discovery")
        p_city = st.selectbox("Sightseeing City", ["Paris", "Tokyo", "London", "New York", "Rome"], key="places_city")
        p_type = st.selectbox("Activity Type Filter", [None, "Museum", "Park", "Sightseeing", "Historic"])
        if st.button("Run Sightseeing Finder"):
            res = tools.discover_places(p_city, place_type=p_type, min_rating=0.0)
            st.json(res)

with tab3:
    st.subheader("💻 Raw Python codebase tailored for your Streamlit Cloud Deployment")
    st.markdown("Follow the steps below to deploy this entire bundle directly onto Streamlit Cloud:")
    
    col_steps, col_files = st.columns([1, 2])
    
    with col_steps:
        st.markdown("""
        ### Setup Steps:
        1. **Create GitHub Repository** or include these files in your folder.
        2. **Create these files** verbatim from the right-hand panel:
           - `app.py`
           - `agent.py`
           - `tools.py`
           - `flights.json`
           - `hotels.json`
           - `places.json`
           - `requirements.txt`
        3. **Commit & Push** your codes.
        4. **Deploy on Streamlit community cloud**:
           - Sign into to [Streamlit Share](https://share.streamlit.io).
           - Connect your repo, and specify `app.py` as the entry script.
           - Add your `GOOGLE_API_KEY` or `GEMINI_API_KEY` inside the Streamlit advanced credentials config secrets!
        """)
        
    with col_files:
        code_file_choice = st.selectbox("Choose a script to inspect & copy:", [
            "tools.py", "agent.py", "app.py", "requirements.txt", "flights.json", "hotels.json", "places.json"
        ])
        
        if code_file_choice == "tools.py":
            with open("tools.py", "r") as f:
                st.code(f.read(), language="python")
        elif code_file_choice == "agent.py":
            with open("agent.py", "r") as f:
                st.code(f.read(), language="python")
        elif code_file_choice == "app.py":
            with open("app.py", "r") as f:
                st.code(f.read(), language="python")
        elif code_file_choice == "requirements.txt":
            st.code("streamlit>=1.30.0\nrequests>=2.31.0\npandas>=2.1.0\npython-dotenv>=1.0.0\nlangchain>=0.1.0\nlangchain-google-genai>=1.0.0\nlangchain-community>=0.0.10\ngoogle-genai>=0.1.1", language="text")
        elif code_file_choice == "flights.json":
            with open("flights.json", "r") as f:
                st.code(f.read(), language="json")
        elif code_file_choice == "hotels.json":
            with open("hotels.json", "r") as f:
                st.code(f.read(), language="json")
        elif code_file_choice == "places.json":
            with open("places.json", "r") as f:
                st.code(f.read(), language="json")
