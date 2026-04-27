---
sidebar_position: 2
title: "설치"
---

# 설치

## Marketplace에서 설치

```bash
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
/plugin install kiro-review@oh-my-cloud-skills
```

## 로컬에서 직접 로드

```bash
claude --plugin-dir ./plugins/kiro-review
```

## 사전 요구사항

### kiro-cli-plugin (필수)

Kiro CLI 플러그인이 설치되어 있어야 합니다:

```bash
/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin
```

:::warning
kiro-cli-plugin이 없으면 Phase 2 (코드 리뷰)와 Phase 4 (적대적 보안 리뷰)가 Kiro CLI 위임 없이 자체 분석만으로 수행됩니다.
:::

## 제거

```bash
/plugin uninstall kiro-review@oh-my-cloud-skills
```
