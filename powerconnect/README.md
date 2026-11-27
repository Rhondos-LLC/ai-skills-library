# powerconnect — one skill for all PowerConnect data

**Status: draft (0.2.0).** A single installable skill that routes any
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
2. **Update check.** The router runs `scripts/fetch.py --check`, which
   compares the installed copy with the release published in this
   repository. If the published one is newer, the assistant reads every
   file through the script for the rest of the conversation (see
   [Live updates](#live-updates)).
3. **Backend.** The router looks at the tools available and reads one
   adapter from `backends/`: Splunk, Dynatrace, or the generic one that
   discovers the field mapping on any other platform.
4. **Profile or setup.** It looks for `customer-profile.md` (beside
   `SKILL.md`, then in the project, then in the conversation). If there is
   none and the question needs live data, [playbooks/setup.md](playbooks/setup.md)
   offers a short guided setup: it detects platform, scope, systems and
   PowerConnect version, asks the rest as multiple-choice questions, and
   writes the profile. The user can skip it.
5. **Orient.** One cheap query confirms the scope holds SAP data and finds
   the newest event, so every time window is anchored on the data.
6. **Route.** The routing table maps the question to one playbook, which
   the assistant reads in full. On ECS / RISE landscapes it also reads the
   overlay.
7. **Investigate.** The playbook names the event types, the fields and the
   query for each step in SPL and DQL. The first query against any event
   type is a one-record sample to confirm field names.
8. **Answer.** Findings carry event type, window, counts and identifiers,
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
  manifest.json                   version + checksum per file (generated)
  customer-profile.template.md    filled in by the guided setup on first use
  scripts/
    fetch.py                      serves the newest published copy of a file
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
- For live updates (optional): `python3` and HTTPS access to
  `raw.githubusercontent.com`. Without them the skill uses its bundled
  files.

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

## Live updates

The installed skill can pick up new and corrected playbooks without a
reinstall. Once per conversation the router runs
[scripts/fetch.py](scripts/fetch.py) `--check`, which does one HTTP GET
for `manifest.json` on the `release` branch of this repository:

```
https://raw.githubusercontent.com/Rhondos-LLC/ai-skills-library/release/powerconnect/manifest.json
```

- **Published version newer than installed:** it downloads every file
  whose checksum differs, rejects any download that does not match the
  manifest, and caches them in `~/.cache/powerconnect-skill/`. The
  assistant then reads every file through the script, so one conversation
  never mixes two versions. If the router itself changed, the script
  prints the new one and the assistant follows it.
- **Same or older version, no network, or any error:** the assistant reads
  the bundled files as usual. A failed check never blocks an answer.

A file read re-checks after six hours; `--check` always checks. GitHub
caches raw files for up to five minutes, so a check right after a release
can see the old version, or a mismatch that falls back to the installed
copy until the cache expires.

| Where the skill runs | Live updates |
|---|---|
| Claude Code | Yes. Allow `Bash(python3 <skill folder>/scripts/fetch.py:*)` to skip the permission prompt. |
| Claude.ai, Claude desktop | Only if the organisation's code-execution network settings allow `raw.githubusercontent.com`. |
| Claude API (skills in the code-execution container) | No network: bundled files only. |

What it cannot change: the `description` in the frontmatter (it decides
when the skill triggers and is read only at install time) and
`scripts/fetch.py` itself (the script serves Markdown only, never code).
Changes to either need a reinstall.

**Publishing a release.** `main` is where work lands; `release` is what
every installed copy reads, so only promote what has been validated:

1. Merge to `main` with `metadata.version` bumped and the manifest
   rebuilt (`python3 tools/build_powerconnect_manifest.py`; the
   consistency check fails if it is stale). An installed copy only
   switches when the published version is higher than its own.
2. Fast-forward the release branch:

   ```bash
   git push origin main:release
   ```

3. To withdraw a bad release, revert on `main`, bump the version again and
   promote. Lowering the version on `release` instead would leave copies
   that already moved on with the bad files until their next reinstall.

Protect the `release` branch: anyone who can push to it changes what
every installed assistant does.

**Testing a release before promoting it.** Point one session at another
copy with `POWERCONNECT_BUNDLE_URL` (https, or http on localhost), or
turn the network off with `POWERCONNECT_OFFLINE=1`. These are for
maintainers; the skill tells the assistant never to set them.

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
8. **Check and version.** Bump `metadata.version` in `SKILL.md` (minor
   for a new playbook, patch for fixes), rebuild the manifest and run the
   consistency check:

```bash
python3 tools/build_powerconnect_manifest.py
```

```bash
python3 tools/check_powerconnect_bundle.py
```

   It verifies that every routed file exists, links resolve, cited
   documentation slugs exist, the description fits, the manifest is
   current, and the queries follow the conventions learned from live
   validation.
9. **Open a pull request** that says which backend and which kind of
   system the queries were run on, and which fields remain unconfirmed.
   Installed copies get it only once it is promoted to `release` (see
   [Live updates](#live-updates)).

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
do not go stale. It also rebuilds `manifest.json`; bump the version before
you promote the result.
