import streamlit as st
import os
import agent
import tools

# Set Streamlit Page Config
st.set_page_config(
    page_title="Elite AI Travel Agent",
    page_icon="✈️",
    layout="wide"
)

# App Header
st.title("✈️ Elite AI Travel Specialist")
st.caption("A multi-tool ReAct AI Agent to plan and optimize custom holidays using Groq.")

# The Groq API key is automatically retrieved from Streamlit Secrets
# No sidebar input required.

# Main Layout
# Removed "Test Python Tools" and "Download" tabs
st.subheader("🔮 Your Travel Requirements")
user_query = st.text_area(
    "Where do you want to go? Include dates, budget, and preferences.",
    height=120
)

button_clicked = st.button("🚀 Compose Travel Plan with Agent", type="primary")

if button_clicked:
    # Check for API key in secrets
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ GROQ_API_KEY is not configured in Streamlit Cloud Secrets.")
    else:
        status_container = st.empty()
        st.subheader("🕵️ Agent Reasoning Traces")
        trace_area = st.empty()
        
        log_messages = []
        def streamlit_logger(log_type, message, metadata):
            log_messages.append(f"• {message}")
            trace_area.markdown("\n".join(log_messages))
        
        with st.spinner("Agent is planning your trip..."):
            result = agent.run_travel_agent(user_query, callback_log=streamlit_logger)
            
        if result.get("success"):
            st.success("🎉 Travel Plan generated!")
            st.markdown(result["itinerary"])
        else:
            st.error("Failed to compile trip itinerary.")
            st.text(result.get("itinerary"))
