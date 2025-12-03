"""mdd.py 테스트 코드

MDD 계산이 정확한지 다양한 케이스로 검증
"""

import pandas as pd
import pytest
from src.stock.mdd import calculate_mdd


class TestCalculateMdd:
    """calculate_mdd 함수 테스트"""

    def test_simple_case(self):
        """
        테스트 1: 간단한 숫자로 MDD 계산 확인

        주가: 100 → 120 → 90 → 110 → 80
        고점: 120, 저점: 80
        MDD = (80 - 120) / 120 * 100 = -33.33%
        """
        prices = pd.Series([100, 120, 90, 110, 80])
        mdd = calculate_mdd(prices)

        # -33.33%에 가까운지 확인
        # pytest.approx: 소수점 오차를 허용하며 비교
        assert mdd == pytest.approx(-33.33, rel=0.01)

    def test_no_drawdown(self):
        """
        테스트 2: 계속 오르기만 하면 MDD는 0

        주가: 100 → 110 → 120 → 130
        하락이 없으므로 MDD = 0
        """
        prices = pd.Series([100, 110, 120, 130])
        mdd = calculate_mdd(prices)

        assert mdd == 0.0

    def test_constant_price(self):
        """
        테스트 3: 가격 변동이 없으면 MDD는 0

        주가: 100 → 100 → 100 → 100
        """
        prices = pd.Series([100, 100, 100, 100])
        mdd = calculate_mdd(prices)

        assert mdd == 0.0

    def test_empty_series(self):
        """
        테스트 4: 빈 데이터면 0 반환
        """
        prices = pd.Series([], dtype=float)
        mdd = calculate_mdd(prices)

        assert mdd == 0.0

    def test_all_zeros(self):
        """
        테스트 5: 모두 0이면 0 반환 (0으로 나누기 방지)
        """
        prices = pd.Series([0, 0, 0])
        mdd = calculate_mdd(prices)

        assert mdd == 0.0

    def test_real_stock_data(self):
        """
        테스트 6: 실제 주가 데이터로 테스트

        실제 데이터는 변동이 있으므로 MDD가 음수여야 함
        """
        from src.stock.fetcher import fetch_stock_data

        tsla = fetch_stock_data("TSLA", period="1mo")
        mdd = calculate_mdd(tsla["Close"])

        # MDD는 0 이하여야 함 (하락이 있거나 없거나)
        assert mdd <= 0
