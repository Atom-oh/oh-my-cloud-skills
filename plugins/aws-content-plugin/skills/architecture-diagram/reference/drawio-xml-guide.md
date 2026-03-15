# Draw.io XML Direct Writing Guide

Create .drawio files directly without MCP dependency. This method always works.

## Basic XML Structure

```xml
<mxfile host="app.diagrams.net" agent="Claude">
  <diagram name="Architecture" id="arch-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10"
                  defaultFontFamily="Amazon Ember">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- AWS Cloud Container -->
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

---

## AWS Service Icon Styles

### EC2 Instance

```xml
<mxCell id="ec2-1" value="Web Server"
        style="shape=mxgraph.aws4.ec2;
               fontFamily=Amazon Ember;fontSize=12;
               labelPosition=center;verticalLabelPosition=bottom;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="200" width="60" height="60" as="geometry"/>
</mxCell>
```

### S3 Bucket

```xml
<mxCell id="s3-1" value="Static Assets"
        style="shape=mxgraph.aws4.s3;
               fontFamily=Amazon Ember;fontSize=12;
               labelPosition=center;verticalLabelPosition=bottom;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="200" width="60" height="60" as="geometry"/>
</mxCell>
```

### Lambda Function

```xml
<mxCell id="lambda-1" value="API Handler"
        style="shape=mxgraph.aws4.lambda;
               fontFamily=Amazon Ember;fontSize=12;
               labelPosition=center;verticalLabelPosition=bottom;"
        vertex="1" parent="1">
  <mxGeometry x="300" y="200" width="60" height="60" as="geometry"/>
</mxCell>
```

---

## Resource vs Function Icons

### Resource Icon (with gradient)

```xml
style="outlineConnect=0;fontColor=#232F3E;
       gradientColor=#F78E04;gradientDirection=north;
       fillColor=#D05C17;strokeColor=#ffffff;
       shape=mxgraph.aws4.resourceIcon;
       resIcon=mxgraph.aws4.lambda;"
```

### Function/Object Icon (solid color)

```xml
style="outlineConnect=0;fontColor=#232F3E;
       gradientColor=none;fillColor=#D05C17;
       strokeColor=none;
       shape=mxgraph.aws4.lambda_function;"
```

---

## Connection Styles

### Basic Arrow

```xml
<mxCell id="edge-1" value=""
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;
               orthogonalLoop=1;jettySize=auto;
               strokeWidth=2;strokeColor=#545B64;"
        edge="1" parent="1" source="ec2-1" target="s3-1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Bidirectional Arrow

```xml
<mxCell id="edge-2" value=""
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;
               strokeWidth=2;strokeColor=#808080;
               startArrow=classic;endArrow=classic;"
        edge="1" parent="1" source="cell-1" target="cell-2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Direct Connect (Orange)

```xml
style="strokeColor=#F58536;strokeWidth=3;"
```

### PrivateLink (Purple)

```xml
style="strokeColor=#5A30B5;strokeWidth=2;dashed=1;"
```

---

## Container Hierarchy

### VPC Container

```xml
<mxCell id="vpc" value="VPC (10.0.0.0/16)"
        style="rounded=1;fillColor=#248814;fillOpacity=20;
               strokeColor=#248814;strokeWidth=2;
               fontFamily=Amazon Ember;fontSize=14;fontColor=#248814;
               verticalAlign=top;spacingTop=8;"
        vertex="1" parent="region">
  <mxGeometry x="20" y="40" width="720" height="380" as="geometry"/>
</mxCell>
```

### Public Subnet

```xml
<mxCell id="public-subnet" value="Public Subnet"
        style="rounded=1;fillColor=#E7F4E8;
               strokeColor=#248814;strokeWidth=1;
               fontFamily=Amazon Ember;fontSize=12;
               verticalAlign=top;spacingTop=6;"
        vertex="1" parent="vpc">
  <mxGeometry x="20" y="40" width="300" height="320" as="geometry"/>
</mxCell>
```

### Private Subnet

```xml
<mxCell id="private-subnet" value="Private Subnet"
        style="rounded=1;fillColor=#E6F2F8;
               strokeColor=#147EBA;strokeWidth=1;
               fontFamily=Amazon Ember;fontSize=12;
               verticalAlign=top;spacingTop=6;"
        vertex="1" parent="vpc">
  <mxGeometry x="400" y="40" width="300" height="320" as="geometry"/>
</mxCell>
```

---

## Badge Styles

### BYOL Badge

```xml
<mxCell id="byol-badge" value="BYOL"
        style="rounded=1;fillColor=#FFF9C4;strokeColor=#F57F17;
               fontFamily=Amazon Ember;fontSize=9;fontColor=#F57F17;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="400" y="420" width="55" height="22" as="geometry"/>
</mxCell>
```

### Marketplace Badge

```xml
<mxCell id="marketplace-badge" value="Marketplace"
        style="rounded=1;fillColor=#E3F2FD;strokeColor=#1976D2;
               fontFamily=Amazon Ember;fontSize=9;fontColor=#1976D2;fontStyle=1;"
        vertex="1" parent="1">
  <mxGeometry x="465" y="420" width="75" height="22" as="geometry"/>
</mxCell>
```

---

## Legend Example

### PrivateLink Legend Item

```xml
<mxCell id="leg-private-desc" value="(VPC 간 프라이빗 연결)"
        style="text;html=1;fontSize=8;fontColor=#5A30B5;fontStyle=2;"
        vertex="1" parent="1">
  <mxGeometry x="410" y="720" width="120" height="15" as="geometry"/>
</mxCell>
```

---

## Canvas Size Settings

### PPT Full Slide (16:9)

```xml
<mxGraphModel dx="1920" dy="1080" grid="1" gridSize="10"
              pageWidth="1920" pageHeight="1080"
              defaultFontFamily="Amazon Ember">
```

### PPT Content Area (Recommended)

```xml
<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10"
              pageWidth="1600" pageHeight="900"
              defaultFontFamily="Amazon Ember">
```

---

## Common Shape Names

| Service | Shape Name |
|---------|------------|
| EC2 | `mxgraph.aws4.ec2` |
| Lambda | `mxgraph.aws4.lambda` |
| S3 | `mxgraph.aws4.s3` |
| RDS | `mxgraph.aws4.rds` |
| DynamoDB | `mxgraph.aws4.dynamodb` |
| API Gateway | `mxgraph.aws4.api_gateway` |
| CloudFront | `mxgraph.aws4.cloudfront` |
| Route 53 | `mxgraph.aws4.route_53` |
| ALB | `mxgraph.aws4.application_load_balancer` |
| NLB | `mxgraph.aws4.network_load_balancer` |
| VPC | `mxgraph.aws4.vpc` |
| IAM | `mxgraph.aws4.iam` |
| Cognito | `mxgraph.aws4.cognito` |
| SQS | `mxgraph.aws4.sqs` |
| SNS | `mxgraph.aws4.sns` |
| Kinesis | `mxgraph.aws4.kinesis` |
| Glue | `mxgraph.aws4.glue` |
| Athena | `mxgraph.aws4.athena` |
| CloudWatch | `mxgraph.aws4.cloudwatch` |
| ECS | `mxgraph.aws4.ecs` |
| EKS | `mxgraph.aws4.eks` |

---

## Label Positioning

Always place labels below icons:

```xml
verticalLabelPosition=bottom
labelPosition=center
fontFamily=Amazon Ember
fontSize=12
fontColor=#FFFFFF  <!-- Dark theme -->
```

---

## Best Practices

1. **Font**: Use `Amazon Ember` everywhere
2. **Icon size**: Consistent 60x60 px
3. **Grid**: Enable with `gridSize=10`
4. **Hierarchy**: Cloud > Region > VPC > Subnet > Resources
5. **Labels**: Always below icons with service name
6. **Colors**: Use AWS official colors (see color guide)
