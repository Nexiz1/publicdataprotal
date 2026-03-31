# core/google_calendar.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from core.config import settings
from core.constants import GOOGLE_CALENDAR_SCOPES


def get_calendar_service(access_token: str):
    """Google Calendar API 서비스 객체를 반환 (동적 토큰 기반)"""
    creds = Credentials(token=access_token)
    return build("calendar", "v3", credentials=creds)


def add_umbrella_reminder(date: str, message: str, access_token: str, summary: str = "☂️ 우산 챙기세요!", notification_minutes: int = 720) -> dict:
    """
    구글 캘린더에 우산 알림 종일 이벤트를 추가한다.

    Args:
        date: 이벤트 날짜 (YYYY-MM-DD)
        message: 이벤트 설명
        access_token: 대상 사용자의 OAuth Web Access Token
        summary: 이벤트 제목
        notification_minutes: 알림 시간 (분 전)
    Returns:
        생성된 이벤트 정보 dict
    """
    service = get_calendar_service(access_token)

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
