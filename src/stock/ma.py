"""이동평균선(Moving Average) 계산 모듈

이동평균선이란?
- 일정 기간 동안의 주가 평균을 연결한 선
- 단기 노이즈를 제거하고 추세를 파악하는 데 유용

200일 이동평균선:
- 장기 추세 판단의 대표적인 지표
- 현재가 > 200일선: 상승 추세 (강세장)
- 현재가 < 200일선: 하락 추세 (약세장)
- 많은 기관 투자자들이 매매 기준으로 활용
"""

import pandas as pd


def calculate_ma(prices: pd.Series, window: int = 200) -> float | None:
    """
    이동평균선을 계산합니다.

    Args:
        prices: 주가 데이터 (pandas Series, 보통 종가 Close)
        window: 이동평균 기간 (기본값: 200일)

    Returns:
        이동평균 값. 데이터가 부족하면 None 반환.
    """
    if prices.empty or len(prices) < window:
        return None

    ma = prices.rolling(window=window).mean().iloc[-1]

    if pd.isna(ma):
        return None

    return float(ma)


def calculate_ma_analysis(current_price: float, ma_200: float) -> dict:
    """
    200일 이동평균선 대비 현재가 분석을 수행합니다.

    Args:
        current_price: 현재 주가
        ma_200: 200일 이동평균선 가격

    Returns:
        {
            "ma_200": 220.30,           # 200일선 가격
            "diff_pct": 13.6,           # 현재가와 200일선 차이 (%)
            "trend": "상승 추세 유지",   # 추세 설명
            "position": "above",        # 위치 (above/below)
        }
    """
    if ma_200 is None or ma_200 <= 0:
        return {
            "ma_200": None,
            "diff_pct": None,
            "trend": "데이터 부족",
            "position": "unknown",
        }

    # 현재가와 200일선 차이 계산 (%)
    diff_pct = (current_price - ma_200) / ma_200 * 100

    # 추세 판단
    if diff_pct >= 0:
        position = "above"
        trend = "상승 추세 유지"
    else:
        position = "below"
        trend = "약세 구간, 신중한 접근 필요"

    return {
        "ma_200": ma_200,
        "diff_pct": diff_pct,
        "trend": trend,
        "position": position,
    }
