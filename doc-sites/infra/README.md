# Guide site deployment

The public site is a bilingual React/Docusaurus build served by a Node 24 Lambda
Web Function. CloudFront signs origin requests with OAC `always-amz-auth`. The
endpoint uses `IamAuth`; only this distribution's resource policy grants access.
This is not a Lambda Function URL or a Lambda Web Adapter deployment.

The public guide is readable without an account. Chat uses Cognito managed login,
authorization code + PKCE, short-lived access tokens and server-side JWT
verification. The browser stores the access token only in the current tab's
session storage; it discards refresh and ID tokens. Chat has a transactional
DynamoDB quota: 250 accepted questions per UTC day globally and 30 per account.
Counters contain hashed subject identifiers, have KMS encryption and a two-day
TTL. Conversation contents are neither stored nor logged.

`aws-content-plugin`, `aws-ops-plugin`, `co-agent`, `project-init`, `pr-dash` and
`agent-dash` have separate Haiku specialists. Retrieval chooses at most three
specialists and three bounded excerpts each. Luna synthesizes the successful
specialists' notes. Unavailable specialists are disclosed, and total failure
returns an error. Provider model IDs stay on the server. The source links are
selected from the corpus, not invented by a model.

## Validate and package

Run from the repository root:

```bash
npm ci --prefix doc-sites
npm ci --prefix doc-sites/server
npm run typecheck --prefix doc-sites
npm run test:server --prefix doc-sites
cfn-lint doc-sites/infra/assets.yaml doc-sites/infra/site.yaml --regions us-east-1
cfn-guard validate --rules doc-sites/infra/security.guard --data doc-sites/infra/assets.yaml --data doc-sites/infra/site.yaml
npm run package:aws --prefix doc-sites
```

`infra/artifacts/site.zip` contains an explicit allowlist of server files,
production dependencies, the public corpus and the static site. Never package
the repository or local configuration directories. S3 source versions used by
active revisions must be retained. There is deliberately no automatic source
object expiration.

The required repository checks and the content-review-agent score >=85 must
pass before executing a production change set. CI prepares an artifact; release
approval remains attached to the reviewed source/artifact.

## Deploy

Use `us-east-1` for this deployment. Confirm the registered Web Function resource
types, US Haiku/Luna profiles, Route 53 hosted zone, and issued us-east-1
certificate covering `skills.atomai.click`. Infrastructure parameters do not
contain secrets. For another account, verify its actual inference-profile and
destination model ARN set and update the restricted IAM statement accordingly.

1. Deploy `assets.yaml` as `skills-guide-assets`, passing `FunctionName=skills-guide`.
2. Upload the ZIP under a content-addressed key:
   `releases/<sha256>.zip`. Record the returned S3 version ID.
3. Create a change set for `site.yaml` as `skills-guide`, with `CodeBucket`,
   `CodeKey`, `CodeVersion`, `HostedZoneId`, `CertificateArn` and
   `FunctionName=skills-guide`. Include `CAPABILITY_IAM`.
4. Inspect the change set and pre-deployment events. Execute after the required
   content, code and infrastructure reviews pass.
5. Wait for the stack and CloudFront to finish. Verify `/`, `/en/`, a guide
   deep link, `/api/config` and `/api/health`; direct unauthenticated access to the
   Lambda origin must be denied. Verify `/api/chat` rejects unauthenticated
   requests, then use an authenticated test account for an actual Haiku/Luna call.
6. For updates, invalidate CloudFront paths after switching the revision.
   Preserve the preceding S3 object version for rollback.

Users create and verify their own account in Cognito; deployment does not create
accounts or send invitations. The normal Cognito welcome/login flow is the only
way the site obtains user identity. Account confirmation is not bypassed.

## Local preview

After a production build, copy `doc-sites/build` to `doc-sites/server/public`
and start `npm run start:server --prefix doc-sites`. The default listener is
`127.0.0.1:3000`; set `AWS_LAMBDA_HTTP_ENDPOINT` for another local port.
Without Cognito and quota configuration, chat is visibly unavailable and no
provider call occurs. Unit tests inject model/auth functions and do not certify
live provider readiness.

The HTTP server preserves old `/oh-my-cloud-skills/` paths by redirecting to the
root path and retaining queries. The existing static `/ko/` redirects preserve
fragments. The old GitHub Pages origin remains a historical deployment until an
explicit redirect/cutover is made there; do not claim old external URLs migrated
merely because the new server handles the same paths.

## Official implementation references

- Lambda Web Function runtimes:
  `https://docs.aws.amazon.com/lambda/latest/dg/web-functions-runtimes.html`
- Versioned S3 source and service-principal access:
  `https://docs.aws.amazon.com/lambda/latest/dg/web-functions-code-s3.html`
- CloudFront OAC signing and endpoint policy:
  `https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-lambda-web.html`
- CloudFormation WebFunction, WebFunctionRevision, WebFunctionEndpoint and
  ResourcePolicy schemas were checked on 2026-11-14 against AWS documentation.
