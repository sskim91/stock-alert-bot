"""MDD (Maximum Drawdown) 계산 모듈

MDD란?
- Maximum Drawdown = 최대 낙폭
- 투자 기간 중 고점에서 저점까지 최대 하락폭
- 투자 위험을 측정하는 중요한 지표
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
        prices: 주가 데이터 (pandas Series, 보통 종가 Close)

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
