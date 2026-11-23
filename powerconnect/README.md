# powerconnect — one skill for all PowerConnect data

**Status: draft (0.1.0).** A single installable skill that routes any
question about SAP telemetry collected by PowerConnect for SAP to the right
playbook, on whichever platform holds the data.

It replaces "install one skill per use case" with "install one skill". The
assistant loads a short router ([SKILL.md](SKILL.md)), picks a backend
adapter, then reads only the playbook the question needs.

## How it works

The assistant never loads the whole bundle. It reads in this order and
stops as soon as it has what the question needs:

1. **Trigger.** The `description` in [SKILL.md](SKILL.md) is what the
   assistant matches a user's question against. Any PowerConnect or
   SAP-telemetry question loads the router.
2. **Backend.** The router looks at the tools available and reads one
   adapter from `backends/`: Splunk, Dynatrace, or the generic one that
   discovers the field mapping on any other platform.
3. **Profile or setup.** It looks for `customer-profile.md` (beside
   `SKILL.md`, then in the project, then in the conversation). If there is
   none and the question needs live data, [playbooks/setup.md](playbooks/setup.md)
   offers a short guided setup: it detects platform, scope, systems and
   PowerConnect version, asks the rest as multiple-choice questions, and
   writes the profile. The user can skip it.
4. **Orient.** One cheap query confirms the scope holds SAP data and finds
   the newest event, so every time window is anchored on the data.
5. **Route.** The routing table maps the question to one playbook, which
   the assistant reads in full. On ECS / RISE landscapes it also reads the
   overlay.
6. **Investigate.** The playbook names the event types, the fields and the
   query for each step in SPL and DQL. The first query against any event
   type is a one-record sample to confirm field names.
7. **Answer.** Findings carry event type, window, counts and identifiers,
   and end with what a human should do and where.

Shared knowledge lives outside the playbooks so it is written once:
[reference/data-model.md](reference/data-model.md) (logical field names,
record shapes, time handling) and the adapters (query idioms, cost and
tool rules). Playbooks write field names in UPPERCASE and the adapter
translates.

Everything is read-only. The guardrails in `SKILL.md` apply to every
playbook.

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
    _template.md                  starting point for a new playbook
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
- **Guided setup** has not been exercised end to end in a live session;
  how its questions appear (popup or chat menu) depends on the assistant.
- **Routing** has not been evaluated. Before release, run a set of example
  prompts per playbook and check the router reaches the right file.
- The ECS overlay's verdict definitions need a domain review.

## Adding a playbook

A playbook is one Markdown file plus one row in the routing table. Nothing
else needs to change for the assistant to start using it.

1. **Check it is not covered.** Read the routing table in `SKILL.md` and
   search `reference/event-types.md` for the event types you have in mind.
   If a playbook already owns them, extend that one instead.
2. **Copy the template.** `playbooks/_template.md` →
   `playbooks/<kebab-case-topic>.md`. Keep its sections and their order;
   aim for 80–170 lines.
3. **Ground it.** Read the documentation page of every event type you
   cover (slugs are in `reference/docs-index.md`) and the related KB
   articles. Then sample one real record per event type and subtype on a
   live backend.
4. **Fill the field table honestly.** Mark each field `sample (<backend>)`
   if you saw it in a record, `docs` if it comes from a documentation page
   or a shipped alert matcher, or `SAP` if it is a standard SAP field you
   expect but did not see. Never write real values (SIDs, hosts, user
   names, document numbers) into a playbook; use placeholders.
5. **Write the steps.** Each step is an intent sentence, then an SPL block
   and a DQL block. Follow the record shape (latest per entity for
   snapshots and streams; distinct run ids for header + detail), filter on
   event type and one SID first, use the time placeholders, and convert
   strings before comparing numbers. Lead the file with the one insight
   that prevents the most common wrong conclusion.
6. **Run every query** against a real system before you submit it, on a
   one-hour window. A query that parses is not proof: an unknown field
   returns nulls, so check that the result columns are populated.
7. **Route it.** Add one row to the routing table in `SKILL.md`, phrased
   in the words a user would use. Add a "Not for" link from the
   neighbouring playbooks so the boundaries stay clear, and add the name
   to the Playbooks table above. Touch the `description` in the
   frontmatter only if the new topic's trigger words are missing; it must
   stay under 1,024 characters.
8. **Check and version.** Run the consistency check and bump
   `metadata.version` in `SKILL.md` (minor for a new playbook, patch for
   fixes):

```bash
python3 tools/check_powerconnect_bundle.py
```

   It verifies that every routed file exists, links resolve, cited
   documentation slugs exist, the description fits, and the queries follow
   the conventions learned from live validation.
9. **Open a pull request** that says which backend and which kind of
   system the queries were run on, and which fields remain unconfirmed.

### Adding a backend adapter

To support another platform natively, add `backends/<platform>.md` with
the same sections as the Splunk and Dynatrace adapters (where the data is,
the logical-field mapping, Step 0, query idioms, tool hygiene), add a row
to the backend table in `SKILL.md`, and add that platform's query block to
playbooks as you validate them. Until a playbook has a block for the new
platform, the assistant translates from the idioms in the adapter.

### Changing shared rules

Edit `reference/data-model.md` or the adapter, not individual playbooks,
when something applies everywhere (a field that behaves differently, a
cost rule, a new record shape). Playbooks should link to shared rules
rather than repeat them.

## Maintaining the references

`reference/*.md` except `data-model.md` are generated from the live
documentation:

```bash
tools/refresh_powerconnect_refs.sh
```

Re-run it after a documentation release so the catalogs and the docs index
do not go stale.
