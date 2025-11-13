# src/infrastructure/database/db_manager.py
"""SQLite 데이터베이스 관리 모듈"""
import sqlite3
import os
from pathlib import Path

# 데이터베이스 파일 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "database", "tour_data.db")

def get_connection():
    """SQLite 데이터베이스 연결을 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 컬럼 이름으로 접근 가능하게
    return conn

def initialize_database():
    """데이터베이스 테이블을 초기화합니다."""
    conn = get_connection()
    cursor = conn.cursor()

    # 축제 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS festivals (
            contentid INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            eventstartdate TEXT,
            eventenddate TEXT,
            addr1 TEXT,
            addr2 TEXT,
            areacode INTEGER,
            cat1 TEXT,
            cat2 TEXT,
            cat3 TEXT,
            contenttypeid INTEGER,
            mapx REAL,
            mapy REAL,
            tel TEXT,
            firstimage TEXT,
            firstimage2 TEXT,
            overview TEXT,
            playtime TEXT,
            eventplace TEXT,
            sponsor1 TEXT,
            sponsor1tel TEXT,
            sponsor2 TEXT,
            sponsor2tel TEXT,
            eventhomepage TEXT,
            usetimefestival TEXT,
            festivalgrade TEXT,
            placeinfo TEXT,
            subevent TEXT,
            program TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 문화시설 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS culture_facilities (
            contentid INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            addr1 TEXT,
            addr2 TEXT,
            areacode INTEGER,
            cat1 TEXT,
            cat2 TEXT,
            cat3 TEXT,
            contenttypeid INTEGER,
            mapx REAL,
            mapy REAL,
            tel TEXT,
            firstimage TEXT,
            firstimage2 TEXT,
            overview TEXT,
            usefee TEXT,
            infocenterculture TEXT,
            usetimeculture TEXT,
            restdateculture TEXT,
            parkingculture TEXT,
            chkcreditcardculture TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 여행코스 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travel_courses (
            contentid INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            addr1 TEXT,
            addr2 TEXT,
            areacode INTEGER,
            cat1 TEXT,
            cat2 TEXT,
            cat3 TEXT,
            contenttypeid INTEGER,
            mapx REAL,
            mapy REAL,
            firstimage TEXT,
            firstimage2 TEXT,
            overview TEXT,
            distance TEXT,
            schedule TEXT,
            taketime TEXT,
            theme TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 제목 검색을 위한 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_festivals_title ON festivals(title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_culture_title ON culture_facilities(title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_courses_title ON travel_courses(title)')

    conn.commit()
    conn.close()

    print(f"[OK] 데이터베이스 초기화 완료: {DB_PATH}")

if __name__ == "__main__":
    initialize_database()
