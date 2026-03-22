# Image Directive Reference

An alternate image syntax with additional configuration options for displaying images in workshop content.

## Declaration Types

| Type | Supported | Syntax | Use Case |
|------|-----------|--------|----------|
| Text | Yes | `:image[alt]{props}` | Inline images in text |
| Leaf | No | - | Not supported |
| Container | No | - | Not supported |

## Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `src` | `string` | Yes | - | Image source URL or relative path |
| `width` | `number` | No | - | Width in pixels |
| `height` | `number` | No | - | Height in pixels |
| `disableZoom` | `boolean` | No | `false` | Disables image zoom functionality |
| `title` | `string` | No | - | Image title (tooltip on hover) |

## Image Sources

| Source Type | Path Format | Example |
|-------------|-------------|---------|
| Repository static | `/static/path/to/image.png` | `/static/img/diagram.png` |
| S3 assets | `/assets/path/to/image.png` | `/assets/screenshots/step1.png` |
| Asset URL directive | `:assetUrl{path="/image.png"}` | Dynamic path resolution |
| External URL | Full URL | `https://example.com/image.png` |

## Examples

### Basic Image

```markdown
:image[Architecture diagram]{src="/static/img/architecture.png"}
```

### Image with Dimensions

```markdown
:image[AWS Console screenshot]{src="/static/img/console.png" width=800 height=450}
```

### Image without Zoom

```markdown
:image[Small icon]{src="/static/img/icon.png" disableZoom=true}
```

### Image with Title

```markdown
:image[System architecture]{src="/static/img/arch.png" title="High-level system architecture"}
```

### Image from S3 Assets

```markdown
:image[Step 1 screenshot]{src="/assets/screenshots/step1.png"}
```

### Image with Asset URL Directive

```markdown
:image[Diagram]{src=":assetUrl{path=\"/diagram.png\"}"}
```

### Image as Link

```markdown
Click here to launch [:image[Launch stack]{src="/static/img/cloudformation-launch-stack.png"}](https://console.aws.amazon.com/cloudformation/home)
```

## Standard Markdown Images

You can also use standard markdown image syntax:

```markdown
![Alt text](/static/img/screenshot.png)

![Alt text](/assets/diagram.png)
```

Both `/static` and `/assets` paths are automatically resolved to the correct URLs.

## Best Practices

### Do

```markdown
:image[EC2 Dashboard]{src="/static/img/ec2-dashboard.png" width=800 height=600}
```

```markdown
:image[Small button icon]{src="/static/img/button.png" width=200 disableZoom=true}
```

### Don't

```markdown
:image[Screenshot]{src="/static/img/full-res-4k-screenshot.png"}
```

```markdown
:image[]{src="/static/img/image.png"}
```

## Image Guidelines

| Aspect | Recommendation |
|--------|----------------|
| File format | PNG for screenshots, SVG for diagrams |
| Resolution | Match display size to reduce load time |
| Alt text | Always provide descriptive alt text |
| Dimensions | Specify width/height to prevent layout shift |
| Zoom | Disable for small icons/buttons |

## Common Patterns

### Console Screenshots

```markdown
:image[Navigate to S3 in the AWS Console]{src="/static/img/s3-console.png" width=800 height=500}
```

### Architecture Diagrams

```markdown
:image[Solution architecture showing VPC, EC2, and RDS components]{src="/static/img/architecture-diagram.png" width=900 height=600}
```

### Step-by-Step Instruction Images

```markdown
## Step 1: Create a bucket

:image[Click Create bucket button]{src="/assets/step1-create-bucket.png" width=600}

## Step 2: Configure settings

:image[Enter bucket name and select region]{src="/assets/step2-configure.png" width=600}
```

### Icon or Button Images

```markdown
Click the :image[settings icon]{src="/static/img/settings-icon.png" width=24 height=24 disableZoom=true} to open preferences.
```

### Launch Stack Button

```markdown
[:image[Launch CloudFormation Stack]{src="/static/img/launch-stack.png" width=144 height=27 disableZoom=true}](https://console.aws.amazon.com/cloudformation/home?region={{.AWSRegion}}#/stacks/create/review?templateURL=https://s3.amazonaws.com/{{.AssetsBucketName}}/template.yaml)
```

## Asset Management Notes

### Repository Assets (`/static`)
- Stored in workshop repository under `/static` folder
- Version controlled with workshop content
- Best for: diagrams, icons, reusable images

### S3 Assets (`/assets`)
- Stored in S3 assets bucket
- Managed separately from repository
- Best for: large files, frequently updated screenshots

### Syncing Assets

Assets under `/assets` must be synced to S3 before the workshop build:

```bash
# Sync local assets to S3
aws s3 sync ./assets s3://workshop-assets-bucket/
```

Then push the workshop commit to trigger a build.
