# SQL Injection 취약점과 Prepared Statement 방어 기법 탐구

## 1. 프로젝트 소개

이 프로젝트는 같은 로그인 기능을 두 가지 SQL 실행 방식으로 구현하여 차이를 관찰하는
교육용 로컬 웹 애플리케이션입니다.

- 취약한 방식: 사용자 입력을 문자열 연결로 SQL문에 직접 결합
- 안전한 방식: `?` placeholder와 Prepared Statement 사용
- 사용 기술: Python, Flask, SQLite, HTML, CSS
- 실행 범위: `127.0.0.1` 로컬 환경 전용

취약한 코드는 SQL Injection이 발생하는 원리를 확인하기 위해 의도적으로 포함했습니다.
실제 서비스 코드로 재사용하면 안 됩니다.

## 2. 파일 구조

```text
SQL--security/
├─ .github/
│  └─ workflows/
│     └─ test.yml
├─ app.py
├─ init_db.py
├─ requirements.txt
├─ requirements-dev.txt
├─ README.md
├─ TESTING.md
├─ CHANGELOG.md
├─ VERSION
├─ tests/
│  └─ test_app.py
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ vulnerable_login.html
│  ├─ safe_login.html
│  ├─ result.html
│  └─ about.html
└─ static/
   └─ style.css
```

`python init_db.py`를 실행하면 프로젝트 폴더에 `study.db`가 생성됩니다.

프로젝트 문서는 [테스트 안내](TESTING.md)와 [변경 기록](CHANGELOG.md)에서
추가로 확인할 수 있습니다.

## 3. 필요한 패키지 설치와 실행 방법

Python 3.10 이상 사용을 권장합니다.

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

Windows에서 `python` 명령이 동작하지 않으면 다음처럼 실행할 수 있습니다.

```bash
py -m pip install -r requirements.txt
py init_db.py
py app.py
```

웹 브라우저에서 다음 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

서버 종료는 실행 중인 터미널에서 `Ctrl+C`를 누릅니다.

### 자동 테스트 실행

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --cov=app --cov=init_db --cov-report=term-missing --cov-fail-under=80
```

테스트는 임시 SQLite 데이터베이스를 사용하므로 실습용 `study.db` 파일을 변경하지
않습니다. 자세한 내용은 `TESTING.md`에서 확인할 수 있습니다.

## 4. DB 초기화 방법

```bash
python init_db.py
```

이 명령은 이 프로젝트의 `study.db` 안에 있는 `users` 테이블을 새로 만들고 실습용
가상 계정 3개를 저장합니다. 다시 실행하면 기존 실습 데이터는 초기 상태로 돌아갑니다.

## 5. 테스트용 계정 정보

| id | username | password | role |
|---:|---|---|---|
| 1 | `admin` | `1234` | `administrator` |
| 2 | `user1` | `pass1` | `user` |
| 3 | `student` | `gcu1234` | `user` |

모든 정보는 학습을 위해 만든 가상의 값이며 실제 개인정보가 아닙니다.

이 예제에서는 SQL 처리 차이에 집중하기 위해 비밀번호를 평문으로 저장합니다.
**실제 서비스에서는 비밀번호를 절대로 평문으로 저장하지 말고 Argon2, bcrypt 같은
검증된 알고리즘으로 해시하여 저장해야 합니다.**

## 6. 취약한 방식과 안전한 방식 비교

### 취약한 로그인 방식

```python
query = (
    "SELECT * FROM users WHERE username = '"
    + username
    + "' AND password = '"
    + password
    + "'"
)
cursor.execute(query)
```

입력값과 SQL 문법이 하나의 문자열로 합쳐집니다. 입력에 따옴표나 SQL 주석 기호가
포함되면 원래 조건문의 구조가 바뀔 수 있습니다.

### Prepared Statement 방식

```python
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))
```

SQL문 구조와 사용자 입력값이 별도로 전달됩니다. 입력에 SQL처럼 보이는 문자가 있어도
데이터베이스는 전체 입력을 하나의 값으로 처리합니다.

| 비교 항목 | 문자열 연결 방식 | Prepared Statement 방식 |
|---|---|---|
| SQL문과 입력값 | 하나의 문자열로 결합 | 구조와 값이 분리됨 |
| 특수문자 처리 | SQL 문법으로 해석될 수 있음 | 파라미터 데이터로 처리 |
| SQL Injection 위험 | 높음 | 핵심 공격 경로 차단 |
| 실제 서비스 사용 | 사용 금지 | 기본적으로 사용해야 함 |
| 화면 표시 | 완성된 SQL문 | SQL문 구조와 파라미터를 따로 표시 |

## 7. 탐구 보고서에 활용할 수 있는 실험 절차

### 실험 1: 정상 로그인 비교

1. `/vulnerable` 페이지에서 `admin` / `1234`를 입력합니다.
2. 로그인이 성공하는지 확인하고 완성된 SQL문을 기록합니다.
3. `/safe` 페이지에서 같은 값을 입력합니다.
4. 로그인이 성공하는지 확인하고 SQL문 구조와 파라미터를 기록합니다.

예상 결과: 두 방식 모두 정상 로그인에 성공합니다.

### 실험 2: 잘못된 비밀번호 비교

1. 두 페이지에서 username은 `admin`, password는 `wrong-password`를 입력합니다.
2. 로그인 결과를 기록합니다.

예상 결과: 두 방식 모두 로그인에 실패합니다.

### 실험 3: 로컬 환경에서 SQL 구조 변조 관찰

아래 입력은 반드시 이 프로젝트의 로컬 페이지에서만 사용합니다.

```text
username: admin' --
password: wrong-password
```

username 값 마지막에 공백 한 칸을 포함해 입력합니다.

1. `/vulnerable` 페이지에 위 값을 입력합니다.
2. 결과 화면에서 실제 SQL문을 확인합니다.
3. username 뒤의 `--`로 인해 뒤쪽 password 조건이 주석으로 처리되는지 관찰합니다.
4. `/safe` 페이지에 완전히 같은 값을 입력합니다.
5. SQL문은 `?` 구조를 유지하고 입력값은 별도 파라미터가 되는지 확인합니다.

예상 결과:

- 취약한 방식: password가 틀려도 `admin` 계정으로 로그인될 수 있음
- Prepared Statement 방식: 입력 전체를 username 데이터로 비교하므로 로그인 실패

### 보고서에 기록할 항목

- 실험 목적과 가설
- 각 실험에서 사용한 입력값
- 취약한 방식에서 완성된 SQL문
- 안전한 방식의 SQL문 구조와 파라미터
- 로그인 성공 또는 실패 결과
- SQL문 구조가 변했는지 여부
- Prepared Statement가 입력을 데이터로 처리한다는 해석

## 8. 실험 전/후 비교표

| 관찰 항목 | 실험 전 예상 | 취약한 방식 실험 후 | Prepared Statement 실험 후 |
|---|---|---|---|
| 정상 계정 입력 | 로그인 성공 | 성공 | 성공 |
| 잘못된 비밀번호 | 로그인 실패 | 실패 | 실패 |
| SQL 형태의 특수 입력 | 방식에 따라 결과가 다를 것 | 입력이 SQL 구조에 영향을 줌 | `?` 구조가 유지됨 |
| password 조건 | 항상 검사될 것으로 예상 | 주석 처리되어 무시될 수 있음 | 독립된 파라미터로 계속 검사됨 |
| 입력값의 역할 | 단순한 로그인 데이터 | SQL 문법 일부가 될 수 있음 | 끝까지 데이터로 처리됨 |
| 결론 | 방어 방식의 차이를 확인할 필요 | 문자열 연결은 위험함 | Prepared Statement가 구조 변조를 방지함 |

## 9. 실제 서비스에서 필요한 추가 보안 대책

Prepared Statement만 적용했다고 모든 로그인 보안 문제가 해결되는 것은 아닙니다.

- 모든 SQL 실행에 Prepared Statement 사용
- 입력값의 길이, 형식, 허용 범위 검증
- 상세한 DB 에러 메시지의 사용자 화면 노출 제한
- DB 계정에 필요한 최소 권한만 부여
- 비밀번호를 안전한 해시 방식으로 저장
- 로그인 시도 횟수 제한과 지연 적용
- 보안 로그와 이상 로그인 시도 모니터링
- 운영 환경에서 디버그 모드 비활성화

## 10. 주의사항

> 이 프로젝트는 보안 학습을 위한 로컬 실습용 예제입니다. 실제 웹사이트나 허가받지 않은 시스템에 SQL Injection을 시도하면 법적 문제가 발생할 수 있습니다. 반드시 본인이 만든 로컬 실습 환경에서만 사용해야 합니다.

- Flask 서버는 `127.0.0.1`에만 바인딩되며 외부 공개용으로 구성하지 않았습니다.
- 취약한 `/vulnerable` 코드는 교육 목적의 의도적인 취약점입니다.
- 이 프로젝트를 인터넷에 배포하거나 공용 서버에서 실행하지 마세요.
- 실제 계정, 실제 비밀번호, 개인정보를 데이터베이스에 넣지 마세요.
