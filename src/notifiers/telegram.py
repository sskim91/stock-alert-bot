"""텔레그램 알림 모듈 (Async 버전)

python-telegram-bot 라이브러리를 사용한 비동기 메시지 전송

비동기(Async)란?
- Java의 CompletableFuture, Spring WebFlux와 비슷한 개념
- 네트워크 요청 같은 I/O 작업을 기다리는 동안 다른 작업 가능
- async def: 비동기 함수 정의 (Java의 CompletableFuture 반환 메서드와 유사)
- await: 결과를 기다림 (Java의 .get() 또는 .join()과 유사)
"""

from telegram import Bot
from telegram.error import TelegramError


class TelegramNotifier:
    """텔레그램 봇을 통한 알림 전송 (Async)

    사용 예시:
        notifier = TelegramNotifier(token="봇토큰", chat_id="채팅방ID")
        await notifier.send_message("안녕하세요!")

    Java로 비유하면:
        - 이 클래스 = @Service 클래스
        - send_message() = CompletableFuture<Result> 반환하는 메서드
    """

    def __init__(self, token: str, chat_id: str):
        """
        Args:
            token: 텔레그램 봇 토큰 (BotFather에서 받은 것)
            chat_id: 메시지를 보낼 채팅방 ID
        """
        self.chat_id = chat_id
        # python-telegram-bot의 Bot 객체 생성
        # Java로 비유: RestTemplate 또는 WebClient 인스턴스 생성
        self.bot = Bot(token=token)

    async def send_message(self, message: str) -> dict:
        """
        텔레그램으로 메시지를 전송합니다.

        Args:
            message: 전송할 메시지 내용

        Returns:
            성공 시: {"ok": True, "message_id": 123}
            실패 시: {"ok": False, "error": "에러 메시지"}

        Java 비유:
            public CompletableFuture<Result> sendMessage(String message)
        """
        try:
            # await = 비동기 작업 완료를 기다림
            # Java의 future.get() 또는 Mono.block()과 비슷하지만
            # 스레드를 블로킹하지 않음 (이게 핵심!)
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",  # <b>굵게</b> 같은 HTML 태그 사용 가능
            )

            return {
                "ok": True,
                "message_id": result.message_id,
            }

        except TelegramError as e:
            # 텔레그램 API 에러 (토큰 잘못됨, 채팅방 없음 등)
            return {
                "ok": False,
                "error": f"Telegram API 에러: {e}",
            }

        except Exception as e:
            # 기타 에러 (네트워크 등)
            return {
                "ok": False,
                "error": f"에러 발생: {e}",
            }

    async def send_daily_report(
        self,
        fear_greed: dict,
        stock_results: list[dict],
    ) -> dict:
        """
        일일 리포트를 보기 좋게 포맷팅해서 전송합니다.

        Args:
            fear_greed: Fear & Greed Index 데이터
                {"score": 24.5, "rating": "extreme fear", ...}
            stock_results: 각 종목의 고점 대비 하락률 및 매수 신호
                [
                    {
                        "symbol": "TSLA",
                        "peak_price": 500.0,
                        "current_price": 446.74,
                        "drawdown_pct": -10.8,
                        "buy_signal": "1차 매수 (정찰병)",
                    },
                    ...
                ]

        Returns:
            send_message()와 동일한 형식
        """
        # 메시지 조립 (Java의 StringBuilder와 비슷)
        lines = []

        # 헤더
        lines.append("<b>Daily Stock Report</b>")
        lines.append("")

        # Fear & Greed Index 섹션
        lines.append("<b>Fear & Greed Index</b>")
        score = fear_greed.get("score")
        if score is not None:
            rating = fear_greed.get("rating", "unknown")
            lines.append(f"  Score: {score:.1f} ({rating})")

            # 이전 데이터가 있으면 변화량 표시
            prev = fear_greed.get("previous_close")
            if prev is not None:
                try:
                    diff = float(score) - float(prev)
                    arrow = "+" if diff >= 0 else ""
                    lines.append(f"  vs Yesterday: {arrow}{diff:.1f}")
                except (TypeError, ValueError):
                    pass
        else:
            lines.append(f"  Error: {fear_greed.get('error', 'Unknown')}")

        lines.append("")

        # 52주 고점 대비 하락률 & 매수 신호 섹션
        lines.append("<b>52주 고점 대비 & 매수 신호</b>")
        for item in stock_results:
            symbol = item.get("symbol")
            drawdown_pct = item.get("drawdown_pct")
            peak_price = item.get("peak_price", 0)
            current_price = item.get("current_price", 0)
            buy_signal = item.get("buy_signal", "")

            # 필수 데이터가 없으면 건너뛰기
            if not symbol or drawdown_pct is None:
                continue

            try:
                # 종목 정보 라인
                lines.append(
                    f"  <b>{symbol}</b>: {float(drawdown_pct):.1f}% "
                    f"(${float(current_price):.2f})"
                )
                # 52주 최고가 표시
                lines.append(f"    Peak: ${float(peak_price):.2f}")
                # 매수 신호 표시 (있을 때만)
                if buy_signal:
                    lines.append(f"    → <b>{buy_signal}</b>")
                else:
                    lines.append("    → 관망")
            except (TypeError, ValueError):
                continue

        # 리스트를 줄바꿈으로 합치기
        message = "\n".join(lines)

        # await으로 비동기 전송
        return await self.send_message(message)
