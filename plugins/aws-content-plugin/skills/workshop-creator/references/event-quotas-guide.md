# Event Quotas & Cost Guide

Covers how much account capacity an event operator can use, how to request special resources when needed,
and where to check costs.

---

## Account quota structure

| Concept | Description |
|------|------|
| **Monthly account quota** | number of AWS accounts refilled per user each month (default 110, does not roll over) |
| **Quota consumed** | permanently deducted the moment an event is **provisioned** — not recovered even if canceled |
| **Quota allocated (refundable)** | an event is **Scheduled** but not yet provisioned — recovered into the quota if canceled |
| **Quota available** | accounts remaining for use this month |
| **Workshop (content) quota** | a separate cap on the number of workshops that can be published. Deleting one on schedule (up to 30 days) frees up the quota |

Each team in an event consumes 1 account (e.g. a 25-team event → 25 accounts). Check actual
consumption/allocation on the event detail's Quotas tab.

---

## Grants — a separate quota for marketing events

**Content authors cannot create Grants directly** — they are issued by the Workshop Studio team, and only
for AWS marketing-organized events such as re:Invent, re:Inforce, and AWS Summit. Unlike the monthly quota,
a Grant is not tied to calendar-month boundaries; it's consumed only within a designated active/expiration
window and is not auto-refilled.

A Grant comes with constraints enforced at event creation — event title, max duration, team size,
participant count, deployable/accessible regions, a pre-deployed participant allowlist, whether autostart
is forced, etc. When an event is created from a Grant, these constraints are auto-filled in the event
creation wizard or shown as locked values. **A Grant cannot be swapped for another after event creation** —
you must cancel and recreate.

Something for content authors to keep in mind: a given Grant may be restricted to "only this content is
usable," so if you're preparing content for a major event, coordinate in advance with the Event Marketing team.

---

## Required Resources — requesting resources beyond standard account limits

Workshop Studio accounts are provisioned with low resource limits by default (to prevent abuse). If you
need a resource that's typically blocked, such as GPU-accelerated compute, you must explicitly declare it
in `contentspec.yaml`.

```yaml
infrastructure:
  # requiredResources sits under infrastructure
  requiredResources:
    sagemaker:
      - type: endpoint/ml.g5.12xlarge   # only allow-listed types are permitted
        quantity: 1
```

- **Only 1 Required Resource can be declared per piece of content** — declaring both sagemaker and
  guardduty simultaneously means neither applies.
- The only currently allowed services are `sagemaker` (specific instance/job types, region-restricted to
  us-east-1, us-west-2, etc.) and `guardduty` (detector, no region restriction) — the type/quantity must
  exactly match the allow-list to pass build validation.
- **This does not guarantee capacity** — it only grants access permission; actual available capacity
  (especially for accelerated compute) is a separate matter, so always verify it with a test event.
- Not needed for resources already allowed by default — use this field only when there's a strong business justification.

---

## Event Cost — checking event costs

Costs are visible **only after the event ends**, and the data may not be finalized until up to 48 hours
after that. The displayed amount is an estimate (USD) based on AWS public pricing.

- Event Overview tab → total event cost + average cost per team (total cost ÷ number of teams)
- Teams tab → per-team cost
- Team detail → cost breakdown by service, filterable by region
- Events canceled before provisioning incur no cost

---

## On-Demand Capacity Reservations (ODCR) — beta

> ⚠️ Beta feature. Requires Workshop Studio team approval before use.

Workshop Studio accounts are set with a low internal risk-assessment score to prevent abuse, so they cannot
normally receive a shared ODCR (the recipient side needs a certain trust level). For cases like GenAI
workshops where guaranteed accelerated-compute capacity is essential, use the following workaround path:

1. Prepare a separate AWS account to own the ODCR, and request approval from the EC2 service team so that
   account can share the ODCR even to low-trust accounts
2. Create/provision the event
3. Via **External Event Lifecycle Notifications** (see `references/central-account-guide.md`), trigger a
   Lambda whenever a team account enters the `deployment_queued` state, and dynamically share the ODCR to
   that team account via `ram.associate_resource_share()`
4. A CloudFormation custom resource on the team-account side polls for the RAM share invitation → accepts
   it → returns a `CapacityReservationId` so subsequent resources can reference it

**Caveats**: since the ODCR is shared as a whole, a single participant could consume all of it. There's a
timing gap between the share automation (step 3) and the acceptance polling (step 4), so give the custom
resource's Lambda a generous timeout of at least 10 minutes.

---

## Checklist

- [ ] Confirm in advance that this month's account quota can cover the event scale (team count)
- [ ] For content aimed at a large marketing event, understand Grant constraints (region/duration/team size) in advance
- [ ] If a resource beyond standard limits is needed, declare `requiredResources` and verify with a test event (note this is not a capacity guarantee)
- [ ] Inform the operator in advance that cost data may take up to 48 hours after the event ends to appear
- [ ] For workloads heavy enough to need ODCR, start with the beta approval process (not usable as a general experiment)
