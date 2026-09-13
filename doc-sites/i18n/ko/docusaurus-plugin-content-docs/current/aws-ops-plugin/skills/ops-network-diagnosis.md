---
sidebar_position: 3
title: "네트워크 진단"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="ops-network-diagnosis" />
<span id="description" />
<span id="trigger-keywords" />
<span id="diagnosis-workflow" />
<span id="step-1-layer-identification" />
<span id="step-2-layer-specific-diagnosis" />
<span id="step-3-resolution-verification" />
<span id="quick-connectivity-tests" />
<span id="vpc-cni-deep-guide" />
<span id="architecture-overview" />
<span id="ip-allocation-modes" />
<span id="instance-type-limits" />
<span id="key-environment-variables" />
<span id="vpc-cni-diagnostic-commands" />
<span id="ip-exhaustion-solutions" />
<span id="subnet-cidr-planning-best-practice" />
<span id="vpc-cni-error-solutions" />
<span id="load-balancer-troubleshooting" />
<span id="prerequisites-checklist" />
<span id="key-annotations-reference" />
<span id="alb-ingress" />
<span id="nlb-service" />
<span id="alb-not-created---debugging" />
<span id="targets-unhealthy---debugging" />
<span id="502-bad-gateway-resolution" />
<span id="subnet-tagging" />
<span id="cost-optimization---alb-sharing" />
<span id="dns-deep-diagnosis" />
<span id="coredns-architecture-in-eks" />
<span id="dns-diagnostic-commands" />
<span id="dns-resolution-timeout-solutions" />
<span id="coredns-scaling" />
<span id="coredns-configmap-customization" />
<span id="external-dns-not-resolving-from-pods" />
<span id="route-53-integration---external-dns" />
<span id="dns-error-solutions" />
<span id="layer-specific-diagnosis-guide" />
<span id="l3---iprouting" />
<span id="l4---security-groups" />
<span id="l7---load-balancer" />
<span id="usage-examples" />
<span id="ip-exhaustion-issue" />
<span id="alb-502-error" />
<span id="reference-files" />


# 네트워크 진단

AWS/EKS 연결 실패, 비정상 대상, DNS 오류, IP 고갈을 추적합니다.

## 워크플로 {#workflow}

출발지, 목적지, 프로토콜, 포트, 예상 경로를 정의합니다. 엔드포인트와 서비스 선택을 확인하고 CNI 할당, 라우팅 테이블, SG/NACL 규칙, 네트워크 정책, 로드 밸런서 상태, DNS, 프라이빗 엔드포인트를 점검합니다.

## 대상 범위 {#coverage}

VPC CNI/IPAMD, ENI·서브넷 용량, ALB/NLB 대상 그룹, CoreDNS와 업스트림 이름 해석, 파드에서 서비스로의 접근과 VPC 간 접근, 보안 그룹·경로 제약을 다룹니다.

## 보고 및 경계 {#reporting-and-boundaries}

시정 조치 전에 관찰한 경로의 근거를 활용합니다. 보안 그룹 변경은 저장소의 IaC 정책을 따릅니다. 광범위한 공개 인바운드 허용을 진단 지름길로 사용하지 않습니다.

소스 스킬에는 명령별 실행 절차, 의사결정 트리, 예제, 참조 파일, 호스트·팀 연동이 포함되어 있습니다. 수행할 작업의 정확한 절차는 소스 스킬에서 확인합니다.

[기준 워크플로 및 실행 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-network-diagnosis/SKILL.md)
