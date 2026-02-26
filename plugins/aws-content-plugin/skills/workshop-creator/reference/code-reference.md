# Code Directive Reference

A container that displays terminal output or code snippets with syntax highlighting.

## Declaration Types

| Type | Supported | Syntax | Use Case |
|------|-----------|--------|----------|
| Text | Yes | `:code[content]{props}` | Inline code with copy action |
| Leaf | Yes | `::code[content]{props}` | Single-line code blocks |
| Container | Yes | `:::code{props}\ncontent\n:::` | Multi-line code blocks |

## Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `language` | `string` | No | - | Syntax highlighting language |
| `showLineNumbers` | `boolean` | No | `true` if `language` specified | Display line numbers |
| `showCopyAction` | `boolean` | No | `true` if `showLineNumbers` is `true` | Display copy button |
| `copyAutoReturn` | `boolean` | No | `false` | Include newline at end when copied |
| `highlightLines` | `string` | No | - | Comma-separated line numbers/ranges to highlight |
| `highlightLinesStart` | `number` | No | - | Starting index for highlight line tracking |
| `lineNumberStart` | `number` | No | `1` | Starting line number to display |

## Supported Languages

| Language | Aliases |
|----------|---------|
| `arduino` | `ino` |
| `bash` | `sh`, `shell` |
| `c` | - |
| `cedar` | - |
| `cpp` | - |
| `css` | - |
| `csharp` | `cs`, `dotnet` |
| `dart` | - |
| `diff` | - |
| `docker` | `dockerfile` |
| `git` | - |
| `go` | - |
| `graphql` | - |
| `java` | - |
| `javascript` | `js` |
| `jq` | - |
| `json` | `webmanifest` |
| `jsx` | - |
| `kotlin` | `kt`, `kts` |
| `less` | - |
| `lisp` | `elisp`, `emacs`, `emacs-lisp` |
| `llvm` | - |
| `lua` | - |
| `makefile` | - |
| `markdown` | `md` |
| `markup` | `atom`, `html`, `mathml`, `rss`, `ssml`, `svg`, `xml` |
| `nginx` | - |
| `objectivec` | `objc` |
| `perl` | - |
| `php` | - |
| `powershell` | - |
| `python` | `py` |
| `r` | - |
| `regex` | - |
| `ruby` | `rb` |
| `rust` | - |
| `sass` | - |
| `scss` | - |
| `sql` | - |
| `swift` | - |
| `template` | - |
| `toml` | - |
| `tsx` | - |
| `typescript` | `ts` |
| `vim` | - |
| `wasm` | - |
| `yaml` | `yml` |

## Examples

### Basic Terminal Output (Leaf)

```markdown
::code[aws s3 ls]
```

### Inline Code with Copy Action (Text)

```markdown
Your current region is :code[us-west-2]{showCopyAction=true}.
```

### Auto-Execute Command

```markdown
::code[npm start]{showCopyAction=true copyAutoReturn=true}
```

### Syntax Highlighting

```markdown
::code[console.log('Hello world!')]{language=js}
```

### Multi-line Code Block (Container)

```markdown
:::code{language=python}
def hello_world():
    '''A hello world program'''
    print("Hello world!")
:::
```

### Code Without Line Numbers

```markdown
:::code{language=jsx showLineNumbers=false showCopyAction=false}
const MyCoolComponent = (props) => (
    <section>
        <h1>{props.title}</h1>
    </section>
);
:::
```

### Custom Starting Line Number

```markdown
:::code{language=ts lineNumberStart=54}
// Creates a distribution from an S3 bucket.
const myBucket = new s3.Bucket(this, 'myBucket');
new cloudfront.Distribution(this, 'myDist', {
  defaultBehavior: { origin: new origins.S3Origin(myBucket) },
});
:::
```

### Line Highlighting

```markdown
:::code{language=ts highlightLines=4-8,13,14}
// Creating a custom origin request policy
declare const bucketOrigin: origins.S3Origin;
const myOriginRequestPolicy = new cloudfront.OriginRequestPolicy(this, 'OriginRequestPolicy', {
  originRequestPolicyName: 'MyPolicy',
  comment: 'A default policy',
  cookieBehavior: cloudfront.OriginRequestCookieBehavior.none(),
  headerBehavior: cloudfront.OriginRequestHeaderBehavior.all('CloudFront-Is-Android-Viewer'),
  queryStringBehavior: cloudfront.OriginRequestQueryStringBehavior.allowList('username'),
});

new cloudfront.Distribution(this, 'myDistCustomPolicy', {
  defaultBehavior: {
    origin: bucketOrigin,
    originRequestPolicy: myOriginRequestPolicy,
  },
});
:::
```

### Line Highlighting with Custom Start

```markdown
:::code{language=yaml lineNumberStart=105 highlightLines=4-6,8 highlightLinesStart=1}
EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
        ImageId: !FindInMap [ AWSRegionArch2AMI, !Ref 'AWS::Region' , !FindInMap [ AWSInstanceType2Arch, !Ref InstanceType, Arch ] ]
        KeyName: !Ref KeyName
        InstanceType: !Ref InstanceType
        SecurityGroups:
        - !Ref Ec2SecurityGroup
:::
```

### Mermaid Diagrams

```markdown
:::code{language=mermaid}
graph TD
    A[Start] --> B{Is it?};
    B -- Yes --> C[OK];
    C --> D[Rethink];
    D --> B;
    B -- No ----> E[End];
:::
```

## Standard Markdown Code Blocks

You can also use standard markdown code blocks with language specifiers:

````markdown
```python
# Some lovely python code
def hello_world():
    '''A hello world program'''
    print("Hello world!")
```
````

When a language is specified, line numbers and copy action are enabled automatically.

## Best Practices

### Do

```markdown
:::code{language=bash}
# Install dependencies
npm install

# Start the development server
npm run dev
:::
```

```markdown
::code[aws configure]{showCopyAction=true copyAutoReturn=true}
```

### Don't

```markdown
:::code{}
some code without language specification when syntax highlighting would help
:::
```

```markdown
::code[very long command that should be in a container block for readability]
```

## Common Patterns

### AWS CLI Commands

```markdown
:::code{language=bash}
# Create an S3 bucket
aws s3 mb s3://my-workshop-bucket-{{.AccountId}}

# Upload files
aws s3 cp ./data s3://my-workshop-bucket-{{.AccountId}}/data --recursive
:::
```

### CloudFormation Template

```markdown
:::code{language=yaml}
AWSTemplateFormatVersion: '2010-09-09'
Description: Workshop resources

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'workshop-${AWS::AccountId}'
:::
```

### Configuration Files

```markdown
:::code{language=json}
{
  "name": "workshop-app",
  "version": "1.0.0",
  "dependencies": {
    "aws-sdk": "^2.1000.0"
  }
}
:::
```
