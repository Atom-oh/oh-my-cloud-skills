---
sidebar_position: 7
title: 코드 블록
---

# 코드 블록

Remarp는 향상된 코드 블록을 지원합니다. 파일명 표시, 라인 하이라이팅, diff 모드 등의 기능을 제공합니다.

## 기본 코드 블록

표준 마크다운 코드 펜스를 사용합니다:

````markdown
```python
def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```
````

## 파일명 표시

`{filename="..."}` 속성으로 코드 블록 위에 파일명을 표시합니다:

````markdown
```yaml {filename="serverless.yml"}
service: my-api
provider:
  name: aws
  runtime: python3.9
  region: us-east-1

functions:
  hello:
    handler: handler.hello
    events:
      - http:
          path: /hello
          method: get
```
````

## 라인 하이라이팅

`{highlight="..."}` 속성으로 특정 라인을 강조합니다:

````markdown
```python {highlight="3-5"}
def handler(event, context):
    # Process the event
    user_id = event['pathParameters']['userId']
    action = event['queryStringParameters'].get('action', 'read')
    timestamp = datetime.now().isoformat()

    return {'statusCode': 200, 'body': 'OK'}
```
````

### 하이라이트 형식

| 형식 | 예시 | 설명 |
|------|------|------|
| 단일 라인 | `{highlight="3"}` | 3번째 줄만 강조 |
| 범위 | `{highlight="3-5"}` | 3~5번째 줄 강조 |
| 복합 | `{highlight="1,3,7-9"}` | 1번, 3번, 7~9번 줄 강조 |

## 속성 조합

파일명과 하이라이트를 함께 사용할 수 있습니다:

````markdown
```typescript {filename="handler.ts" highlight="5-8"}
import { APIGatewayEvent, Context } from 'aws-lambda';

export async function handler(event: APIGatewayEvent, context: Context) {
  const userId = event.pathParameters?.userId;

  // Highlighted: Input validation
  if (!userId) {
    return { statusCode: 400, body: 'Missing userId' };
  }

  return { statusCode: 200, body: `Hello ${userId}` };
}
```
````

## Diff 모드

변경 사항을 표시하려면 `diff` 언어를 사용합니다:

````markdown
```diff {filename="config.yaml"}
 database:
   host: localhost
-  port: 5432
+  port: 5433
   name: myapp
+  pool_size: 10
```
````

| 접두사 | 의미 |
|--------|------|
| `-` | 삭제된 라인 (빨간색) |
| `+` | 추가된 라인 (녹색) |
| ` ` (공백) | 변경되지 않은 라인 |

## 지원되는 언어

주요 지원 언어:

| 언어 | 식별자 |
|------|--------|
| Python | `python`, `py` |
| JavaScript | `javascript`, `js` |
| TypeScript | `typescript`, `ts` |
| YAML | `yaml`, `yml` |
| JSON | `json` |
| Bash/Shell | `bash`, `sh`, `shell` |
| Go | `go` |
| Java | `java` |
| SQL | `sql` |
| HCL (Terraform) | `hcl`, `terraform` |
| Dockerfile | `dockerfile` |

## 구문 강조 클래스

코드 블록 내에서 다음 CSS 클래스가 사용됩니다:

| 클래스 | 용도 |
|--------|------|
| `.comment` | 주석 |
| `.keyword` | 키워드 |
| `.string` | 문자열 |
| `.key` | YAML/JSON 키 |
| `.value` | 값 |
| `.number` | 숫자 |

## 예제: 다양한 코드 블록

### Lambda 핸들러

````markdown
```python {filename="handler.py" highlight="4-7"}
import json
import boto3

def handler(event, context):
    # Extract user ID from path
    user_id = event['pathParameters']['userId']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    response = table.get_item(Key={'userId': user_id})
    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Item', {}))
    }
```
````

### Kubernetes 설정

````markdown
```yaml {filename="deployment.yaml" highlight="12-14"}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:latest
        resources:
          limits:
            cpu: "500m"
            memory: "128Mi"
```
````

### 설정 변경 비교

````markdown
```diff {filename="terraform.tfvars"}
 environment = "production"
 region      = "us-east-1"
-instance_type = "t3.micro"
+instance_type = "t3.small"

+# New settings for auto-scaling
+min_capacity = 2
+max_capacity = 10
```
````

## 코드 슬라이드 타입

10줄 이상의 긴 코드 블록이 있으면 자동으로 `@type: code`가 감지됩니다. 명시적으로 지정할 수도 있습니다:

```markdown
---
@type: code

## Full Implementation

```python {filename="complete_handler.py"}
# Long code block here...
```
```
