"""Stock Alert Bot - 메인 실행 파일

이 파일은 crontab에서 실행됩니다.
모든 모듈을 통합하여 일일 주식 리포트를 텔레그램으로 전송합니다.

사용법:
    # 직접 실행
    uv run python main.py

    # crontab 설정 (매일 오전 9시)
    0 9 * * * cd /home/ubuntu/dev/stock-alert-bot && /home/ubuntu/.local/bin/uv run python main.py >> /home/ubuntu/logs/stock-alert.log 2>&1
"""

import asyncio
from datetime import datetime

# 우리가 만든 모듈들
from src.config import Config
from src.stock.fetcher import fetch_stock_data
from src.stock.mdd import calculate_drawdown_from_peak, get_buy_signal
from src.indicators.fear_greed import get_fear_greed_index
from src.notifiers.telegram import TelegramNotifier


# 분석 기간 설정 (52주 = 1년)
ANALYSIS_PERIOD = "1y"


def collect_stock_data(symbols: list[str]) -> list[dict]:
    """
    각 종목의 고점 대비 하락률과 매수 신호를 수집합니다.

    Args:
        symbols: 종목 심볼 리스트 (예: ["TSLA", "SCHD", "SCHG"])

    Returns:
        [
            {
                "symbol": "TSLA",
                "peak_price": 500.0,      # 52주 최고가
                "current_price": 400.0,   # 현재가
                "drawdown_pct": -20.0,    # 고점 대비 하락률
                "buy_signal": "2차 매수 (비중 확대)",  # 매수 신호
            },
            ...
        ]
    """
    results = []

    for symbol in symbols:
        print(f"  - {symbol} 데이터 수집 중...")

        # 52주(1년) 데이터 가져오기
        data = fetch_stock_data(symbol, period=ANALYSIS_PERIOD)

        if data.empty:
            print(f"    ⚠️ {symbol}: 데이터 없음")
            continue

        # 고점 대비 하락률 계산
        drawdown_data = calculate_drawdown_from_peak(data["Close"])

        # 매수 신호 확인
        buy_signal = get_buy_signal(drawdown_data["drawdown_pct"])

        results.append({
            "symbol": symbol,
            "peak_price": drawdown_data["peak_price"],
            "current_price": drawdown_data["current_price"],
            "drawdown_pct": drawdown_data["drawdown_pct"],
            "buy_signal": buy_signal,
        })

        # 로그 출력
        signal_text = f" → {buy_signal}" if buy_signal else " → 관망"
        print(f"    ✓ {symbol}: {drawdown_data['drawdown_pct']:.1f}% from peak (${drawdown_data['current_price']:.2f}){signal_text}")

    return results


async def send_report(notifier: TelegramNotifier) -> bool:
    """
    일일 리포트를 수집하고 텔레그램으로 전송합니다.

    Returns:
        성공 여부
    """
    print("\n" + "=" * 50)
    print(f"📊 Stock Alert Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # 1. Fear & Greed Index 수집
    print("\n[1/3] Fear & Greed Index 수집 중...")
    fear_greed = get_fear_greed_index()

    if fear_greed.get("score") is not None:
        print(f"  ✓ Score: {fear_greed['score']:.1f} ({fear_greed['rating']})")
    else:
        print(f"  ⚠️ Error: {fear_greed.get('error', 'Unknown')}")

    # 2. 52주 고점 대비 하락률 수집
    print(f"\n[2/3] 52주 고점 대비 하락률 수집 중... (종목: {Config.WATCH_SYMBOLS})")
    stock_results = collect_stock_data(Config.WATCH_SYMBOLS)

    # 3. 텔레그램 전송
    print("\n[3/3] 텔레그램 전송 중...")
    result = await notifier.send_daily_report(fear_greed, stock_results)

    if result.get("ok"):
        print(f"  ✓ 전송 완료! (message_id: {result.get('message_id', 'N/A')})")
        return True
    else:
        print(f"  ❌ 전송 실패: {result.get('error', 'Unknown error')}")
        return False


def main():
    """메인 함수 - crontab에서 호출됩니다."""
    print(f"\n🚀 Stock Alert Bot 시작 - {datetime.now()}")

    # 1. 설정 검증
    if not Config.validate():
        print("❌ 설정 오류! .env 파일을 확인하세요.")
        return 1  # 에러 코드 반환

    print(f"📊 관심 종목: {', '.join(Config.WATCH_SYMBOLS)}")

    # 2. 텔레그램 알리미 생성
    notifier = TelegramNotifier(
        token=Config.TELEGRAM_BOT_TOKEN,
        chat_id=Config.TELEGRAM_CHAT_ID,
    )

    # 3. 리포트 전송 (async 함수 실행)
    # asyncio.run(): async 함수를 일반 함수에서 실행하는 방법
    success = asyncio.run(send_report(notifier))

    # 4. 결과 출력
    print("\n" + "=" * 50)
    if success:
        print("✅ 완료!")
        return 0  # 성공 코드
    else:
        print("❌ 실패!")
        return 1  # 에러 코드


if __name__ == "__main__":
    # 스크립트로 직접 실행될 때만 main() 호출
    # crontab이나 터미널에서 `python main.py` 실행 시
    exit_code = main()
    exit(exit_code)
