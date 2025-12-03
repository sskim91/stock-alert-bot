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


@pytest.fixture(scope="module")
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

        mdd_results = [
            {"symbol": "TSLA", "mdd": -15.32, "current_price": 250.50},
            {"symbol": "SCHD", "mdd": -5.21, "current_price": 78.30},
            {"symbol": "SCHG", "mdd": -8.45, "current_price": 95.10},
        ]

        result = await notifier.send_daily_report(fear_greed, mdd_results)

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
