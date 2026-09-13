---
sidebar_position: 1
title: "Kiro 위임 스킬"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거" />
<span id="안전의-의미와-한계" />
<span id="명령" />
<span id="pre-commit-리뷰-opt-in" />
<span id="구현-모델과-리뷰-모델을-다르게-유지하는-이유" />
<span id="default-delegate-모드" />
<span id="절대-하지-않는-것" />
<span id="참고-파일" />


# Kiro 위임 스킬

Kiro CLI에 구현 작업을 맡길 때 이 스킬을 사용합니다. 명시적인 위임 요청이 해당 워크플로를 승인합니다. 자동 배정은 `default_delegate`가 제어하며 기본적으로 꺼져 있습니다.

## 파이프라인 및 결과 {#pipeline-and-output}

승인된 계획과 Kiro 전용 작업 명세를 준비하고 격리된 작업 트리에서 실행합니다. 선언된 경로의 변경을 캡처·검증한 뒤 적용하고 호스트 검증을 실행합니다. 한도가 있는 수정 반복 절차를 사용하며 테스트, 호스트 전환, 위임 범위를 보고합니다. 호스트가 커밋과 최종 결과를 책임집니다.

## 범위 및 셸 신뢰 {#scope-and-shell-trust}

Kiro는 별도의 git 작업 트리에서 실행됩니다. 메인 트리에는 캡처된 diff만 적용할 수 있으며 `scope_guard.py`가 계획에 선언된 전체 파일 집합을 기준으로 경로를 검증합니다. 호스트가 검증을 실행하고 커밋을 책임집니다.

이 방식은 캡처된 변경 중 어떤 변경이 메인 트리에 반영될지 통제합니다. Kiro의 파일 시스템 샌드박스는 아닙니다. `--trust-tools`는 도구 사용을 승인할 뿐 디렉터리 접근 범위를 제한하지 않습니다. 구현자의 `execute_bash` 기능은 기본적으로 꺼져 있으며 별도로 동의해야 하는 신뢰 결정입니다. 이를 켜면 작업 트리 밖의 호스트에도 영향을 줄 수 있습니다.

## 검토 설정 {#review-configuration}

요청 시 검토는 구현과 별개입니다. 커밋·푸시 검토 훅은 기본적으로 꺼져 있으며 독립적인 검토 설정을 사용합니다. 추적되는 로컬 설정이 보호된 동의 설정을 사용자 모르게 활성화할 수는 없습니다. `/kiro:configure`로 실제 적용 설정을 확인합니다.

[스킬 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/SKILL.md) · [기본 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)
