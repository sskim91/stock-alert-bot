"""mdd.py 테스트 코드

MDD 계산이 정확한지 다양한 케이스로 검증
"""

import pandas as pd
import pytest

from src.stock.mdd import calculate_drawdown_from_peak, calculate_mdd, get_buy_signal


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


class TestCalculateDrawdownFromPeak:
    """calculate_drawdown_from_peak 함수 테스트 (52주 고점 대비 하락률)"""

    def test_simple_drawdown(self):
        """
        테스트 1: 간단한 숫자로 고점 대비 하락률 계산

        주가: 100 → 120 → 90 → 100
        고점: 120, 현재가: 100
        하락률 = (100 - 120) / 120 * 100 = -16.67%
        """
        prices = pd.Series([100, 120, 90, 100])
        result = calculate_drawdown_from_peak(prices)

        assert result["peak_price"] == 120.0
        assert result["current_price"] == 100.0
        assert result["drawdown_pct"] == pytest.approx(-16.67, rel=0.01)

    def test_at_peak(self):
        """
        테스트 2: 현재가가 고점이면 하락률 0%

        주가: 100 → 90 → 110 → 120
        고점: 120, 현재가: 120
        하락률 = 0%
        """
        prices = pd.Series([100, 90, 110, 120])
        result = calculate_drawdown_from_peak(prices)

        assert result["peak_price"] == 120.0
        assert result["current_price"] == 120.0
        assert result["drawdown_pct"] == 0.0

    def test_empty_series(self):
        """
        테스트 3: 빈 데이터면 모두 0 반환
        """
        prices = pd.Series([], dtype=float)
        result = calculate_drawdown_from_peak(prices)

        assert result["peak_price"] == 0.0
        assert result["current_price"] == 0.0
        assert result["drawdown_pct"] == 0.0

    def test_thirty_percent_drop(self):
        """
        테스트 4: 정확히 30% 하락 케이스

        고점 500, 현재가 350
        하락률 = (350 - 500) / 500 * 100 = -30%
        """
        prices = pd.Series([400, 500, 450, 350])
        result = calculate_drawdown_from_peak(prices)

        assert result["peak_price"] == 500.0
        assert result["current_price"] == 350.0
        assert result["drawdown_pct"] == pytest.approx(-30.0, rel=0.01)


class TestGetBuySignal:
    """get_buy_signal 함수 테스트 (매수 신호 판단)"""

    def test_no_signal_above_minus_10(self):
        """
        테스트 1: -10% 미만 하락은 관망 (빈 문자열)
        """
        assert get_buy_signal(-5.0) == ""
        assert get_buy_signal(-9.9) == ""
        assert get_buy_signal(0.0) == ""

    def test_first_buy_signal(self):
        """
        테스트 2: -10% ~ -20% 하락은 1차 매수

        -10% 이상 -20% 미만 하락 시 "1차 매수 (정찰병)"
        """
        assert get_buy_signal(-10.0) == "1차 매수 (정찰병)"
        assert get_buy_signal(-15.0) == "1차 매수 (정찰병)"
        assert get_buy_signal(-19.9) == "1차 매수 (정찰병)"

    def test_second_buy_signal(self):
        """
        테스트 3: -20% ~ -30% 하락은 2차 매수

        -20% 이상 -30% 미만 하락 시 "2차 매수 (비중 확대)"
        """
        assert get_buy_signal(-20.0) == "2차 매수 (비중 확대)"
        assert get_buy_signal(-25.0) == "2차 매수 (비중 확대)"
        assert get_buy_signal(-29.9) == "2차 매수 (비중 확대)"

    def test_third_buy_signal(self):
        """
        테스트 4: -30% 이상 하락은 3차 매수

        -30% 이상 하락 시 "3차 매수 (과매도 구간)"
        """
        assert get_buy_signal(-30.0) == "3차 매수 (과매도 구간)"
        assert get_buy_signal(-40.0) == "3차 매수 (과매도 구간)"
        assert get_buy_signal(-50.0) == "3차 매수 (과매도 구간)"
