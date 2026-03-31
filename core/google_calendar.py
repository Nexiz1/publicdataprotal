# core/google_calendar.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
def get_calendar_service(access_token: str):
    """Google Calendar API 서비스 객체를 반환 (동적 토큰 기반)"""
    creds = Credentials(token=access_token)
    return build("calendar", "v3", credentials=creds)


def find_existing_umbrella_event(service, date: str, summary: str):
    time_min = date + "T00:00:00Z"
    time_max = date + "T23:59:59Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        q=summary,
        singleEvents=True,
    ).execute()
    
    for event in events_result.get("items", []):
        if event.get("summary") == summary:
            return event
    return None

def upsert_umbrella_event(date: str, message: str, access_token: str, summary: str = "☂️ 우산 챙기세요!", notification_minutes: int = 720) -> dict:
    """
    구글 캘린더에 우산 알림 종일 이벤트를 추가하거나 최신화(업데이트)한다.
    """
    service = get_calendar_service(access_token)

    event_body = {
        "summary": summary,
        "description": message,
        "start": {"date": date},
        "end": {"date": date},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": notification_minutes},
            ],
        },
    }

    existing_event = find_existing_umbrella_event(service, date, summary)
    
    if existing_event:
        return service.events().update(
            calendarId="primary",
            eventId=existing_event["id"],
            body=event_body
        ).execute()
    else:
        return service.events().insert(
            calendarId="primary",
            body=event_body
        ).execute()

def delete_umbrella_event_if_exists(date: str, access_token: str, summary: str = "☂️ 우산 챙기세요!") -> bool:
    """
    비가 오지 않도록 예보가 바뀌었다면 기존 캘린더 일정을 삭제한다.
    """
    service = get_calendar_service(access_token)
    existing_event = find_existing_umbrella_event(service, date, summary)
    if existing_event:
        service.events().delete(
            calendarId="primary",
            eventId=existing_event["id"]
        ).execute()
        return True
    return False
