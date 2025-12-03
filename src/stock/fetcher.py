"""주가 데이터 수집 모듈 (yfinance 활용)"""
import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    yfinance를 사용하여 특정 기간의 주식 데이터를 가져옵니다.

    Args:
        symbol: 주식 심볼 (예: 'TSLA', 'AAPL')
        period: 데이터 조회 기간 (예: '1d', '5d', '1mo', '1y', 'max')

    Returns:
        주가 정보가 담긴 pandas DataFrame. 데이터가 없거나 오류 발생 시 빈 DataFrame을 반환합니다.
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if data.empty:
            print(f"'{symbol}'에 대한 데이터를 찾을 수 없습니다.")
            return pd.DataFrame()
        return data
    except Exception as e:
        print(f"'{symbol}' 데이터 조회 중 오류 발생: {e}")
        return pd.DataFrame()
