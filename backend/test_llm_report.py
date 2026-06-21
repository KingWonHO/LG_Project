from src.llm_report import generate_llm_summary


sample_analysis_json = {
    "final_judgement": "FAIL",
    "trip_count": 2,
    "abnormal_items": ["Vdc 저하", "Temperature 상승"],
    "baseline_deviation": [
        {
            "column": "Vdc",
            "status": "low",
            "description": "정상 기준보다 낮은 전압 구간 발생",
        },
        {
            "column": "Temperature",
            "status": "high",
            "description": "온도 상승 구간 발생",
        },
    ],
    "data_quality": "정상",
    "root_cause_candidates": ["전원 공급 불안정", "냉각 성능 저하"],
    "recommended_actions": ["전원부 점검", "냉각 조건 확인"],
}

sample_rag_results = [
    "Vdc 저하는 전원 공급 불안정 또는 인버터 입력 전압 문제와 관련될 수 있다.",
    "Temperature 상승은 냉각 조건 불량, 과부하 운전, 센서 이상 가능성과 관련된다.",
]


candidate_models = [
    "gemma3:4b",
    "qwen2.5:3b",
    "llama3.2",
]


if __name__ == "__main__":
    for model in candidate_models:
        print("=" * 80)
        print(f"[모델 테스트] {model}")
        print("=" * 80)

        summary = generate_llm_summary(
            analysis_json=sample_analysis_json,
            rag_results=sample_rag_results,
            model_name=model,
        )

        print(summary)
        print()