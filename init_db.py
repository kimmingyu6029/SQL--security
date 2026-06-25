"""교육용 SQLite 데이터베이스를 초기화하는 스크립트."""

import sqlite3
from contextlib import closing
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "study.db"

DEMO_USERS = [
    ("admin", "1234", "administrator"),
    ("user1", "pass1", "user"),
    ("student", "gcu1234", "user"),
]


def initialize_database():
    """users 테이블을 새로 만들고 가상의 실습 계정을 저장한다."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        cursor = connection.cursor()

        # 이 프로젝트 전용 DB만 초기화한다.
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )

        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            DEMO_USERS,
        )
        connection.commit()

    print(f"데이터베이스 초기화 완료: {DATABASE_PATH}")
    print(f"실습용 계정 {len(DEMO_USERS)}개가 생성되었습니다.")


if __name__ == "__main__":
    initialize_database()
