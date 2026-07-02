---
sidebar_position: 2
title: "설치"
---

# Kiro Power Converter 설치

Kiro Power Converter 플러그인을 설치하고 사용하는 방법을 설명합니다.

## 마켓플레이스 설치

Claude Code의 플러그인 마켓플레이스를 통해 설치할 수 있습니다.

```bash
# 마켓플레이스에서 플러그인 추가
/plugin marketplace add kiro-power-converter
```

## 로컬 로딩

개발 또는 테스트 목적으로 로컬에서 플러그인을 직접 로드할 수 있습니다.

```bash
# 로컬 플러그인 디렉토리 지정하여 Claude Code 실행
claude --plugin-dir ./plugins/kiro-power-converter
```

## 설치 확인

플러그인이 정상적으로 설치되었는지 확인합니다.

### 매니페스트 검증

```bash
python3 -c "import json; d=json.load(open('plugins/kiro-power-converter/.claude-plugin/plugin.json')); print(f'kiro-power-converter: {len(d[\"agents\"])} agents, {len(d[\"skills\"])} skills')"
```

예상 출력:
```
kiro-power-converter: 1 agents, 1 skills
```

### 파일 참조 검증

모든 `plugin.json` 참조가 실제 파일로 연결되는지 확인합니다.

```bash
cd plugins/kiro-power-converter && python3 -c "
import json, os
d = json.load(open('.claude-plugin/plugin.json'))
for a in d['agents']:
    assert os.path.isfile(a.lstrip('./')), f'Missing agent: {a}'
for s in d['skills']:
    assert os.path.isfile(s.lstrip('./') + '/SKILL.md'), f'Missing skill: {s}'
print('All references OK')
"
```

## 플러그인 구조

설치된 플러그인의 디렉토리 구조는 다음과 같습니다.

```
kiro-power-converter/
├── .claude-plugin/
│   └── plugin.json          # 플러그인 매니페스트
├── CLAUDE.md                # 자동 호출 규칙 및 라우팅
├── agents/
│   └── kiro-converter-agent.md   # 변환 에이전트
└── skills/
    └── kiro-convert/        # 변환 스킬
        ├── SKILL.md         # 스킬 진입점
        └── references/      # 참조 문서
            ├── kiro-power-format.md    # Kiro Power 포맷 명세
            └── conversion-rules.md     # 변환 규칙 상세
```

## 자동 호출 키워드

플러그인 설치 후, 다음 키워드를 사용하면 자동으로 Kiro Converter Agent가 활성화됩니다.

| 키워드 (영어) | 키워드 (한국어) | 동작 |
|--------------|----------------|------|
| "convert to kiro" | "키로 변환" | Claude Code 플러그인을 Kiro Power 포맷으로 변환 |
| "kiro power" | "키로 파워" | 변환 에이전트 활성화 |
| "export to kiro" | - | 변환 및 내보내기 |
| "claude to kiro" | - | Claude → Kiro 변환 |
| "install kiro power" | "키로 설치" | 변환 후 설치 |
| "kiro install" | "키로 파워 설치" | 변환 후 설치 |

:::tip 빠른 시작
플러그인 설치 후 "convert my-plugin to kiro" 또는 "키로 변환"이라고 입력하면 대화형 변환 워크플로우가 시작됩니다.
:::
