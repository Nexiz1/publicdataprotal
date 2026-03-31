import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from core.config import settings
from core.constants import KMA_SHORT_TERM_FORECAST_URL, KMA_BASE_TIMES
from core.database import insert_forecast_items
from core.weather_analyzer import analyze_umbrella_need
from core.google_calendar import add_umbrella_reminder
from core.exceptions import KMAApiException, get_kma_error_message
from .schemas import (
    ShortTermForecastRequest, KMAResponse,
    UmbrellaReminderRequest, UmbrellaReminderResponse,
)
from urllib.parse import unquote

app = FastAPI(title="Weather & Google Calendar API")


@app.get("/")
def read_root():
    return {"message": "API is running"}


# --------------------------------------------------
# 기상청 단기예보 조회
# --------------------------------------------------

def _fetch_forecast(base_date: str, base_time: str, nx: int, ny: int) -> list:
    """기상청 단기예보를 호출하고 item 리스트를 반환하는 내부 유틸"""
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
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": result_code,
                "message": f"기상청 API 에러: {error_description}",
                "raw_msg": header.get("resultMsg")
            }
        )

    # 응답 구조가 정상인지 추가 확인 (body 유무 등)
    if "body" not in data.get("response", {}):
         raise HTTPException(
            status_code=502,
            detail="기상청 API 응답 형식이 올바르지 않습니다. (body 누락)"
        )

    return data


@app.get("/api/weather/forecast", response_model=KMAResponse)
def get_short_term_forecast(params: ShortTermForecastRequest = Depends()):
    """단기예보 조회 (기존 엔드포인트)"""
    data = _fetch_forecast(params.base_date, params.base_time, params.nx, params.ny)

    # 응답받은 기상 정보를 SQLite에 백업
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if items:
        try:
            insert_forecast_items(items)
        except Exception as e:
            print(f"Failed to backup to SQLite: {e}")

    return data


# --------------------------------------------------
# 우산 알림 → 구글 캘린더 등록
# --------------------------------------------------

def _get_latest_base_time(now: datetime) -> tuple[str, str]:
    """현재 시각 기준 가장 최근 발표된 base_date, base_time 을 구한다."""
    # 발표시각 + 10분 뒤 API 제공 (예: 0200 발표 → 02:10부터 조회 가능)
    available_times = []
    for bt in KMA_BASE_TIMES:
        hour, minute = int(bt[:2]), int(bt[2:])
        available_at = now.replace(hour=hour, minute=minute + 10, second=0, microsecond=0)
        if available_at <= now:
            available_times.append(bt)

    if available_times:
        base_time = available_times[-1]
        base_date = now.strftime("%Y%m%d")
    else:
        # 오늘 아직 발표된 게 없으면 어제 마지막 발표(2300)
        yesterday = now - timedelta(days=1)
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from core.config import settings
from core.constants import KMA_SHORT_TERM_FORECAST_URL, KMA_BASE_TIMES
from core.database import insert_forecast_items
from core.weather_analyzer import analyze_umbrella_need
from core.google_calendar import add_umbrella_reminder
from core.exceptions import KMAApiException, get_kma_error_message
from .schemas import (
    ShortTermForecastRequest, KMAResponse,
    UmbrellaReminderRequest, UmbrellaReminderResponse,
)
from urllib.parse import unquote

app = FastAPI(title="Weather & Google Calendar API")


@app.get("/")
def read_root():
    return {"message": "API is running"}


# --------------------------------------------------
# 기상청 단기예보 조회
# --------------------------------------------------

def _fetch_forecast(base_date: str, base_time: str, nx: int, ny: int) -> list:
    """기상청 단기예보를 호출하고 item 리스트를 반환하는 내부 유틸"""
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
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": result_code,
                "message": f"기상청 API 에러: {error_description}",
                "raw_msg": header.get("resultMsg")
            }
        )

    # 응답 구조가 정상인지 추가 확인 (body 유무 등)
    if "body" not in data.get("response", {}):
         raise HTTPException(
            status_code=502,
            detail="기상청 API 응답 형식이 올바르지 않습니다. (body 누락)"
        )

    return data


@app.get("/api/weather/forecast", response_model=KMAResponse)
def get_short_term_forecast(params: ShortTermForecastRequest = Depends()):
    """단기예보 조회 (기존 엔드포인트)"""
    data = _fetch_forecast(params.base_date, params.base_time, params.nx, params.ny)

    # 응답받은 기상 정보를 SQLite에 백업
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if items:
        try:
            insert_forecast_items(items)
        except Exception as e:
            print(f"Failed to backup to SQLite: {e}")

    return data


# --------------------------------------------------
# 우산 알림 → 구글 캘린더 등록
# --------------------------------------------------

def _get_latest_base_time(now: datetime) -> tuple[str, str]:
    """현재 시각 기준 가장 최근 발표된 base_date, base_time 을 구한다."""
    # 발표시각 + 10분 뒤 API 제공 (예: 0200 발표 → 02:10부터 조회 가능)
    available_times = []
    for bt in KMA_BASE_TIMES:
        hour, minute = int(bt[:2]), int(bt[2:])
        available_at = now.replace(hour=hour, minute=minute + 10, second=0, microsecond=0)
        if available_at <= now:
            available_times.append(bt)

    if available_times:
        base_time = available_times[-1]
        base_date = now.strftime("%Y%m%d")
    else:
        # 오늘 아직 발표된 게 없으면 어제 마지막 발표(2300)
        yesterday = now - timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = "2300"

    return base_date, base_time


@app.post("/api/calendar/umbrella-reminder", response_model=UmbrellaReminderResponse)
def create_umbrella_reminder(req: UmbrellaReminderRequest):
    """
    현재 시점 기준 단기예보를 조회하여 우산 필요 여부를 판별하고,
    비가 오는 날에는 구글 캘린더에 '우산 챙기세요!' 종일 이벤트를 등록한다.
    """
    now = datetime.now()
    base_date, base_time = _get_latest_base_time(now)

    # 1) 단기예보 조회 (최대 4일치 데이터 수신)
    data = _fetch_forecast(base_date, base_time, req.nx, req.ny)
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    if items:
        try:
            insert_forecast_items(items)
        except Exception as e:
            print(f"Failed to backup to SQLite: {e}")

    # 2) 날짜별 우산 필요 여부 분석
    analysis = analyze_umbrella_need(items)

    # 3) 우산 필요한 날만 구글 캘린더에 이벤트 생성 (sync_calendar가 True일 때만)
    calendar_events = []
    if req.sync_calendar:
        if not req.access_token:
            raise HTTPException(status_code=401, detail="Google Access Token이 필요합니다.")
            
        for day in analysis:
            if day["need_umbrella"]:
                try:
                    event = add_umbrella_reminder(
                        date=day["date"],
                        message=f"강수 예보: {day['reason']}",
                        access_token=req.access_token,
                        summary=req.event_title,
                        notification_minutes=req.notification_minutes
                    )
                    calendar_events.append({
                        "date": day["date"],
                        "event_id": event.get("id", "N/A"),
                        "html_link": event.get("htmlLink")
                    })
                except Exception as e:
                    # 캘린더 등록 오류는 분석 결과에 지장을 주지 않도록 로깅만 하거나 에러를 던짐
                    print(f"Calendar Sync Error: {e}")
                    raise HTTPException(status_code=500, detail=f"Google Calendar Sync Failed: {str(e)}")

    message = "분석이 완료되었습니다."
    if req.sync_calendar:
        if calendar_events:
            message = f"총 {len(calendar_events)}개의 일정이 구글 캘린더에 성공적으로 등록되었습니다."
        else:
            message = "비 소식이 없어 캘린더에 일정을 등록하지 않았습니다."
    else:
        rainy_count = sum(1 for d in analysis if d["need_umbrella"])
        if rainy_count > 0:
            message = f"향후 4일 중 {rainy_count}일 비 소식이 있습니다. 캘린더에 등록하시겠습니까?"
        else:
            message = "향후 4일간 비 소식이 없습니다. 우산이 필요 없어요! ☀️"

    return UmbrellaReminderResponse(
        analysis=analysis,
        calendar_events=calendar_events,
        message=message,
    )
