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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_user_location(email: str, lat: float, lon: float):
    if not email:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, lat, lon, updated_at) 
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(email) DO UPDATE SET lat=excluded.lat, lon=excluded.lon, updated_at=CURRENT_TIMESTAMP
    ''', (email, lat, lon))
    conn.commit()
    conn.close()

def get_user_location(email: str):
    if not email:
        return None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT lat, lon FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"lat": row[0], "lon": row[1]}
    return None

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
