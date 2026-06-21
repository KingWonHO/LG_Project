# Ollama (로컬 LLM) 설치 · 연결 가이드

> 이 프로젝트의 백엔드는 `src/llm_report.py`에서 **`ollama` 파이썬 패키지**로
> **로컬 Ollama 데몬(`http://localhost:11434`)**에 접속한다.
> vLLM/`LLM_BASE_URL` 방식이 아니다. (그 항목들은 현재 코드 미사용)

핵심 3가지만 맞으면 동작한다:
1. Ollama 앱(데몬)이 설치되어 11434에서 실행 중
2. 사용할 모델을 `ollama pull` 로 받아둠 (기본 `gemma3:4b`)
3. 백엔드 가상환경에 `ollama` 파이썬 패키지 설치됨 (`uv sync` 시 자동)

---

## 1. Ollama 설치 (Windows)

방법 A — 설치 파일 (권장)
1. https://ollama.com/download/windows 에서 `OllamaSetup.exe` 다운로드
2. 실행 → 설치 (Windows 10/11 64bit). 설치 후 **백그라운드 서비스로 자동 실행**되고 API가 `http://localhost:11434`에 열린다.

방법 B — winget (PowerShell)
```powershell
winget install Ollama.Ollama
```

설치 확인:
```powershell
ollama --version
```
> `'ollama' 용어가 인식되지 않습니다` 가 나오면 → 터미널을 **새로 열거나** PC 재로그인 (PATH 갱신). 그래도 안 되면 설치가 안 된 것.

시스템 요건: 디스크 최소 4GB(+모델 수~수십 GB), RAM 8GB 이상(권장 16GB+). GPU 없어도 CPU로 동작(느림).

---

## 2. 데몬 실행 확인

Ollama 앱이 실행 중이면 데몬은 자동으로 떠 있다. 확인:
```powershell
ollama list                                   # 설치된 모델 목록
curl http://localhost:11434/api/tags          # JSON 응답이 오면 데몬 정상
```
- 응답이 없으면 시작 메뉴에서 **Ollama** 실행, 또는 `ollama serve` 수동 실행.

---

## 3. 모델 받기 (pull)

기본 모델(gemma3:4b):
```powershell
ollama pull gemma3:4b
```
Qwen을 쓰려면:
```powershell
ollama pull qwen2.5:3b
```
받은 모델 단독 테스트:
```powershell
ollama run gemma3:4b "한 문장으로 자기소개 해줘"
```
→ 답변이 나오면 LLM 자체는 정상.

---

## 4. 백엔드와 연결

백엔드 `.env`:
```
LOCAL_LLM_MODEL=gemma3:4b      # Qwen이면 qwen2.5:3b
# OLLAMA_HOST=http://localhost:11434   # 기본값이라 보통 생략
```
- 모델 선택 우선순위: 함수 인자 > 환경변수 `LOCAL_LLM_MODEL` > 기본값 `gemma3:4b`.
- 백엔드 의존성 설치(`ollama` 포함):
```bash
cd backend
uv sync
```

연결 테스트 (백엔드 폴더에서):
```bash
uv run python test_llm_report.py
```
→ gemma3/qwen2.5/llama3.2 각 모델로 요약문이 출력되면 **연결 성공**.

---

## 5. 자주 나는 문제 (Troubleshooting)

| 증상 | 원인 | 해결 |
|------|------|------|
| `'ollama' 인식 안 됨` | PATH 미반영/미설치 | 터미널 새로 열기, 재로그인, 재설치 |
| 요약에 `[로컬 LLM 호출 실패…]` | 데몬 미실행 또는 모델 미pull | `ollama list`로 모델 확인, 앱 실행 확인 |
| `model "gemma3:4b" not found` | 모델 안 받음 | `ollama pull gemma3:4b` |
| `ModuleNotFoundError: ollama` | 파이썬 패키지 누락 | `uv sync` (또는 `uv add ollama`) |
| 연결은 되는데 매우 느림 | GPU 없음/모델 큼 | 더 작은 모델(`qwen2.5:3b`) 사용, GPU 권장 |
| 포트 충돌(11434) | 다른 프로세스 점유 | 해당 프로세스 종료 또는 `OLLAMA_HOST` 변경 |

> 중요: 데몬이 안 떠 있거나 모델이 없어도 백엔드는 **죽지 않고 rule-based 요약으로 폴백**한다.
> 요약 앞에 `[로컬 LLM 호출 실패…]` 문구가 보이면 = Ollama가 실제로는 연결 안 된 상태다.

---

## 6. Docker로 띄울 때

`docker-compose.yml`의 `qwen` 서비스(ollama 이미지)가 데몬 역할. 단, 백엔드 코드는
`ollama` 파이썬 패키지가 기본 `localhost:11434`를 보므로, 컨테이너에서는
백엔드 환경변수에 `OLLAMA_HOST=http://qwen:11434`를 지정해야 한다(서비스명으로 접속).
모델은 최초 1회 받아야 함:
```bash
docker exec -it lgproject-qwen ollama pull gemma3:4b
```

---

_최종 수정: 2026-06-21_
