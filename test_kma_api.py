# test_kma_api.py
import requests
from datetime import datetime

url = "http://127.0.0.1:8000/api/weather/forecast"
params = {
    "base_date": datetime.now().strftime("%Y%m%d"),
    "base_time": "1400",
    "nx": 55,
    "ny": 127
}

try:
    print(f"Testing API with params: {params}")
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result_code = data.get("response", {}).get("header", {}).get("resultCode")
        result_msg = data.get("response", {}).get("header", {}).get("resultMsg")
        print(f"KMA Result Code: {result_code}")
        print(f"KMA Result Msg: {result_msg}")
        
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        print(f"Items received: {len(items)}")
        if items:
            print("First item sample:", items[0])
    else:
        print("Error Response:", response.text)
except Exception as e:
    print(f"Test failed: {e}")
