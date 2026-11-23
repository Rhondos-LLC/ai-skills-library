# AI Skills Library for PowerConnect Data

Agent skills that investigate SAP telemetry collected by **PowerConnect for SAP**, on whichever platform holds it: **Splunk**, **Dynatrace**, or any other backend an AI assistant can query. A skill is a set of Markdown playbooks that an assistant (Claude Code, Claude.ai, Cursor, Codex, OpenCode and others) loads and follows, querying the platform through its MCP server or query tool.

Every skill in this library is **read-only**: it investigates through queries, quotes evidence with timestamps and counts, and recommends fixes for humans to carry out in SAP. No skill deletes data, changes configuration, or treats field contents as instructions.

The library has two forms. The **`powerconnect` bundle** is one skill that covers every topic and is where new work goes. The **standalone skills** are the earlier single-purpose, Splunk-only skills.

## Skills

### Bundle (`powerconnect/`) — draft

One installable skill that routes any PowerConnect question to the right playbook.

**How it works:** the assistant loads a short router, picks the adapter for the platform it can query (Splunk, Dynatrace or a generic one), reads the customer profile or offers a guided setup on first use, confirms the scope holds data, and then reads only the one playbook the question needs. Each playbook names the event types, the fields and the query for every step in both SPL and DQL.

| Group | Playbooks |
|---|---|
| Platform and collector | setup, explorer, feed-health, powerconnect-footprint, data-reconciliation, extractor-config-advisor, install-upgrade-advisor, docs-qa, dashboard-finder, alert-builder |
| Basis operations | system-availability, performance-triage, abap-dumps, background-jobs, system-log, locks-and-updates, os-resources, database-health, java-stack, output-and-spool |
| Interfaces | idocs, rfc-and-queues, integration-messages |
| Security, change, compliance | security-audit, user-and-authorization-review, change-tracking, certificates-and-licenses |
| Cloud and business | cloud-services, business-process, user-activity-and-fiori |
| Overlay | ecs-overlay, applied after any playbook on ECS / RISE landscapes |

`docs-qa` answers product questions from the documentation at docs.rhondos.com and cites the pages it read.

See [`powerconnect/README.md`](powerconnect/README.md) for the full flow, requirements, validation status and what "draft" means. Install either the bundle or the standalone explorer skills below, not both; they trigger on the same questions.

### Standalone skills, base line (`Skills/`)

Splunk only. For standard SAP landscapes.

| Skill | What it does | Data it needs |
|---|---|---|
| [`powerconnect-explorer`](Skills/powerconnect-explorer/) | Discovers which indexes and sourcetypes carry SAP events, checks whether PowerConnect is still sending or a feed has gone stale, assesses observability coverage, and drafts a `customer-profile.md`. **Run this first** on any unfamiliar stack. | Any `sap:abap*` sourcetypes, plus PowerConnect health types (`PC_HEALTH`, `PC_SCHEDULE`, `PC_SENT_STATS`) where collected |
| [`sap-ai-activity-audit`](Skills/sap-ai-activity-audit/) | Audits what an AI triage account actually did in Splunk: every search it ran, what it touched, how much data it pulled. For security reviews, post-incident forensics, and auditor evidence. **Must run from a privileged security/admin session**, never from the AI account itself. | Splunk's own `_audit` index; no SAP event types required |

### Standalone skills, ECS line (`ECS Optimized Skills/`)

Splunk only. For landscapes operated by SAP Enterprise Cloud Services (RISE with SAP). ECS variants end every investigation with an ownership verdict (customer-actionable / ECS service request / insufficient evidence) and read contract facts from customer-maintained lookups.

| Skill | Base equivalent |
|---|---|
| [`powerconnect-explorer-ecs`](ECS%20Optimized%20Skills/powerconnect-explorer-ecs/) | `powerconnect-explorer` |

Each skill folder contains a `SKILL.md` (the playbook the agent loads) and a `README.md` with full details: install options, example prompts, data requirements, and version history.

## Requirements

- **A query tool for the platform that holds the SAP data**, connected to the assistant you are using: a Splunk MCP server exposing `splunk_run_query`, a Dynatrace MCP server exposing `execute-dql`, or any other query tool (bundle only; the standalone skills need Splunk).
- **PowerConnect for SAP data on that platform** (not needed for `sap-ai-activity-audit`, which reads only Splunk's `_audit`).
- **A least-privilege, read-only account** for that connection, scoped to the SAP data. On Splunk: scoped to the SAP index(es) via `srchIndexesAllowed` and `srchFilter`, with the `saia_*` question-answering tools withheld.
- **For the bundle:** an assistant that can read the files bundled next to `SKILL.md`, and web access to `docs.rhondos.com` for documentation questions.

Skills read their scope from a `customer-profile.md`. The bundle creates it through a guided setup on first use; `powerconnect-explorer` can draft it for the standalone skills.

## Installation

### Any agent, via the `skills` CLI

Works with Claude Code, Cursor, Codex, OpenCode and other agents that support the [`skills`](https://github.com/vercel-labs/skills) CLI.

```bash
npx skills add Rhondos-LLC/ai-skills-library --list                                  # see every skill
npx skills add Rhondos-LLC/ai-skills-library --skill powerconnect                    # the bundle, into this project
npx skills add Rhondos-LLC/ai-skills-library --skill powerconnect-explorer           # a standalone skill, into this project
npx skills add Rhondos-LLC/ai-skills-library --skill powerconnect-explorer -g        # install into your user profile
npx skills add Rhondos-LLC/ai-skills-library --skill powerconnect-explorer -a claude-code -y   # one agent, no prompts
```

### Claude.ai / Claude Desktop

Zip a skill folder as `<skill-name>.skill` and upload it under **Settings → Capabilities → Skills**. Enable it for the project or chat that has the Splunk or Dynatrace connector. For the bundle, zip the whole `powerconnect/` folder with the folder itself at the top level of the archive:

```bash
zip -r powerconnect.skill powerconnect -x "*.DS_Store"
```

### Claude Code, by hand

Copy a skill folder (for the bundle, the whole `powerconnect/` folder with its subfolders) so that `SKILL.md` sits at one of these paths, then restart the session:

```
~/.claude/skills/<skill-name>/SKILL.md      # personal, all projects
.claude/skills/<skill-name>/SKILL.md        # this project only
```

## Usage

Once a skill is installed, ordinary prompts trigger it. For example:

- "What SAP data do we have, and is PowerConnect still sending?"
- "Which background jobs failed last night on production, and why?"
- "PowerConnect is raising dumps. Is it loading the system?"
- "The record is in SAP but not in Dynatrace. Where did it go?"
- "How do I upgrade PowerConnect ABAP from 8.x to 9.x?"
- "What has the AI triage account been doing in Splunk this week?" (standalone `sap-ai-activity-audit`)

The first time the bundle is asked a data question without a customer profile, it offers a short guided setup: it detects the platform, scope, systems and PowerConnect version, asks the rest as multiple-choice questions, and saves the profile. The setup can be skipped, and "update the profile" runs it again later.

Every investigation starts with **Step 0 — Orient**: the skill confirms the profile scope holds data, anchors its time windows on the newest event rather than the clock, and states platform, scope, systems and data age in one line before doing anything else. If the scope is empty or stale it says so and stops rather than silently widening it.

## Adding a playbook to the bundle

A new topic is one Markdown file in `powerconnect/playbooks/` plus one row in the routing table in `powerconnect/SKILL.md`:

1. Copy `powerconnect/playbooks/_template.md` and keep its sections.
2. Ground it in the documentation pages of the event types it covers, and sample one real record per event type.
3. Write each step with an SPL and a DQL query, and run every query on a real system.
4. Add the routing row, then run the consistency check:

```bash
python3 tools/check_powerconnect_bundle.py
```

The full guide, including field-confirmation rules, adding a backend adapter and where shared rules live, is in [`powerconnect/README.md`](powerconnect/README.md#adding-a-playbook).

## Versioning

Skills follow semver independently of one another. The version lives in each `SKILL.md` frontmatter and in the skill's README. The bundle has one version for the whole folder: a new playbook is a minor bump.

- **major**: the investigation method or data model changed. Re-read the skill.
- **minor**: new step, pattern, alert, or data source.
- **patch**: wording, thresholds, field-name fixes.

The standalone skill files are generated by the maintainers' build. Every field name in their SPL is verified at build time against real PowerConnect captures and DDIC structures, so fixes ship as a new version rather than as direct edits to `SKILL.md`. The bundle is maintained directly in this repository while it is a draft; its README states which queries have been validated and how.

## Support & Feedback

Feature requests, suggestions and bug reports are welcome via [GitHub issues](https://github.com/Rhondos-LLC/ai-skills-library/issues).

When a query misfires, please include the playbook, the SPL or DQL that ran, what came back (error or empty result), and one sample event (secrets and personal data removed) showing the real field shape.

Contact: engineering@rhondos.com

## Licensing

Copyright 2026 RHONDOS Inc. or RHONDOS LLC and ai-skills-library contributors. Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for copyright and license information.
