"""telegram.py 테스트 코드

텔레그램 알림 모듈이 정상 작동하는지 테스트

Async 테스트란?
- 비동기 함수를 테스트하려면 특별한 방법이 필요
- @pytest.mark.asyncio: 이 테스트가 async 함수임을 표시
- Java로 비유: @Async 메서드를 테스트할 때 CompletableFuture를 기다리는 것과 유사
"""

import pytest
from src.notifiers.telegram import TelegramNotifier
from src.config import Config


@pytest.fixture
def notifier():
    """
    fixture: TelegramNotifier 인스턴스를 생성해서 재사용

    .env 파일에서 토큰과 채팅방 ID를 읽어옴
    """
    # 설정 검증
    if not Config.validate():
        pytest.skip("텔레그램 설정이 없어서 테스트 건너뜀")

    return TelegramNotifier(
        token=Config.TELEGRAM_BOT_TOKEN,
        chat_id=Config.TELEGRAM_CHAT_ID,
    )


class TestTelegramNotifier:
    """TelegramNotifier 클래스 테스트"""

    @pytest.mark.asyncio
    async def test_send_message_success(self, notifier):
        """
        테스트 1: 간단한 메시지 전송 테스트

        실제로 텔레그램에 메시지가 전송됨!
        """
        result = await notifier.send_message("테스트 메시지입니다.")

        # 전송 성공 확인
        assert result["ok"] is True
        assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_daily_report(self, notifier):
        """
        테스트 2: 일일 리포트 전송 테스트

        실제 데이터 형식으로 리포트가 잘 만들어지는지 확인
        """
        # 테스트용 가짜 데이터
        fear_greed = {
            "score": 25.5,
            "rating": "extreme fear",
            "previous_close": 24.0,
        }

        # 새로운 형식: 52주 고점 대비 하락률 + 매수 신호
        stock_results = [
            {
                "symbol": "TSLA",
                "peak_price": 300.00,
                "current_price": 250.50,
                "drawdown_pct": -16.5,
                "buy_signal": "1차 매수 (정찰병)",
            },
            {
                "symbol": "SCHD",
                "peak_price": 80.00,
                "current_price": 78.30,
                "drawdown_pct": -2.1,
                "buy_signal": "",
            },
            {
                "symbol": "SCHG",
                "peak_price": 100.00,
                "current_price": 70.00,
                "drawdown_pct": -30.0,
                "buy_signal": "3차 매수 (과매도 구간)",
            },
        ]

        # period 인자 추가 (기본값 사용 또는 명시적 지정)
        result = await notifier.send_daily_report(fear_greed, stock_results, period="1y")

        assert result["ok"] is True


class TestTelegramNotifierInvalidToken:
    """잘못된 토큰으로 테스트 (API 호출 실패 케이스)"""

    @pytest.mark.asyncio
    async def test_invalid_token_returns_error(self):
        """
        테스트 3: 잘못된 토큰은 에러 반환

        잘못된 토큰으로 API 호출 시 에러가 정상적으로 반환되는지 확인
        """
        notifier = TelegramNotifier(
            token="invalid_token_12345",
            chat_id="12345",
        )

        result = await notifier.send_message("테스트")

        # 실패해야 함
        assert result["ok"] is False
        assert "error" in result
