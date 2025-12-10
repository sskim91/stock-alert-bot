"""ma.py 테스트 코드

200일 이동평균선 계산 및 분석이 정확한지 검증
"""

import pandas as pd
import pytest
from src.stock.ma import calculate_ma, calculate_ma_analysis


class TestCalculateMa:
    """calculate_ma 함수 테스트"""

    def test_basic_ma(self):
        """
        테스트 1: 기본 이동평균 계산

        5개 데이터의 5일 이동평균
        [10, 20, 30, 40, 50] → 평균 = 30
        """
        prices = pd.Series([10, 20, 30, 40, 50])
        ma = calculate_ma(prices, window=5)

        assert ma == pytest.approx(30.0)

    def test_ma_with_more_data(self):
        """
        테스트 2: 데이터가 window보다 많을 때

        마지막 5개의 평균: [60, 70, 80, 90, 100] → 평균 = 80
        """
        prices = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        ma = calculate_ma(prices, window=5)

        assert ma == pytest.approx(80.0)

    def test_insufficient_data(self):
        """
        테스트 3: 데이터가 부족하면 None 반환

        3개 데이터로 5일 이동평균 계산 불가
        """
        prices = pd.Series([10, 20, 30])
        ma = calculate_ma(prices, window=5)

        assert ma is None

    def test_empty_series(self):
        """
        테스트 4: 빈 데이터면 None 반환
        """
        prices = pd.Series([], dtype=float)
        ma = calculate_ma(prices, window=5)

        assert ma is None

    def test_200_day_ma(self):
        """
        테스트 5: 200일 이동평균 계산 (실제 사용 케이스)

        200개의 데이터로 200일 이동평균 계산
        """
        # 1부터 200까지의 숫자 → 평균 = 100.5
        prices = pd.Series(range(1, 201))
        ma = calculate_ma(prices, window=200)

        assert ma == pytest.approx(100.5)


class TestCalculateMaAnalysis:
    """calculate_ma_analysis 함수 테스트"""

    def test_above_ma(self):
        """
        테스트 1: 현재가가 200일선 위에 있을 때

        현재가 250, 200일선 220
        차이 = (250 - 220) / 220 * 100 = +13.64%
        """
        result = calculate_ma_analysis(current_price=250.0, ma_200=220.0)

        assert result["ma_200"] == 220.0
        assert result["diff_pct"] == pytest.approx(13.64, rel=0.01)
        assert result["trend"] == "상승 추세 유지"
        assert result["position"] == "above"

    def test_below_ma(self):
        """
        테스트 2: 현재가가 200일선 아래에 있을 때

        현재가 180, 200일선 220
        차이 = (180 - 220) / 220 * 100 = -18.18%
        """
        result = calculate_ma_analysis(current_price=180.0, ma_200=220.0)

        assert result["ma_200"] == 220.0
        assert result["diff_pct"] == pytest.approx(-18.18, rel=0.01)
        assert result["trend"] == "약세 구간, 신중한 접근 필요"
        assert result["position"] == "below"

    def test_at_ma(self):
        """
        테스트 3: 현재가가 200일선과 같을 때

        차이 = 0%, 상승 추세로 분류
        """
        result = calculate_ma_analysis(current_price=220.0, ma_200=220.0)

        assert result["diff_pct"] == pytest.approx(0.0)
        assert result["trend"] == "상승 추세 유지"
        assert result["position"] == "above"

    def test_none_ma(self):
        """
        테스트 4: MA가 None이면 데이터 부족 반환
        """
        result = calculate_ma_analysis(current_price=250.0, ma_200=None)

        assert result["ma_200"] is None
        assert result["diff_pct"] is None
        assert result["trend"] == "데이터 부족"
        assert result["position"] == "unknown"

    def test_zero_ma(self):
        """
        테스트 5: MA가 0이면 데이터 부족 반환 (0으로 나누기 방지)
        """
        result = calculate_ma_analysis(current_price=250.0, ma_200=0.0)

        assert result["ma_200"] is None
        assert result["trend"] == "데이터 부족"


class TestRealStockData:
    """실제 주가 데이터로 테스트"""

    def test_tsla_ma_200(self):
        """
        테스트: TSLA의 200일 이동평균선 계산

        실제 데이터로 200일선이 정상 계산되는지 확인
        """
        from src.stock.fetcher import fetch_stock_data

        data = fetch_stock_data("TSLA", period="1y")

        if len(data) >= 200:
            ma = calculate_ma(data["Close"], window=200)
            assert ma is not None
            assert ma > 0

            # 분석 결과도 확인
            current_price = float(data["Close"].iloc[-1])
            analysis = calculate_ma_analysis(current_price, ma)

            assert analysis["ma_200"] == ma
            assert analysis["diff_pct"] is not None
            assert analysis["position"] in ["above", "below"]
