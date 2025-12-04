# Stock Alert Bot

매일 정해진 시간에 주식 고점 대비 하락률과 Fear & Greed Index를 텔레그램으로 알려주는 자동화 봇

## 기능

- **고점 대비 하락률**: 52주(또는 설정 기간) 최고가 대비 현재 하락률 분석
- **분할매수 신호**: -10%, -20%, -30% 구간별 매수 신호 제공
- **Fear & Greed Index**: CNN 시장 심리 지표 알림
- **텔레그램 봇 명령어**: `/report`, `/status` 등 실시간 명령어 지원
- **유연한 분석 기간**: CLI 또는 환경변수로 분석 기간 설정 가능

## 관심 종목

- TSLA (Tesla)
- SCHD (Schwab US Dividend Equity ETF)
- SCHG (Schwab US Large-Cap Growth ETF)

## 설치

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일에 텔레그램 봇 토큰과 채팅 ID 입력
```

## 실행 방법

### 1. 단일 실행 (Cron용)
```bash
# 기본 실행 (1년 기준)
uv run python main.py

# 특정 기간으로 실행
uv run python main.py --period 6mo
uv run python main.py --period 3mo

# 도움말
uv run python main.py --help
```

### 2. 텔레그램 봇 모드
```bash
# 봇 명령어 대기 모드
uv run python main.py --bot
```

**지원 명령어:**
| 명령어 | 설명 |
|--------|------|
| `/report` | 기본 기간(1년)으로 리포트 요청 |
| `/report 6mo` | 6개월 기간으로 리포트 요청 |
| `/status` | 현재 설정 확인 |
| `/help` | 도움말 |

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | (필수) |
| `TELEGRAM_CHAT_ID` | 메시지를 받을 채팅 ID | (필수) |
| `ANALYSIS_PERIOD` | 분석 기간 | `1y` |
| `ALERT_TIME` | 알림 시간 | `09:00` |

**유효한 분석 기간:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

## Oracle Cloud 배포 가이드

### 1. 서버 준비

```bash
# Ubuntu에 uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 프로젝트 클론
cd ~/dev
git clone https://github.com/your-repo/stock-alert-bot.git
cd stock-alert-bot

# 의존성 설치
uv sync
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ANALYSIS_PERIOD=1y
EOF
```

### 3. Crontab 설정 (매일 자동 실행)

```bash
# crontab 편집
crontab -e

# 매일 오전 9시 (한국시간) 실행 - 서버가 UTC인 경우 0시
# 로그 파일로 출력 저장
0 0 * * * cd /home/ubuntu/dev/stock-alert-bot && /home/ubuntu/.local/bin/uv run python main.py >> /home/ubuntu/logs/stock-alert.log 2>&1
```

**Crontab 시간 설정 참고:**
```
# ┌───────────── 분 (0-59)
# │ ┌───────────── 시 (0-23)
# │ │ ┌───────────── 일 (1-31)
# │ │ │ ┌───────────── 월 (1-12)
# │ │ │ │ ┌───────────── 요일 (0-6, 0=일요일)
# │ │ │ │ │
# * * * * * command

# 예시:
0 0 * * *     # 매일 00:00 (UTC) = 09:00 (KST)
0 0 * * 1-5   # 평일만 00:00 (UTC)
0 9 * * *     # 매일 09:00 (서버 시간)
```

### 4. 로그 디렉토리 생성

```bash
mkdir -p /home/ubuntu/logs
```

### 5. 테스트 실행

```bash
# 수동 테스트
cd /home/ubuntu/dev/stock-alert-bot
uv run python main.py

# crontab 로그 확인
tail -f /home/ubuntu/logs/stock-alert.log
```

### 6. 봇 모드로 상시 실행 (선택사항)

systemd 서비스로 봇 모드를 상시 실행하려면:

```bash
# 서비스 파일 생성
sudo cat > /etc/systemd/system/stock-alert-bot.service << 'EOF'
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

# 상태 확인
sudo systemctl status stock-alert-bot

# 로그 확인
sudo journalctl -u stock-alert-bot -f
```

## 프로젝트 구조

```
stock-alert-bot/
├── main.py              # 메인 실행 파일 (CLI + Bot 모드)
├── src/
│   ├── config.py        # 설정 관리
│   ├── stock/
│   │   ├── fetcher.py   # 주가 데이터 수집 (yfinance)
│   │   └── mdd.py       # 고점 대비 하락률 계산
│   ├── indicators/
│   │   └── fear_greed.py # Fear & Greed Index (CNN API)
│   └── notifiers/
│       └── telegram.py  # 텔레그램 알림 + 봇 명령어
├── tests/               # 테스트 코드
├── pyproject.toml
└── .env.example
```
