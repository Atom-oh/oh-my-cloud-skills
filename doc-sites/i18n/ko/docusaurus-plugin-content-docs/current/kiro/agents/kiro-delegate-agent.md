---
sidebar_position: 1
title: "Kiro 위임 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거-키워드" />
<span id="신뢰-경계" />
<span id="파이프라인-kirodelegate" />
<span id="참고-파일" />
<span id="다른-에이전트와의-연계" />


# Kiro 위임 에이전트

오케스트레이터는 계획 작성, Kiro 작업 실행, diff 캡처, 범위 검사, 호스트 검증, 커밋, 최종 위임 보고서를 관리합니다. 명시적인 Kiro 구현 요청이나 사용자가 켠 기본 위임 설정에 따라 활성화됩니다.

## 작업 파이프라인 {#task-pipeline}

설정된 CLI와 모델을 확인하고 Kiro 전용 명세를 준비합니다. 작업 트리로 작업을 격리하고 설정된 병렬 실행 및 수정 한도를 적용합니다. 프로젝트의 실제 테스트 명령으로 결과 변경을 검증합니다. 호스트 구현으로 전환한 작업이 있으면 보고서에 명시합니다.

## 신뢰 경계 {#trust-boundary}

Kiro는 별도의 git 작업 트리에서 실행됩니다. 메인 트리에는 캡처된 diff만 적용할 수 있으며 `scope_guard.py`가 계획에 선언된 전체 파일 집합을 기준으로 경로를 검증합니다. 호스트가 검증을 실행하고 커밋을 책임집니다.

이 방식은 캡처된 변경 중 어떤 변경이 메인 트리에 반영될지 통제합니다. Kiro의 파일 시스템 샌드박스는 아닙니다. `--trust-tools`는 도구 사용을 승인할 뿐 디렉터리 접근 범위를 제한하지 않습니다. 구현자의 `execute_bash` 기능은 기본적으로 꺼져 있으며 별도로 동의해야 하는 신뢰 결정입니다. 이를 켜면 작업 트리 밖의 호스트에도 영향을 줄 수 있습니다.

## 관련 워크플로 {#related-workflows}

검토만 수행하려면 `/kiro:review`를 사용합니다. 다양한 패널의 추가 의견이 필요하면 co-agent를 사용합니다. co-agent의 harness는 구현자 자격 요건이 다릅니다.

[에이전트 정의](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/agents/kiro-delegate-agent.md)
