# PowerConnect data model (backend-neutral)

PowerConnect agents (ABAP, Java, Cloud) extract SAP data on a schedule and
send each record as one flat JSON event to the configured platform. The
content is the same everywhere; only the envelope and the field-name casing
change. Playbooks use the **logical names** below. The backend adapter tells
you what each one is called on your platform.

## Logical fields carried by every event

| Logical name | Meaning | Splunk | Dynatrace |
|---|---|---|---|
| `EVENT_TYPE` | Which extractor produced the record (ST22, SM37, WE02, ...) | `EVENT_TYPE` field, or the suffix of `sourcetype=sap:abap:<TYPE>` | `dt.source_entity_name` (also `event_type`) |
| `EVENT_SUBTYPE` | Record kind inside a type (SM37 `STEP`/`LOGS`, PC_HEALTH `INFO`/`STAT`/`ERROR`) | `EVENT_SUBTYPE` | `dt.source_entity_type` (also `event_subtype`) |
| `SID` | SAP system ID | `source` | `log.source` |
| `HOST` | Application server that produced the record (absent on some system-wide types such as AL08, which carry an instance name field instead) | `host` | `host.name` |
| `STACK` | Which agent family | `sourcetype` (`sap:abap`, `sap_abap`, `sap:java`, `jmx`, `sap:cloud`) | `service.name` (`sap:abap`, `sap:java`, `sap:cloud`) |
| `EXTRACTED_AT` | Extraction time, `yyyymmddhhmmss`. Its time zone is not uniform: treated as system-local on Splunk feeds, but equal to the UTC event time in sampled Dynatrace records. Compare it with the platform event time once and note the result in the profile | `CURRENT_TIMESTAMP` | `current_timestamp` |
| `UTC offset` | Offset of system-local time from UTC | `UTCDIFF`, `UTCSIGN` | `utcdiff`, `utcsign` |
| `CLIENT` | SAP client, on the few types that carry it (some use `CLIENT` instead, for example NRIV) | `MANDT` | `mandt` |

SAP payload fields keep their SAP technical names (`JOBNAME`, `JOBCOUNT`,
`DOCNUM`, `VBSTATE`, ...). They are UPPERCASE in Splunk and lowercase in
Dynatrace. Playbooks write them in UPPERCASE; apply the adapter's casing.
Java agent fields are the exception: they keep the agent's own mixed case
(`mbean_name`, `Count`, `OneMinuteRate`) on every platform.
ABAP event types are UPPERCASE (`SM37`); Java and Cloud event types are
lowercase (`jmx`, `cpi_message`).

Some platforms add **derived fields** that do not exist in the raw record
(for example Dynatrace's `older_than_24h` on SM12 or `cert_days_to_expiry`
on Java certificates). Playbooks mark these with the platform they belong
to. Do not expect them elsewhere; compute the value instead.

## Three record shapes — the shape dictates the query

1. **Event streams** — one record per occurrence (WE02 status transitions,
   ST22 dumps, SM20 / SM21_LOG / SLG1 messages, SM37 log lines).
   An entity's current state is its *latest* record per entity key. Never
   count raw rows as entities.
2. **Snapshots** — the collector polls current state (SMQ1/SMQ2 queues,
   SM12 locks, SM51/SM50 work processes, SM04/AL08 sessions, ST06).
   The lookback must exceed the poll cadence. Per-entity state is the latest
   record by entity key. Never sum or average across snapshots without first
   reducing to one value per poll. A missing row means "not seen in this
   poll", not "gone".
3. **Header + detail**, discriminated by `EVENT_SUBTYPE` (SM37 uses empty,
   `STEP`, `LOGS`, `SPOOL`; STAD uses `MAIN` / `SUB*`). Always filter the
   subtype explicitly and count runs with a distinct count on the run id
   (for example distinct `JOBCOUNT`), because headers re-emit on every poll
   while the object is active.

## Field behaviour that bites every investigation

- **Numbers are often strings.** Convert before comparing or doing
  arithmetic (the adapter gives the function).
- **Dates and times are split, system-local pairs** (`STRTDATE` +
  `STRTTIME`, `yyyymmdd` + `hhmmss`). Compare local pairs to local pairs or
  to `EXTRACTED_AT`. Never mix a local string with the platform's event
  time unless you apply the UTC offset.
- **Unpopulated fields are `???` or an empty string, not null.** Test for
  those values explicitly.
- **Field shapes drift across PowerConnect releases** (SMQ2 depth is
  `ENTRIES` on some feeds and `QDEEP` on others; job logs may be inline or
  separate `LOGS` records). When a documented field returns nothing, pull
  one record, look at what is there and adapt. Never conclude "no data"
  from a field name you have not seen in a sample.
- **KPI records share the event type.** Newer releases also emit records
  with `EVENT_SUBTYPE` = `_METRICS_` (`NAME`, `VALUE`, `UNIT`,
  `DIMENSIONS`) under the same event type. They carry no entity fields, so
  require the entity key to be present (non-empty) before a
  latest-per-entity reduction, or they pollute the result.
- **Entity keys are only unique within one SID.** Restrict to one system
  or add the SID to every group-by key.
- **Snapshot types can carry a second subtype.** SMQ1, SMQ2 and SM58 also
  emit `STATISTICS` records; select the subtype you mean before reducing.
- **Cloud agent records differ.** They have lowercase field names on every
  platform and no `EXTRACTED_AT` or UTC offset fields; use the platform
  event time.
- **Metric filters shape the data.** Many extractors only send what an
  administrator has allowed in `/BNWVS/MAIN` → Administrator → Metric
  Filters (SM37 job logs, SM20 and SM21 messages, STAD records, WE02). An
  absent job log or audit message may be filtered out at the source. The
  per-event documentation page describes the filter.

## Time: anchor on the data, not on the clock

The platform's event time says when the record arrived. When the thing
happened in SAP is in payload fields (`DATUM`/`UZEIT`, `DATE_INT`/`TIME`,
`STRTDATE`/`STRTTIME`). On replayed or demo feeds the two can be far apart;
use the payload time for "when did it happen" and the event time for
windowing queries.


Take `T_END` = the newest SAP event found in Step 0. Express every window
relative to `T_END` as absolute timestamps. Seeded, replayed or lagging
feeds are often hours old, and a window of "last 8 hours" then returns
nothing. Only when `T_END` is within 10 minutes of now may you use relative
time ranges.

## Feed freshness — judge against the record shape

| Class | Types (typical) | Expected cadence | Verdict rule |
|---|---|---|---|
| Snapshots | SMQ1/SMQ2, SM12, SM50/SM51, SM04/AL08, SPAD_STATUS, ST06 | poll every 5–15 min | age < 2× cadence = LIVE; 2–6× = LAGGING; > 6× = DEAD |
| Collector batches | SM37, STAD, ST03_*, CCMS, NRIV | 5–60 min | same rule against the observed cadence |
| Event streams | WE02, ST22, SM20, SM21_LOG, SLG1 | only when something happens | judge against that system's own history and business hours, never a fixed age |
| Low-cadence inventories | SLICENSE, SE06, STMS_TPLOG, STMS_ALERT, PC_SENT_STATS | every few hours to daily | look back at least 6–24 h before calling them absent |
| Collector self-telemetry | PC_HEALTH, PC_SCHEDULE, PC_SENT_STATS, `agent_health` | continuous | absence or silence here explains every other gap |

An event stream that is quiet may be healthy. A snapshot that is quiet is a
broken feed.

## Generic method when no playbook fits

1. Find the event type in [event-types.md](event-types.md) by SAP
   transaction or topic.
2. Confirm it is collected: count records and newest timestamp for that
   type in the profile scope.
3. Sample one record with all fields. Identify the entity key, the state
   field, the time fields and the record shape.
4. Read the event's documentation page (see
   [../playbooks/docs-qa.md](../playbooks/docs-qa.md)) for its use cases and
   metric filter.
5. Aggregate in the backend according to the record shape, then drill into
   at most a handful of concrete records.
6. Report with event type, window, counts and identifiers, and state which
   field names you confirmed by sample.
