"""텔레그램 알림 모듈 (Async 버전)

python-telegram-bot 라이브러리를 사용한 비동기 메시지 전송 및 봇 명령어 처리

기능:
    - 매일 정해진 시간에 자동 리포트 전송 (ALERT_TIME 설정)
    - 텔레그램 명령어로 즉시 리포트 요청 가능

지원 명령어:
    /report         - 현재 설정된 기간으로 리포트 요청
    /report 6mo     - 특정 기간으로 리포트 요청
    /status         - 현재 설정 확인 (관심종목, 기간 등)
    /help           - 도움말
"""

import asyncio
import datetime

from zoneinfo import ZoneInfo
from telegram import Bot, BotCommand, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

from src.config import Config
from src.stock.fetcher import fetch_stock_data
from src.stock.mdd import calculate_drawdown_from_peak, get_buy_signal
from src.stock.ma import calculate_ma, calculate_ma_analysis
from src.indicators.fear_greed import get_fear_greed_index


class TelegramNotifier:
    """텔레그램 봇을 통한 알림 전송 (Async)"""

    def __init__(self, token: str, chat_id: str):
        """
        Args:
            token: 텔레그램 봇 토큰 (BotFather에서 받은 것)
            chat_id: 메시지를 보낼 채팅방 ID
        """
        self.chat_id = chat_id
        self.bot = Bot(token=token)

    async def send_message(self, message: str) -> dict:
        """텔레그램으로 메시지를 전송합니다."""
        try:
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",
            )
            return {"ok": True, "message_id": result.message_id}

        except TelegramError as e:
            return {"ok": False, "error": f"Telegram API 에러: {e}"}

        except Exception as e:
            return {"ok": False, "error": f"에러 발생: {e}"}

    async def send_daily_report(
        self,
        fear_greed: dict,
        stock_results: list[dict],
        period: str = "1y",
    ) -> dict:
        """일일 리포트를 포맷팅해서 전송합니다."""
        period_display = Config.get_period_display(period)
        lines = []

        # 헤더
        lines.append("<b>📊 Daily Stock Report</b>")
        lines.append("")

        # Fear & Greed Index
        score = fear_greed.get("score")
        if score is not None:
            try:
                score = float(score)
                rating = fear_greed.get("rating", "unknown")
                emoji = _get_fear_greed_emoji(score)
                lines.append(f"{emoji} Fear & Greed: {score:.1f} ({rating})")
            except (TypeError, ValueError):
                lines.append("⚠️ Fear & Greed: 데이터 오류")

            prev = fear_greed.get("previous_close")
            if prev is not None:
                try:
                    diff = float(score) - float(prev)
                    arrow = "📈" if diff >= 0 else "📉"
                    sign = "+" if diff >= 0 else ""
                    lines.append(f"   전일 대비: {sign}{diff:.1f} {arrow}")
                except (TypeError, ValueError):
                    pass
        else:
            lines.append(f"⚠️ Fear & Greed: {fear_greed.get('error', 'Unknown')}")

        lines.append("")
        lines.append("")

        # 고점 대비 하락률
        lines.append(f"<b>📉 고점 대비 하락률 ({period_display})</b>")
        lines.append("")

        for item in stock_results:
            symbol = item.get("symbol")
            drawdown_pct = item.get("drawdown_pct")
            peak_price = item.get("peak_price", 0)
            current_price = item.get("current_price", 0)
            buy_signal = item.get("buy_signal", "")

            if not symbol or drawdown_pct is None:
                continue

            try:
                cur = float(current_price)
                peak = float(peak_price)
                pct = float(drawdown_pct)
                signal = "🔔" if buy_signal else "⏸️"

                lines.append(f"<b>{symbol}</b>  {pct:.1f}%  {signal}")
                lines.append(f"   ${cur:.2f} → ${peak:.2f}")

                # TSLA 200일 이동평균선 정보 추가
                ma_200_data = item.get("ma_200")
                if ma_200_data and ma_200_data.get("ma_200") is not None:
                    ma_price = ma_200_data["ma_200"]
                    ma_diff = ma_200_data["diff_pct"]
                    ma_trend = ma_200_data["trend"]
                    ma_position = ma_200_data["position"]

                    position_text = "위" if ma_position == "above" else "아래"
                    sign = "+" if ma_diff >= 0 else ""
                    lines.append(
                        f"   📏 200일선: ${ma_price:.2f} ({sign}{ma_diff:.1f}%)"
                    )
                    lines.append(f"   → 현재가가 200일선 {position_text} = {ma_trend}")

                lines.append("")
            except (TypeError, ValueError):
                continue

        message = "\n".join(lines)
        return await self.send_message(message)


def _get_fear_greed_emoji(score: float) -> str:
    """Fear & Greed 점수에 따른 이모지 반환"""
    if score <= 24:
        return "😱"  # Extreme Fear
    elif score <= 44:
        return "😰"  # Fear
    elif score <= 55:
        return "😐"  # Neutral
    elif score <= 75:
        return "😊"  # Greed
    else:
        return "🤑"  # Extreme Greed


# ============================================================
# 공통 함수
# ============================================================


async def _fetch_single_stock(symbol: str, period: str) -> dict | None:
    """단일 종목 데이터를 가져와 처리합니다."""
    data = await asyncio.to_thread(fetch_stock_data, symbol, period)
    if data.empty:
        return None

    close_prices = data.get("Close")
    if close_prices is None or close_prices.empty:
        return None

    drawdown_data = calculate_drawdown_from_peak(close_prices)
    buy_signal = get_buy_signal(drawdown_data.get("drawdown_pct", 0))

    result = {
        "symbol": symbol,
        "peak_price": drawdown_data.get("peak_price", 0),
        "current_price": drawdown_data.get("current_price", 0),
        "drawdown_pct": drawdown_data.get("drawdown_pct", 0),
        "buy_signal": buy_signal,
    }

    # TSLA만 200일 이동평균선 분석 추가
    if symbol == "TSLA":
        # 200일선 계산용 데이터 결정 (부족하면 1년 데이터 사용)
        ma_prices = close_prices
        if len(close_prices) < 200:
            data_1y = await asyncio.to_thread(fetch_stock_data, symbol, "1y")
            if not data_1y.empty:
                ma_prices = data_1y.get("Close")

        # MA 계산 및 분석
        if ma_prices is not None and len(ma_prices) >= 200:
            ma_200 = calculate_ma(ma_prices, window=200)
            result["ma_200"] = calculate_ma_analysis(result["current_price"], ma_200)

    return result


async def _collect_report_data(period: str) -> tuple[dict, list[dict]]:
    """리포트에 필요한 데이터를 병렬로 수집합니다."""
    # Fear & Greed와 주식 데이터를 병렬로 수집
    fear_greed_task = asyncio.to_thread(get_fear_greed_index)
    stock_tasks = [
        _fetch_single_stock(symbol, period) for symbol in Config.WATCH_SYMBOLS
    ]

    results = await asyncio.gather(fear_greed_task, *stock_tasks)

    fear_greed = results[0]
    stock_results = [r for r in results[1:] if r is not None]

    return fear_greed, stock_results


# ============================================================
# 텔레그램 봇 명령어 핸들러
# ============================================================

# 고정 메뉴 명령어 정의
BOT_COMMANDS = [
    BotCommand("report", "📊 리포트 (1년 기준)"),
    BotCommand("report6mo", "📆 6개월 리포트"),
    BotCommand("report3mo", "📆 3개월 리포트"),
    BotCommand("status", "📈 현재 설정 확인"),
    BotCommand("help", "❓ 도움말"),
]


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어 핸들러"""
    help_text = """<b>Stock Alert Bot</b>

<b>명령어 (메뉴 버튼 사용)</b>
/report - 1년 기준 리포트
/report6mo - 6개월 리포트
/report3mo - 3개월 리포트
/status - 현재 설정 확인

<b>직접 입력</b>
/report [기간] - 특정 기간 리포트
(1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)"""

    await update.message.reply_text(help_text, parse_mode="HTML")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재 설정 확인 명령어 핸들러"""
    symbols = ", ".join(Config.WATCH_SYMBOLS)
    period_display = Config.get_period_display(Config.ANALYSIS_PERIOD)

    status_text = f"""<b>현재 설정</b>

관심 종목: {symbols}
분석 기간: {period_display}
알림 시간: {Config.ALERT_TIME}"""

    await update.message.reply_text(status_text, parse_mode="HTML")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """리포트 요청 명령어 핸들러"""
    # 기간 파싱 (/report 6mo 형태)
    if context.args and len(context.args) > 0:
        period = context.args[0].lower()
        if not Config.is_valid_period(period):
            await update.message.reply_text(
                f"유효하지 않은 기간: {period}\n"
                f"사용 가능: {', '.join(Config.VALID_PERIODS)}"
            )
            return
    else:
        period = Config.ANALYSIS_PERIOD

    period_display = Config.get_period_display(period)

    processing_msg = None
    try:
        processing_msg = await update.message.reply_text(
            f"리포트 생성 중... ({period_display})"
        )

        fear_greed, stock_results = await _collect_report_data(period)

        notifier = TelegramNotifier(
            token=Config.TELEGRAM_BOT_TOKEN,
            chat_id=str(update.effective_chat.id),
        )
        result = await notifier.send_daily_report(fear_greed, stock_results, period)

        # 임시 메시지 삭제 (실패해도 무시)
        try:
            await processing_msg.delete()
        except TelegramError:
            pass

        if not result.get("ok"):
            await update.message.reply_text(
                f"리포트 전송 실패: {result.get('error', 'Unknown')}"
            )

    except Exception as e:
        print(f"cmd_report 오류: {e}")  # 서버 로그에만 기록
        error_msg = "리포트 생성 중 오류가 발생했습니다."
        if processing_msg:
            await processing_msg.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)


async def cmd_report_6mo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """6개월 리포트 명령어 핸들러"""
    context.args = ["6mo"]
    await cmd_report(update, context)


async def cmd_report_3mo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """3개월 리포트 명령어 핸들러"""
    context.args = ["3mo"]
    await cmd_report(update, context)


async def scheduled_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """매일 정해진 시간에 자동으로 리포트를 전송합니다."""
    chat_id = context.job.chat_id
    period = Config.ANALYSIS_PERIOD

    print(f"[{datetime.datetime.now()}] 스케줄 리포트 전송 시작")

    try:
        fear_greed, stock_results = await _collect_report_data(period)

        notifier = TelegramNotifier(
            token=Config.TELEGRAM_BOT_TOKEN,
            chat_id=str(chat_id),
        )
        result = await notifier.send_daily_report(fear_greed, stock_results, period)

        if result.get("ok"):
            print("  -> 전송 완료")
        else:
            print(f"  -> 전송 실패: {result.get('error')}")

    except Exception as e:
        print(f"  -> 오류: {e}")


def _parse_alert_time(alert_time: str) -> datetime.time:
    """ALERT_TIME 문자열을 datetime.time으로 파싱 (09:00 또는 0900 형식 지원)"""
    kst = ZoneInfo("Asia/Seoul")
    try:
        alert_time = alert_time.strip()

        if ":" in alert_time:
            # 09:00 형식
            parts = alert_time.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        elif len(alert_time) == 4 and alert_time.isdigit():
            # 0900 형식
            hour = int(alert_time[:2])
            minute = int(alert_time[2:])
        else:
            raise ValueError(f"Unknown format: {alert_time}")

        return datetime.time(hour=hour, minute=minute, tzinfo=kst)
    except (ValueError, IndexError) as e:
        print(f"ALERT_TIME 파싱 실패 ({alert_time}: {e}), 기본값 09:00 사용")
        return datetime.time(hour=9, minute=0, tzinfo=kst)


async def post_init(application):
    """봇 시작 시 메뉴 명령어 등록"""
    await application.bot.set_my_commands(BOT_COMMANDS)
    print("봇 메뉴 명령어 등록 완료")


def run_telegram_bot():
    """텔레그램 봇 실행 (polling 모드 + 스케줄러)"""
    application = (
        Application.builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("start", cmd_help))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("report", cmd_report))
    application.add_handler(CommandHandler("report6mo", cmd_report_6mo))
    application.add_handler(CommandHandler("report3mo", cmd_report_3mo))

    job_queue = application.job_queue
    alert_time = _parse_alert_time(Config.ALERT_TIME)

    job_queue.run_daily(
        scheduled_daily_report,
        time=alert_time,
        chat_id=Config.TELEGRAM_CHAT_ID,
        name="daily_report",
    )

    print(f"스케줄 등록: 매일 {Config.ALERT_TIME}에 리포트 전송")

    application.run_polling(allowed_updates=Update.ALL_TYPES)
