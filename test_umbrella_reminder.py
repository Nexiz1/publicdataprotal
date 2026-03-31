# test_umbrella_reminder.py
import requests

url = "http://127.0.0.1:8000/api/calendar/umbrella-reminder"
payload = {
    "nx": 55,
    "ny": 127
}

try:
    print(f"Testing Umbrella Reminder with payload: {payload}")
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Analysis Summary:")
        for day in data.get("analysis", []):
            print(f" - {day['date']}: Need Umbrella? {day['need_umbrella']} (POP: {day['max_pop']}%, Reason: {day['reason']})")
        
        events = data.get("calendar_events", [])
        print(f"Calendar events created: {len(events)}")
        for ev in events:
            print(f"   * {ev['date']}: {ev['html_link']}")
            
        print(f"Final Message: {data.get('message')}")
    else:
        print("Error Response:", response.text)
except Exception as e:
    print(f"Test failed: {e}")
