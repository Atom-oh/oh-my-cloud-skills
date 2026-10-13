# Tabs Directive Reference

Enables users to switch between different categories of information in the same view.

## Declaration Types

| Directive | Type | Supported | Syntax |
|-----------|------|-----------|--------|
| Tabs | Text | No | - |
| Tabs | Leaf | No | - |
| Tabs | Container | Yes | `::::tabs{props}\n:::tab{props}\ncontent\n:::\n::::` |
| Tab | Text | No | - |
| Tab | Leaf | No | - |
| Tab | Container | Yes | `:::tab{props}\ncontent\n:::` |

## Tabs Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `activeTabId` | `string` | No | First tab | The `id` of the initially active tab |
| `variant` | `string` | No | `"default"` | Visual style: `default` or `container` |
| `groupId` | `string` | No | - | Synchronizes tabs across multiple tab groups |

## Tab Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `id` | `string` | No | `tab-<index>` | Unique identifier for the tab |
| `label` | `string` | No | `"Tab <index>"` | Tab label shown in the UI |
| `disabled` | `boolean` | No | `false` | Whether the tab is disabled |

## Nesting Syntax

Tabs require proper colon nesting:
- `::::tabs` - Tabs container (4 colons)
- `:::tab` - Tab content (3 colons)
- `:::::tabs` - If nesting code blocks inside (5 colons)
- `::::tab` - Tab with code blocks (4 colons)

## Examples

### Basic Tabs

```markdown
::::tabs
:::tab
Content for tab 1
:::
:::tab
Content for tab 2
:::
:::tab
Content for tab 3
:::
::::
```

### Container Variant

```markdown
::::tabs{variant="container"}
:::tab
Content for tab 1
:::
:::tab
Content for tab 2
:::
:::tab
Content for tab 3
:::
::::
```

### Custom Tab IDs and Labels

```markdown
::::tabs{variant="container" activeTabId="angular"}
:::tab{id="react" label="React"}
React content
:::
:::tab{id="angular" label="Angular"}
Angular content
:::
:::tab{id="vue" label="Vue"}
Vue content
:::
::::
```

### Active Tab ID (Default IDs)

```markdown
::::tabs{variant="container" activeTabId="tab-2"}
:::tab
Content for tab 1
:::
:::tab
Content for tab 2 (will be active)
:::
:::tab
Content for tab 3
:::
::::
```

### Disabled Tab

```markdown
::::tabs{variant="container"}
:::tab{id="react" label="React"}
React content
:::
:::tab{id="angular" label="Angular" disabled=true}
Angular content
:::
:::tab{id="vue" label="Vue"}
Vue content
:::
::::
```

### Synchronized Tabs (groupId)

```markdown
::::tabs{variant="container" groupId=codeSample}
:::tab{label="React"}
React content
:::
:::tab{id="angular" label="Angular"}
Angular content
:::
:::tab{label="Vue"}
Vue content
:::
::::

Some text between tab groups...

::::tabs{variant="container" groupId=codeSample}
:::tab{label="React"}
More React content
:::
:::tab{id="angular" label="Angular"}
More Angular content
:::
:::tab{label="Vue"}
More Vue content
:::
::::
```

### Tabs with Code Blocks (Extra Colons)

```markdown
:::::tabs{variant="container"}

::::tab{id="js" label="JavaScript"}
```javascript
function helloWorld() {
    print('Hello, World!');
}
```
::::

::::tab{id="java" label="Java"}
```java
class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
```
::::

::::tab{id="python" label="Python"}
```python
def hello_world():
    print('Hello, World!')
```
::::

:::::
```

### Tabs with Code Directive

```markdown
:::::tabs{variant="container"}

::::tab{id="js" label="JavaScript"}
:::code{language=javascript}
function helloWorld() {
    console.log('Hello, World!');
}
:::
::::

::::tab{id="python" label="Python"}
:::code{language=python}
def hello_world():
    print('Hello, World!')
:::
::::

:::::
```

## Best Practices

### Do

```markdown
::::tabs{variant="container"}
:::tab{id="console" label="AWS Console"}
1. Navigate to the S3 service
2. Click "Create bucket"
3. Enter your bucket name
:::
:::tab{id="cli" label="AWS CLI"}
```bash
aws s3 mb s3://my-bucket-name
```
:::
:::tab{id="cdk" label="AWS CDK"}
```typescript
new s3.Bucket(this, 'MyBucket', {
  bucketName: 'my-bucket-name'
});
```
:::
::::
```

### Don't

```markdown
::::tabs
:::tab
Short
:::
:::tab
This tab has way more content than the others which creates an unbalanced user experience when switching between tabs
:::
::::
```

```markdown
:::tabs
Content without proper tab structure
:::
```

## Common Patterns

### Multi-Language Code Examples

```markdown
:::::tabs{variant="container" groupId="lang"}
::::tab{id="python" label="Python"}
:::code{language=python}
import boto3

s3 = boto3.client('s3')
response = s3.list_buckets()
:::
::::
::::tab{id="javascript" label="JavaScript"}
:::code{language=javascript}
const AWS = require('aws-sdk');

const s3 = new AWS.S3();
const response = await s3.listBuckets().promise();
:::
::::
::::tab{id="go" label="Go"}
:::code{language=go}
import (
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/s3"
)

sess := session.Must(session.NewSession())
svc := s3.New(sess)
result, _ := svc.ListBuckets(nil)
:::
::::
:::::
```

### Console vs CLI Instructions

```markdown
::::tabs{variant="container"}
:::tab{id="console" label="Using Console"}
1. Open the AWS Management Console
2. Navigate to **EC2** > **Instances**
3. Click **Launch Instance**
4. Select your AMI and instance type
:::
:::tab{id="cli" label="Using CLI"}
```bash
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key-pair
```
:::
::::
```

### Operating System Specific

```markdown
::::tabs{variant="container"}
:::tab{id="mac" label="macOS"}
```bash
brew install awscli
```
:::
:::tab{id="linux" label="Linux"}
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
:::
:::tab{id="windows" label="Windows"}
Download and run the AWS CLI MSI installer from the AWS website.
:::
::::
```
