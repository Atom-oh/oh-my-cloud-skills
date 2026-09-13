---
sidebar_position: 1
title: "Atlas 명령어"
---
# Atlas 명령어

| 워크플로 | 용도 |
| --- | --- |
| `/atlas:init` | 주제 목록을 제안하고 승인된 페이지를 작성한 뒤 INDEX.md를 생성합니다. |
| `/atlas:add-doc` | 대상 범위 메타데이터와 함께 주제 하나를 추가하고 인덱스를 갱신합니다. |
| `/atlas:sync` | 변경 불일치를 감지하고 선택한 오래된 페이지를 수정합니다. |
| `/atlas:graph` | 페이지 간 연결, 고립된 페이지, 끊어진 참조를 표시합니다. |
| `/atlas:configure` | 위키 루트와 동기화 설정을 확인합니다. |

Codex는 이에 대응하는 생성된 스킬을 제공합니다. 무인 Claude 수정 도구는 호스트의 기본 기능을 이용한 수정과 별개의 선택 사항입니다.

## 로컬 점검 {#local-checks}

위키가 있는 저장소의 루트에서 실행합니다. 아래 스크립트 경로는 이 마켓플레이스 체크아웃을 기준으로 합니다:

```bash
python3 plugins/atlas/skills/atlas/scripts/atlas_drift.py --json --root .
python3 plugins/atlas/skills/atlas/scripts/atlas_index.py --validate --root .
```

이 점검에는 Claude CLI가 필요하지 않습니다. 선택적 수정 도구는 `--dry-run`을
사용해도 인수를 해석하기 전에 PATH에서 `claude`를 확인합니다. Claude CLI가 설치되어 있으면
모델을 호출하거나 파일을 쓰지 않고 수정 계획을 미리 확인할 수 있습니다:

```bash
python3 plugins/atlas/skills/atlas/scripts/atlas_sync.py --dry-run --root .
```

이 스크립트에서 `--root`는 위키 디렉터리가 아니라 저장소 루트를 의미합니다. 각 문서는 자체 리비전 기준점을 유지합니다. 범위를 명시하면 모든 문서의 왼쪽 기준점을 바꾸는 대신 비교 대상인 오른쪽 리비전이 바뀝니다.

스키마 오류, 확인할 수 없는 리비전, 로컬 수정, 시간 초과, 작업 범위 제한 실패는 반드시 보고합니다. 푸시 훅이 실패 시 허용하는 동작을 문서의 최신성이 검증된 것으로 오인하지 않습니다.
