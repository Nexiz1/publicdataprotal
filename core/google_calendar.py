# core/google_calendar.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from core.config import settings
from core.constants import GOOGLE_CALENDAR_SCOPES


def get_google_credentials() -> Credentials:
    """Google OAuth 2.0 인증 수행 및 토큰 반환"""
    creds = None
    token_path = settings.GOOGLE_TOKEN_PATH

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, GOOGLE_CALENDAR_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_calendar_service():
    """Google Calendar API 서비스 객체를 반환"""
    creds = get_google_credentials()
    return build("calendar", "v3", credentials=creds)


def add_umbrella_reminder(date: str, message: str, summary: str = "☂️ 우산 챙기세요!", notification_minutes: int = 720) -> dict:
    """
    구글 캘린더에 우산 알림 종일 이벤트를 추가한다.

    Args:
        date: 이벤트 날짜 (YYYY-MM-DD)
        message: 이벤트 설명
        summary: 이벤트 제목
        notification_minutes: 알림 시간 (분 전)
    Returns:
        생성된 이벤트 정보 dict
    """
    service = get_calendar_service()

    event = {
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

    created_event = (
        service.events()
        .insert(calendarId="primary", body=event)
        .execute()
    )
    return created_event
