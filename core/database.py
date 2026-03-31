# core/database.py
import sqlite3

DB_PATH = "data/weather_backup.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecast_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baseDate TEXT,
            baseTime TEXT,
            category TEXT,
            fcstDate TEXT,
            fcstTime TEXT,
            fcstValue TEXT,
            nx INTEGER,
            ny INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_forecast_items(items: list):
    if not items:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        INSERT INTO forecast_items (baseDate, baseTime, category, fcstDate, fcstTime, fcstValue, nx, ny)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    values = [
        (
            item.get("baseDate"),
            item.get("baseTime"),
            item.get("category"),
            item.get("fcstDate"),
            item.get("fcstTime"),
            item.get("fcstValue"),
            item.get("nx"),
            item.get("ny")
        )
        for item in items
    ]
    
    cursor.executemany(query, values)
    conn.commit()
    conn.close()

# 모듈 로드 시 테이블 자동 생성 (없을 경우)
init_db()
