---
sidebar_position: 1
title: "Atlas"
---
# Atlas

git 기반 변경 불일치 감지와 선택적 푸시 시 동기화로 주제별 저장소 위키를 관리합니다.

## 위키 모델 {#wiki-model}

설정된 위키 루트(기본값 `docs/atlas/`)의 페이지는 `description`, `covers`, `related`, `code_rev`, `updated`를 선언합니다. 호스트는 `INDEX.md`를 통해 모든 문서를 읽지 않고 관련 주제를 선택할 수 있습니다.

변경 불일치 감지는 각 페이지의 `code_rev`와 HEAD를 해당 `covers` glob에 맞는 파일에 대해 비교합니다. `*`는 경로 구분자를 넘지 않고, `**`는 디렉터리를 가로질러 일치합니다. 잘못된 스키마, 빈 대상 범위, 확인할 수 없는 리비전은 잘못된 “최신” 결과 대신 안내를 생성합니다.

## 동기화 {#synchronization}

`atlas_drift.py --json`은 모델 호출이나 Claude CLI 없이 오래된 페이지와 대상 파일 범위를
나열합니다. 선택적 수정 미리보기인 `atlas_sync.py --dry-run`은 모델을 호출하거나 파일을 쓰지
않아도 PATH에 `claude`가 있어야 합니다. [로컬 점검](commands.md#local-checks)를 참고합니다. 요청 시 수정에는 현재 호스트를 사용할 수 있습니다. 선택적 푸시 시 동기화는 작업 범위가 제한된 Claude CLI 수정 도구로 리비전 기준점을 갱신하고 인덱스를 다시 생성한 뒤 수정한 위키 페이지를 커밋합니다.

`sync.on_push`는 기본적으로 꺼져 있습니다. 이를 켜면 대상 파일의 diff를 설정된 Claude 서비스로 전송하도록 승인합니다. 훅은 지원되는 셸 도구의 푸시 호출을 감지하며, 터미널에 직접 입력한 푸시는 가로채지 않습니다. 훅 실패는 안내로 처리하고 작업을 허용합니다. `atlas_index.py --validate`는 스키마와 그래프를 명시적으로 검증하는 게이트입니다.

[Atlas 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/atlas/skills/atlas/SKILL.md) · [기본 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/atlas/skills/atlas/atlas.defaults.json)
