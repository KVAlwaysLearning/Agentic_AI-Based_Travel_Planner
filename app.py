import streamlit as st
import os
import agent
import tools
from datetime import datetime, date, timedelta

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Indica Odyssey Planner", layout="wide", page_icon="✈️")

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0a0c10 !important;
    color: #e8e0d4 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 0%, #1a1225 0%, #0a0c10 55%),
                radial-gradient(ellipse at 80% 100%, #0d1a24 0%, transparent 60%) !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1300px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12101a 0%, #0d1520 100%) !important;
    border-right: 1px solid rgba(255,200,100,0.08) !important;
}
[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #1e1628, #0f1e2e) !important;
    color: #c9a96e !important;
    border: 1px solid rgba(201,169,110,0.3) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    border-color: #c9a96e !important;
    box-shadow: 0 0 16px rgba(201,169,110,0.2) !important;
}

/* ── Page title ── */
.odyssey-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.8rem;
    font-weight: 300;
    letter-spacing: 0.12em;
    background: linear-gradient(135deg, #e8d5a3, #c9a96e, #e8d5a3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0;
    line-height: 1.1;
}
.odyssey-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(201,169,110,0.55);
    margin-top: 0.1rem;
    margin-bottom: 1.6rem;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    color: rgba(232,224,212,0.45) !important;
    border-radius: 9px !important;
    padding: 8px 22px !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e1628, #0f1e2e) !important;
    color: #c9a96e !important;
    border: 1px solid rgba(201,169,110,0.25) !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4) !important;
}

/* ── Cards / glass panels ── */
.glass-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(8px);
}
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(201,169,110,0.6);
    margin-bottom: 0.9rem;
}
.section-heading {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: #e8d5a3;
    margin-bottom: 0.25rem;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(201,169,110,0.06), rgba(201,169,110,0.02)) !important;
    border: 1px solid rgba(201,169,110,0.15) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.3rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: rgba(201,169,110,0.55) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.6rem !important;
    font-weight: 600 !important;
    color: #e8d5a3 !important;
}

/* ── Primary buttons ── */
.stButton button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #c9a96e, #a07840) !important;
    color: #0a0c10 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 20px rgba(201,169,110,0.25) !important;
}
.stButton button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 6px 28px rgba(201,169,110,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Text inputs & textareas ── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e8e0d4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color: rgba(201,169,110,0.4) !important;
    box-shadow: 0 0 0 2px rgba(201,169,110,0.1) !important;
}

/* ── Selectboxes & multiselect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e8e0d4 !important;
}
[data-baseweb="select"] span { color: #e8e0d4 !important; }
[data-baseweb="popover"] { background: #12141c !important; border: 1px solid rgba(201,169,110,0.2) !important; border-radius: 10px !important; }
[data-baseweb="menu"] li { background: transparent !important; color: #c9bba5 !important; }
[data-baseweb="menu"] li:hover { background: rgba(201,169,110,0.08) !important; }
[data-baseweb="tag"] { background: rgba(201,169,110,0.15) !important; border: 1px solid rgba(201,169,110,0.3) !important; color: #c9a96e !important; border-radius: 6px !important; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }

/* ── Tables ── */
[data-testid="stTable"] table {
    background: transparent !important;
    border-collapse: separate !important;
    border-spacing: 0 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
}
[data-testid="stTable"] th {
    background: rgba(201,169,110,0.08) !important;
    color: rgba(201,169,110,0.7) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    border: none !important;
    padding: 10px 14px !important;
}
[data-testid="stTable"] td {
    background: rgba(255,255,255,0.025) !important;
    color: #c9bba5 !important;
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.04) !important;
    padding: 9px 14px !important;
}
[data-testid="stTable"] tr:hover td { background: rgba(201,169,110,0.05) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
}
.stSuccess { background: rgba(100,200,120,0.08) !important; border-color: rgba(100,200,120,0.25) !important; }
.stWarning { background: rgba(201,169,110,0.08) !important; border-color: rgba(201,169,110,0.25) !important; }
.stError   { background: rgba(220,80,80,0.08) !important;  border-color: rgba(220,80,80,0.2) !important; }
.stInfo    { background: rgba(80,140,220,0.08) !important; border-color: rgba(80,140,220,0.2) !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: #c9a96e !important; font-family: 'DM Sans', sans-serif !important; }

/* ── Markdown ── */
.stMarkdown h1, .stMarkdown h2 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600 !important;
    color: #e8d5a3 !important;
    letter-spacing: 0.04em !important;
}
.stMarkdown h3 {
    font-family: 'Cormorant Garamond', serif !important;
    color: #c9a96e !important;
}
.stMarkdown p, .stMarkdown li { color: #c9bba5 !important; line-height: 1.75 !important; }
.stMarkdown strong { color: #e8d5a3 !important; }
.stMarkdown code {
    background: rgba(201,169,110,0.1) !important;
    color: #c9a96e !important;
    border-radius: 4px !important;
    padding: 1px 6px !important;
    font-size: 0.82em !important;
}
.stMarkdown table {
    border-collapse: collapse !important;
    font-size: 0.83rem !important;
    width: 100% !important;
}
.stMarkdown th {
    background: rgba(201,169,110,0.08) !important;
    color: rgba(201,169,110,0.7) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 10px 14px !important;
}
.stMarkdown td {
    color: #c9bba5 !important;
    border-color: rgba(255,255,255,0.06) !important;
    padding: 8px 14px !important;
}

/* ── Date input ── */
[data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e8e0d4 !important;
}

/* ── Form field labels ── */
label[data-testid="stWidgetLabel"] p,
.stSelectbox label, .stMultiSelect label,
.stTextArea label, .stDateInput label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: rgba(201,169,110,0.6) !important;
}

/* ── Trace log container ── */
.trace-box {
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    color: #8a9bb0;
    max-height: 220px;
    overflow-y: auto;
    line-height: 1.8;
}

/* ── Sidebar info box ── */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(201,169,110,0.06) !important;
    border: 1px solid rgba(201,169,110,0.15) !important;
    border-radius: 10px !important;
    font-size: 0.78rem !important;
    color: rgba(201,169,110,0.7) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="odyssey-title">Indica Odyssey</p>', unsafe_allow_html=True)
st.markdown('<p class="odyssey-sub">AI-Powered Multi-City Travel Planner &nbsp;·&nbsp; v3.0</p>', unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 1.2rem;">
        <p style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:600;
                  color:#c9a96e;letter-spacing:0.08em;margin-bottom:0.1rem;">State Engine</p>
        <p style="font-family:'DM Sans',sans-serif;font-size:0.68rem;letter-spacing:0.18em;
                  text-transform:uppercase;color:rgba(201,169,110,0.4);margin-top:0;">Control Panel</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳  Clear State Memory", type="secondary"):
        tools.reset_memory()
        st.success("State memory cleared.")

    st.info(f"📦  Cost log entries: **{len(tools.city_data_memory)}**")

    st.markdown("""
    <div style="margin-top:2rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,0.06);">
        <p style="font-family:'DM Sans',sans-serif;font-size:0.68rem;letter-spacing:0.15em;
                  text-transform:uppercase;color:rgba(255,255,255,0.2);margin-bottom:0.6rem;">Available Cities</p>
    """, unsafe_allow_html=True)
    cities_display = ["Delhi", "Mumbai", "Hyderabad", "Bangalore", "Chennai", "Goa", "Kolkata", "Jaipur"]
    for c in cities_display:
        st.markdown(f'<p style="font-family:\'DM Sans\',sans-serif;font-size:0.78rem;color:rgba(201,169,110,0.5);margin:0.15rem 0;">→ {c}</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Data ────────────────────────────────────────────────────────────────────────
available_cities = ["Delhi", "Mumbai", "Hyderabad", "Bangalore", "Chennai", "Goa", "Kolkata", "Jaipur"]
available_attractions = ["lake", "temple", "museum", "park", "fort", "beach", "market", "monument"]

# ── Logic helpers (unchanged) ───────────────────────────────────────────────────
def extract_trip_details_from_prompt(prompt, logged_cities=None):
    prompt_lower = prompt.lower()
    cities_in_prompt = []
    for c in available_cities:
        idx = prompt_lower.find(c.lower())
        if idx != -1:
            cities_in_prompt.append((idx, c))
    cities_in_prompt.sort(key=lambda x: x[0])
    if not cities_in_prompt:
        return "Delhi", ["Mumbai"]
    origin = None
    origin_words = ["from", "starting in", "starting at", "originating in", "departure", "out of"]
    for idx, c in cities_in_prompt:
        start_idx = max(0, idx - 15)
        context = prompt_lower[start_idx:idx]
        if any(ow in context for ow in origin_words):
            origin = c
            break
    dest_cities = []
    if origin:
        dest_cities = [c for _, c in cities_in_prompt if c != origin]
    else:
        if len(cities_in_prompt) == 1:
            single_city = cities_in_prompt[0][1]
            origin = "Delhi"
            if single_city == "Delhi":
                dest_cities = ["Mumbai"]
            else:
                dest_cities = [single_city]
        else:
            first_city = cities_in_prompt[0][1]
            if first_city == "Delhi" or first_city == "Hyderabad":
                origin = first_city
                dest_cities = [c for _, c in cities_in_prompt if c != origin]
            else:
                origin = "Delhi"
                dest_cities = [c for _, c in cities_in_prompt if c != "Delhi"]
    if not dest_cities:
        dest_cities = ["Delhi"] if origin != "Delhi" else ["Mumbai"]
    return origin, dest_cities

def extract_constraints_from_prompt(prompt):
    prompt_lower = prompt.lower()
    days = None
    import re
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14
    }
    for word, val in words.items():
        if re.search(rf"\b{word}\s*days?\b", prompt_lower) or re.search(rf"\b{word}\s*-\s*days?\b", prompt_lower):
            days = val
            break
    if not days:
        digit_match = re.search(r"\b(\d+)\s*-\s*days?\b", prompt_lower) or re.search(r"\b(\d+)\s*days?\b", prompt_lower)
        if digit_match:
            try:
                days = int(digit_match.group(1))
            except ValueError:
                pass
    start_date = None
    match = re.search(r"\b(202\d-\d{2}-\d{2})\b", prompt)
    if match:
        start_date = match.group(1)
    else:
        match = re.search(r"\b(\d{2})[-/](\d{2})[-/](202\d)\b", prompt)
        if match:
            day, month, year = match.groups()
            start_date = f"{year}-{month}-{day}"
        else:
            months = ["january", "february", "march", "april", "may", "june", "july", "august",
                      "september", "october", "november", "december",
                      "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            for m_idx, m in enumerate(months):
                pattern = rf"\b{m}\s*(\d{{1,2}})(?:st|nd|rd|th)?\b"
                m_match = re.search(pattern, prompt_lower)
                if m_match:
                    day_val = int(m_match.group(1))
                    month_num = (m_idx % 12) + 1
                    start_date = f"2026-{month_num:02d}-{day_val:02d}"
                    break
                pattern_rev = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s*of\s*{m}\b"
                m_match_rev = re.search(pattern_rev, prompt_lower)
                if m_match_rev:
                    day_val = int(m_match_rev.group(1))
                    month_num = (m_idx % 12) + 1
                    start_date = f"2026-{month_num:02d}-{day_val:02d}"
                    break
                pattern_rev_simple = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s*{m}\b"
                m_match_rev_s = re.search(pattern_rev_simple, prompt_lower)
                if m_match_rev_s:
                    day_val = int(m_match_rev_s.group(1))
                    month_num = (m_idx % 12) + 1
                    start_date = f"2026-{month_num:02d}-{day_val:02d}"
                    break
    hotel_tier = "budget"
    if "cheap" in prompt_lower or "budget" in prompt_lower:
        hotel_tier = "cheapest" if "cheapest" in prompt_lower or "very cheap" in prompt_lower else "budget"
    elif "luxury" in prompt_lower or "luxurious" in prompt_lower or "expensive" in prompt_lower or "five star" in prompt_lower:
        hotel_tier = "luxurious"
    attraction = None
    for attr in available_attractions:
        if attr in prompt_lower:
            attraction = attr
            break
    is_completed_before = False
    before_keywords = ["before", "by", "complete before", "completed before", "end by", "finish by",
                       "return by", "completed by", "arrive by", "back by", "leave before"]
    if any(kw in prompt_lower for kw in before_keywords):
        is_completed_before = True
    return days, start_date, hotel_tier, attraction, is_completed_before

# ── Tabs ────────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["  ✦  AI Prompt Planner  ", "  ⊞  Constraint Control Panel  "])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI Prompt Planner
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div class="glass-card" style="margin-bottom:1.4rem;">
        <p class="section-label">Natural Language Interface</p>
        <p class="section-heading">Tell the AI where you want to go</p>
        <p style="font-family:'DM Sans',sans-serif;font-size:0.84rem;color:rgba(201,185,165,0.65);margin:0;">
            Describe your trip in plain English — cities, duration, dates, budget preferences.
            The specialist agent handles the rest.
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_query = st.text_area(
        "Your travel request",
        placeholder="e.g. · 5-day trip from Delhi to Bangalore and Goa, budget hotels, starting June 10",
        height=110,
        key="prompt_input",
        label_visibility="collapsed"
    )

    st.markdown('<p style="font-family:\'DM Sans\',sans-serif;font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:rgba(201,169,110,0.4);margin-bottom:0.6rem;">Include: origin city · destinations · number of days · hotel class · dates</p>', unsafe_allow_html=True)

    button_clicked = st.button("✈  Compose Travel Plan with AI Agent", type="primary")

    if button_clicked:
        if not user_query.strip():
            st.warning("Please describe your trip before submitting.")
        else:
            # ── Logic: unchanged ──
            origin, dest_cities = extract_trip_details_from_prompt(user_query)
            p_days, p_start_date, p_hotel_tier, p_attr, is_completed_before = extract_constraints_from_prompt(user_query)
            n_days = p_days if p_days is not None else 5
            m_cities = len(dest_cities)

            if m_cities > n_days:
                st.error(f"Tour not possible in {n_days} days — consider {m_cities} days, or reduce destinations.")
            else:
                if p_start_date:
                    try:
                        start_date_obj = datetime.strptime(p_start_date, "%Y-%m-%d")
                        if is_completed_before:
                            start_date_obj = start_date_obj - timedelta(days=(n_days - 1))
                        resolved_start_date_str = start_date_obj.strftime("%Y-%m-%d")
                    except Exception:
                        resolved_start_date_str = datetime.now().strftime("%Y-%m-%d")
                else:
                    resolved_start_date_str = datetime.now().strftime("%Y-%m-%d")

                end_date_obj = datetime.strptime(resolved_start_date_str, "%Y-%m-%d") + timedelta(days=n_days)
                date_range_str = f"{resolved_start_date_str} to {end_date_obj.strftime('%Y-%m-%d')}"

                payload = {
                    "origin": origin,
                    "cities": dest_cities,
                    "days": n_days,
                    "hotel_types": p_hotel_tier if p_hotel_tier else "budget",
                    "attractions": [p_attr] if p_attr else []
                }

                tools.resolve_and_save_state(payload, date_range=date_range_str)

                # ── Trace panel ──
                st.markdown("""
                <div style="margin:1.2rem 0 0.5rem;">
                    <p class="section-label">Agent Reasoning Traces</p>
                </div>
                """, unsafe_allow_html=True)
                trace_area = st.empty()
                log_messages = []

                def streamlit_logger(log_type, message, metadata):
                    icon = "⚙" if log_type == "tool_call_start" else "✓"
                    log_messages.append(f"{icon}  {message}")
                    trace_area.markdown(
                        '<div class="trace-box">' + "<br>".join(log_messages[-12:]) + '</div>',
                        unsafe_allow_html=True
                    )

                with st.spinner("Agent is composing your itinerary…"):
                    result = agent.run_travel_agent(user_query, callback_log=streamlit_logger)

                if result.get("success"):
                    st.success("✦  Travel plan composed successfully.")
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown(result["itinerary"])
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("AI specialist is busy — programmatic engine solved your route.")

                # ── Programmatic tables (always rendered) ──
                costs_data = tools.run_full_itinerary_generation(tools.df_flights, tools.df_hotels)

                if isinstance(costs_data, dict) and "error" not in costs_data:
                    summary = costs_data.get("summary", {})

                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.markdown("""
                    <p class="section-label" style="margin-bottom:0.8rem;">Package Cost Summary</p>
                    """, unsafe_allow_html=True)

                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("✈  Flights", f"₹{summary.get('total_flight', 0):,}")
                    sc2.metric("🏨  Hotels", f"₹{summary.get('total_hotel', 0):,}")
                    sc3.metric("☕  Daily Buffer", f"₹{summary.get('total_misc', 0):,}")
                    sc4.metric("◈  Grand Total", f"₹{summary.get('grand_total', 0):,}")

                    st.markdown("""
                    <p class="section-label" style="margin:1.4rem 0 0.5rem;">Day-by-Day Cost Schedule</p>
                    """, unsafe_allow_html=True)

                    flight_legs = costs_data.get("flight_legs", [])
                    rows = tools.build_cost_breakdown_table(
                        costs_data.get("itinerary", []),
                        costs_data.get("flight_legs", []),
                        costs_data.get("itinerary", []),
                        resolved_start_date_str
                    )
                    st.table(rows)

                    no_direct_warnings = []
                    for leg in flight_legs:
                        if not leg.get("is_direct", True) and "leg" in leg:
                            try:
                                start_c, end_c = leg["leg"].split("->")
                                no_direct_warnings.append(f"No direct flights between {start_c} and {end_c} — connecting route shown.")
                            except Exception:
                                pass
                    for warn in no_direct_warnings:
                        st.warning(f"⚠  {warn}")

                    st.markdown("""
                    <p class="section-label" style="margin:1.4rem 0 0.5rem;">Selected Flights</p>
                    """, unsafe_allow_html=True)
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

                    st.markdown("""
                    <p class="section-label" style="margin:1.4rem 0 0.5rem;">Selection Intelligence</p>
                    """, unsafe_allow_html=True)
                    st.markdown("""
                    - **Flight Routing** — Direct paths prioritised; where unavailable a BFS algorithm resolves the cheapest connecting chain.
                    - **Hotel Selection** — Highest-rated verified property within the requested class (Cheapest / Budget / Luxury).
                    """)
                else:
                    st.error("Failed to solve optimal itinerary constraints.")
                    if not result.get("success"):
                        st.text(result.get("itinerary"))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Constraint Control Panel
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="glass-card" style="margin-bottom:1.4rem;">
        <p class="section-label">Structured Input Interface</p>
        <p class="section-heading">Constraint-Driven Itinerary Builder</p>
        <p style="font-family:'DM Sans',sans-serif;font-size:0.84rem;color:rgba(201,185,165,0.65);margin:0;">
            Set precise parameters or choose <strong style="color:#c9a96e;">Flexible</strong> to let the engine
            auto-resolve optimal allocations via constraint propagation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<p class="section-label">Origin & Destinations</p>', unsafe_allow_html=True)
        origin_input = st.selectbox(
            "Journey Origin City",
            options=["Flexible"] + available_cities,
            index=1
        )
        dest_cities = st.multiselect(
            "Destination / Intermediate Cities",
            options=["Flexible"] + available_cities,
            default=["Mumbai"]
        )
        hotel_category = st.selectbox(
            "Lodging Class",
            options=["Flexible", "cheapest", "budget", "luxurious"],
            index=2
        )

    with col2:
        st.markdown('<p class="section-label">Duration & Preferences</p>', unsafe_allow_html=True)
        attraction_interest = st.selectbox(
            "Attraction Interest",
            options=["Flexible"] + available_attractions,
            index=0
        )
        trip_days = st.selectbox(
            "Trip Duration (Days)",
            options=["Flexible"] + list(range(1, 15)),
            index=5
        )
        date_range_selection = st.date_input(
            "Departure Date Range",
            value=[date(2026, 6, 1), date(2026, 6, 6)]
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.button("⛓  Map Constraints & Build Itinerary", type="primary"):
        # ── Logic: unchanged ──
        start_date_str = "2026-06-01"
        formatted_dates = "2026-06-01 to 2026-06-06"

        if isinstance(date_range_selection, (list, tuple)) and len(date_range_selection) == 2:
            formatted_dates = " to ".join([d.strftime("%Y-%m-%d") for d in date_range_selection])
            start_date_str = date_range_selection[0].strftime("%Y-%m-%d")
        elif isinstance(date_range_selection, date):
            start_date_str = date_range_selection.strftime("%Y-%m-%d")
            formatted_dates = start_date_str

        payload = {
            "origin": origin_input,
            "cities": dest_cities if len(dest_cities) > 0 else "Flexible",
            "days": trip_days,
            "hotel_types": hotel_category,
            "attractions": [attraction_interest] if attraction_interest != "Flexible" else []
        }

        with st.spinner("Resolving constraint domains & propagating matrices…"):
            status_msg = tools.resolve_and_save_state(payload, date_range=formatted_dates)

            resolved_origin   = tools.global_trip_state.get('origin', origin_input)
            resolved_cities   = tools.global_trip_state.get('cities', dest_cities)
            resolved_category = tools.global_trip_state.get('hotel_types', hotel_category)
            try:
                resolved_days = int(tools.global_trip_state.get('days', 5))
            except Exception:
                resolved_days = 5

            n = resolved_days
            m = len(resolved_cities)

            if m > n:
                st.error(f"Tour not possible in {n} days — consider {m} days, or reduce destinations.")
            else:
                st.toast(f"⚡  Constraints resolved: {status_msg}")

                res_itinerary = tools.run_full_itinerary_generation(tools.df_flights, tools.df_hotels)

                if isinstance(res_itinerary, str) or ("error" in res_itinerary and res_itinerary["error"]):
                    st.error("Routing error: " + (res_itinerary if isinstance(res_itinerary, str) else res_itinerary.get("message", "Impossible route.")))
                else:
                    st.success("✦  Itinerary calculations complete.")

                    itinerary_md = tools.build_itinerary_markdown_report_from_state(
                        res_itinerary, resolved_origin, resolved_cities, formatted_dates, resolved_category
                    )
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown(itinerary_md)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("<hr>", unsafe_allow_html=True)
                    summary = res_itinerary.get("summary", {})

                    st.markdown('<p class="section-label" style="margin-bottom:0.8rem;">Package Cost Summary</p>', unsafe_allow_html=True)
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("✈  Flights",      f"₹{summary.get('total_flight', 0):,}")
                    sc2.metric("🏨  Hotels",       f"₹{summary.get('total_hotel', 0):,}")
                    sc3.metric("☕  Daily Buffer",  f"₹{summary.get('total_misc', 0):,}")
                    sc4.metric("◈  Grand Total",   f"₹{summary.get('grand_total', 0):,}")

                    st.markdown('<p class="section-label" style="margin:1.4rem 0 0.5rem;">Day-by-Day Cost Schedule</p>', unsafe_allow_html=True)
                    rows = tools.build_cost_breakdown_table(
                        res_itinerary.get("itinerary", []),
                        res_itinerary.get("flight_legs", []),
                        res_itinerary.get("itinerary", []),
                        start_date_str
                    )
                    st.table(rows)

                    no_direct_warnings = []
                    flight_legs = res_itinerary.get("flight_legs", [])
                    for leg in flight_legs:
                        if not leg.get("is_direct", True):
                            start_c, end_c = leg["leg"].split("->")
                            no_direct_warnings.append(f"No direct flights between {start_c} and {end_c} — connecting route shown.")
                    for warn in no_direct_warnings:
                        st.warning(f"⚠  {warn}")

                    st.markdown('<p class="section-label" style="margin:1.4rem 0 0.5rem;">Selected Flights</p>', unsafe_allow_html=True)
                    flight_rows = []
                    for leg in flight_legs:
                        for segment in leg.get("segments", []):
                            flight_rows.append({
                                "Flight No": segment.get("flight_id"),
                                "Airline":   segment.get("airline"),
                                "From":      segment.get("from"),
                                "To":        segment.get("to"),
                                "Cost":      f"₹{segment.get('price'):,}"
                            })
                    if flight_rows:
                        st.table(flight_rows)
                    else:
                        st.info("No flight segment details available.")

                    st.markdown('<p class="section-label" style="margin:1.4rem 0 0.5rem;">Selection Intelligence</p>', unsafe_allow_html=True)
                    st.markdown("""
                    - **Flight Routing** — Direct paths prioritised; where unavailable a BFS algorithm resolves the cheapest connecting chain.
                    - **Hotel Selection** — Highest-rated verified property within the requested class (Cheapest / Budget / Luxury).
                    """)
