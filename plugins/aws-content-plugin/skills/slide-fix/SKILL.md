---
name: slide-fix
description: "Remarp 슬라이드 이슈 어노테이션(<!-- issue: -->)을 읽고 수정 반영. Triggers: /slide-fix, issue 반영, slide fix, 이슈 수정, 슬라이드 이슈, fix slide issues, apply issue annotations"
model: sonnet
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
---

# Slide Fix Skill

Remarp `.md` 파일에 삽입된 `<!-- issue: 내용 -->` 어노테이션을 읽고, 각 이슈를 소스 슬라이드에 반영한 뒤 어노테이션을 제거합니다.

---

## 워크플로우

### Step 1: 이슈 수집

프로젝트 디렉토리 또는 파일 경로를 찾아 `remarp_to_slides.py issues` 명령으로 이슈 목록을 수집합니다.

```bash
# 프로젝트 디렉토리 (여러 .md 파일 스캔)
python3 <script_path>/remarp_to_slides.py issues <project_dir> --json

# 단일 파일
python3 <script_path>/remarp_to_slides.py issues <file.md> --json
```

**스크립트 위치 탐색 순서:**
1. 현재 워크스페이스의 `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
2. `scripts/remarp_to_slides.py`
3. Glob으로 `**/remarp_to_slides.py` 검색

**JSON 출력 형식:**
```json
[
  {
    "file": "docs/static/demos/my-session/01-intro.md",
    "block": "01-intro",
    "slide": 3,
    "title": "Architecture Overview",
    "issue": "다이어그램을 추가해주세요"
  }
]
```

### Step 2: 이슈별 수정

각 이슈에 대해:

1. **소스 파일 읽기**: `file` 경로의 `.md` 파일을 Read
2. **슬라이드 위치 찾기**: `---` 구분자로 슬라이드를 구분하고 `slide` 번호(1-based)에 해당하는 슬라이드 찾기
3. **이슈 내용 반영**: `issue` 텍스트에 기술된 개선사항을 슬라이드에 적용
   - 텍스트 수정, 레이아웃 변경, 내용 추가/삭제 등
   - Remarp 문법 규칙을 준수 (reactive-presentation SKILL.md 참조)
4. **어노테이션 제거**: 수정 완료 후 해당 `<!-- issue: ... -->` 주석을 제거

### Step 3: 리빌드

모든 이슈 수정 후 HTML을 재생성합니다.

```bash
python3 <script_path>/remarp_to_slides.py build <project_dir>
```

---

## 주의사항

- 한 번에 하나의 이슈씩 처리하고, 각 수정 후 어노테이션을 즉시 제거
- 이슈와 무관한 슬라이드는 수정하지 않음
- `:::html` + `:::css` 블록 수정 시 기존 스타일 패턴 유지
- `:::canvas` DSL은 박스 5개 이상이면 `:::html`로 변환 (reactive-presentation SKILL.md 규칙)
- 이슈가 0개이면 "이슈 어노테이션이 없습니다." 메시지 출력 후 종료

---

## 예시

사용자가 `/slide-fix`를 실행하면:

```
1. remarp_to_slides.py issues docs/static/demos/my-session/ --json
   → 3개 이슈 발견

2. 이슈 1: slide 3 "Architecture Overview" → "다이어그램을 추가해주세요"
   → 01-intro.md 슬라이드 3에 아키텍처 다이어그램 추가
   → <!-- issue: 다이어그램을 추가해주세요 --> 제거

3. 이슈 2: slide 5 "Performance" → "수치를 그래프로 변경"
   → 01-intro.md 슬라이드 5의 텍스트 수치를 :::html 그래프로 변환
   → <!-- issue: 수치를 그래프로 변경 --> 제거

4. 이슈 3: slide 2 "Overview" → "탭으로 분리"
   → 02-deep-dive.md 슬라이드 2를 탭 UI로 재구성
   → <!-- issue: 탭으로 분리 --> 제거

5. remarp_to_slides.py build docs/static/demos/my-session/
   → HTML 재생성 완료
```
