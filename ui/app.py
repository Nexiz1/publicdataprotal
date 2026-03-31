# ui/app.py
import streamlit as st
import requests
import sys
import os
from datetime import datetime

# 프로젝트 루트를 패스에 추가하여 core 모듈을 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import map_to_grid

API_BASE_URL = "http://localhost:8000"

# --- Page Configuration ---
st.set_page_config(
    page_title="SkyCast — Umbrella Reminder",
    page_icon="☂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 24px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        margin-bottom: 25px;
    }
    
    .forecast-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(5px);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease;
    }
    .forecast-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.6);
    }
    
    h1, h2, h3 {
        color: #1a2a6c;
        font-weight: 600 !important;
    }
    
    .status-text {
        font-size: 1.5rem;
        color: #4b6cb7;
        margin-top: 10px;
    }
    
    div.stButton > button:first-child {
        background-color: #4b6cb7;
        color: white;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #182848;
        border: none;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if 'lat' not in st.session_state:
    st.session_state.lat = 37.5665
if 'lon' not in st.session_state:
    st.session_state.lon = 126.9780

# --- Helper Functions ---
def search_address(query):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "SkyCast-Umbrella-App"}
        params = {"q": query, "format": "json", "limit": 1}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200 and resp.json():
            result = resp.json()[0]
            return float(result["lat"]), float(result["lon"]), result["display_name"]
    except Exception as e:
        st.error(f"Search failed: {e}")
    return None

def fetch_analysis(nx, ny, sync=False, title=None, notif=None):
    try:
        payload = {
            "nx": nx, 
            "ny": ny, 
            "sync_calendar": sync
        }
        if title: payload["event_title"] = title
        if notif: payload["notification_minutes"] = notif
        
        resp = requests.post(f"{API_BASE_URL}/api/calendar/umbrella-reminder", json=payload)
        if resp.status_code == 200:
            return resp.json()
        
        # Handle structured error from KMA
        err_json = resp.json()
        if "detail" in err_json:
            detail = err_json["detail"]
            if isinstance(detail, dict):
                return {"error": f"{detail.get('message')} ({detail.get('error_code')})"}
        return {"error": f"API Error: {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# --- Sidebar / Settings (Location Wizard) ---
with st.sidebar:
    st.title("📍 Location Wizard")
    
    address_query = st.text_input("Search Address", placeholder="e.g. Seoul, Gangnam")
    if st.button("Search & Update"):
        res = search_address(address_query)
        if res:
            st.session_state.lat, st.session_state.lon, name = res
            st.success(f"Found: {name}")
        else:
            st.warning("Address not found.")

    st.divider()
    
    with st.expander("Manual Coordinates"):
        st.session_state.lat = st.number_input("Latitude", value=st.session_state.lat, format="%.4f")
        st.session_state.lon = st.number_input("Longitude", value=st.session_state.lon, format="%.4f")
    
    st.divider()
    
    nx, ny = map_to_grid(st.session_state.lat, st.session_state.lon)
    st.code(f"KMA Grid: {nx}, {ny}")
    
    import pandas as pd
    map_data = pd.DataFrame({'lat': [st.session_state.lat], 'lon': [st.session_state.lon]})
    st.map(map_data, zoom=10)

# --- Main UI ---
st.title("☂️ SkyCast")
st.markdown("##### Intelligent Weather Insights & Smart Calendar Sync")

# Initial preview call (sync_calendar=False) - WON'T trigger OAuth
analysis_res = fetch_analysis(nx, ny, sync=False)

if "error" in analysis_res:
    st.error(f"⚠️ {analysis_res['error']}")
else:
    analysis = analysis_res.get("analysis", [])
    if analysis:
        today = analysis[0]
        need_umbrella = today["need_umbrella"]
        
        status_color = "#4b6cb7" if not need_umbrella else "#e63946"
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 4rem;">{'☀️' if not need_umbrella else '☂️'}</div>
                    <div>
                        <h1 style="margin:0; color:{status_color}; font-size:2.5rem;">
                            {'No Umbrella Needed' if not need_umbrella else 'Bring an Umbrella!'}
                        </h1>
                        <div class="status-text">{today['reason']}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("Upcoming Forecast")
        cols = st.columns(len(analysis))
        for idx, day in enumerate(analysis):
            with cols[idx]:
                icon = "☂️" if day["need_umbrella"] else "☀️"
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                weekday = date_obj.strftime("%a").upper()
                day_str = date_obj.strftime("%d %b")
                st.markdown(f"""
                    <div class="forecast-card">
                        <div style="font-weight:600; font-size:0.8rem; color:#888;">{weekday}</div>
                        <div style="font-size:1.1rem; margin-bottom:10px;">{day_str}</div>
                        <div style="font-size:2.5rem; margin:15px 0;">{icon}</div>
                        <div style="font-size:1.2rem; font-weight:600; color:#1a2a6c;">{day['max_pop']}%</div>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("🗓️ Smart Calendar Sync")
            st.write("Automatically register rainy day alerts to your Google Calendar.")
            
            if st.button("🚀 Sync All Rainy Days Now", key="sync_btn"):
                with st.spinner("Syncing..."):
                    result = fetch_analysis(nx, ny, sync=True) # Explicit sync = True
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        events = result.get("calendar_events", [])
                        if events:
                            st.success(f"Synced {len(events)} events!")
                            for ev in events:
                                st.markdown(f"✅ {ev['date']}: [View in Calendar]({ev['html_link']})")
                        else:
                            st.info(result.get("message", "No rainy days to sync."))

        with col_right:
            with st.expander("⚙️ Advanced Sync Settings"):
                st.write("Customize your reminder")
                adv_title = st.text_input("Event Title", value="☂️ 우산 챙기세요!")
                adv_notif = st.select_slider(
                    "Reminder Notification",
                    options=[30, 60, 180, 360, 720, 1440],
                    value=720,
                    format_func=lambda x: f"{x//60} hours before" if x >= 60 else f"{x} mins before"
                )
                if st.button("Sync with Custom Settings"):
                    with st.spinner("Syncing..."):
                        result = fetch_analysis(nx, ny, sync=True, title=adv_title, notif=adv_notif)
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success("Custom sync complete!")

# Detailed Data
with st.expander("📊 View Raw Forecast Data"):
    try:
        resp = requests.get(f"{API_BASE_URL}/api/weather/forecast", params={"nx": nx, "ny": ny})
        if resp.status_code == 200:
            forecast = resp.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
            st.dataframe(forecast, use_container_width=True)
    except:
        st.write("No raw data available.")

st.markdown("<br><br><div style='text-align:center; color:#888; font-size:0.8rem;'>Powered by KMA Open API & Google Calendar</div>", unsafe_allow_html=True)
