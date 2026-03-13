---
name: architecture-diagram
description: AWS 아키텍처 다이어그램을 draw.io MCP로 생성. 사용자가 "아키텍처 다이어그램 그려줘", "AWS 구성도 만들어줘", "인프라 다이어그램", "시스템 아키텍처", "클라우드 아키텍처"를 요청할 때 활성화.
model: sonnet
allowed-tools:
  - Read
  - Write
  - Bash
---

# Architecture Diagram Skill

AWS 아키텍처 다이어그램을 생성하는 스킬. **두 가지 모드**를 지원합니다:

| 모드 | 방식 | 장점 | 사용 시점 |
|------|------|------|----------|
| **XML 직접 작성** | Write 도구로 .drawio 파일 생성 | 의존성 없음, 안정적 | 기본 (항상 사용 가능) |
| **Draw.io MCP** | MCP로 실시간 편집 | 대화형 수정, 실시간 미리보기 | 선택적 (설정 필요) |

---

## Draw.io MCP 설정 가이드 (선택사항)

### 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         사용자 시스템                                    │
│                                                                          │
│  ┌──────────────────┐                      ┌─────────────────────────┐  │
│  │ Draw.io          │   WebSocket (:3333)  │ drawio-mcp-server       │  │
│  │ (브라우저/앱)    │◄────────────────────►│ (Singleton 인스턴스)    │  │
│  │ + Browser        │                      │                         │  │
│  │   Extension      │                      │ HTTP :3000/mcp          │  │
│  └──────────────────┘                      └────────────┬────────────┘  │
│                                                         │               │
│                                                         ▼               │
│  ┌──────────────────┐     HTTP            ┌─────────────────────────┐  │
│  │ Claude Code      │◄───────────────────►│ /mcp endpoint           │  │
│  │ Session 1        │                     │ (다중 클라이언트 지원)   │  │
│  └──────────────────┘                     └─────────────────────────┘  │
│                                                         ▲               │
│  ┌──────────────────┐     HTTP                          │               │
│  │ Claude Code      │◄──────────────────────────────────┘               │
│  │ Session 2        │                                                   │
│  └──────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**핵심 포인트:**
- **HTTP 모드** 사용으로 다중 Claude Code 세션 지원
- 서버는 **1개 인스턴스만** 실행 (포트 충돌 방지)
- Browser Extension은 WebSocket으로 연결, Claude Code는 HTTP로 연결

---

### Step 1: drawio-mcp-server 설치 및 실행

#### 1.1 서버 시작 (HTTP 모드)

```bash
# 터미널에서 실행 (포그라운드)
npx -y drawio-mcp-server --transport http --http-port 3000

# 또는 백그라운드로 실행
npx -y drawio-mcp-server --transport http --http-port 3000 &

# stdio와 HTTP 동시 지원 (선택사항)
npx -y drawio-mcp-server --transport stdio,http --http-port 3000
```

#### 1.2 서버 상태 확인

```bash
# Health check
curl http://localhost:3000/health
# 응답: {"status":"ok"}
```

#### 1.3 자동 시작 설정 (선택사항)

**macOS - LaunchAgent 등록:**

```bash
# ~/Library/LaunchAgents/com.drawio.mcp.plist 생성
cat << 'EOF' > ~/Library/LaunchAgents/com.drawio.mcp.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.drawio.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/npx</string>
        <string>-y</string>
        <string>drawio-mcp-server</string>
        <string>--transport</string>
        <string>http</string>
        <string>--http-port</string>
        <string>3000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# 서비스 등록 및 시작
launchctl load ~/Library/LaunchAgents/com.drawio.mcp.plist
```

**Linux - systemd 서비스:**

```bash
# ~/.config/systemd/user/drawio-mcp.service 생성
cat << 'EOF' > ~/.config/systemd/user/drawio-mcp.service
[Unit]
Description=Draw.io MCP Server
After=network.target

[Service]
ExecStart=/usr/bin/npx -y drawio-mcp-server --transport http --http-port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

# 서비스 활성화
systemctl --user daemon-reload
systemctl --user enable drawio-mcp
systemctl --user start drawio-mcp
```

---

### Step 2: Browser Extension 설치

Draw.io MCP는 **Browser Extension**을 통해 Draw.io 앱과 통신합니다.

#### 2.1 Chrome Extension 설치

1. **Chrome Web Store**에서 설치:
   - [Draw.io MCP Extension](https://chrome.google.com/webstore/detail/drawio-mcp-extension/okdbbjbbccdhhfaefmcmekalmmdjjide)

2. 또는 **수동 설치** (개발자 모드):
   ```bash
   # Extension 소스 클론
   git clone https://github.com/lgazo/drawio-mcp-extension.git

   # Chrome에서 로드
   # chrome://extensions → 개발자 모드 → 압축해제된 확장 프로그램 로드
   ```

#### 2.2 Extension 설정

1. Extension 아이콘 클릭
2. **WebSocket Port**: `3333` (기본값)
3. **Connect** 클릭

#### 2.3 Draw.io 앱 열기

- **웹 버전**: https://app.diagrams.net/
- **데스크톱 앱**: draw.io Desktop

---

### Step 3: 연결 확인

#### 3.1 서버 연결 테스트

```bash
# 1. HTTP 엔드포인트 확인
curl http://localhost:3000/health
# {"status":"ok"}

# 2. MCP 엔드포인트 확인
curl http://localhost:3000/mcp
# MCP 프로토콜 응답
```

#### 3.2 Claude Code에서 확인

```bash
# Claude Code에서 MCP 상태 확인
/mcp

# drawio 서버가 connected 상태인지 확인
```

#### 3.3 Draw.io에서 확인

1. Draw.io 열기
2. Browser Extension 아이콘 → "Connected" 상태 확인
3. Extension에서 "Test Connection" 클릭

---

### Step 4: 사용 방법

MCP 연결이 완료되면 다음 도구 사용 가능:

```yaml
# 카테고리 조회
mcp__drawio__get-shape-categories

# AWS 아이콘 목록
mcp__drawio__get-shapes-in-category:
  category: "AWS"

# 아이콘 추가
mcp__drawio__add-cell-of-shape:
  shape: "mxgraph.aws4.ec2"
  x: 200
  y: 200
  width: 60
  height: 60

# 연결선 추가
mcp__drawio__add-edge:
  source: "cell-id-1"
  target: "cell-id-2"
```

---

### Troubleshooting

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| `Connection refused` | 서버 미실행 | `npx -y drawio-mcp-server --transport http` 실행 |
| `Port already in use` | 포트 충돌 | 기존 프로세스 종료: `lsof -ti:3000 \| xargs kill` |
| Extension "Disconnected" | WebSocket 연결 실패 | Extension 포트 설정 확인 (기본 3333) |
| MCP tools not available | HTTP 연결 실패 | `curl http://localhost:3000/health` 확인 |
| Draw.io 앱 미응답 | Extension 미설치 | Chrome Extension 설치 및 활성화 |

#### 포트 설정 변경 시

```bash
# 서버 - WebSocket 포트 변경 (Extension용)
npx -y drawio-mcp-server --transport http --extension-port 8080

# Extension 설정에서도 동일한 포트로 변경 필요!
```

---

### Plugin MCP 설정

이 Plugin은 HTTP 모드로 drawio MCP를 사용하도록 설정되어 있습니다:

**`.mcp.json`:**
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

**사전 요구사항:**
1. drawio-mcp-server가 HTTP 모드로 실행 중이어야 함
2. Browser Extension이 설치되고 연결되어야 함
3. Draw.io 앱이 열려 있어야 함

---

### MCP 없이 사용하기 (Fallback)

MCP 설정이 어렵거나 연결이 불안정한 경우, **XML 직접 작성 방식**을 사용합니다:

```
1. Write 도구로 .drawio XML 파일 생성
2. /opt/homebrew/bin/drawio CLI로 PNG 내보내기
3. PPT/문서에 이미지 삽입
```

이 방식은 **항상 작동**하며 별도 설정이 필요 없습니다.

---

## PPT용 아키텍처 다이어그램 워크플로우

PPT에 삽입할 아키텍처 다이어그램 생성 시 **반드시 캔버스 크기를 먼저 설정**합니다.

### Step 1: 캔버스 크기 설정 (PPT 레이아웃 기준)

PPT 16:9 Widescreen 기준 권장 크기:

| 용도 | 캔버스 크기 (px) | 비율 | 설명 |
|------|------------------|------|------|
| 전체 슬라이드 | 1920 x 1080 | 16:9 | 슬라이드 전체 사용 |
| 콘텐츠 영역 | 1600 x 900 | 16:9 | 여백 포함 |
| 절반 슬라이드 | 900 x 900 | 1:1 | 텍스트와 함께 사용 |
| 2/3 슬라이드 | 1200 x 900 | 4:3 | 텍스트 + 다이어그램 |

```xml
<!-- 전체 슬라이드용 캔버스 -->
<mxGraphModel dx="1920" dy="1080" grid="1" gridSize="10"
              pageWidth="1920" pageHeight="1080"
              defaultFontFamily="Amazon Ember">

<!-- 콘텐츠 영역용 캔버스 (권장) -->
<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10"
              pageWidth="1600" pageHeight="900"
              defaultFontFamily="Amazon Ember">
```

### Step 2: 다이어그램 생성

1. 템플릿 또는 MCP로 아키텍처 구성
2. AWS 아이콘 배치
3. 연결선 추가

### ⚠️ 필수: AWS 아이콘 라벨 표시

**모든 AWS 아이콘 아래에 서비스 이름을 반드시 표시합니다.**

```
┌─────────────┐
│   [아이콘]   │
│             │
│ Lambda      │  ← 서비스 이름 필수
└─────────────┘
```

**라벨 설정:**
- `verticalLabelPosition=bottom` (아이콘 아래에 라벨)
- `fontFamily=Amazon Ember`
- `fontSize=12`
- `fontColor=#FFFFFF` (Dark 테마)

### Step 3: PNG Export

```bash
# 고해상도 PNG 내보내기 (PPT용)
drawio -x -f png -s 2 -o architecture.png architecture.drawio

# 투명 배경 (Dark 테마 PPT용)
drawio -x -f png -s 2 -t -o architecture.png architecture.drawio
```

### Step 4: PPT에 삽입

```
mcp__ppt__manage_image:
  operation: "add"
  slide_index: 1
  image_source: "/path/to/architecture.png"
  left: 0.5      # inches
  top: 1.5       # inches
  width: 12.0    # inches (거의 전체 너비)
  height: 5.5    # inches
```

### PPT 슬라이드 영역 참조

PPT 16:9 (13.333" x 7.5") 기준:

```
┌─────────────────────────────────────────────────────────┐
│ Title Area (0.5" ~ 1.3")                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Content Area                                           │
│  Left: 0.5"   Top: 1.5"                                │
│  Width: 12.3" Height: 5.5"                             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Architecture Diagram                     │   │
│  │         (1600 x 900 px → 12" x 6.75")           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Footer (7.0" ~ 7.5")                                    │
└─────────────────────────────────────────────────────────┘
```

### 완전한 워크플로우 예시

```bash
# 1. drawio 파일 생성 (캔버스 크기 1600x900)
# 2. 아키텍처 다이어그램 작성
# 3. PNG export
drawio -x -f png -s 2 -o /tmp/arch.png architecture.drawio

# 4. PPT에 삽입
mcp__ppt__manage_image:
  operation: "add"
  slide_index: 2
  image_source: "/tmp/arch.png"
  left: 0.5
  top: 1.5
  width: 12.0
  height: 5.5
```

---

## MCP 서버 설정

### 방법 1: HTTP 모드 (권장 - 다중 세션 지원)

**사전 작업**: drawio-mcp-server를 HTTP 모드로 실행
```bash
npx -y drawio-mcp-server --transport http --http-port 3000
```

**Claude Code 설정** (~/.claude/settings.json 또는 .mcp.json):
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

### 방법 2: stdio 모드 (단일 세션용)

⚠️ **주의**: stdio 모드는 한 번에 하나의 Claude Code 세션만 사용 가능

```json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["-y", "drawio-mcp-server"]
    }
  }
}
```

### 모드 비교

| 항목 | HTTP 모드 | stdio 모드 |
|------|----------|-----------|
| 다중 세션 | ✅ 지원 | ❌ 포트 충돌 |
| 설정 복잡도 | 서버 별도 실행 필요 | 간단 |
| 안정성 | 높음 (Singleton) | 세션 의존적 |
| 권장 사용 | 일반 사용 | 테스트/개발 |

## Draw.io MCP 도구

### 다이어그램 조회

| 도구 | 설명 |
|------|------|
| `get-selected-cell` | 현재 선택된 셀 정보 조회 |
| `get-shape-categories` | 사용 가능한 shape 카테고리 목록 |
| `get-shapes-in-category` | 특정 카테고리의 shape 목록 |
| `get-shape-by-name` | 이름으로 shape 검색 |
| `list-paged-model` | 페이지네이션된 다이어그램 셀 정보 |

### 다이어그램 수정

| 도구 | 설명 |
|------|------|
| `add-rectangle` | 사각형 추가 |
| `add-edge` | 두 셀 연결 (화살표) |
| `delete-cell-by-id` | 셀 삭제 |
| `add-cell-of-shape` | 라이브러리에서 shape 추가 |
| `set-cell-shape` | 셀 모양 변경 |
| `set-cell-data` | 셀에 커스텀 속성 저장 |
| `edit-cell` | vertex 속성 수정 |
| `edit-edge` | edge 연결 수정 |

## AWS 아키텍처 다이어그램 가이드

### 폰트 설정

**Amazon Ember** 폰트를 기본으로 사용:

```xml
<mxGraphModel defaultFontFamily="Amazon Ember">
```

모든 텍스트 요소에 명시적으로 설정:

```
fontFamily=Amazon Ember;fontSize=14;
```

Amazon Ember 폰트가 없는 환경에서는 대체 폰트 순서:
1. Amazon Ember (AWS 공식)
2. Arial (범용)
3. Helvetica (macOS)

### AWS 아이콘 활용

Draw.io에서 AWS 아이콘 라이브러리 활성화:
1. draw.io 열기
2. File > Open Library > AWS 선택
3. 또는 More Shapes > AWS 카테고리 활성화

#### 주요 AWS 아이콘 카테고리

| 카테고리 | 서비스 예시 |
|----------|-------------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, EBS, EFS, Glacier |
| Database | RDS, DynamoDB, ElastiCache, Aurora |
| Networking | VPC, CloudFront, Route 53, ALB/NLB |
| Security | IAM, WAF, Shield, KMS |
| Analytics | Kinesis, Athena, EMR, Redshift |
| Integration | SQS, SNS, EventBridge, Step Functions |

### MCP로 AWS 아이콘 추가

```
mcp__drawio__get-shape-categories
→ AWS 카테고리 확인

mcp__drawio__get-shapes-in-category
→ category: "AWS"

mcp__drawio__add-cell-of-shape
→ shape: "mxgraph.aws4.ec2"
→ x, y, width, height 지정
```

## 아키텍처 다이어그램 레이아웃

### AWS 3-Tier Architecture 패턴

```
┌─────────────────────────────────────────────────────────┐
│                        AWS Cloud                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                     Region                         │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │                    VPC                       │  │  │
│  │  │  ┌─────────────┐    ┌─────────────────────┐ │  │  │
│  │  │  │ Public      │    │ Private Subnet      │ │  │  │
│  │  │  │ Subnet      │    │                     │ │  │  │
│  │  │  │ ┌─────────┐ │    │ ┌─────┐   ┌─────┐  │ │  │  │
│  │  │  │ │   ALB   │ │───▶│ │ EC2 │   │ RDS │  │ │  │  │
│  │  │  │ └─────────┘ │    │ └─────┘   └─────┘  │ │  │  │
│  │  │  └─────────────┘    └─────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 레이아웃 원칙

1. **외부에서 내부로**: 사용자/인터넷 → AWS Cloud → Region → VPC → Subnet
2. **왼쪽에서 오른쪽으로**: 데이터 흐름 방향
3. **계층 구분**: 프레젠테이션 → 애플리케이션 → 데이터
4. **AZ 표시**: 고가용성 설계 시 가용영역 명확히 구분

### 하이브리드 아키텍처 패턴 (IDC + AWS)

```
┌──────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────────┐ │
│  │ Security VPC│   │ Network VPC │   │      Workload VPC           │ │
│  │             │   │             │   │                             │ │
│  │  [GWLB]     │   │ [DX GW]     │   │ [GWLBe]  [Services]        │ │
│  │  [FW EC2]   │   │ [TGW]       │   │          [Data]            │ │
│  └─────────────┘   └─────────────┘   └─────────────────────────────┘ │
│                           │                                          │
└───────────────────────────┼──────────────────────────────────────────┘
                            │ Direct Connect
┌───────────────────────────┼──────────────────────────────────────────┐
│  On-Premise (IDC)         │                                          │
│  [Firewall] [Router] ─────┘                                          │
└──────────────────────────────────────────────────────────────────────┘
```

**필수 구성 요소:**

| VPC | 포함 서비스 | 용도 |
|-----|------------|------|
| **Security VPC** | GWLB, Firewall EC2 | 트래픽 검사 |
| **Network VPC** | DX Gateway, Transit Gateway | 네트워크 허브 |
| **Workload VPC** | GWLB Endpoint, AI/데이터 서비스 | 실제 워크로드 |

### 라이선스 뱃지 표시

방화벽 등 3rd Party 솔루션에는 **BYOL + Marketplace** 뱃지를 나란히 표시:

```xml
<!-- BYOL 뱃지 -->
<mxCell id="byol-badge" value="BYOL"
        style="rounded=1;fillColor=#FFF9C4;strokeColor=#F57F17;
               fontFamily=Amazon Ember;fontSize=9;fontColor=#F57F17;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="420" width="55" height="22" as="geometry" />
</mxCell>

<!-- Marketplace 뱃지 -->
<mxCell id="marketplace-badge" value="Marketplace"
        style="rounded=1;fillColor=#E3F2FD;strokeColor=#1976D2;
               fontFamily=Amazon Ember;fontSize=9;fontColor=#1976D2;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="465" y="420" width="75" height="22" as="geometry" />
</mxCell>
```

### 범례(Legend) 필수 항목

범례 박스에 포함해야 할 항목:

| 항목 | 설명 |
|------|------|
| AWS 아이콘 | GWLB, EC2, Endpoint 등 |
| 연결선 | Direct Connect (주황), PrivateLink (보라) |
| 라이선스 | BYOL, Marketplace 뱃지 |
| PrivateLink 설명 | "(VPC 간 프라이빗 연결)" |

```xml
<!-- PrivateLink 범례 예시 -->
<mxCell id="leg-private-desc" value="(VPC 간 프라이빗 연결)"
        style="text;html=1;fontSize=8;fontColor=#5A30B5;fontStyle=2;"
        vertex="1" parent="1">
  <mxGeometry x="410" y="720" width="120" height="15" as="geometry" />
</mxCell>
```

### ⚠️ 요소 겹침 방지

**범례/설명 박스는 VPC 영역과 겹치지 않도록 위치 조정:**

```
AWS Cloud 영역:     y=50 ~ y=600
Network VPC:        y=485 ~ y=600
범례/트래픽 박스:    y=620 이후 (최소 20px 여백)
```

VPC 추가 시 아래 영역 요소 위치를 자동으로 내려야 함.

### 색상 가이드 (AWS 공식)

| 용도 | 색상 코드 | 설명 |
|------|-----------|------|
| AWS Cloud | #232F3E | 다크 네이비 (배경) |
| Region | #147EBA | 블루 |
| VPC | #248814 | 그린 |
| Public Subnet | #E7F4E8 | 라이트 그린 |
| Private Subnet | #E6F2F8 | 라이트 블루 |
| Security Group | #DF3312 | 레드 (보더) |
| 화살표 | #545B64 | 그레이 |

## XML 직접 작성 (MCP 없이)

MCP가 없는 환경에서 .drawio 파일 직접 생성:

### 기본 구조

```xml
<mxfile host="app.diagrams.net" agent="Claude">
  <diagram name="Architecture" id="arch-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10"
                  defaultFontFamily="Amazon Ember">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- AWS Cloud 컨테이너 -->
        <mxCell id="aws-cloud" value="AWS Cloud"
                style="rounded=1;fillColor=#232F3E;fontColor=#FFFFFF;
                       fontFamily=Amazon Ember;fontSize=16;
                       verticalAlign=top;spacingTop=10;"
                vertex="1" parent="1">
          <mxGeometry x="50" y="50" width="800" height="500" as="geometry"/>
        </mxCell>

        <!-- Region -->
        <mxCell id="region" value="ap-northeast-2"
                style="rounded=1;fillColor=#147EBA;fontColor=#FFFFFF;
                       fontFamily=Amazon Ember;fontSize=14;
                       verticalAlign=top;spacingTop=8;"
                vertex="1" parent="aws-cloud">
          <mxGeometry x="20" y="40" width="760" height="440" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### AWS 서비스 아이콘 스타일

```xml
<!-- EC2 인스턴스 -->
<mxCell id="ec2-1" value="Web Server"
        style="shape=mxgraph.aws4.ec2;
               fontFamily=Amazon Ember;fontSize=12;
               labelPosition=center;verticalLabelPosition=bottom;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="200" width="60" height="60" as="geometry"/>
</mxCell>

<!-- S3 버킷 -->
<mxCell id="s3-1" value="Static Assets"
        style="shape=mxgraph.aws4.s3;
               fontFamily=Amazon Ember;fontSize=12;
               labelPosition=center;verticalLabelPosition=bottom;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="200" width="60" height="60" as="geometry"/>
</mxCell>
```

## 워크플로우

### MCP 활용 시

1. draw.io 앱 열기 (브라우저 또는 데스크톱)
2. MCP 서버 연결 확인
3. `get-shape-categories`로 AWS 카테고리 확인
4. `add-cell-of-shape`로 AWS 아이콘 추가
5. `add-edge`로 연결선 추가
6. `edit-cell`로 스타일 조정

### XML 직접 작성 시

1. 템플릿 파일 복사
2. AWS 아이콘 shape 추가
3. 연결선 (edge) 추가
4. PNG 내보내기

## PNG 내보내기

### draw.io CLI 사용법

macOS에서 Homebrew로 설치된 draw.io CLI 경로: `/opt/homebrew/bin/drawio`

```bash
# 기본 PNG 내보내기
drawio -x -f png -o output.png input.drawio

# 고해상도 PNG (2배 스케일, PPT용 권장)
drawio -x -f png -s 2 -o output.png input.drawio

# 투명 배경 (Dark 테마 PPT용)
drawio -x -f png -s 2 -t -o output.png input.drawio

# SVG 내보내기 (벡터, 확대해도 선명)
drawio -x -f svg -o output.svg input.drawio

# PDF 내보내기 (문서 첨부용)
drawio -x -f pdf -o output.pdf input.drawio
```

### CLI 옵션 상세

| 옵션 | 설명 | 권장값 |
|------|------|--------|
| `-x` | 내보내기 모드 | 필수 |
| `-f <format>` | 출력 형식 (png, svg, pdf, jpg) | png |
| `-s <scale>` | 확대 배율 | 2 (고해상도) |
| `-t` | 투명 배경 | Dark PPT용 |
| `-o <file>` | 출력 파일 경로 | 필수 |
| `--width <px>` | 출력 너비 지정 | - |
| `--height <px>` | 출력 높이 지정 | - |
| `-b <color>` | 배경색 지정 | #232F3E (AWS Dark) |

### 내보내기 예시

```bash
# 하나카드 아키텍처 다이어그램 내보내기 (실제 사용 예시)
/opt/homebrew/bin/drawio -x -f png -s 2 \
  -o /path/to/assets/HanaCard_Hybrid_Architecture.png \
  /path/to/assets/HanaCard_Hybrid_Architecture.drawio

# Markdown에서 참조
![아키텍처 다이어그램](../assets/HanaCard_Hybrid_Architecture.png)
```

### 자동화 스크립트

```bash
#!/bin/bash
# export-drawio.sh - Draw.io 파일을 PNG로 일괄 변환

DRAWIO_CMD="/opt/homebrew/bin/drawio"
SCALE=2

for file in *.drawio; do
  output="${file%.drawio}.png"
  echo "Exporting: $file -> $output"
  $DRAWIO_CMD -x -f png -s $SCALE -o "$output" "$file"
done
```

## 템플릿 활용

### 사용 가능한 템플릿

| 파일 | 설명 | 용도 |
|------|------|------|
| `templates/aws-basic.drawio` | VPC, Subnet, AZ 기본 구조 | 빈 캔버스에서 시작 |
| `templates/aws-samples.drawio` | Data Lake 아키텍처 샘플 | 아이콘 복사/참조용 |

### aws-samples.drawio 활용법

이 샘플 파일에는 다음 AWS 서비스 아이콘이 포함되어 있어 복사하여 사용 가능:

**인증/보안**:
- Amazon Cognito
- Active Directory
- IAM Roles

**컴퓨팅**:
- Lambda (리소스 아이콘 + 함수 아이콘)

**통합/API**:
- Amazon API Gateway

**스토리지/데이터베이스**:
- Amazon S3
- Amazon DynamoDB

**분석**:
- AWS Glue
- Amazon Athena
- Amazon ElasticSearch Service

**모니터링**:
- Amazon CloudWatch
- CloudWatch Logs

**연결선 스타일**:
- 양방향 화살표 (strokeWidth=2, strokeColor=#808080)
- orthogonalEdgeStyle 사용

### 템플릿에서 아이콘 복사하기

1. `templates/aws-samples.drawio` 파일을 draw.io에서 열기
2. 필요한 아이콘 선택 후 복사 (Ctrl/Cmd + C)
3. 새 다이어그램에 붙여넣기 (Ctrl/Cmd + V)
4. 위치와 라벨 수정

### 템플릿 스타일 참조

aws-samples.drawio의 아이콘 스타일 패턴:

```xml
<!-- 리소스 아이콘 (그라데이션 있음) -->
style="outlineConnect=0;fontColor=#232F3E;
       gradientColor=#F78E04;gradientDirection=north;
       fillColor=#D05C17;strokeColor=#ffffff;
       shape=mxgraph.aws4.resourceIcon;
       resIcon=mxgraph.aws4.lambda;"

<!-- 함수/객체 아이콘 (단색) -->
style="outlineConnect=0;fontColor=#232F3E;
       gradientColor=none;fillColor=#D05C17;
       strokeColor=none;
       shape=mxgraph.aws4.lambda_function;"
```

## 참조 문서

상세 가이드는 다음 파일 참조:
- **`reference/aws-icons.md`** - AWS 아이콘 shape 이름 및 스타일
- **`reference/best-practices.md`** - 아키텍처 다이어그램 모범사례

## Quality Review (필수 — 생략 불가)

다이어그램 완성 후 배포/완료 선언 전에 반드시:
1. content-review-agent 호출 → `review content at [파일경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> ⚠️ 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

## 검증 체크리스트

- [ ] Amazon Ember 폰트가 모든 텍스트에 설정되었는가
- [ ] AWS 공식 색상을 사용하고 있는가
- [ ] 계층 구조가 명확한가 (Cloud > Region > VPC > Subnet)
- [ ] 데이터 흐름 방향이 일관성 있는가
- [ ] 아이콘 크기가 균일한가 (권장: 60x60)
- [ ] 라벨이 아이콘 아래에 배치되었는가
