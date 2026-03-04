# Remarp Format Guide

Remarp is the next-generation content authoring format for reactive-presentation. It extends Marp-style markdown with enhanced directives, animations, layouts, and canvas DSL while maintaining backward compatibility.

## File Convention

### Single-File Format
For simple presentations, use a single `.md` file (previously `.remarp.md`):

```
my-presentation.md
```

### Multi-File Project Format
For larger presentations, split content into multiple files:

```
my-presentation/
  _presentation.md           # Global frontmatter (required)
  01-introduction.md         # Block 1
  02-architecture.md         # Block 2
  03-implementation.md       # Block 3
  assets/                    # Images, diagrams
```

The `_presentation.md` file contains only frontmatter and imports blocks by filename pattern (`01-*.md`, `02-*.md`, etc.). All files must have `remarp: true` in frontmatter to be recognized. The `.remarp.md` extension is also supported for backward compatibility.

---

## Global Frontmatter

The global frontmatter defines presentation-wide settings. In single-file format, place at the top. In multi-file format, use `_presentation.remarp.md`.

```yaml
---
remarp: true
version: 1
title: "AWS Architecture Deep Dive"
author: "Cloud Team"
date: 2025-01-15
event: "AWS Summit 2025"
lang: ko

blocks:
  - name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 30
  - name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 25
  - name: hands-on
    title: "Block 3: Hands-On Lab"
    duration: 45

theme:
  primary: "#232F3E"
  accent: "#FF9900"
  font: "Amazon Ember"
  codeTheme: "github-dark"

transition:
  default: slide
  duration: 400

keys:
  next: ["ArrowRight", "Space", "n"]
  prev: ["ArrowLeft", "Backspace", "p"]
  overview: ["o", "Escape"]
  presenter: ["s"]
---
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `remarp` | boolean | Yes | Must be `true` to enable remarp processing |
| `version` | number | No | Format version (default: 1) |
| `title` | string | Yes | Presentation title (used in HTML `<title>`) |
| `author` | string | No | Presenter name |
| `date` | date | No | Presentation date (YYYY-MM-DD) |
| `event` | string | No | Event or conference name |
| `lang` | string | No | Language code (`ko`, `en`, `ja`) |
| `blocks` | array | Yes | Block definitions (see below) |
| `theme` | object | No | Theme configuration |
| `transition` | object | No | Transition defaults |
| `keys` | object | No | Keyboard shortcut overrides |

### Block Definition

```yaml
blocks:
  - name: architecture     # URL-safe slug (used in filenames)
    title: "Architecture"  # Human-readable title
    duration: 30           # Duration in minutes
```

### Theme Configuration

```yaml
theme:
  primary: "#232F3E"       # Primary color (headers, backgrounds)
  accent: "#FF9900"        # Accent color (highlights, links)
  font: "Amazon Ember"     # Body font family
  codeTheme: "github-dark" # Code syntax theme
```

### Transition Configuration

```yaml
transition:
  default: slide           # Default transition type
  duration: 400            # Transition duration in ms
```

Available transition types: `none`, `fade`, `slide`, `convex`, `concave`, `zoom`

---

## Block File Format

Each block file has local frontmatter followed by slides separated by `---`.

```markdown
---
remarp: true
block: fundamentals
---

# Introduction to AWS
Block 1: Fundamentals (30 min)

---

## Why Cloud Computing?

- Scalability on demand
- Pay-as-you-go pricing
- Global infrastructure

---

## AWS Global Infrastructure

Content about regions and availability zones...
```

### Local Frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `remarp` | boolean | Yes | Must be `true` to identify as remarp file |
| `block` | string | Yes | Block name (must match `blocks[].name` in global frontmatter) |
| `title` | string | No | Block title (overrides global blocks[].title) |

---

## Slide Directives

Slide directives control individual slide behavior. Place them on the line immediately after `---`, before slide content. Use `@` prefix.

```markdown
---
@type: compare
@layout: two-column
@transition: zoom
@background: linear-gradient(135deg, #232F3E, #1a1a2e)
@class: highlight-slide
@timing: 3min
@canvas-id: arch-flow

## Slide Title
```

### Available Directives

| Directive | Values | Description |
|-----------|--------|-------------|
| `@type` | `content`, `compare`, `canvas`, `quiz`, `tabs`, `timeline`, `checklist`, `code` | Slide type |
| `@layout` | `default`, `two-column`, `three-column`, `grid-2x2`, `split-left`, `split-right` | Layout preset |
| `@transition` | `none`, `fade`, `slide`, `convex`, `concave`, `zoom` | Slide-specific transition |
| `@background` | CSS color/gradient/image | Slide background |
| `@class` | CSS class names | Additional CSS classes |
| `@timing` | `Xmin` or `Xs` | Target duration for this slide |
| `@canvas-id` | identifier | Canvas element ID for `@type: canvas` |

### Type Auto-Detection

Some types are auto-detected from content:

| Content Pattern | Auto-Detected Type |
|-----------------|-------------------|
| `# ` (H1) at slide start | Title slide |
| Multiple `### ` headings | `compare` |
| `[x]` / `[ ]` checkboxes | `quiz` |
| Code fence with 10+ lines | `code` |
| `:::canvas` block | `canvas` |

---

## Column and Grid Layouts

Use fenced div syntax (`:::`) for multi-column layouts.

### Two-Column Layout

```markdown
---
@layout: two-column

## Feature Comparison

::: left
### Pros
- Fast deployment
- Lower cost
- Easy maintenance
:::

::: right
### Cons
- Limited customization
- Vendor lock-in
- Learning curve
:::
```

### Three-Column Layout

```markdown
---
@layout: three-column

## Service Options

::: col
### Basic
- 10 GB storage
- 1 vCPU
- $5/month
:::

::: col
### Standard
- 100 GB storage
- 2 vCPU
- $20/month
:::

::: col
### Premium
- 1 TB storage
- 8 vCPU
- $100/month
:::
```

### 2x2 Grid Layout

```markdown
---
@layout: grid-2x2

## AWS Pillars

::: cell
### Operational Excellence
Automate, document, iterate
:::

::: cell
### Security
Defense in depth, least privilege
:::

::: cell
### Reliability
Fault tolerance, recovery
:::

::: cell
### Performance
Right-size, monitor, optimize
:::
```

### Split Layouts

```markdown
---
@layout: split-left
@background: url(architecture.png) right/50% no-repeat

## Architecture Overview

::: left
The system uses a microservices architecture with:
- API Gateway for routing
- Lambda for compute
- DynamoDB for storage
:::
```

---

## Element Animations (Fragments)

Control reveal order of elements within a slide.

### Inline Click Animation

Add `{.click}` after any element to make it appear on click:

```markdown
## Build Process

1. Code commit triggers pipeline {.click}
2. Unit tests run in parallel {.click}
3. Integration tests validate APIs {.click}
4. Deployment to staging {.click}
5. Canary deployment to production {.click}
```

### Block Click Animation

Wrap multiple elements in `:::click` to animate together:

```markdown
## Deployment Stages

:::click
### Stage 1: Build
- Compile source code
- Run linters
- Generate artifacts
:::

:::click
### Stage 2: Test
- Unit tests
- Integration tests
- Security scans
:::

:::click
### Stage 3: Deploy
- Blue/green deployment
- Health checks
- Rollback capability
:::
```

### Animation Order

Control reveal order with `order=N`:

```markdown
## Out of Order Reveal

Item shown third {.click order=3}

Item shown first {.click order=1}

Item shown second {.click order=2}
```

### Animation Types

Specify animation type with the animation name:

```markdown
## Animation Showcase

- Fade in (default) {.click}
- Fade from above {.click .fade-down}
- Fade from below {.click .fade-up}
- Fade from left {.click .fade-left}
- Fade from right {.click .fade-right}
- Grow in size {.click .grow}
- Shrink in size {.click .shrink}
- Highlight yellow {.click .highlight}
- Highlight red {.click .highlight-red}
- Highlight green {.click .highlight-green}
- Strikethrough {.click .strike}
- Fade out {.click .fade-out}
```

### Available Animation Types

| Class | Effect |
|-------|--------|
| `.fade-in` | Fade in (default) |
| `.fade-up` | Fade in from below |
| `.fade-down` | Fade in from above |
| `.fade-left` | Fade in from right |
| `.fade-right` | Fade in from left |
| `.grow` | Scale from 0 to 100% |
| `.shrink` | Scale from 150% to 100% |
| `.highlight` | Yellow background highlight |
| `.highlight-red` | Red background highlight |
| `.highlight-green` | Green background highlight |
| `.strike` | Strikethrough text |
| `.fade-out` | Fade out (for removing elements) |

---

## Canvas DSL

The Canvas DSL provides a declarative way to create animated diagrams with step-based reveals.

### Basic Canvas Block

```markdown
---
@type: canvas
@canvas-id: simple-arch

## Simple Architecture

:::canvas
box api "API Gateway" at 100,200 size 120,60 color #FF9900
box lambda "Lambda" at 300,200 size 120,60 color #FF9900
box dynamo "DynamoDB" at 500,200 size 120,60 color #3B48CC

arrow api -> lambda "invoke"
arrow lambda -> dynamo "read/write"
:::
```

### Canvas Elements

#### Box Element
```
box <id> "<label>" at <x>,<y> size <width>,<height> color <color> [step <n>]
```

```markdown
:::canvas
box user "User" at 50,100 size 80,40 color #232F3E
box web "Web App" at 200,100 size 100,50 color #FF9900 step 2
box db "Database" at 400,100 size 100,50 color #3B48CC step 3
:::
```

#### Circle Element
```
circle <id> "<label>" at <x>,<y> radius <r> color <color> [step <n>]
```

```markdown
:::canvas
circle start "Start" at 50,100 radius 30 color #4CAF50
circle process "Process" at 200,100 radius 40 color #FF9900 step 2
circle end "End" at 350,100 radius 30 color #f44336 step 3
:::
```

#### Icon Element
```
icon <id> "<aws-service>" at <x>,<y> size <s> [step <n>]
```

AWS service names map to Architecture Icons:

```markdown
:::canvas
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48 step 2
icon table "DynamoDB" at 400,150 size 48 step 3
:::
```

#### Arrow Element
```
arrow <from-id> -> <to-id> "<label>" [color <color>] [style <dashed|dotted>] [step <n>]
```

```markdown
:::canvas
box a "Service A" at 50,100 size 100,50 color #232F3E
box b "Service B" at 250,100 size 100,50 color #232F3E

arrow a -> b "HTTP" step 2
arrow b -> a "Response" color #4CAF50 style dashed step 3
:::
```

#### Group Element
```
group "<label>" containing <id1>, <id2>, ... [color <color>] [step <n>]
```

```markdown
:::canvas
box web1 "Web 1" at 100,100 size 80,40 color #FF9900
box web2 "Web 2" at 100,160 size 80,40 color #FF9900
box web3 "Web 3" at 100,220 size 80,40 color #FF9900

group "Auto Scaling Group" containing web1, web2, web3 color #232F3E
:::
```

### Step-Based Reveal

Use `step N` on any element to control when it appears:

```markdown
---
@type: canvas
@canvas-id: data-flow

## Data Pipeline

:::canvas
# Step 1: Source appears first
icon s3src "S3" at 50,150 size 48 step 1
box source "Source Bucket" at 30,210 size 90,30 color #3B48CC step 1

# Step 2: Processing layer
icon lambda "Lambda" at 200,150 size 48 step 2
box transform "Transform" at 180,210 size 90,30 color #FF9900 step 2

# Step 3: Destination
icon s3dst "S3" at 350,150 size 48 step 3
box dest "Dest Bucket" at 330,210 size 90,30 color #3B48CC step 3

# Step 4: Arrows connect everything
arrow source -> transform "trigger" step 4
arrow transform -> dest "write" step 4
:::
```

### JavaScript Escape Hatch

For complex animations beyond DSL capabilities, use raw JavaScript:

```markdown
:::canvas js
const canvas = document.getElementById('complex-animation');
const ctx = canvas.getContext('2d');

// Custom animation logic
function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // ... custom drawing code
  requestAnimationFrame(animate);
}
animate();
:::
```

---

## Speaker Notes

Add presenter notes with timing cues and markers.

### Basic Notes

```markdown
## Slide Title

Content here

:::notes
Remember to explain the cost implications.
Mention that this feature was added in version 2.3.
:::
```

### Timing Markers

```markdown
:::notes
{timing: 3min}
This slide should take about 3 minutes to cover.
Key points:
- Explain the architecture
- Show the demo
- Answer questions
:::
```

### Cue Markers

```markdown
:::notes
{timing: 5min}
{cue: demo}
Live demo of the deployment pipeline.

{cue: pause}
Give audience time to absorb the architecture diagram.

{cue: question}
Ask: "Has anyone implemented this pattern?"

{cue: transition}
Transition to the next section on security.
:::
```

### Available Cues

| Cue | Purpose |
|-----|---------|
| `{cue: demo}` | Reminder to show live demonstration |
| `{cue: pause}` | Pause for audience absorption |
| `{cue: question}` | Ask audience a question |
| `{cue: transition}` | Verbal transition to next topic |
| `{cue: poll}` | Launch audience poll |
| `{cue: break}` | Take a break |

---

## Interactive Slide Types

### Quiz Slides

Quizzes are auto-detected when content contains `[x]` or `[ ]` checkboxes:

```markdown
---
@type: quiz

## Knowledge Check

**Q1: Which service provides serverless compute?**
- [ ] EC2
- [x] Lambda
- [ ] ECS
- [ ] EKS

**Q2: What is the maximum Lambda timeout?**
- [ ] 5 minutes
- [x] 15 minutes
- [ ] 30 minutes
- [ ] 60 minutes

**Q3: Lambda supports which runtimes? (Select all)**
- [x] Python
- [x] Node.js
- [x] Java
- [ ] COBOL
```

### Compare Slides

Comparison slides use toggle buttons to switch between options:

```markdown
---
@type: compare

## EC2 vs Lambda

### EC2
- Full control over instance
- Persistent compute
- Pay per hour
- Best for: Long-running workloads

### Lambda
- Serverless, no management
- Event-driven
- Pay per invocation
- Best for: Short, bursty workloads
```

### Tabs Slides

Tabbed content for organizing related information:

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
data:
  database_url: "postgres://..."
```

### JSON
```json
{
  "apiVersion": "v1",
  "kind": "ConfigMap",
  "metadata": {
    "name": "app-config"
  }
}
```

### TOML
```toml
[database]
url = "postgres://..."
```
````

### Timeline Slides

Horizontal timeline for sequential events:

```markdown
---
@type: timeline

## Project Milestones

### Q1 2025
Design phase complete
Architecture approved

### Q2 2025
Development sprint 1-3
Alpha release

### Q3 2025
Beta testing
Performance optimization

### Q4 2025
Production launch
GA release
```

### Checklist Slides

Interactive click-to-toggle checklists:

```markdown
---
@type: checklist

## Deployment Checklist

- [ ] Code review approved
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Security scan complete
- [ ] Documentation updated
- [ ] Stakeholder sign-off
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
```

---

## Code Blocks

Enhanced code blocks with highlighting and metadata.

### Basic Code Block

````markdown
```python
def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```
````

### Line Highlighting

Highlight specific lines with `{highlight="..."}`:

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

Highlight formats:
- `{highlight="3"}` - Single line
- `{highlight="3-5"}` - Range
- `{highlight="1,3,7-9"}` - Multiple lines/ranges

### Filename Display

Show filename above code block:

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

### Combined Attributes

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

### Diff Display

Show code changes with diff syntax:

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

---

## Backward Compatibility

Remarp maintains backward compatibility with Marp format:

| Marp Syntax | Remarp Equivalent | Notes |
|-------------|-------------------|-------|
| `marp: true` | `remarp: true` | Both work, remarp enables new features |
| `<!-- type: X -->` | `@type: X` | HTML comments still work |
| `<!-- notes: ... -->` | `:::notes ... :::` | Both supported |
| `<!-- block: name -->` | `block: name` in frontmatter | Frontmatter preferred |
| Plain markdown | Same | Full markdown support |

### Migration Example

**Marp format:**
```markdown
---
marp: true
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---

<!-- block: intro -->

# Welcome
Introduction content

---
<!-- type: compare -->
## Options

### Option A
Content A

### Option B
Content B

<!-- notes: Remember to explain both options -->
```

**Remarp format:**
```markdown
---
remarp: true
version: 1
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---

---
remarp: true
block: intro
---

# Welcome
Introduction content

---
@type: compare

## Options

::: left
### Option A
Content A
:::

::: right
### Option B
Content B
:::

:::notes
Remember to explain both options
:::
```

---

## Complete Example: Multi-Block Presentation

### _presentation.md

```yaml
---
remarp: true
version: 1
title: "AWS Serverless Architecture"
author: "Cloud Team"
date: 2025-03-01
event: "AWS Tech Talk"
lang: en

blocks:
  - name: fundamentals
    title: "Block 1: Serverless Fundamentals"
    duration: 25
  - name: patterns
    title: "Block 2: Architecture Patterns"
    duration: 30
  - name: hands-on
    title: "Block 3: Hands-On Lab"
    duration: 35

theme:
  primary: "#232F3E"
  accent: "#FF9900"

transition:
  default: slide
  duration: 400
---
```

### 01-fundamentals.md

```markdown
---
remarp: true
block: fundamentals
---

# AWS Serverless Architecture
Block 1: Serverless Fundamentals (25 min)

:::notes
{timing: 2min}
Welcome everyone. Quick intro, then dive into serverless concepts.
:::

---

## What is Serverless?

- No server management {.click}
- Auto-scaling built-in {.click}
- Pay-per-use pricing {.click}
- Event-driven execution {.click}

:::notes
{timing: 3min}
{cue: question}
Ask who has used Lambda before.
:::

---
@type: compare

## Serverless vs Traditional

::: left
### Traditional
- Provision servers
- Manage capacity
- Pay for idle time
- OS patching required
:::

::: right
### Serverless
- No servers to manage
- Auto-scales to zero
- Pay only for execution
- Fully managed
:::

---
@type: canvas
@canvas-id: lambda-flow

## Lambda Execution Model

:::canvas
icon trigger "API-Gateway" at 50,150 size 48 step 1
icon lambda "Lambda" at 200,150 size 48 step 2
icon dynamo "DynamoDB" at 350,150 size 48 step 3

arrow trigger -> lambda "invoke" step 4
arrow lambda -> dynamo "read/write" step 5
:::

:::notes
{timing: 5min}
{cue: demo}
Show the Lambda console and execution flow.
:::

---
@type: quiz

## Quick Check

**Q1: Lambda maximum timeout?**
- [ ] 5 minutes
- [x] 15 minutes
- [ ] 30 minutes

**Q2: Lambda pricing is based on?**
- [ ] Provisioned capacity
- [x] Request count + duration
- [ ] Fixed monthly fee
```

### 02-patterns.md

````markdown
---
remarp: true
block: patterns
---

# Architecture Patterns
Block 2 (30 min)

---
@layout: two-column

## Common Patterns

::: left
### Synchronous
- API Gateway + Lambda
- Direct invocation
- Request/Response
:::

::: right
### Asynchronous
- S3 + Lambda
- SQS + Lambda
- EventBridge + Lambda
:::

---
@type: canvas
@canvas-id: api-pattern

## API Backend Pattern

:::canvas
box client "Client" at 30,150 size 80,40 color #232F3E step 1

icon apigw "API-Gateway" at 150,140 size 48 step 2
icon lambda "Lambda" at 280,140 size 48 step 3
icon dynamo "DynamoDB" at 410,140 size 48 step 4

arrow client -> apigw "HTTPS" step 5
arrow apigw -> lambda "invoke" step 5
arrow lambda -> dynamo "query" step 6
:::

---
@type: tabs

## Code Examples

### Python
```python {filename="handler.py" highlight="4-6"}
import json
import boto3

def handler(event, context):
    # Extract path parameter
    user_id = event['pathParameters']['userId']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    response = table.get_item(Key={'userId': user_id})
    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Item', {}))
    }
```

### Node.js
```javascript {filename="handler.js" highlight="3-5"}
const AWS = require('aws-sdk');

exports.handler = async (event) => {
  // Extract path parameter
  const userId = event.pathParameters.userId;

  const dynamodb = new AWS.DynamoDB.DocumentClient();
  const result = await dynamodb.get({
    TableName: 'Users',
    Key: { userId }
  }).promise();

  return {
    statusCode: 200,
    body: JSON.stringify(result.Item || {})
  };
};
```

---
@type: timeline

## Evolution of Serverless

### 2014
AWS Lambda launched
Event-driven compute

### 2016
API Gateway integration
Serverless APIs

### 2019
Lambda Layers
Provisioned Concurrency

### 2022
Lambda SnapStart
Function URLs

### 2024
Advanced observability
Native OpenTelemetry
````

### 03-hands-on.md

````markdown
---
remarp: true
block: hands-on
---

# Hands-On Lab
Block 3 (35 min)

:::notes
{timing: 2min}
{cue: transition}
Now let's build something together.
:::

---
@type: checklist

## Lab Prerequisites

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] Node.js 18+ or Python 3.9+
- [ ] SAM CLI installed
- [ ] Code editor (VS Code recommended)

---

## Step 1: Create Lambda Function

```bash {filename="terminal"}
# Initialize SAM project
sam init --runtime python3.9 --name my-api

# Navigate to project
cd my-api
```

:::click
After running these commands, you'll have a project structure:
```
my-api/
  template.yaml
  hello_world/
    app.py
    requirements.txt
```
:::

---
@layout: split-left

## Step 2: Deploy

::: left
```bash {filename="terminal" highlight="2,5"}
# Build the application
sam build

# Deploy with guided prompts
sam deploy --guided
```

Follow the prompts:
1. Stack name: `my-api`
2. Region: `us-east-1`
3. Confirm changes: `Y`
:::

:::notes
{timing: 10min}
{cue: demo}
Walk through deployment in terminal.
Explain each SAM deploy prompt.
:::

---
@type: canvas
@canvas-id: final-arch

## Final Architecture

:::canvas
group "AWS Cloud" containing apigw, lambda, dynamo, logs color #232F3E

icon apigw "API-Gateway" at 100,150 size 48 step 1
icon lambda "Lambda" at 250,150 size 48 step 2
icon dynamo "DynamoDB" at 400,150 size 48 step 3
icon logs "CloudWatch" at 250,280 size 48 step 4

arrow apigw -> lambda "REST" step 5
arrow lambda -> dynamo "CRUD" step 5
arrow lambda -> logs "logs" style dashed step 6
:::

---

## Lab Complete!

:::click
### What We Built
- Serverless REST API
- Lambda function with DynamoDB
- CloudWatch logging
:::

:::click
### Next Steps
- Add authentication with Cognito
- Implement CI/CD with CodePipeline
- Add custom domain with Route 53
:::

:::notes
{timing: 3min}
Wrap up, answer questions.
Share links to documentation.
:::
````

---

## CLI Usage

```bash
# Convert single file
remarp build presentation.md -o ./output/

# Convert multi-file project
remarp build ./my-presentation/ -o ./output/

# Watch mode for development
remarp watch ./my-presentation/ -o ./output/

# Export to PDF
remarp export presentation.md --format pdf

# Validate without building
remarp validate presentation.md
```

---

## Quick Reference

### Directives
```
@type: content|compare|canvas|quiz|tabs|timeline|checklist|code
@layout: default|two-column|three-column|grid-2x2|split-left|split-right
@transition: none|fade|slide|convex|concave|zoom
@background: <css-value>
@class: <css-classes>
@timing: Xmin|Xs
@canvas-id: <identifier>
```

### Layouts
```
::: left ... :::      Two-column left
::: right ... :::     Two-column right
::: col ... :::       Three-column
::: cell ... :::      Grid cell
```

### Animations
```
{.click}              Basic click reveal
{.click order=N}      Ordered reveal
{.click .fade-up}     Animation type
:::click ... :::      Block reveal
```

### Canvas DSL
```
box <id> "<label>" at X,Y size W,H color #HEX [step N]
circle <id> "<label>" at X,Y radius R color #HEX [step N]
icon <id> "<service>" at X,Y size S [step N]
arrow <from> -> <to> "<label>" [color #HEX] [style dashed|dotted] [step N]
group "<label>" containing id1, id2, ... [color #HEX] [step N]
```

### Notes
```
:::notes
{timing: Xmin}
{cue: demo|pause|question|transition|poll|break}
Note content here
:::
```

---

## Theme Frontmatter Schema

Extended theme configuration in global frontmatter:

```yaml
---
remarp: true
title: "My Presentation"

theme:
  source: "./company-template.pptx"  # PPTX/PDF file or pre-extracted directory
  footer: auto                        # "auto" extracts from PPTX, or string value
  pagination: true                    # Show/hide page numbers
  logo: auto                          # "auto" uses first extracted logo, or path

transition:
  default: slide
  duration: 400
---
```

### Theme Source Types

| Source Type | Example | Behavior |
|-------------|---------|----------|
| PPTX file | `./template.pptx` | Extract theme to `_theme/` directory |
| PDF file | `./template.pdf` | Extract colors and images |
| Directory | `./_theme/template/` | Use pre-extracted theme |

### Generated CSS Variables

When theme is extracted, the following CSS variables are generated in `theme-override.css`:

```css
:root {
  --pptx-accent1: #FF9900;
  --pptx-accent2: #232F3E;
  --pptx-accent3: #146EB4;
  --pptx-accent4: #4CAF50;
  --pptx-accent5: #f44336;
  --pptx-accent6: #9C27B0;
  --pptx-dk1: #000000;
  --pptx-lt1: #FFFFFF;
  --pptx-dk2: #1A1A1A;
  --pptx-lt2: #F5F5F5;
}
```

---

## Canvas DSL Preset Specification

Presets provide pre-built animated diagram patterns for common AWS scenarios.

### Preset Syntax

```
preset <type> {
  <preset-specific-configuration>
}
```

### EKS Scaling Preset

```markdown
:::canvas
preset eks-scaling {
  cluster "Production EKS" at 40,30
    node "node-1" pods=3 max=4
    node "node-2" pods=2 max=4
    node "node-3" pods=1 max=4

  step 1 scale-out node=0 "Add pod to node-1"
  step 2 scale-out node=1 "Add pod to node-2"
  step 3 add-node "Add new node"
  step 4 scale-out node=3 "Schedule to new node"
}
:::
```

### Preset Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `scale-out` | `node=N` | Add pod to specified node |
| `scale-in` | `node=N` | Remove pod from specified node |
| `add-node` | none | Add new node to cluster |
| `remove-node` | `node=N` | Remove node from cluster |
| `migrate` | `node=N to=M` | Move pod between nodes |

---

## Canvas DSL Icon Specification

Icons can be referenced by AWS service name or full path.

### Service Name Mapping

```markdown
:::canvas
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48
icon db "DynamoDB" at 400,150 size 48
:::
```

### Supported Service Names

| Name | Icon File |
|------|-----------|
| `Lambda` | `Arch_AWS-Lambda_48.svg` |
| `EKS` | `Arch_Amazon-Elastic-Kubernetes-Service_48.svg` |
| `API-Gateway` | `Arch_Amazon-API-Gateway_48.svg` |
| `DynamoDB` | `Arch_Amazon-DynamoDB_48.svg` |
| `S3` | `Arch_Amazon-Simple-Storage-Service_48.svg` |
| `CloudWatch` | `Arch_Amazon-CloudWatch_48.svg` |
| `EC2` | `Arch_Amazon-EC2_48.svg` |
| `VPC` | `Virtual-private-cloud-VPC_32.svg` |
| `RDS` | `Arch_Amazon-RDS_48.svg` |
| `SQS` | `Arch_Amazon-Simple-Queue-Service_48.svg` |
| `SNS` | `Arch_Amazon-Simple-Notification-Service_48.svg` |
| `CloudFront` | `Arch_Amazon-CloudFront_48.svg` |
| `Route53` | `Arch_Amazon-Route-53_48.svg` |
| `Cognito` | `Arch_Amazon-Cognito_48.svg` |
| `StepFunctions` | `Arch_AWS-Step-Functions_48.svg` |
| `Fargate` | `Arch_AWS-Fargate_48.svg` |
| `ECS` | `Arch_Amazon-Elastic-Container-Service_48.svg` |
| `ALB` | `Arch_Elastic-Load-Balancing_48.svg` |
| `IAM` | `Arch_AWS-Identity-and-Access-Management_48.svg` |
| `KMS` | `Arch_AWS-Key-Management-Service_48.svg` |

### Full Path Reference

```markdown
:::canvas
icon custom "../common/aws-icons/services/Arch_Amazon-S3_48.svg" at 100,250 size 48
:::
```

---

## Mermaid Block Specification

Embed Mermaid diagrams in canvas blocks.

### Syntax

```markdown
:::canvas mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Lambda]
    C --> D[DynamoDB]
:::
```

### Supported Diagram Types

- `graph` / `flowchart` — Flow diagrams
- `sequenceDiagram` — Sequence diagrams
- `classDiagram` — Class diagrams
- `stateDiagram` — State diagrams
- `erDiagram` — Entity-relationship diagrams
- `gantt` — Gantt charts
- `pie` — Pie charts

### Theme Integration

Mermaid uses dark theme by default to match the presentation theme:

```javascript
mermaid.initialize({ startOnLoad: true, theme: 'dark' });
```

---

## @ref Directive Specification

Add reference links to slides for presenter view.

### Syntax

```markdown
---
@type content
@ref "https://docs.aws.amazon.com/lambda/" "Lambda Documentation"
@ref "https://aws.amazon.com/blogs/compute/" "AWS Compute Blog"

## Slide Content
```

### Multiple References

```markdown
@ref "https://example.com/doc1" "Primary Reference"
@ref "https://example.com/doc2" "Secondary Reference"
@ref "https://example.com/doc3" "Additional Reading"
```

### Data Attribute

References are stored in the slide's `data-refs` attribute as JSON:

```html
<div class="slide" data-refs='[{"url":"https://...","label":"..."}]'>
```

---

## Animations Field Schema

Custom animations can be defined in frontmatter for complex scenarios.

### Syntax

```yaml
---
remarp: true
title: "Custom Animations"

animations:
  arch-flow:
    module: "./animations/arch-flow.js"
    config:
      duration: 500
      easing: "ease-out"
  data-pipeline:
    module: "./animations/data-pipeline.js"
    config:
      steps: 5
---
```

### Animation Module Interface

```javascript
// animations/arch-flow.js
export function init(canvas, config) {
  const ctx = canvas.getContext('2d');
  // Setup code
  return {
    play: () => { /* Start animation */ },
    reset: () => { /* Reset to initial state */ },
    stepForward: () => { /* Advance one step */ },
    stepBackward: () => { /* Go back one step */ }
  };
}
```

### Using Custom Animations

```markdown
---
@type canvas
@canvas-id arch-flow

## Architecture Flow

:::canvas
# Uses the arch-flow animation module defined in frontmatter
:::
```
