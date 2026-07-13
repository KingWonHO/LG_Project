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
COLLECTION_ENGINEER = "engineer_rag"

# 엔지니어 등록 룰이 이 거리(distance) 이내로 유사하면 기존 trip_codes 대신 엔지니어 룰을 우선 사용.
# 임베딩 정규화(cosine 계열) 기준의 경험값 — 실제 데이터로 조정 가능.
ENGINEER_MATCH_THRESHOLD = 1.0


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


def search_trip_codes(query: str, n_results: int = 5, trip_nos: list[int] | None = None) -> list[dict]:
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

    query_kwargs = dict(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    # 실제 발생한 Trip Code로만 한정 (의미 유사도만으로 무관한 트립이 딸려오는 것 방지)
    if trip_nos:
        query_kwargs["where"] = {"trip_no": {"$in": [int(x) for x in trip_nos]}}
    results = collection.query(**query_kwargs)
    if not results["ids"] or not results["ids"][0]:
        return []

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


def _build_signature(analysis_result: dict) -> str:
    """분석 결과 → 유사도 비교용 시그니처 텍스트.

    검색 쿼리와 엔지니어 룰 인덱싱 임베딩이 **같은 형식**이어야 매칭되므로 공용 함수로 둔다.
    """
    parts = [f"판정: {analysis_result.get('verdict', '')}"]
    trip = analysis_result.get("trip") or {}
    if trip.get("count", 0) > 0:
        parts.append(f"Trip 발생 횟수: {trip['count']}회")
    out_of_range = (analysis_result.get("baseline") or {}).get("out_of_range", [])
    if out_of_range:
        parts.append(f"Baseline 이탈 항목: {', '.join(out_of_range)}")
    return " ".join(parts)


def index_engineer_rule(rule_name: str, interpretation: str, signature_text: str,
                        extra_meta: dict | None = None) -> str:
    """엔지니어가 등록한 룰(해석)을 CSV 분석 시그니처 임베딩으로 engineer_rag 컬렉션에 저장 (RAG-001 확장).

    embedding = 시그니처(판정/트립/이탈) → 이후 유사 분석이 오면 매칭.
    document  = 엔지니어 해석 텍스트 → 매칭 시 LLM 컨텍스트로 반환.
    """
    import uuid

    collection = _get_collection(COLLECTION_ENGINEER)
    emb = _get_embedder().encode([signature_text], normalize_embeddings=True).tolist()
    rid = f"eng-{uuid.uuid4().hex[:12]}"
    meta: dict = {"rule_name": rule_name, "signature": signature_text}
    if extra_meta:
        meta.update({k: v for k, v in extra_meta.items() if isinstance(v, (str, int, float, bool))})
    collection.upsert(ids=[rid], documents=[interpretation], metadatas=[meta], embeddings=emb)
    return rid


def search_engineer_rules(query: str, n_results: int = 3) -> list[dict]:
    """engineer_rag 컬렉션에서 시그니처 유사 룰 검색."""
    collection = _get_collection(COLLECTION_ENGINEER)
    if collection.count() == 0:
        return []
    emb = _get_embedder().encode([query], normalize_embeddings=True).tolist()
    res = collection.query(
        query_embeddings=emb,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"document": d, "metadata": m or {}, "distance": round(dist, 4)}
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def engineer_rules_count() -> int:
    """engineer_rag 컬렉션에 등록된 룰 수."""
    try:
        return _get_collection(COLLECTION_ENGINEER).count()
    except Exception:
        return 0


def _occurred_trip_codes(analysis_result: dict) -> list[int]:
    """분석 결과에서 실제 발생한 Trip Code 목록을 추출한다 (trip_events 우선)."""
    codes: set[int] = set()
    for ev in (analysis_result.get("trip_events") or []):
        for c in (ev.get("codes") or []):
            try:
                codes.add(int(c))
            except (TypeError, ValueError):
                pass
    # 폴백: analysis에 trip_codes 리스트가 있으면 사용
    for c in (analysis_result.get("trip_codes") or []):
        try:
            codes.add(int(c))
        except (TypeError, ValueError):
            pass
    return sorted(codes)


def build_rag_context(analysis_result: dict, n_results: int = 5) -> str:
    """분석 결과 → 이중 검색 후 LLM 주입용 컨텍스트 문자열 반환 (RAG-002).

    1) 엔지니어 등록 룰(engineer_rag)에서 유사 사례 검색 → 임계값(ENGINEER_MATCH_THRESHOLD)
       이내로 유사하면 그 룰을 우선 사용.
    2) 유사한 엔지니어 룰이 없으면 기존 Trip Code 지식(trip_codes)을 사용.
    """
    query = _build_signature(analysis_result)

    # 1) 엔지니어 룰 우선 (유사할 때만)
    eng_hits = [h for h in search_engineer_rules(query, n_results=3) if h["distance"] <= ENGINEER_MATCH_THRESHOLD]
    if eng_hits:
        lines = ["[엔지니어 등록 유사 사례/룰]"]
        for h in eng_hits:
            name = (h["metadata"] or {}).get("rule_name", "")
            lines.append(f"- {name}: {h['document'][:300]}")
        return "\n".join(lines)

    # 2) Trip Code 지식 — 실제 발생한 트립 코드로만 한정 (무관한 트립 딸려오기 방지)
    occurred = _occurred_trip_codes(analysis_result)
    if not occurred:
        # 실제 발생 트립이 없으면 트립 지식은 붙이지 않는다 (관련 없는 내용 차단)
        return ""
    hits = search_trip_codes(query, n_results=len(occurred), trip_nos=occurred)
    if not hits:
        return ""
    lines = ["[발생 Trip Code 참고 자료]"]
    for h in hits:
        lines.append(f"- {h['trip_key']} ({h['trip_name_ko']}): {h['document'][:200]}")
    return "\n".join(lines)
