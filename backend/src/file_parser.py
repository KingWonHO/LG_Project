"""file_parser 모듈: 업로드 파일 파싱 (ANA-001).

CSV/XLSX 파일을 읽어 pandas DataFrame으로 변환한다.
화면/HTTP에 비의존적인 순수 함수로 작성한다 (main.py가 호출).
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd


class FileParseError(ValueError):
    """업로드 파일을 파싱할 수 없을 때 발생하는 예외."""


def parse_csv(content: bytes) -> pd.DataFrame:
    """CSV 바이트 데이터를 DataFrame으로 변환한다.

    인코딩은 UTF-8(BOM 포함)을 우선 시도하고, 실패하면 CP949(엑셀 한글 CSV)로 재시도한다.
    """
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            raise FileParseError(f"CSV 파싱 실패: {exc}") from exc
    raise FileParseError("CSV 인코딩을 인식할 수 없습니다 (utf-8-sig, cp949 시도 실패).")


def parse_excel(content: bytes) -> pd.DataFrame:
    """XLSX 바이트 데이터를 DataFrame으로 변환한다 (첫 번째 시트 사용)."""
    try:
        return pd.read_excel(BytesIO(content), sheet_name=0, engine="openpyxl")
    except Exception as exc:
        raise FileParseError(f"XLSX 파싱 실패: {exc}") from exc


def parse_file(filename: str, content: bytes) -> pd.DataFrame:
    """파일명 확장자를 기준으로 CSV/XLSX를 분기하여 DataFrame으로 변환한다.

    `main.py`의 `/api/analyze`에서 `UploadFile.filename`, `await file.read()` 결과를 그대로 전달한다.
    """
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "csv":
        return parse_csv(content)
    if suffix in ("xlsx", "xls"):
        return parse_excel(content)
    raise FileParseError(f"지원하지 않는 파일 형식입니다: .{suffix or '(확장자 없음)'}")
