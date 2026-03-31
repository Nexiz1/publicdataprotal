import os
import requests
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Depends
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from urllib.parse import unquote

from core.config import settings
from core.constants import KMA_SHORT_TERM_FORECAST_URL, KMA_BASE_TIMES
from core.database import insert_forecast_items, get_all_users_with_tokens
from core.weather_analyzer import analyze_umbrella_need
from core.google_calendar import upsert_umbrella_event, delete_umbrella_event_if_exists
from core.exceptions import KMAApiException, get_kma_error_message
from core.utils import map_to_grid
from .schemas import (
    ShortTermForecastRequest, KMAResponse,
    UmbrellaReminderRequest, UmbrellaReminderResponse,
)

# --------------------------------------------------
# 백그라운드 스케줄러 설정
# --------------------------------------------------
scheduler = AsyncIOScheduler()

def get_fresh_access_token(refresh_token: str) -> str:
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

def run_daily_sync_job():
    print("🌅 [Background Job] Starting daily calendar sync...")
    users = get_all_users_with_tokens()
    now = datetime.now()
    base_date, base_time = _get_latest_base_time(now)
    
    for user in users:
        try:
            email = user["email"]
            print(f"Syncing for: {email}")
            nx, ny = map_to_grid(user["lat"], user["lon"])
            
            access_token = get_fresh_access_token(user["refresh_token"])
            
            data = _fetch_forecast(base_date, base_time, nx, ny)
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            analysis = analyze_umbrella_need(items)
            
            for day in analysis:
                if day["need_umbrella"]:
                    upsert_umbrella_event(
                        date=day["date"],
                        message=f"강수 예보: {day['reason']}",
                        access_token=access_token,
                        summary="☂️ 우산 챙기세요!",
                        notification_minutes=720
                    )
                else:
                    delete_umbrella_event_if_exists(
                        date=day["date"],
                        access_token=access_token,
                        summary="☂️ 우산 챙기세요!"
                    )
        except Exception as e:
            print(f"Failed background sync for {user.get('email')}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_daily_sync_job, 'cron', hour=6, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Weather & Google Calendar API", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "API is running"}

# --------------------------------------------------
# 기상청 단기예보 조회 유틸
# --------------------------------------------------
def _fetch_forecast(base_date: str, base_time: str, nx: int, ny: int) -> list:
    query_params = {
        "serviceKey": unquote(settings.WEATHER_API_KEY),
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    try:
        response = requests.get(KMA_SHORT_TERM_FORECAST_URL, params=query_params, timeout=10.0)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"기상청 API 연동 오류: {str(e)}")

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="기상청 API로부터 유효한 JSON을 받지 못했습니다.")

    header = data.get("response", {}).get("header", {})
    result_code = header.get("resultCode")
    if result_code != "00":
        error_description = get_kma_error_message(result_code)
        raise HTTPException(status_code=400, detail={"error_code": result_code, "message": f"API 에러: {error_description}"})
    if "body" not in data.get("response", {}):
         raise HTTPException(status_code=502, detail="API 응답 형식이 올바르지 않습니다.")
    return data

@app.get("/api/weather/forecast", response_model=KMAResponse)
def get_short_term_forecast(params: ShortTermForecastRequest = Depends()):
    # 날짜나 시간이 누락된 경우, 현재 시간 기준으로 최신 발표시간을 자동 계산
    if not params.base_date or not params.base_time:
        now = datetime.now()
        params.base_date, params.base_time = _get_latest_base_time(now)
        
    data = _fetch_forecast(params.base_date, params.base_time, params.nx, params.ny)
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if items:
        try:
            insert_forecast_items(items)
        except Exception as e:
            print(f"SQLite backup failed: {e}")
    return data

def _get_latest_base_time(now: datetime) -> tuple[str, str]:
    available_times = []
    for bt in KMA_BASE_TIMES:
        hour, minute = int(bt[:2]), int(bt[2:])
        available_at = now.replace(hour=hour, minute=minute + 10, second=0, microsecond=0)
        if available_at <= now:
            available_times.append(bt)
    if available_times:
        return now.strftime("%Y%m%d"), available_times[-1]
    else:
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"

@app.post("/api/calendar/umbrella-reminder", response_model=UmbrellaReminderResponse)
def create_umbrella_reminder(req: UmbrellaReminderRequest):
    now = datetime.now()
    base_date, base_time = _get_latest_base_time(now)

    data = _fetch_forecast(base_date, base_time, req.nx, req.ny)
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    if items:
        try:
            insert_forecast_items(items)
        except Exception:
            pass

    analysis = analyze_umbrella_need(items)
    calendar_events = []
    
    if req.sync_calendar:
        if not req.access_token:
            raise HTTPException(status_code=401, detail="Google Access Token Required.")
        for day in analysis:
            if day["need_umbrella"]:
                try:
                    event = upsert_umbrella_event(
                        date=day["date"],
                        message=f"강수 예보: {day['reason']}",
                        access_token=req.access_token,
                        summary=req.event_title,
                        notification_minutes=req.notification_minutes
                    )
                    calendar_events.append({"date": day["date"], "event_id": event.get("id", "N/A"), "html_link": event.get("htmlLink")})
                except Exception as e:
                    print(f"Calendar Sync Error: {e}")
                    raise HTTPException(status_code=500, detail=f"Google Calendar Sync Failed: {str(e)}")
            else:
                try:
                    delete_umbrella_event_if_exists(date=day["date"], access_token=req.access_token, summary=req.event_title)
                except Exception as e:
                    print(f"Calendar Delete Error: {e}")

    message = "완료되었습니다."
    return UmbrellaReminderResponse(analysis=analysis, calendar_events=calendar_events, message=message)
