---
sidebar_position: 3
title: "설치"
---

# 설치

AWS Content Plugin을 설치하고 사용하는 방법입니다.

## Marketplace 설치

Claude Code의 플러그인 마켓플레이스에서 설치합니다:

```bash
# 마켓플레이스 추가
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills

# 플러그인 설치
/plugin install aws-content-plugin@oh-my-cloud-skills
```

## 로컬 로딩

개발 또는 테스트 목적으로 로컬에서 플러그인을 로드할 수 있습니다:

```bash
claude --plugin-dir ./plugins/aws-content-plugin
```

## 설치 확인

플러그인이 올바르게 로드되었는지 확인합니다:

```bash
# 플러그인 매니페스트 검증
python3 -c "import json; d=json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json')); print(f'agents: {len(d[\"agents\"])}, skills: {len(d[\"skills\"])}')"
```

정상 출력:
```
agents: 8, skills: 5
```

## 파일 참조 확인

모든 에이전트와 스킬 파일이 존재하는지 확인합니다:

```bash
cd plugins/aws-content-plugin && python3 -c "
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

설치 후 플러그인 구조:

```
aws-content-plugin/
├── .claude-plugin/
│   └── plugin.json          # 매니페스트 파일
├── CLAUDE.md                # 자동 호출 규칙
├── agents/
│   ├── presentation-agent.md
│   ├── reactive-presentation-agent.md
│   ├── architecture-diagram-agent.md
│   ├── animated-diagram-agent.md
│   ├── document-agent.md
│   ├── gitbook-agent.md
│   ├── workshop-agent.md
│   └── content-review-agent.md
└── skills/
    ├── reactive-presentation/
    ├── architecture-diagram/
    ├── animated-diagram/
    ├── gitbook/
    └── workshop-creator/
```

## 자동 호출

플러그인이 로드되면 특정 키워드에 따라 에이전트가 자동으로 활성화됩니다.

:::info 자동 호출 키워드
각 에이전트의 트리거 키워드는 해당 에이전트 문서 페이지에서 확인할 수 있습니다.
:::

## 다음 단계

- [Presentation Agent](./agents/presentation-agent) - 프레젠테이션 생성
- [Architecture Diagram Agent](./agents/architecture-diagram-agent) - 아키텍처 다이어그램 생성
- [Content Review Agent](./agents/content-review-agent) - 콘텐츠 품질 검토
