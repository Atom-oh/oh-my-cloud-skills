# Supported Services & Limitations Guide

A guide for judging, before designing content, "can this workshop actually run in a Workshop Studio
account?" The fundamental constraint of a standard account comes from **account recycling** — an account
must be returned to a clean state after an event ends so it can be reused for the next event, so **any
service without a Delete/Unregister API, or any resource that can't be undone, is fundamentally unsupported.**

---

## Things fundamentally unsupported

| Category | Reason |
|------|------|
| **Services dependent on AWS Organizations** (Control Tower, Landing Zone, Firewall Manager, etc.) | Workshop Studio itself uses Organizations for account management, so nesting it inside a participant account isn't possible |
| **Changing the account's own settings** (allowlists, raising service limits, etc.) | breaks the account-recycling premise — never attempt this directly with internal tools |
| **Immutable storage** (S3 Object Lock, AWS Backup Legal Hold) | creates a resource Workshop Studio can never delete afterward |
| **Long-term purchases/commitments** (EC2/RDS Reserved Instances, DynamoDB Reserved Capacity, Route53 domain purchases) | outside the scope of a temporary hands-on event |
| **Business/Enterprise Support, full Trusted Advisor features** | not enabled on the account |
| **Opt-in regions, special regions** (China/GovCloud) | only standard commercial regions are supported |
| Third-party datasets | subject to the asset scanning/policy constraints in `references/workshop-assets-guide.md` |

If a new service/action is needed, you must request it directly from the Workshop Studio team (a service
with no Delete API is fundamentally impossible), and content authors have no way to work around this on their own.

---

## Large instance / GPU constraints

Standard accounts carry an internal risk-assessment score at the level of a newly-verified account — large
instances (e.g. `x1.32xlarge`, hundreds of vCPUs) or EC2-prefix (not `ml.`) GPU instances are almost all
set to **quota 0** by default. SageMaker (`ml.*`) GPUs are allowed, but usually limited to a single
instance and `ml.p3.2xlarge` or below.

If you need a specific instance/job type beyond standard limits, you must explicitly request it via
`requiredResources` in `contentspec.yaml` — details: `references/event-quotas-guide.md`. **Only 1 required
resource declaration is allowed per piece of content**, so sagemaker and another service cannot be
requested simultaneously.

Actual standard EC2 vCPU limits (representative example, common across regions):

| Instance family | On-Demand vCPU limit |
|--------------|---------------------|
| Standard (A/C/D/H/I/M/R/T/Z) | 256 vCPU |
| G/VT (GPU) | 0 vCPU |
| P (GPU) | 0 vCPU |
| High Memory / X | 0 vCPU |
| HPC | 192 vCPU |

→ **Always verify actual limits with a test event.** For limits not listed here, check the Service Quotas
console directly in a test event.

---

## AWS Marketplace support scope

Currently only **free (no-cost) 1st/2nd-party AMI, Container, and Data Exchange products** are supported
(implemented via the Private Marketplace feature). Paid products, 3rd-party products, and SaaS products
are not yet supported, and support will expand gradually. For a workshop that depends on a Marketplace
product, always verify in advance with a test event that it actually subscribes/launches in the account.

## Amazon Bedrock support scope

- **Region restriction**: available only in `us-west-2`, `us-east-1`
- Most Foundation Models are activated via Marketplace access, targeting activation within about 2 weeks
  of public release, though this is coordinated with the Bedrock team and not a fixed schedule. Some
  models like Titan/Nova/OpenAI gpt-oss/Mistral are usable immediately by default
- **Do not use Legacy/EOL models in content** — Bedrock periodically deprecates old models, so content can
  break over time
- For large events (roughly 50+ teams) using a particular service heavily, prior approval from that
  service team may be required due to capacity concerns — Bedrock and a few other services are subject to
  this capacity constraint. If planning a large-scale event, coordinate with the Workshop Studio team in advance.

---

## Cross-region read access

Even **outside** an event's deployable/accessible regions (`deployableRegions`/`accessibleRegions`), the
participant role can call **read-only (Describe/Get/List) APIs without region restriction** for most AWS
services (e.g. `ec2:Describe*`, `s3:Get*`, `sagemaker:List*`, etc.). This is designed so console screens
that display resources in other regions don't break, but **write/create operations remain confined to
deployable/accessible regions**. When designing participant policies, it helps to know this behavior so
you're not confused about "why can I query resources in other regions too."

---

## Checklist

- [ ] Rule out from the start any content that depends on a service with no Delete API
- [ ] If GPU/large instances are needed, declare `requiredResources` and verify actual limits with a test event
- [ ] If using Bedrock, restrict the region to `us-west-2`/`us-east-1` and avoid Legacy models
- [ ] First confirm any Marketplace product is a free 1st/2nd-party AMI/Container/Data Exchange offering
- [ ] For large-scale (tens to hundreds of teams) events, coordinate with the Workshop Studio team in advance
