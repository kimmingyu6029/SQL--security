"""SQL Injection과 Prepared Statement를 비교하는 교육용 Flask 애플리케이션."""

import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "study.db"

app = Flask(__name__)


def get_db_connection():
    """프로젝트 폴더의 SQLite 데이터베이스에 연결한다."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def database_not_ready_result(method, username, password, query, parameters=None):
    """DB를 초기화하지 않았을 때 이해하기 쉬운 안내 화면을 반환한다."""
    return (
        render_template(
            "result.html",
            page_title="데이터베이스 초기화 필요",
            method=method,
            username=username,
            password=password,
            query=query,
            parameters=parameters,
            success=False,
            user=None,
            database_error=(
                "study.db 파일이 없습니다. 터미널에서 python init_db.py를 먼저 실행하세요."
            ),
            analysis="로그인 실험 전에 실습용 users 테이블을 생성해야 합니다.",
        ),
        503,
    )


@app.route("/")
def index():
    """프로젝트 소개와 각 실습 페이지로 이동하는 메인 화면."""
    return render_template("index.html", page_title="SQL Injection 비교 실습")


@app.route("/vulnerable", methods=["GET", "POST"])
def vulnerable_login():
    """문자열 연결 방식으로 작성한 의도적으로 취약한 로그인 예제."""
    if request.method == "GET":
        return render_template(
            "vulnerable_login.html", page_title="취약한 로그인 실습"
        )

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # 교육용 취약 코드: 사용자 입력을 SQL문에 직접 연결한다.
    # 이 방식은 SQL Injection에 취약하므로 실제 서비스에서 절대 사용하면 안 된다.
    query = (
        "SELECT id, username, password, role FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password
        + "'"
    )

    if not DATABASE_PATH.exists():
        return database_not_ready_result(
            "취약한 방식", username, password, query
        )

    database_error = None
    user = None

    try:
        with closing(get_db_connection()) as connection:
            user = connection.execute(query).fetchone()
    except sqlite3.Error:
        # 상세 DB 오류나 내부 구조는 화면에 노출하지 않는다.
        database_error = (
            "SQL 실행 오류가 발생했습니다. 입력으로 인해 SQL문 구성이 "
            "잘못되었을 수 있습니다."
        )

    return render_template(
        "result.html",
        page_title="취약한 방식 실행 결과",
        method="취약한 방식",
        username=username,
        password=password,
        query=query,
        parameters=None,
        success=user is not None,
        user=user,
        database_error=database_error,
        analysis=(
            "사용자 입력값이 SQL문에 직접 결합되어 SQL문의 구조에 영향을 줄 수 있습니다."
        ),
    )


@app.route("/safe", methods=["GET", "POST"])
def safe_login():
    """Prepared Statement의 placeholder를 사용하는 안전한 로그인 예제."""
    if request.method == "GET":
        return render_template("safe_login.html", page_title="안전한 로그인 실습")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # SQL문 구조와 사용자 입력을 분리한다.
    query = (
        "SELECT id, username, password, role "
        "FROM users WHERE username = ? AND password = ?"
    )
    parameters = (username, password)

    if not DATABASE_PATH.exists():
        return database_not_ready_result(
            "Prepared Statement 방식",
            username,
            password,
            query,
            parameters,
        )

    database_error = None
    user = None

    try:
        with closing(get_db_connection()) as connection:
            # ? placeholder에 값이 별도의 데이터로 전달된다.
            user = connection.execute(query, parameters).fetchone()
    except sqlite3.Error:
        # 실제 서비스처럼 상세 DB 오류는 화면에 노출하지 않는다.
        database_error = "데이터베이스 처리 중 오류가 발생했습니다."

    return render_template(
        "result.html",
        page_title="Prepared Statement 실행 결과",
        method="Prepared Statement 방식",
        username=username,
        password=password,
        query=query,
        parameters=parameters,
        success=user is not None,
        user=user,
        database_error=database_error,
        analysis=(
            "SQL문 구조와 사용자 입력값이 분리되어 입력값이 SQL 명령어가 아닌 "
            "데이터로 처리됩니다."
        ),
    )


@app.route("/about")
def about():
    """보고서에 참고할 수 있는 핵심 이론과 추가 보안 대책."""
    return render_template("about.html", page_title="실험 설명")


if __name__ == "__main__":
    # 외부 네트워크에 공개하지 않고 이 컴퓨터에서만 접속할 수 있게 실행한다.
    app.run(host="127.0.0.1", port=5000, debug=False)
