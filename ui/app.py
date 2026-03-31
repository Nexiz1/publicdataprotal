# ui/app.py
import streamlit as st
import requests
import sys
import os
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 프로젝트 루트를 패스에 추가하여 core 모듈을 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import map_to_grid

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SkyCast — Umbrella Reminder",
    page_icon="☂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Look (Theme Agnostic) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .glass-card {
        background: rgba(128, 128, 128, 0.1);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 24px;
        padding: 30px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
    
    .forecast-card {
        background: rgba(128, 128, 128, 0.05);
        backdrop-filter: blur(5px);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.2);
        transition: transform 0.3s ease;
    }
    .forecast-card:hover {
        transform: translateY(-5px);
        background: rgba(128, 128, 128, 0.15);
    }
    
    h1, h2, h3 {
        color: inherit !important;
        font-weight: 600 !important;
    }
    
    .status-text {
        font-size: 1.5rem;
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
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #3b5b97;
        color: white;
        border-style: none;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if 'lat' not in st.session_state:
    st.session_state.lat = 37.5665
if 'lon' not in st.session_state:
    st.session_state.lon = 126.9780
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# --- Helper Functions with Caching ---
@st.cache_data(ttl=3600, show_spinner="지도 주소를 검색하는 중입니다... 🗺️")
def search_address_list(query):
    """Nominatim API로 최대 5개의 유사 주소 목록을 즉각 반환"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "SkyCast-Umbrella-App"}
        params = {"q": query, "format": "json", "limit": 5, "addressdetails": 0}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Search failed: {e}")
    return []

@st.cache_data(ttl=1800, show_spinner="기상청 예보 데이터를 분석 중입니다... ⛅")
def fetch_analysis_cached(nx, ny):
    """캐시가 적용된 분석 전용 API (30분 TTL, 잦은 리렌더링에도 성능 보장)"""
    try:
        resp = requests.post(f"{API_BASE_URL}/api/calendar/umbrella-reminder", json={"nx": nx, "ny": ny, "sync_calendar": False}, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        err_json = resp.json()
        if "detail" in err_json:
            detail = err_json["detail"]
            if isinstance(detail, dict):
                return {"error": f"{detail.get('message')} ({detail.get('error_code')})"}
        return {"error": f"API Error: {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def sync_calendar_event(nx, ny, title=None, notif=None):
    """캘린더 등록 전용 비캐시 함수"""
    payload = {"nx": nx, "ny": ny, "sync_calendar": True}
    if title: payload["event_title"] = title
    if notif: payload["notification_minutes"] = notif
    
    try:
        resp = requests.post(f"{API_BASE_URL}/api/calendar/umbrella-reminder", json=payload, timeout=30)
        return resp.json() if resp.status_code == 200 else {"error": f"API Error: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}

# --- Sidebar / Settings (Location Wizard) ---
with st.sidebar:
    st.title("📍 Location Wizard")
    
    # 1. Autocomplete Search (st.form enables 'Enter' key submission)
    with st.form(key="search_form"):
        address_query = st.text_input("1. Search Address", placeholder="e.g. 강남역, 한강공원")
        search_submit = st.form_submit_button("Search 🔍")
        
        if search_submit and address_query:
            st.session_state.search_results = search_address_list(address_query)
            if not st.session_state.search_results:
                st.warning("주소를 찾을 수 없습니다.")
            
    if st.session_state.search_results:
        options = {res["display_name"]: res for res in st.session_state.search_results}
        selected_name = st.selectbox("Select exact location:", list(options.keys()))
        if st.button("Apply Selection"):
            selected_data = options[selected_name]
            st.session_state.lat = float(selected_data["lat"])
            st.session_state.lon = float(selected_data["lon"])
            st.session_state.search_results = [] # clear after selection
            st.rerun()

    st.divider()
    
    # Grid Info
    nx, ny = map_to_grid(st.session_state.lat, st.session_state.lon)
    st.caption("2. Or Tap on the map to pinpoint!")
    st.code(f"KMA Grid: {nx}, {ny}")
    
    # 2. Interactive Map (folium)
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=11)
    folium.Marker([st.session_state.lat, st.session_state.lon], tooltip="Current Target").add_to(m)
    
    # catch clicks from the map
    map_data = st_folium(m, height=300, use_container_width=True, returned_objects=["last_clicked"])
    if map_data and map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]
        
        # Avoid infinite reruns by checking if coordinate really changed
        if round(clicked_lat, 4) != round(st.session_state.lat, 4) or round(clicked_lon, 4) != round(st.session_state.lon, 4):
            st.session_state.lat = clicked_lat
            st.session_state.lon = clicked_lon
            st.rerun()

# --- Main UI ---
st.title("☂️ SkyCast")
st.markdown("##### Intelligent Weather Insights & Smart Calendar Sync")

# Cached initial preview call
analysis_res = fetch_analysis_cached(nx, ny)

if "error" in analysis_res:
    st.error(f"⚠️ {analysis_res['error']}")
else:
    analysis = analysis_res.get("analysis", [])
    if analysis:
        today = analysis[0]
        need_umbrella = today["need_umbrella"]
        
        status_color = "inherit" if not need_umbrella else "#e63946"
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
                        <div style="font-weight:600; font-size:0.8rem;">{weekday}</div>
                        <div style="font-size:1.1rem; margin-bottom:10px;">{day_str}</div>
                        <div style="font-size:2.5rem; margin:15px 0;">{icon}</div>
                        <div style="font-size:1.2rem; font-weight:600;">{day['max_pop']}%</div>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("🗓️ Smart Calendar Sync")
            st.write("Automatically register rainy day alerts to your Google Calendar.")
            
            if st.button("🚀 Sync All Rainy Days Now", key="sync_btn"):
                with st.spinner("Syncing to Google Calendar..."):
                    result = sync_calendar_event(nx, ny)
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
                    with st.spinner("Syncing to Google Calendar..."):
                        result = sync_calendar_event(nx, ny, title=adv_title, notif=adv_notif)
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success("Custom sync complete!")

# Detailed Data
with st.expander("📊 View Raw Forecast Data"):
    try:
        resp = requests.get(f"{API_BASE_URL}/api/weather/forecast", params={"nx": nx, "ny": ny}, timeout=10)
        if resp.status_code == 200:
            forecast = resp.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
            st.dataframe(forecast, height=300)
    except:
        st.write("No raw data available.")

st.markdown("<br><div style='text-align:center; color:#888; font-size:0.8rem;'>Powered by KMA Open API & Google Calendar</div>", unsafe_allow_html=True)
