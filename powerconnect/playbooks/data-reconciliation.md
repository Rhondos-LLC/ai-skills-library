# Data reconciliation — SAP shows one thing, the platform another

**Use when:** "the record is in SAP but not in Splunk / Dynatrace", "the
newest rows are missing", "events arrive hours or days late", "we get
duplicates", "the value in the platform differs from the SAP screen", "the
counts do not match".
**Not for:** nothing arriving at all, or a whole extractor silent →
[feed-health.md](feed-health.md); deciding what to collect →
[extractor-config-advisor.md](extractor-config-advisor.md).

The core insight: **name the kind of difference before looking for a
cause, and never search by time first.** Every record carries up to four
times that are easy to confuse: when it happened in SAP (payload date and
time, system-local), when PowerConnect extracted it (`EXTRACTED_AT`), the
platform's event time, and when the platform ingested it. A record
"missing from the last hour" is very often present with an event time
somewhere else. Find the record by its **business key** over a wide window
first; only then decide whether it is missing, late, duplicated or altered.

You cannot see SAP. The SAP side of the comparison comes from the user: the
table or transaction, the key of one or two example records, their SAP
timestamp, and a row count for a stated window (SE16).

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| the event type in question | any | any | the records being compared | n/a |
| `PC_SCHEDULE` | ABAP | snapshot | whether and how often that extractor runs | yes |
| `PC_HEALTH` `STAT` / `ERROR` | ABAP | snapshot | unsent metrics and send errors per target | yes |
| `PC_HEALTH` `INFO` | ABAP | snapshot | installed version, to match version-specific KBs | yes |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| business key | what identifies one SAP record (`DOCNUM`, `JOBNAME`+`JOBCOUNT`, table key fields) | take it from a one-record sample, not from memory | per type |
| payload date / time | when it happened in SAP, system-local | names vary: `DATUM`/`UZEIT`, `DATE`/`TIME`, `STRTDATE`/`STRTTIME`, a table's own timestamp field | per type |
| `CURRENT_TIMESTAMP` | extraction time; equals the UTC event time in sampled Dynatrace records, and is a string on some systems, a number on others | | sample (Dynatrace) |
| `UTCDIFF`, `UTCSIGN` | system offset from UTC | needed to compare payload time with event time | sample (Dynatrace) |
| `GROUP_DEF`, `ACTIVE`, `INTERVAL`, `LAST_RUN`, `NEXT_RUN` (PC_SCHEDULE) | extractor, on/off, interval, last and next run (UTC) | | sample (Dynatrace) |
| `TO_SEND`, `IN_ERROR`, `TRGNAME` (PC_HEALTH `STAT`) | waiting and failed metrics per target | | sample (Dynatrace) |

## Investigation sequence

1. **Get the SAP reference** from the user (table, example keys, SAP
   timestamp, count for a window) and sample one platform record of the
   type to learn the key and time field names.
2. **Find the example by key over a wide window.** Report all three times
   side by side. This single step settles most cases.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=<TYPE> source=<SID> <KEY_FIELD>="<KEY>"
| eval event_time=strftime(_time,"%F %T"), indexed=strftime(_indextime,"%F %T")
| table event_time indexed CURRENT_TIMESTAMP <DATE_FIELD> <TIME_FIELD> EVENT_SUBTYPE host
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "<TYPE>" and log.source == "<SID>"
| filter <key_field> == "<KEY>"
| fields timestamp, current_timestamp, <date_field>, <time_field>, dt.source_entity_type, utcdiff, utcsign
| sort timestamp asc | limit 20
```
3. **Late: measure the lag for the whole type.** Compare the SAP time with
   the event time. The payload time is system-local, so subtract the UTC
   offset from the result before judging it.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=<TYPE> source=<SID> <DATE_FIELD>=*
| eval lag_min=round((_time-strptime(<DATE_FIELD>.<TIME_FIELD>,"%Y%m%d%H%M%S"))/60,0)
| stats count median(lag_min) as median perc95(lag_min) as p95 max(lag_min) as max
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "<TYPE>" and log.source == "<SID>"
| filter isNotNull(<date_field>) and <date_field> != ""
| fieldsAdd sap_local = concat(<date_field>, <time_field>)
| parse sap_local, "TIMESTAMP('yyyyMMddHHmmss'):t_sap"
| fieldsAdd lag_min = toLong(timestamp - t_sap) / 60000000000
| summarize {records = count(), median = median(lag_min), p95 = percentile(lag_min, 95), max = max(lag_min)}
```
4. **Duplicates: count copies per key and SAP time.** Decide from the
   record shape whether copies are expected: snapshots and active headers
   repeat on every poll by design; an event stream should not.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=<TYPE> source=<SID> <KEY_FIELD>=*
| stats count as copies dc(CURRENT_TIMESTAMP) as extractions by <KEY_FIELD> <DATE_FIELD> <TIME_FIELD>
| where copies>1 | stats count as duplicated_keys max(copies) as worst avg(extractions) as avg_extractions
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "<TYPE>" and log.source == "<SID>"
| filter isNotNull(<key_field>) and <key_field> != ""
| summarize {copies = count(), extractions = countDistinct(current_timestamp)}, by: {<key_field>, <date_field>, <time_field>}
| filter copies > 1
| summarize {duplicated_keys = count(), worst = max(copies), avg_extractions = avg(extractions)}
```
   `extractions` equal to `copies` means the record was extracted again on
   each run (delta logic or a replay); `extractions` of 1 with several
   copies means it was sent or ingested more than once.
5. **Missing: walk the path.** Is the extractor active and when did it last
   run (PC_SCHEDULE)? Are metrics waiting or in error (PC_HEALTH)? Does a
   metric filter or a per-connection filter exclude the record? Does the
   extractor's delta logic skip it (see the table)?
6. **Different value: find where it changed.** Compare the raw payload
   with the displayed field. On Dynatrace read `content` or `data.<field>`
   beside the top-level field; on Splunk compare `_raw` with the extracted
   field.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Record found, event time far from where the user looked | time-axis confusion: the dashboard charts SAP time, the search window uses event time (or the reverse) | explain the three times; widen the window or chart on event time |
| Lag equals the UTC offset | local time compared with UTC | apply `UTCDIFF` / `UTCSIGN` |
| Old records keep arriving (statistics, change documents) | SAP wrote them late, or the extractor is catching up after a stop (`MAX_INTERVAL_MULTIPLIER`, KB 84) | compare with `LAST_RUN`; expected after downtime |
| Newest table rows never arrive (TREAD_DYN or a custom table) | rows are committed after the extraction window closed | add an extraction delay, KB 180; time-based extraction, KB 75 |
| TREAD_DYN re-sends the whole table every run | date/timestamp delta ignored because no select condition is maintained | KB 196 |
| TREAD_DYN event time is "now" for some rows | long timestamp field with microseconds above 499 | KB 220 |
| STAD duplicates on ABAP 7.03 | known defect | KB 189 |
| Duplicates from two PowerConnect Cloud nodes | both nodes collected the same input | KB 244 on delivery semantics; clustering and checkpoint settings |
| Duplicates after a replay or historical load | intended re-send | `replaying-data`, KB 127 |
| CDPOS change documents missing for some objects | known extractor limitation | KB 138 |
| `IN_ERROR` above zero and the record absent | the send failed; data is held until marked fixed | KB 113 |
| Splunk field empty although `_raw` has it | event longer than the 10,240-character extraction limit | KB 89 |
| Splunk shows sourcetype `httpevent` and no fields | endpoint path ends in `/services/collector/raw` | KB 185 |
| Dynatrace `status` or `loglevel` differs from SAP | the platform's own log fields overwrite the payload names | read `json_status` or `data.status`; see the Dynatrace adapter |
| Dynatrace derived value looks wrong (ages, durations, percentages) | pipeline calculation, often an unapplied UTC offset | recompute from raw fields; report as a possible defect |
| Cloud input field missing | field mapping is an allow-list; unmapped fields are dropped | `field-mapping` |
| Counts differ but every sampled key is present | the SAP count and the platform count use different windows or include repeats | count distinct keys over the same SAP-time window |

## What to tell the user

- The kind of difference (missing, late, duplicate, altered) and the
  evidence: the example key with its three times, the lag figures, or the
  duplicate counts.
- The cause if a row above matches, with the KB; otherwise the point on the
  path where the record was last seen.
- The change that fixes it and who makes it (PowerConnect administrator,
  platform administrator, or Rhondos support for a suspected defect).
- For a support ticket: version, event type, example keys, the three times
  and the troubleshooting dump (KB 97).
- What you could not verify: anything on the SAP side that the user did
  not supply.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Median lag of a business-critical type above its normal value | the type | derive normal from two weeks of history |
| Copies per key above 1 on an event-stream type | the type | exclude snapshot and header shapes |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- KB 75 - Time-Based Extraction — `kb-75-time-based-extraction`
- KB 180 - Add Delay to Data Extraction — `kb-180-add-delay-to-data-extraction`
- KB 196, KB 220 (TREAD_DYN) — `kb-196-tread_dyn-date-timestamp-field-ignored-when`, `kb-220-tread_dyn-timestamp-issue-in-records-with-l`
- KB 189 - STAD extractor sends duplicated events — `kb-189-stad-extractor-sends-duplicated-events`
- KB 244 - PowerConnect Cloud delivery semantics — `kb-244-powerconnect-cloud-scalability-resiliency-and-delivery-semantics`
- KB 113 - Send Metrics in Error After Root Cause is Fixed — `kb-113-send-metrics-in-error-after-root-cause-is-f`
- KB 138 - CDPOS extractor — `kb-138-cdpos-extractor-does-not-collect-change-doc`
- KB 89, KB 185 (Splunk extraction) — `kb-89-splunk-kv-extraction-limit`, `kb-185-automatic-field-extraction-stopped-after-up`
- KB 84, KB 127, KB 97 — `kb-84-global-configuration-parameters`, `kb-127-splunking-historical-data`, `kb-97-troubleshooting-information`
- Replaying Data, Field mapping — `replaying-data`, `field-mapping`
