# Backend adapter — Dynatrace

Use this when the SAP data is in Dynatrace (Grail) and you have a Dynatrace
MCP server exposing `execute-dql`.

## Where the data is

PowerConnect sends every record to the Dynatrace Log ingest API, so SAP
events are **log records** processed by the PowerConnect OpenPipeline
pipeline.

| Logical name | Dynatrace field |
|---|---|
| `STACK` | `service.name` — `sap:abap`, `sap:java`, `sap:cloud` |
| `EVENT_TYPE` | `dt.source_entity_name` (duplicate: `event_type`) — UPPERCASE for ABAP (`SM37`), lowercase for Java and Cloud (`jmx`, `cpi_message`) |
| `EVENT_SUBTYPE` | `dt.source_entity_type` (duplicate: `event_subtype`) |
| `SID` | `log.source` |
| `HOST` | `host.name` |
| `EXTRACTED_AT` | `current_timestamp` (`yyyymmddhhmmss`; in sampled records it equals the UTC `timestamp`, while split date/time pairs such as `sdldate`/`sdltime` are system-local) with `utcdiff`, `utcsign` |
| Event time | `timestamp` |

- **Payload fields are lowercase** SAP technical names (`jobname`,
  `jobcount`, `vbstate`, `qstate`). Lowercase every field name a playbook
  writes in UPPERCASE. Java agent fields keep mixed case (`Count`,
  `OneMinuteRate`); copy those exactly from a sample.
- `host.name` is not reliable: several types and some feeds omit it (seen
  missing on SM51, CCMS, ST22, STATS, SM21_LOG, AL08). Check a sample, and
  fall back to the payload's instance field (`instance_name`, `name`,
  `instid`) or `log.source` as the grouping key.
- **`status` and `loglevel` are Dynatrace's own log fields**, not SAP
  payload, and can read `ERROR` on a healthy record. When the SAP record
  has a field of the same name, the SAP value moves: to `json_status` on
  SM37 headers, to a derived field on others (`state`, `jobstate`,
  `msg_state`, `custom_status`), or it survives only as `data.status`
  (WE02). Sample once to see which.
- **The pipeline can replace raw fields with derived ones** (SM12
  `gtdate`/`gttime` become `lock_start_ts`; SM21_LOG `severity` becomes
  `priority`). If a documented field is missing at top level, look under
  `data.`. Treat derived flags as hints and cross-check them against the
  raw value: a sampled SM12 record had `older_than_24h` = 0 on a lock
  several days old; ST06 `free_mem` is kilobytes although the shipped alert
  compares it with 10 (the percentages are `total_mem` = free % and
  `ram_util` = used %); `swap_util` can go negative.
- `current_timestamp` is a string on some systems and a number on others;
  wrap it in `toLong()` before comparing. Derived timestamps such as STRUST
  `time_to_expire` are durations (divide by `24h` for days).
- Each record also carries the same fields under a `data.` prefix and the
  raw JSON in `content`. Use the top-level fields, and `data.` only for
  the cases above.
- The pipeline adds entity links (`dt.entity.sap:abap:system`,
  `dt.smartscape.ext_sap_*`) and some **derived fields** used by the
  shipped alerts, for example `older_than_24h` (SM12), `cert_days_to_expiry`
  (Java `certificate`), `ccms_avail_perc` (CCMS), `jvm_heap_util` (`jmx`).
  A derived field exists only if the pipeline version installed produces
  it; confirm by sample.
- Some tenants also carry service names with a longer form such as
  `sap:abap:<sid>:<type>`. Match with `startsWith(service.name, "sap:")`
  when orienting, then use the exact value you observed.

## Replayed and demo feeds

Some tenants carry replayed SAP data next to live systems. Signs: payload
dates years away from the event time, instance names that belong to
another SID, the same record re-sent on every poll, subtypes truncated to
15 characters. On such a feed counts over time are inflated and restart or
age figures are meaningless. Say so, deduplicate on the entity key, and
take field names from a live system when one exists.

## Step 0 — Orient

```dql
fetch logs, from: now() - 30m
| filter startsWith(service.name, "sap:")
| summarize {events = count(), newest = max(timestamp)}, by: {service.name, log.source}
| sort events desc
```

`T_END` is the largest `newest`. State stack(s), SIDs and data age in one
line. This is the most expensive query you will run, because the prefix
filter does not prune the scan; keep it at 30 minutes. If nothing returns,
widen in steps (2 h, then 24 h) before concluding the feed is absent, and remember that an empty result can also mean the token lacks
permission to read the bucket.

## Query idioms

| Need | DQL |
|---|---|
| Select an event type | `fetch logs, from: <start>, to: <end> \| filter service.name == "sap:abap" and dt.source_entity_name == "<TYPE>"` |
| Restrict to a system | `\| filter log.source == "<SID>"` |
| Sample one record | `... \| fieldsRemove content, "data*", "dt.*" \| limit 1` (drop the `fieldsRemove` when you need a `data.` field) |
| Project fields | `\| fields timestamp, host.name, log.source, <field>, <field>` |
| Count and freshness per type | `\| summarize {events = count(), newest = max(timestamp)}, by: {dt.source_entity_name}` |
| Latest state per entity | `\| summarize {state = takeLast(<state>), seen = max(timestamp)}, by: {<key>}` (sort by `timestamp asc` first) |
| Distinct runs | `\| summarize runs = countDistinct(<run_id>), by: {<group>}` |
| Numeric comparison | `\| filter toDouble(<field>) > 90` (or `toLong`) |
| Text match | `matchesValue(<field>, "<value>")`, `matchesPhrase(<field>, "<phrase>")`, `contains(<field>, "<text>")` |
| Value in a list | `in(<field>, {"<A>", "<B>"})` (keep the braces; without them the query runs with a notification) |
| Unpopulated value | `<field> != "???" and <field> != "" and isNotNull(<field>)` |
| Time series | `\| makeTimeseries count(), interval: 15m, by: {<field>}` |
| Absolute window | `from: "2026-01-31T08:00:00Z", to: "2026-01-31T12:00:00Z"` |

Rules for the latest-per-entity idiom:

- Guard the entity key with `isNotNull(<key>) and <key> != ""`. Empty
  strings are not null, and KPI or queue records share the event type.

- `takeLast()` skips nulls, so each field can come from a different
  record. When fields must belong together (state and its error text),
  reduce with `sort timestamp desc | dedup <key>` instead.
- Tenants often hold several SIDs, and document numbers, queue names and
  instance names repeat across them. Filter to one `log.source` first, or
  add `log.source` to the key.

## Tool hygiene

- **Queries are billed by bytes scanned.** Always filter on `service.name`
  and `dt.source_entity_name` first, and keep the window as short as the
  question allows. Measured on a busy tenant: an unfiltered scan read about
  2 GB per 15 minutes (9 GB per hour); filtering on `service.name` plus
  SID or event type read 0.3–0.9 GB per hour; a three-day filtered sample
  read up to 14 GB. Time window is the main cost lever, so start at one
  hour and widen only when the result is empty. Windows of 24 hours or
  more belong in scheduled alerts, not in ad hoc investigation.
- Always pass an explicit `from:` (and `to:` when anchoring on `T_END`).
- **Prefix filters do not prune the scan.** `startsWith(dt.source_entity_name,
  "HDB_")` over one hour of `sap:abap` read 7.6 GB; equality or
  `in(dt.source_entity_name, {...})` on exact type names read about 0.3 GB
  per type.
- Do not put `LOGS`, `STAD`, `STATS` or `SLG1` in a multi-type inventory
  query: they are the largest types, and `LOGS` uses the file name as its
  subtype, which explodes a group-by.
- Keep results small: `limit` ≤ 50 for tables; always `| fields` before
  returning records, because each record carries every field twice plus the
  raw JSON.
- Write the DQL yourself and run it with `execute-dql`. Do not use
  `create-dql` to turn a question into a query; it hands the reasoning to
  another model. `explain-dql` is fine for explaining a query you wrote.
- If a query errors on a field name, sample one record and correct the
  name; do not retry unchanged.
- Never call a tool that creates or changes settings, documents, pipelines
  or workflows unless the user explicitly asked for that change.

## Platform features worth knowing

- **Shipped alerts** are Davis event processors in the OpenPipeline log
  pipeline. Each raises a `CUSTOM_ALERT` Davis event against the SAP
  instance entity when a record matches its DQL matcher. The matchers are a
  reliable source of field names and state values; see the alert-builder
  playbook. Existing problems can be read with the Dynatrace MCP problem
  tools (`query-problems`, `get-problem-by-id`).
- **Shipped dashboards** are imported from the PowerConnect Dynatrace app.
  See the dashboard-finder playbook.
- The Dynatrace app has its own **AI Agent** section; this skill is
  independent of it.
