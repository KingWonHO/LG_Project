# Git 협업 워크플로

> 4인 협업 / main 보호(PR 필수). main에는 직접 push 금지, 항상 브랜치 → PR로 머지.

---

## 0. 최초 1회 (저장소 받기)

```bash
git clone https://github.com/KingWonHO/LG_Project.git
cd LG_Project
uv sync            # 의존성 설치
```

---

## 1. 작업 시작 전: main 최신화

작업 시작할 때마다 항상 먼저 실행한다.

```bash
git checkout main
git pull origin main
```

---

## 2. 작업 브랜치 생성

main에서 새 브랜치를 딴다. 이름 규칙: `feature/<이름>-<작업>`

```bash
git checkout -b feature/wonho-parser
```

브랜치 이름 예시:
- `feature/wonho-backend-parser` (기능 추가)
- `fix/jihye-chart-bug` (버그 수정)
- `docs/minsu-readme` (문서)

---

## 3. 작업 → 커밋

```bash
# 파일 수정 후
git add -A
git commit -m "feat: file_parser CSV/XLSX 파싱 구현 (ANA-001)"
```

커밋 메시지 권장 형식: `타입: 설명 (기능ID)`
- `feat:` 기능, `fix:` 버그, `docs:` 문서, `refactor:` 리팩터, `chore:` 잡일

> 작업이 길면 중간중간 자주 커밋. 한 커밋엔 한 가지 일만.

---

## 4. 원격에 push

```bash
git push -u origin feature/wonho-parser
# 이후 같은 브랜치는 git push 만으로 OK
```

---

## 5. Pull Request 생성

1. GitHub 저장소 접속 → 노란 배너 **Compare & pull request** 클릭
   (또는 Pull requests 탭 → New pull request)
2. base: `main` ← compare: `feature/wonho-parser` 확인
3. 제목/설명 작성 → **Create pull request**
4. 리뷰어 지정 (메인 소유자)
5. 승인 1개 이상 받으면 **Merge** 가능 (main 보호 규칙)

---

## 6. 머지 후 정리

PR이 머지되면 로컬 정리하고 다시 main 최신화.

```bash
git checkout main
git pull origin main
git branch -d feature/wonho-parser          # 로컬 브랜치 삭제
git push origin --delete feature/wonho-parser  # (선택) 원격 브랜치 삭제
```

---

## 7. 작업 중 main이 바뀌었을 때 (동기화)

내 브랜치에서 작업하는 동안 다른 사람이 main에 머지했다면, 최신 main을 내 브랜치에 반영한다.

```bash
git checkout main
git pull origin main
git checkout feature/wonho-parser
git merge main          # 또는 git rebase main
# 충돌 나면 해당 파일 수정 → git add <파일> → git commit (merge) / git rebase --continue
git push
```

---

## 충돌(conflict) 기본 대처

1. 충돌 파일 열면 `<<<<<<<`, `=======`, `>>>>>>>` 표시가 있음
2. 원하는 내용으로 직접 정리하고 표시 마커 삭제
3. `git add <파일>` → `git commit` (merge) 또는 `git rebase --continue`

> 충돌을 줄이려면: 사람별로 건드리는 파일/폴더를 나누고, 작업 전 항상 main을 pull.

---

## 빠른 치트시트

```bash
git status                 # 현재 상태
git branch                 # 브랜치 목록
git checkout main          # 브랜치 이동
git checkout -b feature/x  # 새 브랜치 만들고 이동
git add -A && git commit -m "..."
git push -u origin feature/x
git pull origin main
git log --oneline -10      # 최근 커밋 보기
```

---

## 황금 규칙

1. **main에서 직접 작업 금지** — 항상 브랜치 만들고 시작
2. **작업 전 `git pull origin main`** — 최신 상태에서 시작
3. **PR로만 머지** — 리뷰 후 반영
4. **작은 단위로 자주 커밋·PR** — 충돌과 리뷰 부담↓

---

_최종 수정: 2026-06-18_
