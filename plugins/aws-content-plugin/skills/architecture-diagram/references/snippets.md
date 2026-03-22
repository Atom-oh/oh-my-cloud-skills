# Draw.io XML 스니펫

자주 사용하는 AWS 아키텍처 다이어그램 XML 패턴 모음입니다.
복사하여 사용하고, ID와 좌표만 수정하세요.

---

## 기본 구조

### 1. 빈 캔버스 (PPT 1600x900)

```xml
<mxfile host="app.diagrams.net" agent="Claude Code" version="21.0.0" type="device">
  <diagram name="Architecture" id="arch-1">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="900"
                  math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- 여기에 요소 추가 -->

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## 그룹 박스 스니펫

### 2. AWS Cloud Container

```xml
<mxCell id="aws-cloud" value="AWS Cloud"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=14;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="1">
  <mxGeometry x="20" y="20" width="1560" height="860" as="geometry" />
</mxCell>
```

### 3. Region Container

```xml
<mxCell id="region" value="ap-northeast-2 (Seoul)"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;fontFamily=Amazon Ember;dashed=1;"
        vertex="1" parent="aws-cloud">
  <mxGeometry x="20" y="40" width="1520" height="800" as="geometry" />
</mxCell>
```

### 4. VPC Container

```xml
<mxCell id="vpc-1" value="Production VPC (10.0.0.0/16)"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#879196;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#879196;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="region">
  <mxGeometry x="20" y="40" width="500" height="400" as="geometry" />
</mxCell>
```

### 5. Public Subnet (Green)

```xml
<mxCell id="public-subnet" value="Public Subnet (10.0.1.0/24)"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;verticalAlign=top;align=left;spacingLeft=30;fontColor=#248814;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="vpc-1">
  <mxGeometry x="20" y="45" width="220" height="150" as="geometry" />
</mxCell>
```

### 6. Private Subnet (Blue)

```xml
<mxCell id="private-subnet" value="Private Subnet (10.0.10.0/24)"
        style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="vpc-1">
  <mxGeometry x="20" y="210" width="220" height="170" as="geometry" />
</mxCell>
```

### 7. On-Premise (IDC) Container

```xml
<mxCell id="on-prem" value="On-Premise (IDC)"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_corporate_data_center;strokeColor=#5A6C86;fillColor=#E6E6E6;verticalAlign=top;align=left;spacingLeft=30;fontColor=#5A6C86;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="1">
  <mxGeometry x="20" y="45" width="350" height="560" as="geometry" />
</mxCell>
```

### 8. Custom Box (Dark Background)

```xml
<mxCell id="custom-box" value="AWS Managed Services"
        style="rounded=1;arcSize=5;whiteSpace=wrap;html=1;fillColor=#263238;strokeColor=#FF9900;strokeWidth=2;fontFamily=Amazon Ember;fontSize=11;fontStyle=1;verticalAlign=top;spacingTop=8;spacingLeft=10;fontColor=#FF9900;"
        vertex="1" parent="1">
  <mxGeometry x="900" y="80" width="420" height="200" as="geometry" />
</mxCell>
```

### 9. Security VPC (Red Border)

```xml
<mxCell id="security-vpc" value="Security VPC"
        style="sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#C7131F;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#C7131F;fontFamily=Amazon Ember;dashed=0;"
        vertex="1" parent="region">
  <mxGeometry x="550" y="40" width="300" height="250" as="geometry" />
</mxCell>
```

---

## 아이콘 스니펫

### 10. Compute (Orange) - EC2

```xml
<mxCell id="ec2-1" value="Web Server"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;fontFamily=Amazon Ember;"
        vertex="1" parent="private-subnet">
  <mxGeometry x="86" y="60" width="48" height="48" as="geometry" />
</mxCell>
```

### 11. Compute (Orange) - Lambda

```xml
<mxCell id="lambda-1" value="Lambda"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 12. Compute (Orange) - EKS

```xml
<mxCell id="eks-1" value="EKS"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="300" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 13. Database (Blue) - Aurora

```xml
<mxCell id="aurora-1" value="Aurora"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 14. Database (Blue) - DynamoDB

```xml
<mxCell id="dynamodb-1" value="DynamoDB"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.dynamodb;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="500" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 15. Storage (Green) - S3

```xml
<mxCell id="s3-1" value="S3"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#60A337;gradientDirection=north;fillColor=#277116;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="600" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 16. Security (Red) - WAF

```xml
<mxCell id="waf-1" value="WAF"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F54749;gradientDirection=north;fillColor=#C7131F;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="700" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 17. Security (Red) - Secrets Manager

```xml
<mxCell id="secrets-1" value="Secrets Manager"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F54749;gradientDirection=north;fillColor=#C7131F;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.secrets_manager;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="800" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 18. Networking (Purple) - ALB

```xml
<mxCell id="alb-1" value="ALB"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="100" y="200" width="48" height="48" as="geometry" />
</mxCell>
```

### 19. Networking (Purple) - Transit Gateway

```xml
<mxCell id="tgw-1" value="Transit GW"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="750" y="400" width="60" height="60" as="geometry" />
</mxCell>
```

### 20. AI/ML (Teal) - Bedrock

```xml
<mxCell id="bedrock-1" value="Bedrock"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4AB29A;gradientDirection=north;fillColor=#116D5B;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.bedrock;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="300" width="48" height="48" as="geometry" />
</mxCell>
```

### 21. AI/ML (Teal) - SageMaker

```xml
<mxCell id="sagemaker-1" value="SageMaker"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#4AB29A;gradientDirection=north;fillColor=#116D5B;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sagemaker;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="300" y="300" width="48" height="48" as="geometry" />
</mxCell>
```

### 22. Management (Pink) - CloudWatch

```xml
<mxCell id="cloudwatch-1" value="CloudWatch"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F34482;gradientDirection=north;fillColor=#BC1356;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudwatch;fontFamily=Amazon Ember;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="300" width="48" height="48" as="geometry" />
</mxCell>
```

### 23. Traditional Server (On-Premise)

```xml
<mxCell id="server-1" value="Server"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#5A6C86;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=9;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.traditional_server;fontFamily=Amazon Ember;"
        vertex="1" parent="on-prem">
  <mxGeometry x="50" y="100" width="45" height="46" as="geometry" />
</mxCell>
```

### 24. Security Server (Red - Firewall)

```xml
<mxCell id="fw-server" value="Firewall"
        style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#BF0816;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=8;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.traditional_server;fontFamily=Amazon Ember;"
        vertex="1" parent="on-prem">
  <mxGeometry x="50" y="200" width="40" height="41" as="geometry" />
</mxCell>
```

---

## 연결선 스니펫

### 25. 일반 양방향 화살표

```xml
<mxCell id="conn-1" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#545B64;"
        edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>
```

### 26. Direct Connect (Thick Orange)

```xml
<mxCell id="dx-conn" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=4;strokeColor=#FF9800;edgeStyle=orthogonalEdgeStyle;"
        edge="1" parent="1" source="idc-router" target="dx-gateway">
  <mxGeometry width="50" height="50" relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="380" y="400" />
      <mxPoint x="380" y="200" />
    </Array>
  </mxGeometry>
</mxCell>
```

### 27. PrivateLink (Purple)

```xml
<mxCell id="privatelink-conn" value=""
        style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#5A30B5;"
        edge="1" parent="1" source="vpc-endpoint" target="service">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>
```

### 28. Data Flow (Blue Dashed)

```xml
<mxCell id="data-flow" value=""
        style="endArrow=classic;html=1;rounded=0;strokeWidth=2;strokeColor=#3334B9;dashed=1;"
        edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry width="50" height="50" relative="1" as="geometry" />
</mxCell>
```

---

## 텍스트 & 범례 스니펫

### 29. 일반 텍스트 라벨

```xml
<mxCell id="label-1" value="Label Text"
        style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Amazon Ember;fontSize=10;fontColor=#232F3E;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="100" height="20" as="geometry" />
</mxCell>
```

### 30. 범례 박스

```xml
<mxCell id="legend" value="Legend"
        style="rounded=1;arcSize=5;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#5A6C86;strokeWidth=1;fontFamily=Amazon Ember;fontSize=11;fontStyle=1;verticalAlign=top;spacingTop=8;fontColor=#5A6C86;"
        vertex="1" parent="1">
  <mxGeometry x="1100" y="700" width="400" height="100" as="geometry" />
</mxCell>
```

### 31. BYOL 뱃지

```xml
<mxCell id="byol-badge" value="BYOL"
        style="rounded=1;fillColor=#FFF9C4;strokeColor=#F57F17;fontFamily=Amazon Ember;fontSize=9;fontColor=#F57F17;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="420" width="55" height="22" as="geometry" />
</mxCell>
```

### 32. Marketplace 뱃지

```xml
<mxCell id="marketplace-badge" value="Marketplace"
        style="rounded=1;fillColor=#E3F2FD;strokeColor=#1976D2;fontFamily=Amazon Ember;fontSize=9;fontColor=#1976D2;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="465" y="420" width="75" height="22" as="geometry" />
</mxCell>
```

---

## 사용법

1. 필요한 스니펫을 복사
2. ID 값을 고유하게 변경 (예: `ec2-1` → `ec2-web-prod`)
3. 좌표(x, y) 수정
4. parent 속성을 해당 컨테이너 ID로 변경
5. value 텍스트 수정

### 좌표 계산 팁

```
# 아이콘 가운데 정렬
icon_x = container_x + (container_width - icon_width) / 2

# 아이콘 그리드 (48x48, 간격 27px)
icon2_x = icon1_x + 48 + 27

# 다음 행
next_row_y = current_y + 48 + 20 + 20 (아이콘 + 라벨 + 간격)
```
