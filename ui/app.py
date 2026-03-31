# ui/app.py
import streamlit as st
import requests
import sys
import os
import urllib.parse
import folium
from streamlit_folium import st_folium
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

# 프로젝트 루트를 패스에 추가하여 core 모듈을 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import map_to_grid
from core.database import get_user_location, save_user_location

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

# ---# default location (Seoul City Hall)
if "lat" not in st.session_state:
    st.session_state.lat = 37.5665
if "lon" not in st.session_state:
    st.session_state.lon = 126.9780
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# --- OAuth Flow ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"

def do_oauth_exchange():
    if "code" in st.query_params and "access_token" not in st.session_state:
        code = st.query_params["code"]
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        r = requests.post(token_url, data=data)
        if r.status_code == 200:
            token_data = r.json()
            st.session_state.access_token = token_data.get("access_token")
            # Fetch User Email
            user_req = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {st.session_state.access_token}"})
            if user_req.status_code == 200:
                email = user_req.json().get("email")
                st.session_state.email = email
                # Restore Location
                saved_loc = get_user_location(email)
                if saved_loc:
                    st.session_state.lat = saved_loc["lat"]
                    st.session_state.lon = saved_loc["lon"]
        st.query_params.clear()
        st.rerun()

do_oauth_exchange()

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

def sync_to_calendar(nx, ny, access_token, title=None, notif=None):
    payload = {"nx": nx, "ny": ny, "sync_calendar": True, "access_token": access_token}
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
        selected = st.selectbox("2. Select Your Location", list(options.keys()))
        if st.button("Apply Selection"):
            st.session_state.lat = float(options[selected]["lat"])
            st.session_state.lon = float(options[selected]["lon"])
            if "email" in st.session_state:
                save_user_location(st.session_state.email, st.session_state.lat, st.session_state.lon)
            st.rerun()
            
    st.markdown("---")
    
    # 2. Map Interaction
    st.markdown("**(Or click on the map!)**")
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=13)
    folium.Marker([st.session_state.lat, st.session_state.lon], tooltip="Your Location").add_to(m)
    
    # catch clicks from the map
    map_data = st_folium(m, height=300, use_container_width=True, returned_objects=["last_clicked"])
    if map_data and map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]
        
        # Avoid infinite reruns by checking if coordinate really changed
        if round(clicked_lat, 4) != round(st.session_state.lat, 4) or round(clicked_lon, 4) != round(st.session_state.lon, 4):
            st.session_state.lat = clicked_lat
            st.session_state.lon = clicked_lon
            if "email" in st.session_state:
                save_user_location(st.session_state.email, st.session_state.lat, st.session_state.lon)
            st.rerun()
            
    st.markdown("---")
    
    # Sync Google Calendar
    st.markdown("### 📅 Google Calendar Sync")
    if "access_token" in st.session_state:
        st.success(f"👤 {st.session_state.email}")
        if st.button("Sync All Rainy Days Now", use_container_width=True, type="primary"):
            with st.spinner("Syncing..."):
                res = sync_to_calendar(nx, ny, st.session_state.access_token)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(res.get("message", "Synced!"))
        if st.button("Logout", use_container_width=True):
            del st.session_state["access_token"]
            del st.session_state["email"]
            st.rerun()
    else:
        scope_str = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email"
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope={urllib.parse.quote(scope_str)}"
        st.link_button("🔑 Login with Google to Sync Calendar", auth_url, use_container_width=True)

# --- Main UI ---
st.title("☂️ SkyCast")
st.markdown("##### Intelligent Weather Insights & Smart Calendar Sync")

# Grid Info
nx, ny = map_to_grid(st.session_state.lat, st.session_state.lon)

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
            
            if "access_token" in st.session_state:
                st.success(f"Logged in as: {st.session_state.email}")
                if st.button("🚀 Sync All Rainy Days Now", key="sync_btn"):
                    with st.spinner("Syncing to Google Calendar..."):
                        result = sync_to_calendar(nx, ny, st.session_state.access_token)
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
                if st.button("Logout", key="logout_main"):
                    del st.session_state["access_token"]
                    del st.session_state["email"]
                    st.rerun()
            else:
                scope_str = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email"
                auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope={urllib.parse.quote(scope_str)}"
                st.link_button("🔑 Login with Google to Sync Calendar", auth_url, use_container_width=True)

        with col_right:
            if "access_token" in st.session_state:
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
                            result = sync_to_calendar(nx, ny, st.session_state.access_token, title=adv_title, notif=adv_notif)
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
