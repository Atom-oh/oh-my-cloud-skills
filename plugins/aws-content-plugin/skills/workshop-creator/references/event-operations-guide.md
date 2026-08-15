# Event Operations Guide

Event-operations-related features content authors/operators should know — participant surveys, content
file structure rules, autostart, fraud prevention, Opportunity ID requirements, and build-history background.

---

## Participant Survey

Once an event is provisioned, Workshop Studio **automatically, with no configuration needed**, creates a
standard feedback survey. It's activated when the event starts and deactivated 7 days after it ends
(results remain viewable after that).

- Operators: check/share the survey link from the "Participant survey" dropdown in the event detail header,
  view response reports in real time (individual responses, aggregate scores, export)
- Participants: access via the "Share feedback" link in the event portal sidebar (shown after the event
  starts, no separate login required)
- Survey permissions auto-sync with event Administrator/Support Staff permissions
- **Events with a Grant's `Disable Participant Survey` constraint don't get a survey created** — used for
  large marketing events like re:Invent that collect feedback through a separate centralized process

---

## Page Organization (content file structure rules)

All content lives under the `/content` root, with the filename convention `<name>.<localeCode>.md`.

- **Index files**: a file named `index` loads at that folder's root path. **Every content subfolder must
  have an index file.**
- **Named files**: a file whose name isn't `index` creates a standalone page with no child pages (e.g.
  `welcome.en.md` → `/welcome`).
- **⚠️ Index/Named name collisions cause build failures** — if an `introduction/index.en.md` folder and an
  `introduction.en.md` file both exist, both try to create the `/introduction` path and collide. Rename
  either the folder or the file.
- **Path slugification**: even if folders/filenames have mixed case or spaces, the URL path is
  automatically normalized to lowercase + dashes (`-`) (e.g. `Lab modules/module 1.en.md` →
  `/lab-modules/module-1`).
- **Navigation type**: a Named file, or a folder containing only an index → rendered as a Page Link
  (simple link). A folder with additional named files or subfolders → rendered as an Expandable Link
  (expandable menu, navigating to that index on click).
- Static files sit in a `/static` folder alongside `/content` (`/static/img/aws-logo.png` → referenced as
  `/static/img/aws-logo.png` in content).

---

## Autostart

The default behavior is for **the operator to manually start the event**. Enabling `Autostart` starts it
automatically at the scheduled start time.

| Situation | No Grant | With Grant |
|------|-----------|-----------|
| Autostart enabled | starts automatically at the scheduled time | starts automatically at the scheduled time |
| Autostart disabled | auto-starts **48 hours** after provisioning begins | auto-starts after the Grant's provision lead time allowance + 48 hours |

- **Provisioning itself is unaffected by Autostart** — provisioning must always be manually triggered by the operator.
- Can be toggled anytime during event creation, or afterward via "Update Schedule".
- If a Grant forces Autostart, events created from that Grant cannot disable it.

---

## Fraud Prevention

Workshop Studio automatically monitors the 3 account types tied to an event (central account/team
accounts/infrastructure account) for malicious activity. When a high-risk signal is detected:

- If a **team account** is flagged → that team is automatically terminated, and all of that team's
  participants are **banned** from the event (cannot re-enter unless an operator explicitly lifts the ban)
- If a **central/infrastructure account** is flagged → account access is immediately blocked (no operator,
  participant, or team-account application can access it within the scope of the event)
- The remaining, unflagged accounts can continue to be used normally
- A fraud-flag banner is shown on the event detail page

**Operator response**: verify the event/team join code hasn't leaked externally → check how many teams
were terminated to decide whether the entire event needs to be terminated → if the central/infrastructure
account was terminated, be aware that subsequent team additions (capacity expansion) that depend on that
account may no longer work → spot-check remaining team accounts for abnormal activity (mass EC2 creation,
large outbound traffic, etc.).

**Prevention principles**: use least-privilege participant IAM policies, and manage the participant
allowlist carefully in production events — especially in public events open to an unspecified audience,
avoid using an "Allow all" allowlist.

---

## Opportunity/Campaign ID Requirement

Creating a **production event based on publicly published content** requires a valid Salesforce
Opportunity/Campaign ID (15-18 alphanumeric characters). Test events and events based on internally
published content are exempt.

- A separate **special-purpose Opportunity ID** exists (issued by the Workshop Studio team) for roles
  without Opportunity access (no direct or indirect access to Opportunity data), or for operating internal
  events using public content.
- Using an invalid/expired ID notifies the operator and manager, and the value can be corrected at any time
  from the event detail page (even after the event ends).
- **Events created from a Grant have the Opportunity ID auto-filled** — the operator doesn't need to enter it manually.

---

## Embedded builds vs Hugo builds (background)

Workshop Studio previously used a **Hugo-based static site build**, but has since moved to an **embedded
build** (the web console renders markdown + `manifest.json` directly). This change made builds lighter and
faster, and gave content the same look-and-feel as AWS websites/documentation automatically.

**A common pitfall for authors with a Hugo background**: Hugo shortcodes (`{{% notice %}}`, etc.) and the
embedded build's directive syntax are **different systems** and don't map 1:1 — some Hugo shortcodes have
no corresponding embedded directive, and vice versa. **All workshop content in this repository targets the
embedded build, so Hugo shortcodes must never be used** — see the "CRITICAL: Correct Directive Syntax"
warning in `workshop-agent.md` and `directives-complete.md`. Front Matter is also always required to be
YAML in the embedded build (Hugo optionally allowed YAML/TOML/JSON).

---

## Checklist

- [ ] Verify there's no index/named filename collision in the content folder structure (a build-failure cause)
- [ ] Set the participant allowlist carefully unless this is a large public event (fraud prevention)
- [ ] Check whether an Opportunity ID is ready when creating a production event with public content
- [ ] When migrating content from Hugo, never carry shortcodes over as-is — always rewrite them as embedded directives
