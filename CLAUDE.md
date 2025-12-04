# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Alert Bot - 주식 고점 대비 하락률과 Fear & Greed Index를 텔레그램으로 알려주는 봇. 봇 모드로 실행하면 스케줄러 + 명령어 응답을 동시에 처리합니다.

## Commands

```bash
# 의존성 설치 (uv 사용)
uv sync

# 봇 모드 실행 (권장 - 스케줄러 + 명령어 대기)
uv run python main.py --bot

# 단일 실행 (1회성)
uv run python main.py
uv run python main.py --period 6mo

# 테스트
uv run pytest
uv run pytest tests/test_mdd.py
uv run pytest tests/test_mdd.py::TestCalculateMdd::test_simple_case

# 린트
uv run ruff check .
uv run ruff format .
```

## Architecture

### Execution Modes
- **봇 모드** (`--bot`): 텔레그램 polling + JobQueue 스케줄러 (ALERT_TIME에 자동 전송)
- **단일 실행**: 1회 리포트 전송 후 종료

### Data Flow
1. `main.py` - CLI 파싱, 실행 모드 결정
2. `src/config.py` - 환경변수 로드 (TELEGRAM_*, ANALYSIS_PERIOD, ALERT_TIME)
3. `src/stock/fetcher.py` - yfinance로 주가 데이터 수집
4. `src/stock/mdd.py` - 고점 대비 하락률 계산, 분할매수 신호 (-10%: 1차, -20%: 2차, -30%: 3차)
5. `src/indicators/fear_greed.py` - CNN Fear & Greed Index API 호출
6. `src/notifiers/telegram.py` - 메시지 전송 + 봇 명령어 + 스케줄러

### Telegram Bot Commands
- `/report`, `/report6mo`, `/report3mo` - 리포트 요청
- `/status` - 현재 설정 확인
- `/help` - 도움말
- Bot Menu (`set_my_commands`)로 고정 명령어 등록

### Key Implementation Details
- `_collect_report_data()`: Fear & Greed + 주식 데이터를 `asyncio.gather`로 병렬 수집
- `_parse_alert_time()`: `09:00` 또는 `0900` 형식 모두 지원
- `post_init()`: 봇 시작 시 BotCommand 메뉴 등록

## Configuration

`.env` 파일 필수:
```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
ANALYSIS_PERIOD=1y
ALERT_TIME=09:00
```

유효한 기간: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

## Testing

pytest + pytest-asyncio 사용. `test_telegram.py`는 실제 API를 호출하는 통합 테스트.
