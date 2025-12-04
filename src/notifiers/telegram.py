"""텔레그램 알림 모듈 (Async 버전)

python-telegram-bot 라이브러리를 사용한 비동기 메시지 전송 및 봇 명령어 처리

지원 명령어:
    /report         - 현재 설정된 기간으로 리포트 요청
    /report 6mo     - 특정 기간으로 리포트 요청
    /status         - 현재 설정 확인 (관심종목, 기간 등)
    /help           - 도움말
"""

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

from src.config import Config


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
        """
        일일 리포트를 보기 좋게 포맷팅해서 전송합니다.

        Args:
            fear_greed: Fear & Greed Index 데이터
            stock_results: 각 종목의 고점 대비 하락률 및 매수 신호
            period: 분석 기간 (기본값: 1y)
        """
        period_display = Config.get_period_display(period)
        lines = []

        # 헤더
        lines.append("<b>📊 Daily Stock Report</b>")
        lines.append(f"📅 분석 기간: {period_display}")
        lines.append("")

        # Fear & Greed Index 섹션
        lines.append("<b>😱 Fear & Greed Index</b>")
        score = fear_greed.get("score")
        if score is not None:
            rating = fear_greed.get("rating", "unknown")
            emoji = _get_fear_greed_emoji(score)
            lines.append(f"  {emoji} Score: {score:.1f} ({rating})")

            prev = fear_greed.get("previous_close")
            if prev is not None:
                try:
                    diff = float(score) - float(prev)
                    arrow = "📈" if diff >= 0 else "📉"
                    sign = "+" if diff >= 0 else ""
                    lines.append(f"  {arrow} vs Yesterday: {sign}{diff:.1f}")
                except (TypeError, ValueError):
                    pass
        else:
            lines.append(f"  ⚠️ Error: {fear_greed.get('error', 'Unknown')}")

        lines.append("")

        # 고점 대비 하락률 & 매수 신호 섹션
        lines.append(f"<b>📉 {period_display} 고점 대비 하락률</b>")
        for item in stock_results:
            symbol = item.get("symbol")
            drawdown_pct = item.get("drawdown_pct")
            peak_price = item.get("peak_price", 0)
            current_price = item.get("current_price", 0)
            buy_signal = item.get("buy_signal", "")

            if not symbol or drawdown_pct is None:
                continue

            try:
                lines.append(
                    f"  <b>{symbol}</b>: {float(drawdown_pct):.1f}% "
                    f"(${float(current_price):.2f})"
                )
                lines.append(f"    Peak: ${float(peak_price):.2f}")
                if buy_signal:
                    lines.append(f"    🔔 <b>{buy_signal}</b>")
                else:
                    lines.append("    ⏸️ 관망")
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
# 텔레그램 봇 명령어 핸들러
# ============================================================

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어 핸들러"""
    help_text = """<b>📖 Stock Alert Bot 도움말</b>

<b>명령어 목록:</b>
/report - 리포트 요청 (기본 기간: 1년)
/report [기간] - 특정 기간으로 리포트 요청
/status - 현재 설정 확인
/help - 이 도움말

<b>사용 가능한 기간:</b>
1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max

<b>예시:</b>
/report → 1년 기준 리포트
/report 6mo → 6개월 기준 리포트
/report 3mo → 3개월 기준 리포트"""

    await update.message.reply_text(help_text, parse_mode="HTML")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재 설정 확인 명령어 핸들러"""
    symbols = ", ".join(Config.WATCH_SYMBOLS)
    period = Config.ANALYSIS_PERIOD
    period_display = Config.get_period_display(period)

    status_text = f"""<b>⚙️ 현재 설정</b>

📊 관심 종목: {symbols}
📅 기본 분석 기간: {period_display}
⏰ 알림 시간: {Config.ALERT_TIME}

<b>사용 가능한 기간:</b>
{', '.join(Config.VALID_PERIODS)}"""

    await update.message.reply_text(status_text, parse_mode="HTML")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """리포트 요청 명령어 핸들러"""
    # 순환 import 방지를 위해 함수 내부에서 import
    from src.stock.fetcher import fetch_stock_data
    from src.stock.mdd import calculate_drawdown_from_peak, get_buy_signal
    from src.indicators.fear_greed import get_fear_greed_index

    # 기간 파싱 (/report 6mo 형태)
    if context.args and len(context.args) > 0:
        period = context.args[0].lower()
        if not Config.is_valid_period(period):
            await update.message.reply_text(
                f"❌ 유효하지 않은 기간: {period}\n"
                f"사용 가능: {', '.join(Config.VALID_PERIODS)}"
            )
            return
    else:
        period = Config.ANALYSIS_PERIOD

    period_display = Config.get_period_display(period)

    # 처리 중 메시지
    processing_msg = None
    try:
        processing_msg = await update.message.reply_text(
            f"⏳ 리포트 생성 중... (기간: {period_display})"
        )

        # 1. Fear & Greed Index 수집
        fear_greed = get_fear_greed_index()

        # 2. 주식 데이터 수집
        stock_results = []
        for symbol in Config.WATCH_SYMBOLS:
            data = fetch_stock_data(symbol, period=period)
            if data.empty:
                continue

            drawdown_data = calculate_drawdown_from_peak(data["Close"])
            buy_signal = get_buy_signal(drawdown_data.get("drawdown_pct", 0))

            stock_results.append({
                "symbol": symbol,
                "peak_price": drawdown_data.get("peak_price", 0),
                "current_price": drawdown_data.get("current_price", 0),
                "drawdown_pct": drawdown_data.get("drawdown_pct", 0),
                "buy_signal": buy_signal,
            })

        # 3. 리포트 생성 및 전송
        notifier = TelegramNotifier(
            token=Config.TELEGRAM_BOT_TOKEN,
            chat_id=str(update.effective_chat.id),
        )
        result = await notifier.send_daily_report(fear_greed, stock_results, period)

        # 처리 중 메시지 삭제
        await processing_msg.delete()

        if not result.get("ok"):
            await update.message.reply_text(
                f"❌ 리포트 전송 실패: {result.get('error', 'Unknown')}"
            )

    except Exception as e:
        error_msg = f"❌ 오류 발생: {e}"
        if processing_msg:
            await processing_msg.edit_text(error_msg)
        else:
            print(error_msg)


def run_telegram_bot():
    """텔레그램 봇 실행 (polling 모드)"""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("start", cmd_help))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("report", cmd_report))

    # 봇 실행 (polling)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
