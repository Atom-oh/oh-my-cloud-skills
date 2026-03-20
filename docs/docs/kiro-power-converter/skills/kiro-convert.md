---
sidebar_position: 1
title: "Kiro Convert 스킬"
---

# Kiro Convert 스킬

Claude Code 플러그인을 Kiro Power 포맷으로 변환하는 대화형 워크플로우를 제공하는 스킬입니다.

:::warning 비파괴적 변환
이 스킬은 **기존 Claude Code 플러그인을 절대 삭제하거나 수정하지 않습니다**. 원본 플러그인 파일은 그대로 유지되며, Kiro Power 포맷은 별도 위치에 새로 생성됩니다. Claude Code와 Kiro IDE에서 동일한 기능을 동시에 사용할 수 있습니다.
:::

## 기본 정보

| 항목 | 값 |
|------|-----|
| 이름 | `kiro-convert` |
| 설명 | Convert Claude Code plugins to Kiro Power format |

## 트리거 키워드

| 영어 | 한국어 |
|------|--------|
| "convert to kiro" | "키로 변환" |
| "kiro power" | "키로 파워" |
| "kiro convert" | - |
| "claude to kiro" | - |
| "install kiro power" | "키로 설치" |
| "kiro install" | "키로 파워 설치" |

## 대화형 워크플로우

Kiro Convert 스킬은 6단계의 대화형 워크플로우로 구성됩니다.

### Phase 1: 소스 선택

사용자에게 입력 소스 유형을 확인합니다.

| 소스 타입 | 플래그 | 설명 |
|----------|--------|------|
| GitHub URL | `--git-url` | 저장소를 클론하여 플러그인 추출 |
| 로컬 경로 | `--source` | 로컬 플러그인 디렉토리 사용 |
| 마켓플레이스 | `--marketplace` | 플러그인 이름으로 검색 및 다운로드 |
| 개별 스킬 | `--skill` | 특정 스킬만 단독 변환 |

**수집하는 파라미터:**
- Git: URL, 브랜치/태그 (선택), 플러그인 하위 디렉토리 경로 (선택)
- Local: 플러그인 루트의 절대 또는 상대 경로
- Marketplace: 플러그인 이름 또는 검색 쿼리
- Skill: 스킬 디렉토리 경로

### Phase 2: 플러그인 탐색

소스 유형에 따라 플러그인을 탐색하고 검증합니다.

| 소스 | 동작 |
|------|------|
| Git | `git clone --depth 1` 후 플러그인 하위 디렉토리로 이동 |
| Local | `.claude-plugin/plugin.json` 존재 여부 검증 |
| Marketplace | `plugins/` 및 `~/.claude/plugins/` 디렉토리 검색 |
| Skill | `SKILL.md` 존재 여부 검증 |

### Phase 3: 대상 선택

변환된 power의 출력 위치를 선택합니다.

| 대상 | 경로 | 용도 |
|------|------|------|
| `global` | `~/.kiro/powers/<name>/` | 모든 Kiro 프로젝트에서 사용 |
| `project` | `.kiro/powers/<name>/` | 현재 프로젝트에서만 사용 |
| `export` | 사용자 지정 경로 | 공유 또는 수동 설치용 |

### Phase 4: 변환

변환 스크립트를 실행하거나 `references/conversion-rules.md`의 규칙에 따라 수동 변환을 수행합니다.

```bash
python3 {plugin-dir}/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source <plugin-path> --output <output-path> --target <target>
```

**변환 항목:**
- `plugin.json` → `POWER.md`
- `CLAUDE.md` → `steering/routing.md`
- `agents/*.md` → `steering/<agent>.md`
- `skills/*/SKILL.md` → `steering/<skill>.md`
- `skills/*/references/*.md` → `steering/ref-*.md`
- `.mcp.json` → `mcp.json`

### Phase 5: 검증

변환 결과를 검증합니다.

| 검증 항목 | 확인 내용 |
|----------|----------|
| 구조 검사 | `POWER.md`, `steering/` 디렉토리 존재 |
| POWER.md 검사 | frontmatter에 `name`, `displayName`, `description`, `keywords` 포함 |
| Steering 검사 | 모든 steering 파일에 `inclusion` 필드 존재 |
| MCP 검사 | `.mcp.json`이 있었다면 `mcp.json`에 `type` 필드 없음, `autoApprove`/`disabled` 존재 |

### Phase 6: 다음 단계

변환 완료 후 권장하는 후속 작업입니다.

| 작업 | 설명 |
|------|------|
| Kiro에서 테스트 | Kiro IDE를 열고 powers 목록에 표시되는지 확인 |
| GitHub에 게시 | 저장소에 푸시하고 "Add to Kiro" 임포트 사용 |
| 공유 | 내보낸 디렉토리를 다른 Kiro 사용자에게 배포 |

## 사용 예시

### 기본 사용

```
/kiro-convert
```

스킬이 활성화되면 대화형 프롬프트를 통해 필요한 정보를 수집합니다.

### 키워드로 트리거

```
키로 변환
```

```
convert my plugin to kiro
```

### 전체 명령어 예시

**로컬 플러그인을 전역 설치:**
```
convert ./plugins/aws-ops-plugin to kiro and install globally
```

**GitHub 플러그인을 내보내기:**
```
kiro convert https://github.com/user/repo plugins/my-plugin --export /tmp/output
```

**개별 스킬만 변환:**
```
키로 변환 ./plugins/aws-ops-plugin/skills/ops-troubleshoot
```

## 참조 문서

스킬은 다음 참조 문서를 활용합니다.

| 문서 | 내용 |
|------|------|
| `references/kiro-power-format.md` | Kiro Power 디렉토리 구조 및 포맷 명세 |
| `references/conversion-rules.md` | 필드별 상세 변환 규칙 및 엣지 케이스 |

:::tip 수동 변환
변환 스크립트 없이도 `references/conversion-rules.md`의 규칙을 따라 수동으로 변환할 수 있습니다. 이 문서에는 각 파일 유형별 변환 규칙과 특수 케이스 처리 방법이 상세히 기술되어 있습니다.
:::
