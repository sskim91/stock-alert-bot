"""Stock Alert Bot - 메인 실행 파일

실행 모드:
    1. 봇 모드 (권장): 스케줄러 + 명령어 대기를 동시에 처리
    2. 단일 실행: 한 번 실행 후 종료 (외부 스케줄러 사용 시)

사용법:
    # 봇 모드 (권장) - 스케줄러 내장 + 명령어 대기
    uv run python main.py --bot

    # 단일 실행 (환경변수 ANALYSIS_PERIOD 사용, 기본값 1y)
    uv run python main.py

    # 단일 실행 - 기간 지정
    uv run python main.py --period 6mo
"""

import argparse
import asyncio
import sys
from datetime import datetime

from src.config import Config
from src.indicators.fear_greed import get_fear_greed_index
from src.notifiers.telegram import TelegramNotifier
from src.stock.fetcher import fetch_stock_data
from src.stock.ma import calculate_ma, calculate_ma_analysis
from src.stock.mdd import calculate_drawdown_from_peak, get_buy_signal


def collect_stock_data(symbols: list[str], period: str) -> list[dict]:
    """
    각 종목의 고점 대비 하락률과 매수 신호를 수집합니다.

    Args:
        symbols: 종목 심볼 리스트 (예: ["TSLA", "SCHD", "SCHG"])
        period: 분석 기간 (예: "1y", "6mo", "3mo")

    Returns:
        [
            {
                "symbol": "TSLA",
                "peak_price": 500.0,
                "current_price": 400.0,
                "drawdown_pct": -20.0,
                "buy_signal": "2차 매수 (비중 확대)",
            },
            ...
        ]
    """
    results = []

    for symbol in symbols:
        print(f"  - {symbol} 데이터 수집 중...")

        data = fetch_stock_data(symbol, period=period)

        if data.empty:
            print(f"    ⚠️ {symbol}: 데이터 없음")
            continue

        drawdown_data = calculate_drawdown_from_peak(data["Close"])
        buy_signal = get_buy_signal(drawdown_data["drawdown_pct"])

        result = {
            "symbol": symbol,
            "peak_price": drawdown_data["peak_price"],
            "current_price": drawdown_data["current_price"],
            "drawdown_pct": drawdown_data["drawdown_pct"],
            "buy_signal": buy_signal,
        }

        # TSLA만 200일 이동평균선 분석 추가
        if symbol == "TSLA":
            close_prices = data["Close"]
            # 200일선 계산용 데이터 결정 (부족하면 1년 데이터 사용)
            ma_prices = close_prices
            if len(close_prices) < 200:
                data_1y = fetch_stock_data(symbol, period="1y")
                if not data_1y.empty:
                    ma_prices = data_1y["Close"]

            if len(ma_prices) >= 200:
                ma_200 = calculate_ma(ma_prices, window=200)
                result["ma_200"] = calculate_ma_analysis(result["current_price"], ma_200)

        results.append(result)

        signal_text = f" → {buy_signal}" if buy_signal else " → 관망"
        print(
            f"    ✓ {symbol}: {drawdown_data['drawdown_pct']:.1f}% from peak (${drawdown_data['current_price']:.2f}){signal_text}"
        )

    return results


async def send_report(notifier: TelegramNotifier, period: str) -> bool:
    """
    일일 리포트를 수집하고 텔레그램으로 전송합니다.

    Args:
        notifier: TelegramNotifier 인스턴스
        period: 분석 기간

    Returns:
        성공 여부
    """
    period_display = Config.get_period_display(period)

    print("\n" + "=" * 50)
    print(f"📊 Stock Alert Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📅 분석 기간: {period_display}")
    print("=" * 50)

    # 1. Fear & Greed Index 수집
    print("\n[1/3] Fear & Greed Index 수집 중...")
    fear_greed = get_fear_greed_index()

    if fear_greed.get("score") is not None:
        print(
            f"  ✓ Score: {fear_greed.get('score'):.1f} ({fear_greed.get('rating', 'unknown')})"
        )
    else:
        print(f"  ⚠️ Error: {fear_greed.get('error', 'Unknown')}")

    # 2. 고점 대비 하락률 수집
    print(
        f"\n[2/3] {period_display} 고점 대비 하락률 수집 중... (종목: {Config.WATCH_SYMBOLS})"
    )
    stock_results = collect_stock_data(Config.WATCH_SYMBOLS, period)

    # 3. 텔레그램 전송
    print("\n[3/3] 텔레그램 전송 중...")
    result = await notifier.send_daily_report(fear_greed, stock_results, period)

    if result.get("ok"):
        print(f"  ✓ 전송 완료! (message_id: {result.get('message_id', 'N/A')})")
        return True
    else:
        print(f"  ❌ 전송 실패: {result.get('error', 'Unknown error')}")
        return False


def run_once(period: str) -> int:
    """단일 실행 모드 - crontab용"""
    print(f"\n🚀 Stock Alert Bot 시작 - {datetime.now()}")

    if not Config.validate():
        print("❌ 설정 오류! .env 파일을 확인하세요.")
        return 1

    print(f"📊 관심 종목: {', '.join(Config.WATCH_SYMBOLS)}")
    print(f"📅 분석 기간: {Config.get_period_display(period)}")

    notifier = TelegramNotifier(
        token=Config.TELEGRAM_BOT_TOKEN,
        chat_id=Config.TELEGRAM_CHAT_ID,
    )

    success = asyncio.run(send_report(notifier, period))

    print("\n" + "=" * 50)
    if success:
        print("✅ 완료!")
        return 0
    else:
        print("❌ 실패!")
        return 1


def run_bot():
    """봇 모드 - 스케줄러 + 명령어 대기"""
    from src.notifiers.telegram import run_telegram_bot

    print(f"\n🤖 Stock Alert Bot (Bot Mode) 시작 - {datetime.now()}")

    if not Config.validate():
        print("❌ 설정 오류! .env 파일을 확인하세요.")
        return 1

    print(f"📊 관심 종목: {', '.join(Config.WATCH_SYMBOLS)}")
    print("📡 텔레그램 명령어 대기 중... (Ctrl+C로 종료)")

    try:
        run_telegram_bot()
        return 0
    except KeyboardInterrupt:
        print("\n👋 봇 종료")
        return 0


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Stock Alert Bot - 주식 MDD와 Fear & Greed Index 알림",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py                  # 기본 실행 (환경변수 또는 1y)
  python main.py --period 6mo     # 6개월 기간으로 분석
  python main.py --period 3mo     # 3개월 기간으로 분석
  python main.py --bot            # 텔레그램 봇 모드

유효한 기간: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        """,
    )

    parser.add_argument(
        "--period",
        "-p",
        type=str,
        default=None,
        help="분석 기간 (예: 1y, 6mo, 3mo). 미지정시 환경변수 ANALYSIS_PERIOD 또는 1y 사용",
    )

    parser.add_argument(
        "--bot",
        "-b",
        action="store_true",
        help="텔레그램 봇 모드로 실행 (명령어 수신 대기)",
    )

    return parser.parse_args()


def main():
    """메인 함수"""
    args = parse_args()

    # 봇 모드
    if args.bot:
        return run_bot()

    # 단일 실행 모드
    # 우선순위: CLI 인자 > 환경변수 > 기본값(1y)
    period = args.period or Config.ANALYSIS_PERIOD

    # 기간 유효성 검사
    if not Config.is_valid_period(period):
        print(f"❌ 유효하지 않은 기간: {period}")
        print(f"   유효한 기간: {', '.join(Config.VALID_PERIODS)}")
        return 1

    return run_once(period)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
