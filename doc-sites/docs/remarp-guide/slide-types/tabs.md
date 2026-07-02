---
sidebar_position: 5
title: Tabs 슬라이드
---

# Tabs 슬라이드

Tabs 슬라이드는 탭 인터페이스로 관련 콘텐츠를 그룹화합니다. 같은 주제의 다른 형식이나 옵션을 보여줄 때 유용합니다.

## 기본 문법

````markdown
---
@type: tabs

## Configuration Examples

### YAML
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
```

### JSON
```json
{
  "apiVersion": "v1",
  "kind": "ConfigMap"
}
```

### TOML
```toml
[metadata]
name = "app-config"
```
````

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: tabs` | Tabs 타입 지정 (필수) |
| `@timing` | 예상 발표 시간 |

## 구조

`### ` 헤딩이 각 탭의 레이블이 되고, 그 아래 내용이 탭 콘텐츠가 됩니다.

## 예제

### 언어별 코드 예제

````markdown
---
@type: tabs

## Lambda Handler Examples

### Python
```python {filename="handler.py"}
import json

def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello!')
    }
```

### Node.js
```javascript {filename="handler.js"}
exports.handler = async (event) => {
    return {
        statusCode: 200,
        body: JSON.stringify('Hello!')
    };
};
```

### Go
```go {filename="main.go"}
package main

import (
    "github.com/aws/aws-lambda-go/lambda"
)

func handler() (string, error) {
    return "Hello!", nil
}

func main() {
    lambda.Start(handler)
}
```
````

### 배포 옵션

```markdown
---
@type: tabs

## Deployment Methods

### AWS Console
1. Navigate to Lambda service
2. Click "Create function"
3. Configure function settings
4. Upload code or use inline editor
5. Configure triggers and permissions

### AWS CLI
```bash
aws lambda create-function \
  --function-name my-function \
  --runtime python3.9 \
  --handler handler.handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::123456789012:role/lambda-role
```

### SAM
```bash
sam init --runtime python3.9
sam build
sam deploy --guided
```

### CDK
```typescript
new lambda.Function(this, 'MyFunction', {
  runtime: lambda.Runtime.PYTHON_3_9,
  handler: 'handler.handler',
  code: lambda.Code.fromAsset('lambda'),
});
```
```

### 설정 파일 비교

````markdown
---
@type: tabs

## Infrastructure as Code

### Terraform
```hcl {filename="main.tf"}
resource "aws_lambda_function" "example" {
  filename      = "lambda.zip"
  function_name = "my-function"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.9"
}
```

### CloudFormation
```yaml {filename="template.yaml"}
Resources:
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: my-function
      Runtime: python3.9
      Handler: handler.handler
      Code:
        S3Bucket: my-bucket
        S3Key: lambda.zip
```

### Pulumi
```typescript {filename="index.ts"}
const func = new aws.lambda.Function("my-function", {
    runtime: "python3.9",
    handler: "handler.handler",
    code: new pulumi.asset.FileArchive("./lambda"),
    role: role.arn,
});
```
````

## 렌더링

Tabs 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>Title</h2></div>
  <div class="slide-body">
    <div class="tab-bar">
      <button class="tab-btn active" data-tab="t1">Tab 1</button>
      <button class="tab-btn" data-tab="t2">Tab 2</button>
    </div>
    <div class="tab-content active" data-tab="t1">
      <!-- Tab 1 content -->
    </div>
    <div class="tab-content" data-tab="t2">
      <!-- Tab 2 content -->
    </div>
  </div>
</div>
```

## 키보드 조작

| 키 | 동작 |
|----|------|
| `↑` / `↓` | 탭 전환 |
| `←` / `→` | 이전/다음 슬라이드 |

## 팁

:::tip
Tabs 슬라이드는 같은 개념의 다른 구현이나 형식을 보여줄 때 효과적입니다. 예: 같은 설정의 YAML/JSON/TOML 버전
:::

:::info
탭은 5개 이하로 유지하는 것이 좋습니다. 너무 많은 탭은 탐색하기 어렵습니다.
:::
