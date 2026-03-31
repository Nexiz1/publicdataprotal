# core/constants.py

# 기상청 단기예보 API
KMA_SHORT_TERM_FORECAST_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

# 단기예보 발표시각 (1일 8회)
KMA_BASE_TIMES = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]

# 구글 캘린더 API
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 우산 판별 기준
UMBRELLA_POP_THRESHOLD = 50  # 강수확률(%) 이상이면 우산 필요
UMBRELLA_PTY_RAIN_CODES = ["1", "2", "4", "5", "6"]  # 비/비눈/소나기/빗방울/빗방울눈날림
