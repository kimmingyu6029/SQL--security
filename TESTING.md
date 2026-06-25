# 테스트 안내

이 프로젝트는 `pytest`와 Flask 테스트 클라이언트를 사용합니다. 테스트마다 임시 SQLite
데이터베이스를 만들어 실행하므로 실제 `study.db` 파일은 변경하지 않습니다.

## 실행 방법

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --cov=app --cov=init_db --cov-report=term-missing --cov-fail-under=80
```

## 검증 범위

- 메인, 취약 로그인, 안전 로그인, 실험 설명 페이지 응답
- 정상 계정 로그인
- 잘못된 비밀번호 거부
- 취약한 문자열 연결 방식의 교육용 SQL 구조 변조 재현
- Prepared Statement에서 동일 입력을 데이터로 처리하는지 확인
- 데이터베이스를 초기화하지 않았을 때 안내 화면 표시
- 데이터베이스 초기화 시 가상 계정 3개 생성

새로운 라우트나 조건 분기를 추가하면 해당 성공 경로와 실패 경로를 함께 테스트합니다.
