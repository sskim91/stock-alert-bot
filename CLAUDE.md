# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Alert Bot - 매일 주식 MDD(Maximum Drawdown)와 Fear & Greed Index를 텔레그램으로 알려주는 자동화 봇. crontab을 통해 정해진 시간에 실행됩니다.

## Commands

```bash
# 의존성 설치 (uv 사용)
uv sync

# 봇 실행
uv run python main.py

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

### Data Flow
1. `main.py` - crontab에서 호출되는 진입점. 모든 모듈을 통합하여 실행
2. `src/stock/fetcher.py` - yfinance로 주가 데이터 수집 (52주 데이터)
3. `src/stock/mdd.py` - 고점 대비 하락률 계산 및 분할매수 신호 판단
4. `src/indicators/fear_greed.py` - CNN Fear & Greed Index API 호출
5. `src/notifiers/telegram.py` - 비동기(async) 텔레그램 메시지 전송

### Key Modules

**MDD 계산 (`src/stock/mdd.py`)**
- `calculate_mdd()`: 기간 내 최대 낙폭 계산
- `calculate_drawdown_from_peak()`: 52주 고점 대비 현재 하락률
- `get_buy_signal()`: 하락률에 따른 분할매수 신호 (-10%: 1차, -20%: 2차, -30%: 3차)

**텔레그램 알림 (`src/notifiers/telegram.py`)**
- python-telegram-bot 라이브러리 사용
- `async/await` 패턴으로 비동기 메시지 전송
- `send_daily_report()`로 포맷된 리포트 전송

### Configuration
- `.env` 파일에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 설정 필요
- `src/config.py`에서 환경변수 로드 및 관심 종목 설정 (TSLA, SCHD, SCHG)

## Testing

pytest 사용. 각 모듈별 테스트 파일이 `tests/` 디렉토리에 존재:
- `test_fetcher.py` - 주가 데이터 수집 테스트
- `test_mdd.py` - MDD 계산 로직 테스트
- `test_fear_greed.py` - Fear & Greed API 테스트
- `test_telegram.py` - 텔레그램 전송 테스트 (pytest-asyncio 사용)
