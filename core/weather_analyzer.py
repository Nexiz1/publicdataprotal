# core/weather_analyzer.py
from datetime import datetime, timedelta
from typing import List, Dict
from core.constants import UMBRELLA_POP_THRESHOLD, UMBRELLA_PTY_RAIN_CODES


def analyze_umbrella_need(items: List[Dict]) -> List[Dict]:
    """
    단기예보 아이템 목록에서 날짜별로 우산이 필요한지 판별한다.

    판별 기준:
      - 강수확률(POP)이 UMBRELLA_POP_THRESHOLD(50%) 이상인 시간이 하루 중 하나라도 있으면 우산 필요
      - 강수형태(PTY)가 비/눈 관련 코드이면 우산 필요

    Returns:
        [{"date": "2026-03-27", "need_umbrella": True, "reason": "...최대 강수확률 80%"}, ...]
    """
    # 날짜별로 그룹핑
    daily: Dict[str, Dict] = {}

    for item in items:
        fcst_date = item.get("fcstDate", "")
        category = item.get("category", "")
        value = item.get("fcstValue", "")

        if fcst_date not in daily:
            daily[fcst_date] = {"max_pop": 0, "has_rain_pty": False, "rain_times": []}

        if category == "POP":
            try:
                pop = int(value)
                if pop > daily[fcst_date]["max_pop"]:
                    daily[fcst_date]["max_pop"] = pop
            except ValueError:
                pass

        if category == "PTY" and value in UMBRELLA_PTY_RAIN_CODES:
            daily[fcst_date]["has_rain_pty"] = True
            fcst_time = item.get("fcstTime", "")
            daily[fcst_date]["rain_times"].append(fcst_time)

    results = []
    for raw_date, info in sorted(daily.items()):
        need = info["max_pop"] >= UMBRELLA_POP_THRESHOLD or info["has_rain_pty"]

        reasons = []
        if info["max_pop"] >= UMBRELLA_POP_THRESHOLD:
            reasons.append(f"최대 강수확률 {info['max_pop']}%")
        if info["has_rain_pty"]:
            times_str = ", ".join(info["rain_times"][:5])
            reasons.append(f"강수 예보 시간대: {times_str}")

        # YYYYMMDD -> YYYY-MM-DD
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date

        results.append({
            "date": formatted_date,
            "need_umbrella": need,
            "max_pop": info["max_pop"],
            "reason": ", ".join(reasons) if reasons else "강수 가능성 낮음",
        })

    return results
