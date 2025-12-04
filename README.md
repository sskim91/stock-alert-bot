# Stock Alert Bot

주식 고점 대비 하락률과 Fear & Greed Index를 텔레그램으로 알려주는 봇

## 기능

- **고점 대비 하락률**: 설정 기간 내 최고가 대비 현재 하락률 분석
- **분할매수 신호**: -10%, -20%, -30% 구간별 매수 신호
- **Fear & Greed Index**: CNN 시장 심리 지표
- **자동 알림**: 매일 설정 시간에 리포트 전송
- **Bot Menu**: 텔레그램에서 버튼으로 즉시 리포트 요청

## 설치 및 실행

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 봇 실행
uv run python main.py --bot
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | (필수) |
| `TELEGRAM_CHAT_ID` | 메시지를 받을 채팅 ID | (필수) |
| `ANALYSIS_PERIOD` | 분석 기간 | `1y` |
| `ALERT_TIME` | 알림 시간 (09:00 또는 0900) | `09:00` |

## 텔레그램 명령어

메뉴 버튼(☰) 또는 `/` 입력 시 명령어 목록 표시

| 명령어 | 설명 |
|--------|------|
| `/report` | 1년 기준 리포트 |
| `/report6mo` | 6개월 리포트 |
| `/report3mo` | 3개월 리포트 |
| `/status` | 현재 설정 확인 |
| `/help` | 도움말 |

직접 입력: `/report [기간]` (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)

## 서버 배포 (systemd)

```bash
# 서비스 파일 생성
sudo tee /etc/systemd/system/stock-alert-bot.service << 'EOF'
[Unit]
Description=Stock Alert Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/dev/stock-alert-bot
ExecStart=/home/ubuntu/.local/bin/uv run python main.py --bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable stock-alert-bot
sudo systemctl start stock-alert-bot

# 로그 확인
sudo journalctl -u stock-alert-bot -f
```

## 프로젝트 구조

```
stock-alert-bot/
├── main.py                   # CLI + Bot 모드
├── src/
│   ├── config.py             # 설정 관리
│   ├── stock/
│   │   ├── fetcher.py        # 주가 데이터 (yfinance)
│   │   └── mdd.py            # 하락률 계산
│   ├── indicators/
│   │   └── fear_greed.py     # Fear & Greed Index
│   └── notifiers/
│       └── telegram.py       # 텔레그램 봇
└── tests/
```

## TBD

- [ ] **고정 키보드 버튼**: `ReplyKeyboardMarkup(is_persistent=True)`로 입력창 위에 항상 버튼 표시
  - [python-telegram-bot docs](https://docs.python-telegram-bot.org/telegram.replykeyboardmarkup.html)
