from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 기상청 단기예보 Request / Response
# ==========================================

class ShortTermForecastRequest(BaseModel):
    pageNo: int = Field(default=1, description="페이지 번호")
    numOfRows: int = Field(default=1000, description="한 페이지 결과 수")
    dataType: str = Field(default="JSON", description="응답자료형식 (XML/JSON)")
    base_date: str = Field(..., example="20241128", description="발표일자 (YYYYMMDD)")
    base_time: str = Field(..., example="0500", description="발표시각 (HHMM)")
    nx: int = Field(..., example=55, description="예보지점 X 좌표")
    ny: int = Field(..., example=127, description="예보지점 Y 좌표")

class ForecastItem(BaseModel):
    baseDate: str
    baseTime: str
    category: str
    fcstDate: str
    fcstTime: str
    fcstValue: str
    nx: int
    ny: int

class ForecastItemsSummary(BaseModel):
    item: List[ForecastItem] = []

class ForecastBody(BaseModel):
    dataType: str
    items: ForecastItemsSummary
    pageNo: int
    numOfRows: int
    totalCount: int

class ForecastHeader(BaseModel):
    resultCode: str
    resultMsg: str

class ForecastResponseData(BaseModel):
    header: ForecastHeader
    body: Optional[ForecastBody] = None

class KMAResponse(BaseModel):
    response: ForecastResponseData

# ==========================================
# 우산 알림 / 구글 캘린더 연동
# ==========================================

class UmbrellaReminderRequest(BaseModel):
    nx: int = Field(..., example=55, description="예보지점 X 좌표")
    ny: int = Field(..., example=127, description="예보지점 Y 좌표")
    # 커스텀 옵션 (Optional)
    event_title: Optional[str] = Field(default="☂️ 우산 챙기세요!", description="커스텀 이벤트 제목")
    notification_minutes: Optional[int] = Field(default=720, description="알림 시간 (분 전, 기본 12시간)")
    sync_calendar: bool = Field(default=False, description="구글 캘린더 등록 여부")

class DailyUmbrellaResult(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    need_umbrella: bool = Field(..., description="우산 필요 여부")
    max_pop: int = Field(..., description="최대 강수확률(%)")
    reason: str = Field(..., description="판별 사유")

class CalendarEventResponse(BaseModel):
    date: str
    event_id: str
    html_link: str

class UmbrellaReminderResponse(BaseModel):
    analysis: List[DailyUmbrellaResult]
    calendar_events: List[CalendarEventResponse] = []
    message: str
