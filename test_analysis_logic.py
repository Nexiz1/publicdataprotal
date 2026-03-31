# test_analysis_logic.py
from core.weather_analyzer import analyze_umbrella_need

# Mock data with rain (PTY=1) and high POP (80%)
mock_items = [
    {"fcstDate": "20260328", "fcstTime": "1000", "category": "POP", "fcstValue": "80", "nx": 55, "ny": 127},
    {"fcstDate": "20260328", "fcstTime": "1000", "category": "PTY", "fcstValue": "1", "nx": 55, "ny": 127},
    {"fcstDate": "20260329", "fcstTime": "1200", "category": "POP", "fcstValue": "10", "nx": 55, "ny": 127},
    {"fcstDate": "20260329", "fcstTime": "1200", "category": "PTY", "fcstValue": "0", "nx": 55, "ny": 127},
]

results = analyze_umbrella_need(mock_items)
for res in results:
    print(f"Date: {res['date']}, Umbrella: {res['need_umbrella']}, Reason: {res['reason']}")

assert results[0]['need_umbrella'] == True
assert results[1]['need_umbrella'] == False
print("Analysis logic test passed!")
