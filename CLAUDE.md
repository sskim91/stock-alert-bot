# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Alert Bot - 주식 고점 대비 하락률과 Fear & Greed Index를 텔레그램으로 알려주는 자동화 봇. crontab 또는 텔레그램 봇 모드로 실행됩니다.

## Commands

```bash
# 의존성 설치 (uv 사용)
uv sync

# 단일 실행 (기본 1년 기준)
uv run python main.py

# 특정 기간으로 실행
uv run python main.py --period 6mo

# 텔레그램 봇 모드 (명령어 수신 대기)
uv run python main.py --bot

# 테스트 실행
uv run pytest

# 단일 테스트 파일 실행
uv run pytest tests/test_mdd.py

# 특정 테스트 함수 실행
uv run pytest tests/test_mdd.py::TestCalculateMdd::test_simple_case

# 린트 (ruff)
uv run ruff check .
uv run ruff format .
```

## Architecture

### Execution Modes
- **단일 실행 모드**: `main.py` → crontab용, 한 번 실행 후 종료
- **봇 모드**: `main.py --bot` → 텔레그램 명령어 대기 (polling)

### Data Flow
1. `main.py` - CLI 파싱 및 실행 모드 결정
2. `src/config.py` - 환경변수 로드 (ANALYSIS_PERIOD, TELEGRAM_* 등)
3. `src/stock/fetcher.py` - yfinance로 주가 데이터 수집
4. `src/stock/mdd.py` - 고점 대비 하락률 계산 및 분할매수 신호 판단
5. `src/indicators/fear_greed.py` - CNN Fear & Greed Index API 호출
6. `src/notifiers/telegram.py` - 비동기 메시지 전송 + 봇 명령어 핸들러

### Key Modules

**MDD 계산 (`src/stock/mdd.py`)**
- `calculate_mdd()`: 기간 내 최대 낙폭 계산
- `calculate_drawdown_from_peak()`: 고점 대비 현재 하락률
- `get_buy_signal()`: 하락률에 따른 분할매수 신호 (-10%: 1차, -20%: 2차, -30%: 3차)

**텔레그램 (`src/notifiers/telegram.py`)**
- `TelegramNotifier`: 메시지 전송 클래스 (async)
- `run_telegram_bot()`: 봇 모드 실행 (Application + CommandHandler)
- 지원 명령어: `/report [기간]`, `/status`, `/help`

### Configuration
- `.env` 파일에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 필수
- `ANALYSIS_PERIOD`: 분석 기간 (기본값: 1y)
- 유효한 기간: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

## Testing

pytest + pytest-asyncio 사용:
- `test_fetcher.py` - 주가 데이터 수집 테스트
- `test_mdd.py` - MDD 계산 로직 테스트
- `test_fear_greed.py` - Fear & Greed API 테스트
- `test_telegram.py` - 텔레그램 전송 테스트 (실제 API 호출하는 통합 테스트)
