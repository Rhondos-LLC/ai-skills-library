# powerconnect — one skill for all PowerConnect data

**Status: draft (0.1.0).** A single installable skill that routes any
question about SAP telemetry collected by PowerConnect for SAP to the right
playbook, on whichever platform holds the data.

It replaces "install one skill per use case" with "install one skill". The
assistant loads a short router ([SKILL.md](SKILL.md)), picks a backend
adapter, then reads only the playbook the question needs.

## What is inside

```
powerconnect/
  SKILL.md                        router: shared rules + routing table
  customer-profile.template.md    filled in by the guided setup on first use
  backends/
    splunk.md                     Splunk MCP (splunk_run_query, SPL)
    dynatrace.md                  Dynatrace MCP (execute-dql, DQL)
    other.md                      any other query tool: discover, map, record
  playbooks/                      one file per topic (see routing table)
  reference/
    data-model.md                 backend-neutral data model
    event-types.md                catalog of extractors and event types
    dashboards-splunk.md          shipped Splunk dashboards -> event types
    dashboards-dynatrace.md       shipped Dynatrace dashboards
    alerts-dynatrace.md           shipped Dynatrace alerts and DQL matchers
    detections-splunk-es.md       Enterprise Security correlation searches
    docs-index.md                 snapshot of the docs.rhondos.com page index
```

## Playbooks

| Group | Playbooks |
|---|---|
| Platform and collector | setup, explorer, feed-health, powerconnect-footprint, data-reconciliation, extractor-config-advisor, install-upgrade-advisor, docs-qa, dashboard-finder, alert-builder |
| Basis operations | system-availability, performance-triage, abap-dumps, background-jobs, system-log, locks-and-updates, os-resources, database-health, java-stack, output-and-spool |
| Interfaces | idocs, rfc-and-queues, integration-messages |
| Security, change, compliance | security-audit, user-and-authorization-review, change-tracking, certificates-and-licenses |
| Cloud and business | cloud-services, business-process, user-activity-and-fiori |
| Overlay | ecs-overlay (applied after any playbook on ECS / RISE landscapes) |

`docs-qa` answers product questions from the documentation at
docs.rhondos.com. It needs a web-fetch capability in the assistant; without
one it can still point to the right pages from the bundled index.

## Requirements

- An assistant that supports Agent Skills **with bundled files** (it must be
  able to read the files next to `SKILL.md`).
- A query tool for the platform that holds the SAP data: a Splunk MCP server
  exposing `splunk_run_query`, a Dynatrace MCP server exposing
  `execute-dql`, or any other query tool (see `backends/other.md`).
- A least-privilege, read-only account for that tool, scoped to the SAP
  data.
- For `docs-qa`: the ability to fetch `https://docs.rhondos.com`.

## Install

```bash
npx skills add Rhondos-LLC/ai-skills-library --skill powerconnect
```

Or copy the whole `powerconnect/` folder to `~/.claude/skills/powerconnect/`
(personal) or `.claude/skills/powerconnect/` (project). For Claude.ai, zip
the folder as `powerconnect.skill` and upload it under Settings →
Capabilities → Skills.

Do not install this bundle alongside the standalone `powerconnect-explorer`
skills; both would trigger on the same questions.

## Not included on purpose

`sap-ai-activity-audit` stays a separate skill. It audits what an AI account
did in the backend and must run from a privileged security session, so it
must not be installed into the account it audits.

## What "draft" means here

- **Dynatrace:** every DQL block in the playbooks and the adapter (about
  80) was run against a live tenant on one-hour windows. About 50 ran
  correctly as written and about 25 were corrected: most for a syntax
  notice on `in()`, the rest for wrong subtype filters, field names or
  grouping keys. Five could only be syntax-checked because their event
  types had no data (SM13, PC_AUDIT, HDB_DBCC_ALERT, GW_ERROR_*,
  PRC_CHAIN_LOG).
  Field tables mark each name as `sample (Dynatrace)`, `docs` or `SAP`.
  Part of that tenant is replayed demo data, so field names are confirmed
  but result values there are not meaningful.
- **Splunk:** only the explorer playbook's SPL is proven (it is copied
  from the production `powerconnect-explorer` skill). No other SPL has been
  run, and none has passed the maintainers' build-time field verification.
  Splunk field names are assumed to be the UPPERCASE form of the names
  seen in Dynatrace.
- **Cost:** the explorer, feed-health and extractor-config playbooks contain
  24-hour queries meant for scheduled alerts or deliberate assessments; on
  a busy Dynatrace tenant these scan tens of gigabytes.
- **Routing** has not been evaluated. Before release, run a set of example
  prompts per playbook and check the router reaches the right file.
- The ECS overlay's verdict definitions need a domain review.

## Maintaining the references

`reference/*.md` except `data-model.md` are generated from the live
documentation:

```bash
tools/refresh_powerconnect_refs.sh
```

Re-run it after a documentation release so the catalogs and the docs index
do not go stale.
