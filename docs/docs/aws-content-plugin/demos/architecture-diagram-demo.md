---
sidebar_position: 6
title: "Architecture Diagram Demo"
---

# Architecture Diagram Demo

Draw.io XML을 사용하여 3-Tier VPC 아키텍처 다이어그램을 생성하는 데모입니다. architecture-diagram-agent가 XML을 직접 작성하여 .drawio 파일을 생성하고, PNG로 내보내기합니다.

## 생성 프롬프트

```
"3-tier 웹 아키텍처 다이어그램을 그려줘.
VPC 안에 Public/Private 서브넷, ALB, EC2 Auto Scaling, Aurora 포함.
PPT 삽입용으로 1600x900 크기로 만들어줘."
```

## 결과 다이어그램

아래는 생성된 3-Tier 아키텍처 다이어그램의 구조입니다:

```
┌─ AWS Cloud ─────────────────────────────────────────────────────────┐
│  ┌─ Region (ap-northeast-2) ──────────────────────────────────────┐ │
│  │  ┌─ VPC (10.0.0.0/16) ───────────────────────────────────────┐ │ │
│  │  │                                                            │ │ │
│  │  │  ┌─ Public Subnet ─────┐   ┌─ Public Subnet ─────┐        │ │ │
│  │  │  │  AZ-a               │   │  AZ-c               │        │ │ │
│  │  │  │  ┌─────┐            │   │  ┌─────┐            │        │ │ │
│  │  │  │  │ ALB │            │   │  │ ALB │            │        │ │ │
│  │  │  │  └─────┘            │   │  └─────┘            │        │ │ │
│  │  │  └─────────────────────┘   └─────────────────────┘        │ │ │
│  │  │                                                            │ │ │
│  │  │  ┌─ Private Subnet ────┐   ┌─ Private Subnet ────┐        │ │ │
│  │  │  │  AZ-a               │   │  AZ-c               │        │ │ │
│  │  │  │  ┌─────┐ ┌─────┐    │   │  ┌─────┐ ┌─────┐    │        │ │ │
│  │  │  │  │ EC2 │ │ EC2 │    │   │  │ EC2 │ │ EC2 │    │        │ │ │
│  │  │  │  └─────┘ └─────┘    │   │  └─────┘ └─────┘    │        │ │ │
│  │  │  │    Auto Scaling     │   │    Auto Scaling     │        │ │ │
│  │  │  └─────────────────────┘   └─────────────────────┘        │ │ │
│  │  │                                                            │ │ │
│  │  │  ┌─ DB Subnet ─────────────────────────────────────┐      │ │ │
│  │  │  │              ┌─────────┐                         │      │ │ │
│  │  │  │              │ Aurora  │ ←── Multi-AZ           │      │ │ │
│  │  │  │              │ Cluster │                         │      │ │ │
│  │  │  │              └─────────┘                         │      │ │ │
│  │  │  └─────────────────────────────────────────────────┘      │ │ │
│  │  └────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Draw.io XML 코드 (발췌)

### 기본 캔버스 구조

```xml
<mxfile host="app.diagrams.net" agent="Claude Code" version="21.0.0">
  <diagram name="3-Tier Architecture" id="3tier-arch">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="900">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- AWS Cloud Container -->
        <mxCell id="aws-cloud" value="AWS Cloud"
                style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;..."
                vertex="1" parent="1">
          <mxGeometry x="20" y="20" width="1560" height="860" as="geometry" />
        </mxCell>

        <!-- Region Container -->
        <mxCell id="region" value="ap-northeast-2"
                style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;..."
                vertex="1" parent="aws-cloud">
          <mxGeometry x="20" y="40" width="1520" height="800" as="geometry" />
        </mxCell>

        <!-- VPC Container -->
        <mxCell id="vpc" value="Production VPC (10.0.0.0/16)"
                style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;..."
                vertex="1" parent="region">
          <mxGeometry x="20" y="40" width="1480" height="740" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Public Subnet with ALB

```xml
<!-- Public Subnet AZ-a -->
<mxCell id="public-a" value="Public Subnet (10.0.1.0/24) - AZ-a"
        style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;
               strokeColor=#7AA116;fillColor=#F2F6E8;fontColor=#248814;..."
        vertex="1" parent="vpc">
  <mxGeometry x="40" y="40" width="340" height="150" as="geometry" />
</mxCell>

<!-- Application Load Balancer -->
<mxCell id="alb" value="ALB"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;
               gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;
               strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;
               shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer;
               fontFamily=Amazon Ember;fontSize=9;"
        vertex="1" parent="public-a">
  <mxGeometry x="146" y="50" width="48" height="48" as="geometry" />
</mxCell>
```

### Private Subnet with EC2 Auto Scaling

```xml
<!-- Private Subnet AZ-a -->
<mxCell id="private-a" value="Private Subnet (10.0.10.0/24) - AZ-a"
        style="...strokeColor=#00A4A6;fillColor=#E6F6F7;fontColor=#147EBA;..."
        vertex="1" parent="vpc">
  <mxGeometry x="40" y="210" width="340" height="180" as="geometry" />
</mxCell>

<!-- EC2 Instance 1 -->
<mxCell id="ec2-1" value="Web Server"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;
               gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;
               strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;
               shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;
               fontFamily=Amazon Ember;fontSize=9;"
        vertex="1" parent="private-a">
  <mxGeometry x="60" y="60" width="48" height="48" as="geometry" />
</mxCell>

<!-- Auto Scaling Group Label -->
<mxCell id="asg-label" value="Auto Scaling Group"
        style="text;html=1;strokeColor=none;fillColor=none;align=center;
               verticalAlign=middle;fontFamily=Amazon Ember;fontSize=10;
               fontColor=#D05C17;fontStyle=2;"
        vertex="1" parent="private-a">
  <mxGeometry x="40" y="130" width="140" height="20" as="geometry" />
</mxCell>
```

### Aurora Database

```xml
<!-- DB Subnet -->
<mxCell id="db-subnet" value="DB Subnet (10.0.100.0/24)"
        style="...strokeColor=#3334B9;fillColor=#E6E8F8;fontColor=#3334B9;..."
        vertex="1" parent="vpc">
  <mxGeometry x="40" y="420" width="700" height="140" as="geometry" />
</mxCell>

<!-- Aurora Cluster -->
<mxCell id="aurora" value="Aurora MySQL"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;
               gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;
               strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;
               shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora;
               fontFamily=Amazon Ember;fontSize=9;"
        vertex="1" parent="db-subnet">
  <mxGeometry x="326" y="46" width="48" height="48" as="geometry" />
</mxCell>
```

### Connection Arrows

```xml
<!-- ALB to EC2 -->
<mxCell id="alb-to-ec2" value=""
        style="endArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#545B64;"
        edge="1" parent="vpc" source="alb" target="ec2-1">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>

<!-- EC2 to Aurora -->
<mxCell id="ec2-to-aurora" value=""
        style="endArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#545B64;dashed=1;"
        edge="1" parent="vpc" source="ec2-1" target="aurora">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>
```

## PNG 내보내기 명령

```bash
# 고해상도 PNG (PPT용, 권장)
drawio -x -f png -s 2 -o 3tier-architecture.png 3tier-architecture.drawio

# 투명 배경 (Dark 테마 PPT)
drawio -x -f png -s 2 -t -o 3tier-architecture.png 3tier-architecture.drawio

# SVG (벡터, 확대해도 선명)
drawio -x -f svg -o 3tier-architecture.svg 3tier-architecture.drawio
```

## AWS 색상 가이드

| Component | Border Color | Fill Color | Font Color |
|-----------|--------------|------------|------------|
| AWS Cloud | #232F3E | none | #232F3E |
| Region | #00A4A6 | none | #147EBA |
| VPC | #248814 | none | #248814 |
| Public Subnet | #7AA116 | #F2F6E8 | #248814 |
| Private Subnet | #00A4A6 | #E6F6F7 | #147EBA |
| DB Subnet | #3334B9 | #E6E8F8 | #3334B9 |

## 아이콘 카테고리 색상

| Category | fillColor | gradientColor |
|----------|-----------|---------------|
| Compute (EC2, Lambda) | #D05C17 | #F78E04 |
| Database (RDS, Aurora) | #3334B9 | #4D72F3 |
| Networking (ALB, NLB) | #5A30B5 | #945DF2 |
| Storage (S3, EBS) | #277116 | #60A337 |

## 주요 포인트

1. **계층 구조 명확화**: AWS Cloud > Region > VPC > Subnet 순서로 중첩
2. **색상 코딩**: AWS 공식 색상 사용으로 일관성 유지
3. **라벨 배치**: 모든 아이콘 아래에 서비스 이름 표시
4. **Multi-AZ 표현**: 동일 구성을 두 AZ에 배치하여 고가용성 표현
5. **연결선 구분**: 실선(동기 호출) vs 점선(비동기/데이터 흐름)
