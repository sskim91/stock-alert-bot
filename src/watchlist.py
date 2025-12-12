"""Watchlist 관리 모듈

JSON 파일 기반으로 관심 종목과 200일선 분석 설정을 관리합니다.

파일 위치: data/watchlist.json
구조:
{
    "symbols": ["TSLA", "SCHD", "SCHG"],
    "ma_enabled": ["TSLA"]
}
"""

import json
from pathlib import Path

from src.config import Config

# 데이터 파일 경로
DATA_DIR = Path(__file__).parent.parent / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"


def _ensure_data_dir():
    """data 디렉토리가 없으면 생성"""
    DATA_DIR.mkdir(exist_ok=True)


def _get_default_symbols() -> list[str]:
    """환경변수에서 기본 종목 리스트 로드"""
    default_str = Config.DEFAULT_SYMBOLS
    return [s.strip().upper() for s in default_str.split(",") if s.strip()]


def _get_default_ma_symbols() -> list[str]:
    """환경변수에서 기본 MA 활성화 종목 로드"""
    default_str = Config.DEFAULT_MA_SYMBOLS
    if not default_str:
        return []
    return [s.strip().upper() for s in default_str.split(",") if s.strip()]


def load() -> dict:
    """JSON 파일에서 watchlist 로드 (없으면 기본값으로 초기화)"""
    _ensure_data_dir()

    if WATCHLIST_FILE.exists():
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # dict가 아니면 잘못된 형식
                if not isinstance(data, dict):
                    raise json.JSONDecodeError("JSON root is not an object", "", 0)
                # 필수 키가 없으면 추가
                if "symbols" not in data:
                    data["symbols"] = _get_default_symbols()
                if "ma_enabled" not in data:
                    data["ma_enabled"] = _get_default_ma_symbols()
                return data
        except (json.JSONDecodeError, IOError, TypeError):
            pass

    # 파일이 없거나 읽기 실패 시 기본값
    default_data = {
        "symbols": _get_default_symbols(),
        "ma_enabled": _get_default_ma_symbols(),
    }
    save(default_data)
    return default_data


def save(data: dict) -> bool:
    """watchlist를 JSON 파일에 저장"""
    _ensure_data_dir()
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def get_all() -> list[str]:
    """전체 종목 리스트 반환"""
    data = load()
    return data.get("symbols", [])


def add(symbol: str) -> tuple[bool, str]:
    """종목 추가

    Returns:
        (성공여부, 메시지)
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return False, "종목 코드를 입력해주세요."

    data = load()
    if symbol in data["symbols"]:
        return False, f"{symbol}은(는) 이미 등록되어 있습니다."

    data["symbols"].append(symbol)
    save(data)
    return True, f"{symbol} 추가됨"


def remove(symbol: str) -> tuple[bool, str]:
    """종목 삭제

    Returns:
        (성공여부, 메시지)
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return False, "종목 코드를 입력해주세요."

    data = load()
    if symbol not in data["symbols"]:
        return False, f"{symbol}은(는) 목록에 없습니다."

    data["symbols"].remove(symbol)
    # MA 목록에서도 제거
    if symbol in data.get("ma_enabled", []):
        data["ma_enabled"].remove(symbol)
    save(data)
    return True, f"{symbol} 삭제됨"


def is_ma_enabled(symbol: str) -> bool:
    """해당 종목의 MA 분석 활성화 여부"""
    symbol = symbol.strip().upper()
    data = load()
    return symbol in data.get("ma_enabled", [])


def set_ma(symbol: str, enabled: bool) -> tuple[bool, str]:
    """종목의 MA 분석 설정 변경

    Returns:
        (성공여부, 메시지)
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return False, "종목 코드를 입력해주세요."

    data = load()
    if symbol not in data["symbols"]:
        return False, f"{symbol}은(는) 관심 종목에 없습니다."

    ma_list = data.get("ma_enabled", [])

    if enabled:
        if symbol in ma_list:
            return False, f"{symbol}은(는) 이미 MA 분석이 활성화되어 있습니다."
        ma_list.append(symbol)
        data["ma_enabled"] = ma_list
        save(data)
        return True, f"{symbol} 200일선 분석 활성화"
    else:
        if symbol not in ma_list:
            return False, f"{symbol}은(는) MA 분석이 비활성화 상태입니다."
        ma_list.remove(symbol)
        data["ma_enabled"] = ma_list
        save(data)
        return True, f"{symbol} 200일선 분석 비활성화"


def get_ma_symbols() -> list[str]:
    """MA 분석이 활성화된 종목 리스트"""
    data = load()
    return data.get("ma_enabled", [])
