"""Fear & Greed Index 수집 모듈

Fear & Greed Index란?
- CNN에서 제공하는 시장 심리 지표
- 0~100 사이의 숫자로 표현
- 0에 가까울수록 공포(Fear), 100에 가까울수록 탐욕(Greed)

점수 해석:
- 0-24:  Extreme Fear (극도의 공포) - 투자자들이 매우 두려워함
- 25-44: Fear (공포)
- 45-55: Neutral (중립)
- 56-75: Greed (탐욕)
- 76-100: Extreme Greed (극도의 탐욕) - 시장 과열 가능성
"""

import requests

# CNN Fear & Greed API 주소
API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# 브라우저인 척 하기 위한 헤더 (없으면 API가 거부할 수 있음)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_fear_greed_index() -> dict:
    """
    CNN Fear & Greed Index를 가져옵니다.

    Returns:
        성공 시:
        {
            "score": 24.4,           # 현재 점수 (0-100)
            "rating": "extreme fear", # 상태 설명
            "previous_close": 24.3,  # 어제 점수
            "previous_1_week": 18.7, # 1주 전 점수
        }

        실패 시:
        {
            "score": None,
            "rating": "unknown",
            "error": "에러 메시지"
        }
    """
    try:
        # 1. API 호출
        # requests.get(): 웹에서 데이터를 가져오는 함수
        # timeout=10: 10초 안에 응답 없으면 포기
        response = requests.get(API_URL, headers=HEADERS, timeout=10)

        # 2. 응답 상태 확인
        # 200 = 성공, 그 외 = 실패
        if response.status_code != 200:
            return {
                "score": None,
                "rating": "unknown",
                "error": f"API 응답 실패: {response.status_code}",
            }

        # 3. JSON 데이터 파싱 (문자열 → 파이썬 딕셔너리)
        data = response.json()

        # 4. 필요한 데이터 추출
        fear_greed = data["fear_and_greed"]

        return {
            "score": fear_greed["score"],
            "rating": fear_greed["rating"],
            "previous_close": fear_greed.get("previous_close"),
            "previous_1_week": fear_greed.get("previous_1_week"),
        }

    except requests.exceptions.Timeout:
        # 시간 초과
        return {
            "score": None,
            "rating": "unknown",
            "error": "API 요청 시간 초과",
        }

    except requests.exceptions.RequestException as e:
        # 네트워크 에러
        return {
            "score": None,
            "rating": "unknown",
            "error": f"네트워크 에러: {e}",
        }

    except (KeyError, ValueError) as e:
        # 데이터 파싱 에러
        return {
            "score": None,
            "rating": "unknown",
            "error": f"데이터 파싱 에러: {e}",
        }
