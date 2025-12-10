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

    # 분석 기간 (yfinance 형식: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
    ANALYSIS_PERIOD: str = os.getenv("ANALYSIS_PERIOD", "1y")

    # 유효한 분석 기간 목록
    VALID_PERIODS: list[str] = [
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y",
        "max",
    ]

    @classmethod
    def get_period_display(cls, period: str) -> str:
        """분석 기간을 사람이 읽기 좋은 형태로 변환"""
        period_names = {
            "1d": "1일",
            "5d": "5일",
            "1mo": "1개월",
            "3mo": "3개월",
            "6mo": "6개월",
            "1y": "1년 (52주)",
            "2y": "2년",
            "5y": "5년",
            "max": "전체",
        }
        return period_names.get(period, period)

    @classmethod
    def is_valid_period(cls, period: str) -> bool:
        """유효한 분석 기간인지 확인"""
        return period in cls.VALID_PERIODS

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
