"""텔레그램 알림 모듈"""


class TelegramNotifier:
    """텔레그램 봇을 통한 알림 전송"""

    def __init__(self, token: str, chat_id: str):
        """
        Args:
            token: 텔레그램 봇 토큰
            chat_id: 메시지를 보낼 채팅 ID
        """
        self.token = token
        self.chat_id = chat_id

    async def send_message(self, message: str) -> bool:
        """
        메시지를 전송합니다.

        Args:
            message: 전송할 메시지

        Returns:
            전송 성공 여부
        """
        # TODO: 텔레그램 API를 사용하여 구현
        pass
