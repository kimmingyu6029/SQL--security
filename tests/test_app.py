"""교육용 로그인 애플리케이션의 핵심 동작을 검증한다."""

import sqlite3
from contextlib import closing

import pytest

import app as app_module
import init_db as init_db_module


DEMO_USERS = [
    ("admin", "1234", "administrator"),
    ("user1", "pass1", "user"),
    ("student", "gcu1234", "user"),
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """각 테스트가 독립된 임시 SQLite DB를 사용하도록 준비한다."""
    database_path = tmp_path / "test-study.db"

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            DEMO_USERS,
        )
        connection.commit()

    monkeypatch.setattr(app_module, "DATABASE_PATH", database_path)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("route", ["/", "/vulnerable", "/safe", "/about"])
def test_pages_are_available(client, route):
    response = client.get(route)

    assert response.status_code == 200


@pytest.mark.parametrize("route", ["/vulnerable", "/safe"])
def test_normal_account_can_log_in(client, route):
    response = client.post(
        route,
        data={"username": "admin", "password": "1234"},
    )
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "result-status status-success" in page
    assert "<code>admin</code>" in page


@pytest.mark.parametrize("route", ["/vulnerable", "/safe"])
def test_wrong_password_is_rejected(client, route):
    response = client.post(
        route,
        data={"username": "admin", "password": "wrong-password"},
    )

    assert "result-status status-fail" in response.get_data(as_text=True)


def test_vulnerable_login_demonstrates_query_structure_change(client):
    response = client.post(
        "/vulnerable",
        data={"username": "admin' -- ", "password": "wrong-password"},
    )
    page = response.get_data(as_text=True)

    assert "result-status status-success" in page
    assert "admin&#39; --" in page


def test_prepared_statement_treats_same_input_as_data(client):
    response = client.post(
        "/safe",
        data={"username": "admin' -- ", "password": "wrong-password"},
    )
    page = response.get_data(as_text=True)

    assert "result-status status-fail" in page
    assert "username = ? AND password = ?" in page
    assert "admin&#39; --" in page


def test_missing_database_shows_initialization_guide(tmp_path, monkeypatch):
    missing_database = tmp_path / "missing.db"
    monkeypatch.setattr(app_module, "DATABASE_PATH", missing_database)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/safe",
            data={"username": "admin", "password": "1234"},
        )

    assert response.status_code == 503
    assert "python init_db.py" in response.get_data(as_text=True)


def test_database_initialization_creates_demo_users(tmp_path, monkeypatch):
    database_path = tmp_path / "initialized.db"
    monkeypatch.setattr(init_db_module, "DATABASE_PATH", database_path)

    init_db_module.initialize_database()

    with closing(sqlite3.connect(database_path)) as connection:
        users = connection.execute(
            "SELECT username, password, role FROM users ORDER BY id"
        ).fetchall()

    assert users == DEMO_USERS
