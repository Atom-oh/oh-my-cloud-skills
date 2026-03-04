---
sidebar_position: 2
title: "Architecture Diagram"
---

# Architecture Diagram Skill

AWS 아키텍처 다이어그램을 생성하는 스킬입니다. Draw.io MCP 또는 XML 직접 작성 두 가지 모드를 지원합니다.

## 트리거 키워드

다음 키워드로 활성화됩니다:
- "아키텍처 다이어그램 그려줘"
- "AWS 구성도 만들어줘"
- "인프라 다이어그램", "시스템 아키텍처", "클라우드 아키텍처"

## 지원 모드

| 모드 | 방식 | 장점 | 사용 시점 |
|------|------|------|----------|
| **XML 직접 작성** | Write 도구로 .drawio 파일 생성 | 의존성 없음, 안정적 | 기본 (항상 사용 가능) |
| **Draw.io MCP** | MCP로 실시간 편집 | 대화형 수정, 실시간 미리보기 | 선택적 (설정 필요) |

## 제공 리소스

### reference/

| 참조 문서 | 설명 |
|----------|------|
| `aws-icons.md` | AWS 아이콘 shape 이름 및 스타일 |
| `best-practices.md` | 아키텍처 다이어그램 모범사례 |
| `layout-patterns.md` | 레이아웃 패턴 |

### templates/

| 템플릿 | 설명 |
|--------|------|
| `aws-basic.drawio` | VPC, Subnet, AZ 기본 구조 |
| `aws-samples.drawio` | Data Lake 아키텍처 샘플 |

## 캔버스 크기 (PPT용)

| 용도 | 캔버스 크기 (px) | 비율 |
|------|------------------|------|
| 전체 슬라이드 | 1920 x 1080 | 16:9 |
| 콘텐츠 영역 (권장) | 1600 x 900 | 16:9 |
| 절반 슬라이드 | 900 x 900 | 1:1 |
| 2/3 슬라이드 | 1200 x 900 | 4:3 |

## AWS 아이콘 라벨 규칙

:::warning 필수
모든 AWS 아이콘 아래에 서비스 이름을 반드시 표시합니다.
:::

```
┌─────────────┐
│   [아이콘]   │
│             │
│ Lambda      │  ← 서비스 이름 필수
└─────────────┘
```

라벨 설정:
- `verticalLabelPosition=bottom`
- `fontFamily=Amazon Ember`
- `fontSize=12`
- `fontColor=#FFFFFF` (Dark 테마)

## AWS 색상 가이드

| 용도 | 색상 코드 | 설명 |
|------|-----------|------|
| AWS Cloud | #232F3E | 다크 네이비 (배경) |
| Region | #147EBA | 블루 |
| VPC | #248814 | 그린 |
| Public Subnet | #E7F4E8 | 라이트 그린 |
| Private Subnet | #E6F2F8 | 라이트 블루 |
| Security Group | #DF3312 | 레드 (보더) |

## PNG 내보내기

```bash
# 기본 PNG 내보내기
drawio -x -f png -o output.png input.drawio

# 고해상도 PNG (2배 스케일, PPT용 권장)
drawio -x -f png -s 2 -o output.png input.drawio

# 투명 배경 (Dark 테마 PPT용)
drawio -x -f png -s 2 -t -o output.png input.drawio
```

## 사용 예시

```
사용자: "3-tier 웹 아키텍처 다이어그램 그려줘"

1. architecture-diagram-agent 호출
2. 요구사항 분석 (VPC, Subnet, EC2, RDS 등)
3. Draw.io XML 생성
4. PNG 내보내기
5. content-review-agent 검토
```

## Draw.io MCP 설정 (선택사항)

Draw.io MCP를 사용하면 실시간 편집이 가능합니다:

```json
{
  "mcpServers": {
    "drawio": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

사전 요구사항:
1. drawio-mcp-server가 HTTP 모드로 실행 중
2. Browser Extension 설치 및 연결
3. Draw.io 앱 열림

## Quality Review (필수)

다이어그램 완성 후 반드시:
1. `content-review-agent` 호출
2. PASS (85점 이상) 획득 후에만 완료 선언

## 검증 체크리스트

- [ ] Amazon Ember 폰트가 모든 텍스트에 설정됨
- [ ] AWS 공식 색상 사용
- [ ] 계층 구조 명확 (Cloud > Region > VPC > Subnet)
- [ ] 데이터 흐름 방향 일관성
- [ ] 아이콘 크기 균일 (권장: 60x60)
- [ ] 라벨이 아이콘 아래에 배치됨
