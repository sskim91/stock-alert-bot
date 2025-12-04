"""MDD (Maximum Drawdown) 계산 모듈

MDD란?
- Maximum Drawdown = 최대 낙폭
- 투자 기간 중 고점에서 저점까지 최대 하락폭
- 투자 위험을 측정하는 중요한 지표

고점 대비 하락률이란?
- 기간 내 최고가 대비 현재가가 얼마나 떨어졌는지
- 분할매수 타이밍을 잡는 데 유용한 지표
- 예: 52주 최고가 $500, 현재가 $400 → -20% 하락
"""

import pandas as pd


def calculate_mdd(prices: pd.Series) -> float:
    """
    MDD(최대 낙폭)를 계산합니다.

    계산 방법:
    1. 각 시점까지의 누적 최고가(peak)를 구함
    2. 현재가와 누적 최고가의 차이(drawdown)를 계산
    3. 그 중 가장 큰 하락폭이 MDD

    Args:
        prices: 주가 데이터 (pandas Series, 보통 종가 Close) (숫자들의 리스트 같은 것)

    Returns:
        MDD 값 (퍼센트, 예: -33.5는 33.5% 하락을 의미)
    """
    # 데이터가 비어있거나, 모두 0이거나, 모두 NaN이면 0 반환
    if prices.empty or (prices == 0).all() or prices.isna().all():
        return 0.0

    # 1단계: 각 시점까지의 누적 최고가 계산
    # cummax()는 "여기까지 중 최고값"을 구하는 함수
    # 예: [100, 120, 90, 110] → [100, 120, 120, 120]
    peak = prices.cummax()

    # 2단계: 낙폭(drawdown) 계산
    # (현재가 - 고점) / 고점 * 100
    # 예: 현재가 90, 고점 120 → (90-120)/120*100 = -25%
    drawdown = (prices - peak) / peak * 100

    # 3단계: 가장 큰 하락폭(MDD) 반환
    # min()을 쓰는 이유: 낙폭은 음수이므로 가장 작은 값이 가장 큰 하락
    mdd = drawdown.min()

    return float(mdd)


def calculate_drawdown_from_peak(prices: pd.Series) -> dict:
    """
    고점 대비 현재 하락률을 계산합니다.

    MDD와의 차이:
    - MDD: 기간 내 최대 낙폭 (과거에 얼마나 떨어졌었나)
    - 이 함수: 현재가가 고점 대비 얼마나 떨어져 있나 (지금 상태)

    분할매수 전략:
    - -10% 하락: 1차 매수 (정찰병)
    - -20% 하락: 2차 매수 (비중 확대)
    - -30% 하락: 3차 매수 (과매도 구간)

    Args:
        prices: 주가 데이터 (pandas Series, 보통 종가 Close)

    Returns:
        {
            "peak_price": 500.0,       # 기간 내 최고가
            "current_price": 400.0,    # 현재가 (마지막 종가)
            "drawdown_pct": -20.0,     # 고점 대비 하락률 (%)
        }
    """
    # 데이터 검증
    if prices.empty or prices.isna().all():
        return {
            "peak_price": 0.0,
            "current_price": 0.0,
            "drawdown_pct": 0.0,
        }

    # 1. 기간 내 최고가 (52주 최고가 같은 개념)
    peak_price = float(prices.max())

    # 2. 현재가 (가장 최근 종가)
    current_price = float(prices.iloc[-1])

    # 3. 고점 대비 하락률 계산
    # (현재가 - 최고가) / 최고가 * 100
    # 예: (400 - 500) / 500 * 100 = -20%
    if peak_price > 0:
        drawdown_pct = (current_price - peak_price) / peak_price * 100
    else:
        drawdown_pct = 0.0

    return {
        "peak_price": peak_price,
        "current_price": current_price,
        "drawdown_pct": drawdown_pct,
    }


def get_buy_signal(drawdown_pct: float) -> str:
    """
    하락률에 따른 매수 신호를 반환합니다.

    분할매수 전략:
    - 고점 대비 -10% 이상 하락: 1차 매수 (정찰병)
    - 고점 대비 -20% 이상 하락: 2차 매수 (비중 확대)
    - 고점 대비 -30% 이상 하락: 3차 매수 (과매도 구간)

    Args:
        drawdown_pct: 고점 대비 하락률 (음수, 예: -15.5)

    Returns:
        매수 신호 문자열 또는 빈 문자열
    """
    if drawdown_pct <= -30:
        return "3차 매수 (과매도 구간)"
    elif drawdown_pct <= -20:
        return "2차 매수 (비중 확대)"
    elif drawdown_pct <= -10:
        return "1차 매수 (정찰병)"
    else:
        return ""  # 매수 신호 없음 (관망)
