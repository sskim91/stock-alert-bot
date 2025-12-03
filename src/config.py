"""설정 관리 모듈"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """환경 변수 기반 설정"""

    # 텔레그램 설정
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # 관심 종목
    WATCH_SYMBOLS: list[str] = ["TSLA", "SCHD", "SCHG"]

    # 알림 시간 (24시간 형식)
    ALERT_TIME: str = os.getenv("ALERT_TIME", "09:00")

    @classmethod
    def validate(cls) -> bool:
        """필수 설정값 검증"""
        if not cls.TELEGRAM_BOT_TOKEN:
            print("Error: TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            return False
        if not cls.TELEGRAM_CHAT_ID:
            print("Error: TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
            return False
        return True
