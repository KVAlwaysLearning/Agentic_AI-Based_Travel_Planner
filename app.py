import streamlit as st
import os
import agent

# Set Streamlit Page Config
st.set_page_config(page_title="Elite AI Travel Agent", layout="wide")
st.title("✈️ Elite AI Travel Specialist")

# The Groq API key is automatically retrieved from Streamlit Secrets
# No sidebar input required for secrets.

st.subheader("🔮 Your Travel Requirements")
user_query = st.text_area(
    "Where do you want to go? Include dates, cities, and budget.",
    placeholder="Example: I want a 5-day trip: 2 days in Mumbai, then 3 days in Goa. Find cheap flights and good hotels for both.",
    height=120
)

# Keep the button name exactly as requested
button_clicked = st.button("🚀 Compose Travel Plan with Agent", type="primary")

if button_clicked:
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ GROQ_API_KEY is not configured in Streamlit Cloud Secrets.")
    else:
        st.subheader("🕵️ Agent Reasoning Traces")
        trace_area = st.empty()
        log_messages = []

        def streamlit_logger(log_type, message, metadata):
            icon = "🤖" if log_type == "tool_call_start" else "✅"
            log_messages.append(f"{icon} {message}")
            trace_area.markdown("\n\n".join(log_messages))
        
        with st.spinner("Agent is planning your multi-city trip..."):
            result = agent.run_travel_agent(user_query, callback_log=streamlit_logger)
            
        if result.get("success"):
            st.success("🎉 Travel Plan generated!")
            st.markdown(result["itinerary"])
        else:
            st.error("Failed to compile itinerary.")
            st.text(result.get("itinerary"))
