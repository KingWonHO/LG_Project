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
2. base: `main` <- compare: `feature/wonho-parser` 확인
3. 제목/설명 작성 → **Create pull request**
4. 리뷰어 지정 (메인 소유자)
5. 승인 1개 이상 받으면 **Merge** 가능 (main 보호 규칙)

> 자기 PR은 자기가 승인할 수 없음. 혼자 작업 중이면 ruleset의 Required approvals를 0으로 두거나 bypass에 본인 추가.

---

## 6. 머지 후 정리

```bash
git checkout main
git pull origin main
git branch -d feature/wonho-parser
git push origin --delete feature/wonho-parser   # (선택) 원격 브랜치 삭제
```

---

## 7. 작업 중 main이 바뀌었을 때 (동기화)

```bash
git checkout main
git pull origin main
git checkout feature/wonho-parser
git merge main          # 또는 git rebase main
# 충돌 나면 파일 수정 → git add <파일> → git commit / git rebase --continue
git push
```

---

## 충돌(conflict) 기본 대처

1. 충돌 파일 열면 `<<<<<<<`, `=======`, `>>>>>>>` 표시가 있음
2. 원하는 내용으로 정리하고 표시 마커 삭제
3. `git add <파일>` → `git commit` 또는 `git rebase --continue`

> 충돌을 줄이려면: 사람별로 건드리는 파일/폴더를 나누고, 작업 전 항상 main을 pull.

---

## 빠른 치트시트

```bash
git status
git branch
git checkout main
git checkout -b feature/x
git add -A && git commit -m "..."
git push -u origin feature/x
git pull origin main
git log --oneline -10
```

---

## 황금 규칙

1. main에서 직접 작업 금지 — 항상 브랜치 만들고 시작
2. 작업 전 `git pull origin main` — 최신 상태에서 시작
3. PR로만 머지 — 리뷰 후 반영
4. 작은 단위로 자주 커밋·PR — 충돌과 리뷰 부담 감소

---

_최종 수정: 2026-06-18_
