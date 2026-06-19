"""file_parser 모듈: 업로드 파일 파싱 (ANA-001).

CSV/XLSX 파일을 읽어 pandas DataFrame으로 변환한다.
화면/HTTP에 비의존적인 순수 함수로 작성한다 (main.py가 호출).
"""

from __future__ import annotations


class FileParseError(ValueError):
    """업로드 파일을 파싱할 수 없을 때 발생하는 예외."""
