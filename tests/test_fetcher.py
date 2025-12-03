"""fetcher.py 테스트 코드

테스트란?
- 함수가 예상대로 작동하는지 확인하는 코드
- 버그를 미리 발견할 수 있음
- 코드를 수정해도 기존 기능이 깨지지 않았는지 확인 가능
"""

import pandas as pd
from src.stock.fetcher import fetch_stock_data


class TestFetchStockData:
    """fetch_stock_data 함수 테스트"""

    def test_valid_symbol_returns_dataframe(self):
        """
        테스트 1: 유효한 심볼(TSLA)을 넣으면 데이터가 나와야 함

        기대 결과:
        - 빈 DataFrame이 아님
        - Close(종가) 컬럼이 있음
        """
        # 실행
        result = fetch_stock_data("TSLA", period="5d")

        # 검증
        assert isinstance(result, pd.DataFrame)  # DataFrame 타입인가?
        assert not result.empty  # 비어있지 않은가?
        assert "Close" in result.columns  # Close 컬럼이 있는가?

    def test_invalid_symbol_returns_empty_dataframe(self):
        """
        테스트 2: 존재하지 않는 심볼을 넣으면 빈 DataFrame 반환

        기대 결과:
        - 빈 DataFrame을 반환 (에러 대신)
        """
        # 실행 - 존재하지 않는 심볼
        result = fetch_stock_data("INVALID_SYMBOL_12345")

        # 검증
        assert isinstance(result, pd.DataFrame)
        assert result.empty  # 빈 DataFrame이어야 함

    def test_different_periods(self):
        """
        테스트 3: 다양한 기간 옵션이 작동하는지 확인

        기대 결과:
        - 1개월(1mo) 데이터 요청 시 데이터가 반환됨
        """
        # 실행
        result = fetch_stock_data("SCHD", period="1mo")

        # 검증
        assert not result.empty
        assert len(result) > 5  # 1개월이면 5일 이상 데이터가 있어야 함
