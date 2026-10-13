# Workshop Studio Directives Complete Reference

The complete reference for every directive syntax supported by Workshop Studio. Alert/Code/Tabs/Image have
detailed syntax in their own dedicated reference files (`alert-reference.md`/`code-reference.md`/
`tabs-reference.md`/`image-reference.md`); this document covers only summaries of those.

---

## Basic directive syntax

Directives extend Markdown to provide a richer content experience.

### Components

- **Colon (`:`)**: starts a directive
- **Square brackets `[]`**: inline content (single line)
- **Curly braces `{}`**: key/value attributes (quotes can be omitted if the value has no spaces)

```markdown
:directive[content]{key1="value1" key2='value2' key3=value3}
```

### 3 directive types

| Type | Colon count | Description |
|------|-----------|------|
| **Text** | `:` | renders inline within the text flow |
| **Leaf** | `::` | renders as its own block (content goes inside `[]`) |
| **Container** | `:::` | can contain other markdown blocks inside |

```markdown
See the Workshop Studio Wiki :link[here]{href="https://example.com" external="true"}.

::code[console.log('Hello world!');]{showCopyAction=true language="js"}

:::alert{type="success" header="Success"}
Write the content here.
:::
```

### Nested directives (`::::`)

When nesting, **the outer directive must have more colons than the inner one** — too few colons breaks parsing.

```markdown
::::tabs
:::tab{label="First"}
First tab content
:::
:::tab{label="Second"}
Second tab content
:::
::::
```

When nesting 3+ levels (e.g. putting a `code` directive inside a tab), increase the colon count one step
at a time (`:::::tabs` → `::::tab` → `:::code`).

> ⚠️ **Hugo shortcodes (`{{% notice %}}`, etc.) are not supported at all by Workshop Studio.** Always use
> only the colon-based directive syntax above — see the "CRITICAL: Correct Directive Syntax" warning in
> `workshop-agent.md`.

### Extended Parsing — also works inside code blocks / link hrefs

Some directives (`:param`, `:assetUrl`) have their values substituted before markdown processing, so they
work even in regions markdown doesn't parse (such as code blocks). Conversely, other directives
(`:button`, `[link](url)`, etc.) render literally as-is inside code blocks.

---

## Alert

An informational/warning message. Supports Leaf/Container only (not Text). Attributes: `header`,
`type` (`success`|`error`|`warning`|`info`, default `"info"`). Details: `alert-reference.md`

```markdown
::alert[Simple message]{type="warning"}
```

## Code

A code/terminal-output block. Supports Text/Leaf/Container. Attributes: `language`, `showLineNumbers`,
`showCopyAction`, `copyAutoReturn`, `highlightLines`, `highlightLinesStart`, `lineNumberStart`.
Details: `code-reference.md`

```markdown
:::code{language=bash showCopyAction=true}
kubectl get pods -n vllm
:::
```

## Tabs / Tab

`Tabs` is a Container-only directive holding one or more `Tab`s (neither supports Text/Leaf). `Tabs`
attributes: `activeTabId`, `variant` (`default`|`container`), `groupId` (synchronizes multiple tab groups).
`Tab` attributes: `id`, `label`, `disabled`. **`Tabs` itself has no `labels` array attribute** — each label
is set on the individual `:::tab{label="..."}`. Details: `tabs-reference.md`

```markdown
::::tabs{variant="container"}
:::tab{label="Console"}
Console instructions
:::
:::tab{label="CLI"}
CLI instructions
:::
::::
```

## Image

Displays an image. Supports Text only. Attributes: `src`, `width` (px number), `height` (px number),
`disableZoom`, `title`. **`width` is a pixel number, not a percentage string like `"90%"`.** There is no
`signedUrl` attribute. Details: `image-reference.md`

```markdown
:image[Architecture]{src="/static/images/architecture.png" width=800}
```

---

## Param

References a `params` value from contentspec.yaml in the content. Supports Text only. Attributes: `key`
(supports dot/array-index notation), `defaultValue`. Global values `globals.baseUrl`/`globals.locale` are
also available. Details: `event-params-guide.md`

```markdown
Cluster name: :param{key="clusterName"}
```

## Asset URL

Generates an absolute (signed) URL for an asset in `/static` or an S3 assets bucket. **Text only**
(no Leaf/Container) — it uses curly-brace attributes with no square brackets. Attributes: `path` (relative
asset path), `source` (`repo`|`s3`, default `repo`). Since its value is substituted before other markdown
processing, it works safely even in regions markdown doesn't parse, such as code blocks — e.g. `curl`
commands. Because a signed URL containing an `&` character could be misinterpreted by the shell as a
background job, wrap the value in single quotes in such commands.

```markdown
:::code{language=bash}
curl ':assetUrl{path="/resources/setup.yaml"}' --output setup.yaml
curl ':assetUrl{path="/resources/dataset.zip" source=s3}' --output dataset.zip
:::
```

## Button

A clickable button UI. Text only (no Leaf/Container) — put the button label inside the square brackets
(for an icon button with no label, e.g. `variant="icon"`, leave the brackets empty). Attributes: `disabled`,
`href` (if set, acts as a link; combine with `variant="link"` for link-styled buttons), `iconAlign`
(`left`|`right`), `iconName`, `target` (applies only when `href` is set), `variant`
(`normal`|`primary`|`link`|`icon`|`inline-icon`, default `normal`), `wrapText` (default `true`), `action`
(`navigate`|`download`, default `navigate`).

```markdown
:button[Open Console]{href="https://console.aws.amazon.com" variant="primary"}
:button[Download Template]{href="/static/files/template.yaml" action=download}
:button[]{variant="icon" iconName="settings"}
```

## Link

An inline hyperlink/download link. Text only. Attributes: `href` (if absent, renders with button role),
`external` (shows an external-link icon), `target` (setting `_blank` auto-adds `rel="noopener"`), `action`
(`navigate`|`download`, default `navigate`).

```markdown
See :link[AWS Documentation]{href="https://docs.aws.amazon.com" external=true} for details.

:link[Download the CloudFormation template]{href="/static/files/template.yaml" action=download}
```

> Standard markdown links (`[text](url)`) are sufficient in most cases — links starting with `http(s)://`
> automatically open in a new tab. Use the Link directive only when you need behavior standard markdown
> can't express, like download actions or an external-link icon.

## Expand

A collapsible section (accordion). Supports Leaf/Container (not Text). Attributes: `header`,
`defaultExpanded` (default `false`), `variant` (`default`|`container`).

```markdown
::expand[Short answer]{header="See more"}

::::expand{header="Configuration example" defaultExpanded=false}
:::code{language=yaml}
region: ap-northeast-2
:::
::::
```

## Children

Automatically generates a list of the current page's child pages. Leaf only (no Text/Container).
Attributes: `depth` (how many levels deep to show, default `1`), `variant` (`list`|`normal`, default `list`).

```markdown
::children{depth=2}
```

## Video

Embeds a YouTube/Vimeo video in privacy-enhanced mode. Leaf only (no Text/Container). **There is no `src`
attribute** — use `id` (embed ID) and `type` instead. Attributes: `id`, `type` (`youTube`|`vimeo`, default
`youTube`), `autoplay`, `start` (start time, in seconds).

```markdown
::video{id=a9__D53WsUs}
::video{id=395869376 type=vimeo start=63}
```

---

## Markdown syntax cautions

- Workshop Studio **does not render raw HTML** (security policy).
- A **colon (`:`) inside content collides with directive syntax and must be backslash-escaped** — e.g.
  `AWS re\:Invent` → `AWS re:Invent`. Be especially careful with easy-to-miss colon usages like times
  (`10\:30`) or ratios (`3\:1`).
- Header anchors are auto-slugified; non-ASCII headers (e.g. Korean) can specify an explicit anchor ID with
  `## Title {#custom-id}`.
- Inter-page links reference paths without the locale code — both absolute paths
  (`/introduction/getting-started`) and relative paths (`../getting-started`) are supported.

---

## Multilingual support

15 supported locales: `en-US`, `es-US`, `ja-JP`, `fr-FR`, `ko-KR`, `pt-BR`, `de-DE`, `it-IT`, `zh-CN`,
`zh-TW`, `uk-UA`, `pl-PL`, `id-ID`, `nl-NL`, `ar-AE`. For every locale defined in `contentspec.yaml`'s
`localeCodes`, every content folder needs an `index.[localeCode].md` file. Locale-specific files for the
same page must share the same `weight`, or the navigation order will drift — details: `front-matter.md`

---

## Common patterns

### 1. Running a command + expected output

````markdown
Run the following command:

:::code{language="bash" showCopyAction=true}
kubectl get nodes
:::

Expected output:

```
NAME                                           STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ap-northeast-2.compute.internal   Ready    <none>   5m    v1.28.x
```
````

### 2. Step-by-step instructions + caveats

```markdown
## Create the cluster

Create the EKS cluster with the following command:

:::code{language="bash" showCopyAction=true}
eksctl create cluster \
  --name my-cluster \
  --region ap-northeast-2 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3
:::

::alert[Cluster creation takes about 15-20 minutes.]{type="info"}
```

### 3. Choosing an option + explanation

````markdown
::::tabs{variant="container"}
:::tab{label="Basic Install"}
Default settings for a quick start.

```bash
helm install my-release bitnami/nginx
```
:::
:::tab{label="Advanced Install"}
Installation with custom values applied.

```bash
helm install my-release bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=LoadBalancer
```
:::
::::
````
