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
            refresh_token TEXT,
            sync_enabled INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN refresh_token TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN sync_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column might already exist

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

def save_user_refresh_token(email: str, refresh_token: str):
    if not email or not refresh_token:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET refresh_token = ? WHERE email = ?
    ''', (refresh_token, email))
    conn.commit()
    conn.close()

def save_user_sync_preference(email: str, is_enabled: bool):
    if not email:
        return
    val = 1 if is_enabled else 0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET sync_enabled = ? WHERE email = ?', (val, email))
    conn.commit()
    conn.close()

def get_user_sync_preference(email: str) -> bool:
    if not email:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT sync_enabled FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == 1:
        return True
    return False

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

def get_all_users_with_tokens():
    """백그라운드 스케줄러를 위해 리프레시 토큰이 있는 모든 유저 정보를 반환"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT email, lat, lon, refresh_token FROM users WHERE refresh_token IS NOT NULL AND sync_enabled = 1')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
