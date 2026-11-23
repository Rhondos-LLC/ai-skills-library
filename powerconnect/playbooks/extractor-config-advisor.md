# Extractor configuration advisor

**Use when:** the user wants to enable or disable an extractor, change how
often it runs, filter what it sends, mask a field, send a dataset to a
different index or only to one connection, backfill history, reduce data
volume, build a custom extractor, or asks what a global parameter does.
**Not for:** an extractor that is configured but not delivering →
[feed-health.md](feed-health.md). Installing or upgrading the agent →
[install-upgrade-advisor.md](install-upgrade-advisor.md). Anything else the
documentation answers → [docs-qa.md](docs-qa.md).

A documentation-driven playbook: you read the current configuration from
the data, read the matching page, and describe the change for a human to
make. The core insight: **check what is running before advising what to
change.** `PC_SCHEDULE` is the extractor configuration (Group Def) as the
agent sees it, and it often shows the requested extractor is already
active, runs daily, or is hidden by a filter, which changes the advice.
Configuration screens differ by agent and by release, so name the version
your answer applies to.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `PC_SCHEDULE` | ABAP | snapshot per extractor | active flag, interval, delay, last and next run | yes |
| `PC_SENT_STATS` | ABAP | counter per extractor and day | bytes sent, for volume questions | yes |
| `PC_HEALTH` subtype `INFO` | ABAP | snapshot | agent version `RELEASE_NO` (decides which menus and features exist) | yes |
| any type in question | all | as documented | whether it arrives, how often, how large | n/a |

Java and Cloud agents send no schedule event; their configuration is only
visible in their own consoles. If the PC_* types are missing, say so and
ask the user for an export of Setup Group Def.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `GROUP_DEF` | Group Definition = `EVENT_TYPE` the extractor emits | | sample (Dynatrace) |
| `ACTIVE` | "Active" checkbox | `X` / empty | sample (Dynatrace) |
| `COLL_INTERVAL`, `INTERVAL` | "Suspend Interval" in seconds, zero-padded string | `00003600` = hourly | sample (Dynatrace) |
| `COLL_DELAY`, `DELAY`, `RUN_DELAY` | delay values; which one is the configured "Delay" is not established | sample two records before quoting | sample (Dynatrace), meaning unconfirmed |
| `LAST_RUN`, `NEXT_RUN` | `yyyymmddhhmmss` | | sample (Dynatrace) |
| `MTGRP`, `SBGRP`, `UDATE`, `BYTES` (PC_SENT_STATS) | extractor, subgroup, day, bytes; whether `BYTES` is cumulative within the day is not established | compare two polls of one group | sample (Dynatrace), meaning unconfirmed |

## Investigation sequence

**1. Pin down agent and version.** ABAP, Java or Cloud; and the release
(profile, or `PC_HEALTH` subtype `INFO`; see
[install-upgrade-advisor.md](install-upgrade-advisor.md)). Several features
below exist only from a given support pack.

**2. Read the current extractor configuration** (ABAP):

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_SCHEDULE source=<SID>
| stats latest(ACTIVE) as active latest(COLL_INTERVAL) as interval_s latest(LAST_RUN) as last_run by GROUP_DEF
| eval interval_s=tonumber(interval_s)
| sort GROUP_DEF
```

```dql
fetch logs, from: now() - 2h
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_SCHEDULE"
| filter log.source == "<SID>"
| sort timestamp asc
| summarize {active = takeLast(active), interval_s = takeLast(toLong(coll_interval)), last_run = takeLast(last_run)}, by: {group_def}
| sort group_def asc
| limit 400
```

**3. Check what actually arrives and how much.** Count per event type over
a full day (the adapter's "count and freshness per type" idiom), and for
volume questions the bytes per extractor:

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_SENT_STATS source=<SID>
| eval bytes=tonumber(BYTES)
| stats max(bytes) as max_bytes sum(bytes) as sum_bytes by UDATE MTGRP
| sort - max_bytes
| head 30
```

```dql
fetch logs, from: now() - 24h
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_SENT_STATS"
| filter log.source == "<SID>"
| summarize {max_bytes = max(toLong(bytes)), sum_bytes = sum(toLong(bytes))}, by: {udate, mtgrp}
| sort max_bytes desc
| limit 30
```

Both columns are given because the counter semantics are unconfirmed. In
the sample the extractor ran once a day and sent one record per `MTGRP` and
`SBGRP`, so `sum_bytes` was the group total and `max_bytes` its largest
subgroup; with several polls in the window the sum counts a group more
than once. Use them to rank extractors; for exact figures use the
platform's ingest accounting.

**4. Read the page for the requested change** (table below) with
[docs-qa.md](docs-qa.md) and describe the steps for the user's version.

On any other backend, translate steps 2–3 with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Where each change is made

ABAP agent, transaction `/n/BNWVS/MAIN` in the productive client:

| Change | Where | Know this | Page |
|---|---|---|---|
| Enable / disable an extractor | Administrator → Setup Group Def, "Active" | job stop is optional from SP 6.04 | KB 108 |
| Collection interval | Setup Group Def, "Suspend Interval" (seconds) | the guide recommends stopping jobs before Group Def changes | `abap-data-extraction-user-guide` |
| Run at a fixed time | Setup Group Def, "Use schedule" | creates job `/BNWVS/BC_EXT_<group>`; applies after Extractor job restart | KB 75 |
| Read with a delay | Setup Group Def, "Delay" (seconds) | for data written late to the database; usually on support's advice | KB 180 |
| Pin to an app server | Setup Group Def, "AS Instance" | leave blank unless there is a reason | user guide |
| Look-back after an outage | "Maximum Last Interval"; global `MAX_INTERVAL_MULTIPLIER` | default 15× the interval; older data is skipped | user guide, KB 84 |
| Dataset to another Splunk index | Setup Group Def, "Splunk Index" | same Splunk cluster; the HEC token and role must allow the index | KB 143 |
| Dataset to only some connections | Upload Scheme → event type filter on the connection | from SP 7.03; empty filter = everything; filter by Data Kind is broken in SP 8.02 | KB 179, KB 207 |
| Record-level metric filters (SM37, SM20, SM21, STAD, WE02 ...) | Administrator → Metric Filters | described on each event type's page | event page |
| Clear, hash, remove or obfuscate a field | Administrator → Setup Metric → Field filter; Obfuscate Rules | options differ before / from SP 7.02 | KB 177 |
| Add a derived field | Setup Metric → Metric Extensions | field arrives with prefix `PC_`; from SP 6.04 | KB 149 |
| KPIs as metrics | Setup Metric → KPI Definitions | from SP 8.03; subtype `_METRICS_`; no extra extraction | KB 214 |
| Derived events | Setup Metric → Event Definitions | from SP 8.04; subtype `_EVENTS_` | KB 225 |
| Other clients | per-extractor multi-client support | only the extractors listed in the KB | KB 109 |
| Remove an extractor | deactivate, delete in Group Def, delete in Setup Task Group | jobs stopped | KB 118 |
| Custom extractor | subclass `/BNWVS/CL_EXT_SUPER`, redefine `PERFORM_METRIC_CALCULATION`, call `STORE_METRIC`; add Group Def and Task Group entries | flat tables only; reserved field names; batch large sets | KB 61 |
| Historical load | Goto → Test metrics → select period → Send Metric Data | time-based extractors only, never snapshots; Dynatrace: last 24 h only; send in chunks | KB 127 |
| Global parameters | Administrator → Global Configuration | restart jobs after a change | KB 84 |

Global parameters most often asked about (defaults from KB 84, written for
5.x–6.x; confirm on the installed release): `EXTRACTOR_JOB_INTERVAL` 15 s,
`MAX_PARALLEL_PROCESS` 10 % of dialog tasks, `EXTRACT_TRIALS` 5 dumps
before an extractor is blocked, `ARCHIVE_DAYS_TO_RETAIN` 1 day sent /
`..._UNSENT` 3 days, `EXTRACT_TRACE` off (feeds `PC_TRACE`).

Java agent (console `.../spcj_wd/SapPowerConnectJava`): plug-ins are
switched on the General tab; only JMX is on by default. Enabling most
plug-ins needs no restart; changing an interval (milliseconds) does, as do
the log plug-ins (KB 142, `java-data-extraction-user-guide`). From Java
8.1.0 some extractors run once per host, on `server0` unless changed
(KB 200). Event type per extractor: `powerconnect-java-extractors`.

Cloud agent (web UI → Inputs; list in `powerconnect-cloud-inputs`): a field
mapping is an allow-list and replaces the default rather than merging, so
removing a row stops that field being sent; it is the tool for trimming
event size (`field-mapping`). Backfill with Replay on the input,
administrators only (`replaying-data`).

## Reading the results

| You see | It usually means | Advice |
|---|---|---|
| Requested extractor already `ACTIVE`, events absent | not a configuration question | [feed-health.md](feed-health.md) |
| Extractor absent from `PC_SCHEDULE` | not in Group Def, or not shipped in this release | check "Default" and release in `summary-of-extractors-and-event_type-s` |
| Interval far shorter than the data changes | volume without value | lengthen the interval before filtering |
| A few groups dominate `BYTES` | volume is concentrated | metric filter first, then field filter, then interval |
| Snapshot data wanted for last month | cannot be backfilled | say so; it only exists from when the extractor was active |
| User wants a field hidden for privacy | field filter, not a platform-side mask | KB 177; the value never leaves SAP |

## What to tell the user

- Current state from the data: active or not, interval, last run, volume
  rank, with window and `SID`.
- The menu path and steps for their agent and version, and the page.
- Side effects: platform volume and licence usage, load on SAP (dialog
  tasks used for extraction), whether jobs need a restart.
- How to verify: the extractor shows in `PC_SCHEDULE` and its event type
  has a fresh newest timestamp. You do not make the change; on ECS/RISE
  see [ecs-overlay.md](ecs-overlay.md) for who can.

## Alert ideas

An extractor's `ACTIVE` flag or interval changing (`PC_SCHEDULE`, latest
versus previous day) and a group's daily bytes far above its norm
(`PC_SENT_STATS`; starting point 3× the 7-day median). Hand these to
[alert-builder.md](alert-builder.md).

## Documentation

- `abap-data-extraction-user-guide`, `java-data-extraction-user-guide`, `pc_schedule`
- `summary-of-extractors-and-event_type-s`, `powerconnect-java-extractors`, `powerconnect-cloud-inputs`, `field-mapping`, `replaying-data`
- `kb-108-disable-abap-extractor`, `kb-118-remove-powerconnect-extractor`, `kb-84-global-configuration-parameters`, `kb-75-time-based-extraction`, `kb-180-add-delay-to-data-extraction`
- `kb-127-splunking-historical-data`, `kb-177-metric-field-filter`, `kb-149-metric-extension-functionality`, `kb-109-multi-client-functionality`
- `kb-179-group-definition-event-type-filter-per-conn`, `kb-207-group-definition-upload-filter-by-data-kind`, `kb-143-send-individual-dataset-s-to-different-splu`
- `kb-61-creating-a-custom-extractor`, `kb-214-how-to-generate-and-send-kpis-metrics`, `kb-225-how-to-generate-and-send-events`
- `kb-142-modifying-java-extractor-data-collection-in`, `kb-200-powerconnect-java-agent-host-level-scheduli`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
