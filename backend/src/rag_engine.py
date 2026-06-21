"""rag_engine 모듈: ChromaDB + sentence-transformers 기반 RAG (RAG-001, RAG-002).

RAG-001: Trip Code 지식 데이터를 임베딩 후 ChromaDB에 저장
RAG-002: 분석 결과 기반 유사 Trip Code 검색 → LLM 프롬프트 컨텍스트 생성
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from src.config import settings

# ---------------------------------------------------------------------------
# 싱글톤: 임베딩 모델 + Chroma 클라이언트
# ---------------------------------------------------------------------------

_embedder: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None

COLLECTION_TRIP = "trip_codes"


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


def _get_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def _get_collection(name: str) -> chromadb.Collection:
    return _get_client().get_or_create_collection(name=name)


# ---------------------------------------------------------------------------
# RAG-001: 지식 데이터 인덱싱
# ---------------------------------------------------------------------------


def index_trip_codes(trip_codes: list[dict]) -> int:
    """Trip Code 정보를 ChromaDB에 임베딩 후 저장 (upsert — 중복 안전).

    Args:
        trip_codes: trip_no, trip_key, trip_name_ko, summary_ko, solution 키를 가진 dict 리스트
    Returns:
        인덱싱된 건수
    """
    if not trip_codes:
        return 0

    collection = _get_collection(COLLECTION_TRIP)
    embedder = _get_embedder()

    ids, documents, metadatas = [], [], []
    for tc in trip_codes:
        doc = f"[{tc.get('trip_key', '')}] {tc.get('trip_name_ko', '')}\n{tc.get('summary_ko', '')}"
        solution = tc.get("solution")
        if solution:
            sol_text = (
                " ".join(str(v) for v in solution.values())
                if isinstance(solution, dict)
                else str(solution)
            )
            doc += f"\n조치: {sol_text}"

        ids.append(str(tc["trip_no"]))
        documents.append(doc)
        metadatas.append({
            "trip_no": int(tc["trip_no"]),
            "trip_key": tc.get("trip_key", ""),
            "trip_name_ko": tc.get("trip_name_ko", ""),
        })

    embeddings = embedder.encode(documents, normalize_embeddings=True).tolist()
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    return len(ids)


def index_trip_codes_from_db() -> int:
    """DB의 Trip Code 전체를 읽어 Chroma에 인덱싱 (RAG-001 자동 호출용)."""
    from src.db_manager import get_all_trip_codes

    rows = get_all_trip_codes()
    if not rows:
        return 0
    return index_trip_codes([
        {
            "trip_no": r.trip_no,
            "trip_key": r.trip_key,
            "trip_name_ko": r.trip_name_ko,
            "summary_ko": r.summary_ko,
            "solution": r.solution,
        }
        for r in rows
    ])


# ---------------------------------------------------------------------------
# RAG-002: 유사 검색
# ---------------------------------------------------------------------------


def search_trip_codes(query: str, n_results: int = 5) -> list[dict]:
    """분석 결과 쿼리와 유사한 Trip Code를 ChromaDB에서 검색.

    Args:
        query: 검색 텍스트 (판정 + trip/baseline 이탈 정보 등)
        n_results: 반환할 최대 결과 수
    Returns:
        [{trip_no, trip_key, trip_name_ko, document, distance}, ...]
    """
    collection = _get_collection(COLLECTION_TRIP)
    if collection.count() == 0:
        return []

    embedder = _get_embedder()
    query_embedding = embedder.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "trip_no": meta.get("trip_no"),
            "trip_key": meta.get("trip_key", ""),
            "trip_name_ko": meta.get("trip_name_ko", ""),
            "document": doc,
            "distance": round(dist, 4),
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def build_rag_context(analysis_result: dict, n_results: int = 5) -> str:
    """분석 결과 dict → 검색 쿼리 구성 → LLM 주입용 컨텍스트 문자열 반환 (RAG-002).

    Args:
        analysis_result: /api/analyze 응답 형식
            {verdict, trip: {count, ranges}, baseline: {out_of_range}, quality: {...}}
        n_results: 검색할 유사 문서 수
    Returns:
        LLM 프롬프트에 삽입할 참고 자료 문자열 (없으면 빈 문자열)
    """
    parts = [f"판정: {analysis_result.get('verdict', '')}"]

    trip = analysis_result.get("trip") or {}
    if trip.get("count", 0) > 0:
        parts.append(f"Trip 발생 횟수: {trip['count']}회")

    out_of_range = (analysis_result.get("baseline") or {}).get("out_of_range", [])
    if out_of_range:
        parts.append(f"Baseline 이탈 항목: {', '.join(out_of_range)}")

    hits = search_trip_codes(" ".join(parts), n_results=n_results)
    if not hits:
        return ""

    lines = ["[유사 Trip Code 참고 자료]"]
    for h in hits:
        lines.append(f"- {h['trip_key']} ({h['trip_name_ko']}): {h['document'][:200]}")
    return "\n".join(lines)
