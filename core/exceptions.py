# core/exceptions.py
from typing import Dict

KMA_ERROR_CODES: Dict[str, str] = {
    "00": "정상 (NORMAL_SERVICE)",
    "01": "어플리케이션 에러 (APPLICATION_ERROR)",
    "02": "데이터베이스 에러 (DB_ERROR)",
    "03": "데이터없음 에러 (NODATA_ERROR)",
    "04": "HTTP 에러 (HTTP_ERROR)",
    "05": "서비스 연결실패 에러 (SERVICETIME_OUT)",
    "10": "잘못된 요청 파라메터 에러 (INVALID_REQUEST_PARAMETER_ERROR)",
    "11": "필수요청 파라메터가 없음 (NO_MANDATORY_REQUEST_PARAMETERS_ERROR)",
    "12": "해당 오픈API서비스가 없거나 폐기됨 (NO_OPENAPI_SERVICE_ERROR)",
    "20": "서비스 접근거부 (SERVICE_ACCESS_DENIED_ERROR)",
    "21": "일시적으로 사용할 수 없는 서비스 키 (TEMPORARILY_DISABLE_THE_SERVICEKEY_ERROR)",
    "22": "서비스 요청제한횟수 초과에러 (LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR)",
    "30": "등록되지 않은 서비스키 (SERVICE_KEY_IS_NOT_REGISTERED_ERROR)",
    "31": "기한만료된 서비스키 (DEADLINE_HAS_EXPIRED_ERROR)",
    "32": "등록되지 않은 IP (UNREGISTERED_IP_ERROR)",
    "33": "서명되지 않은 호출 (UNSIGNED_CALL_ERROR)",
    "99": "기타에러 (UNKNOWN_ERROR)"
}

class KMAApiException(Exception):
    """기상청 API 관련 커스텀 예외"""
    def __init__(self, result_code: str, result_msg: str):
        self.result_code = result_code
        self.result_msg = result_msg
        self.kr_description = KMA_ERROR_CODES.get(result_code, "알 수 없는 에러")
        super().__init__(f"[{result_code}] {self.kr_description} - {result_msg}")

def get_kma_error_message(result_code: str) -> str:
    """에러 코드에 해당하는 한글 설명을 반환"""
    return KMA_ERROR_CODES.get(result_code, "정의되지 않은 기상청 에러")
