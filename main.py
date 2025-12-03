"""Stock Alert Bot - 주식 알림 봇 메인 모듈"""

from src.config import Config


def main():
    """메인 실행 함수"""
    print("🚀 Stock Alert Bot 시작")

    # 설정 검증
    if not Config.validate():
        print("❌ 설정 오류로 종료합니다.")
        return

    print(f"📊 관심 종목: {', '.join(Config.WATCH_SYMBOLS)}")
    print(f"⏰ 알림 시간: {Config.ALERT_TIME}")

    # TODO: 스케줄러 실행
    print("✅ 봇이 정상적으로 설정되었습니다.")


if __name__ == "__main__":
    main()
