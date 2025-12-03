"""fear_greed.py 테스트 코드

Fear & Greed Index API 호출이 정상 작동하는지 테스트

fixture란?
- 테스트에 필요한 데이터를 미리 준비해두는 것
- 여러 테스트에서 같은 데이터를 재사용할 수 있음
- API 호출을 한 번만 하면 되니까 빠르고 효율적!
"""

import pytest
from src.indicators.fear_greed import get_fear_greed_index


@pytest.fixture(scope="module")
def fear_greed_result():
    """
    fixture: API를 한 번만 호출하고 결과를 재사용

    scope="module" 의미:
    - 이 파일의 모든 테스트가 같은 결과를 공유
    - API 호출이 1번만 일어남 (4번 → 1번으로 줄어듦!)
    """
    return get_fear_greed_index()


class TestGetFearGreedIndex:
    """get_fear_greed_index 함수 테스트"""

    def test_returns_dict(self, fear_greed_result):
        """
        테스트 1: 함수가 딕셔너리를 반환하는지 확인
        """
        # 결과가 딕셔너리인지 확인
        assert isinstance(fear_greed_result, dict)

    def test_has_required_keys(self, fear_greed_result):
        """
        테스트 2: 필수 키(score, rating)가 있는지 확인
        """
        # score와 rating 키가 있어야 함
        assert "score" in fear_greed_result
        assert "rating" in fear_greed_result

    def test_score_range(self, fear_greed_result):
        """
        테스트 3: score가 0-100 사이인지 확인 (성공 시)

        Fear & Greed Index는 0에서 100 사이의 값
        """
        # API 호출 성공 시에만 검증
        if fear_greed_result["score"] is not None:
            assert 0 <= fear_greed_result["score"] <= 100

    def test_rating_is_valid(self, fear_greed_result):
        """
        테스트 4: rating이 유효한 값인지 확인

        가능한 값: extreme fear, fear, neutral, greed, extreme greed, unknown
        """
        valid_ratings = [
            "extreme fear",
            "fear",
            "neutral",
            "greed",
            "extreme greed",
            "unknown",  # 에러 시
        ]

        assert fear_greed_result["rating"] in valid_ratings
