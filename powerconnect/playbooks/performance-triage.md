# Performance triage — slow system or slow transaction

**Use when:** "the system is slow", "transaction X takes too long", "who or
what is consuming the system", "are we short of work processes".
**Not for:** host CPU, memory or disk as the question itself →
[os-resources.md](os-resources.md); database locks, statements or space →
[database-health.md](database-health.md); an instance that stopped answering
→ [system-availability.md](system-availability.md); RFC destinations or
queues → [rfc-and-queues.md](rfc-and-queues.md).

The core insight: **response time is a sum, and the largest component names
the owner.** Never report "slow" without the split into wait (queue), CPU,
database, roll, load/generation, enqueue, RFC and front-end time. Two traps
produce wrong splits: statistics records come as a main record plus
sub-records under `EVENT_SUBTYPE`, so an unfiltered count multiplies every
step; and `STAD`/`STATS` pass through a metric filter, so they are a
selection, not the whole workload. Use `ST03_TIME` for system-wide totals
and `STAD`/`STATS` for one transaction, user or program.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `ST03_TIME` | ABAP | collector batch | workload aggregates per instance, task type and hour bucket: steps, response, CPU, DB, wait, roll-wait, processing | yes |
| `ST03_RFCC`, `ST03_RFCS`, `ST03_TIME_DIST` | ABAP | collector batch | RFC client / server profile per instance (default); response-time distribution buckets (not default) | mixed |
| `STATS` | ABAP | header + detail | statistics records, new extractor (SAP_BASIS above 7.50); main record subtype `MAIN` | no |
| `STAD` | ABAP | header + detail | statistics records, classic extractor; main record subtype `MAIN`, sub-records `SUBDB`, `SUBRFCCL`, `SUBRFCSV`, `SUBHTPC`, `SUBTAB`, `SUBPASSPORT` ... | yes |
| `SM51_QUEUE` | ABAP | snapshot | dispatcher queue per request type: requests waiting for a work process | yes |
| `SM51_STATE` | ABAP | snapshot | work processes configured and busy per instance | no |
| `SDF_MON`, `SDF_SMON` | ABAP | snapshot | /SDF/MON and /SDF/SMON snapshots: CPU, work processes, memory, sessions | no |
| `STAD3`, `ABAP_METER` | ABAP | collector batch | aggregated statistics records (default); ABAP benchmark per SAP Note 2879613 (not default); neither has a documentation page | mixed |
| `WPER` | ABAP | event stream | IS-Retail POS inbound IDoc status, not work processes; use [idocs.md](idocs.md) | no |

Check first which of `STATS` and `STAD` exists; their field names differ
completely. There is no SM50 extractor: the work process list is `SM51`.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `TRANSACTION`, `PROGRAM`, `USER_NAME`, `CLIENT`, `INSTANCE_NAME`, `TASK_TYPE`, `JOB_NAME` (STATS) | who and what | `USER_NAME` = `-- ? --` means the agent user lacks authorization (KB 182) | sample (Dynatrace), docs |
| `RESPONSE_TIME` (STATS) | total response time of the step | SAP reports milliseconds; verify the unit on one record | sample (Dynatrace) |
| `WAIT_TIME`, `CPU_TIME`, `PROCESSING_TIME` | dispatcher wait, CPU, processing | | sample (Dynatrace) |
| `TOTAL_REQUEST_TIME`, `COMMIT_TIME`, `DB_PROCEDURE_TIME`, `HANA_PROCESSING_TIME` | database components | | sample (Dynatrace) |
| `ROLL_WAIT_TIME`, `ROLL_IN_TIME`, `ROLL_OUT_TIME`, `LOAD_GEN_TIME`, `ENQUEUE_TIME`, `RFC_CPIC_TIME`, `GUI_TIME`, `FE_NET_TIME` | roll, load/generation, enqueue, RFC, front end | | sample (Dynatrace) |
| `TRANSACTION_ID`, `ROOT_CONTEXT_ID`, `SESSION_ID` | correlation ids | all `#` on kernel 753 patch 201 (KB 67) | sample (Dynatrace), docs |
| `TCODE`, `PROGRAM_MAIN`, `USER_NAME`, `TRANSID`, `CONTEXT_ID`; `DBCALLS`, `DBCALLTI`, `READSEQTI`, `COMMITTI` (STAD `SUBDB`) | who and what; DB calls and times of one step | | sample (Dynatrace) |
| `TCODE`, `REPORT`, `ACCOUNT`, `MANDT`, `INSTANCE`, `TASKTYPE`, `BTCJOBNAME`, `TRANSID`, `DIALOG_STEP` (STAD `MAIN`) | who and what; the user is `ACCOUNT` and the instance is `INSTANCE`, not `INSTANCE_NAME`; `TASKTYPE` is hex (Dynatrace adds `TaskTypeName`) | `TCODE` empty for RFC and background | sample (Dynatrace) |
| `RESPTI`, `QUEUETI`, `CPUTI`, `DBCALLTI`, `PROCTI`, `ROLLTI`, `LOADTI`, `LOCKTI`, `CPICTI`, `GUITIME`, `GUINETTIME` (STAD `MAIN`) | response, wait, CPU, DB, processing, roll, load, enqueue, RFC/CPIC, GUI and front-end network time | strings, milliseconds; convert | sample (Dynatrace) |
| `WP_NO`, `WP_TYP`, `WP_STATUS`, `WP_BNAME`, `WP_REPORT`, `WP_ELTIME`, `WP_TABLE`, `WP_WAITING`, `TCODE`, `BTCJOBNAME` (SM51 subtype `""`) | work process list: number, type, status, user, program, elapsed time, table, wait reason | `WP_STATUS` text (`Waiting`, `Running` ...); subtypes `CALLSTACK` and `_METRICS_` are separate records | sample (Dynatrace) |
| `TASKTYPETEXT`, `TIME`, `DIASTEPCNT` (ST03_TIME) | task type, hour bucket (`hh--hh`), steps | | sample (Dynatrace) |
| `RESPMT`, `CPUMT`, `DBMT`, `WAITMT`, `ROLLWAITMT`, `PROCMT` | response, CPU, DB, wait, roll-wait, processing time | `*ST` twins exist (`RESPST`, `CPUST` ...); the names suggest mean and total, so check one bucket against ST03N before quoting | sample (Dynatrace) |
| `REQ_TYPE`, `REQ_WAIT`, `QUEUE_FILL_LEVEL_PEAK` (SM51_QUEUE) | waiting requests | `DIA`, `BTC`, `NOWP` | sample (Dynatrace), docs |
| `TASKTYPE` (ST03_RFCC/RFCS, ST03_USRT) | task type as hex | `01` dialog, `02` update, `04` background, `65` HTTP, `FE` RFC | docs |

## Investigation sequence

1. **Confirm feeds and subtypes.** Count per type and subtype; note
   whether `MAIN` exists and which instances report (on agent SP 7.01–7.03
   some application servers may be missing, KB 186 / KB 187).
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (STATS, STAD, ST03_TIME, SM51_QUEUE)
| fillnull value="(none)" EVENT_SUBTYPE | stats count max(_time) as newest dc(eval(coalesce(INSTANCE_NAME, INSTANCE))) as instances by source EVENT_TYPE EVENT_SUBTYPE
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"STATS", "STAD", "ST03_TIME", "SM51_QUEUE"})
| summarize {events = count(), newest = max(timestamp), instances = countDistinct(coalesce(instance_name, instance))},
    by: {log.source, dt.source_entity_name, dt.source_entity_type}
```
2. **System-wide split.** `ST03_TIME` rows are aggregates re-sent per hour
   bucket: take the latest per bucket, never sum across polls (add `TCODE`
   to the grouping if the feed carries per-transaction rows).
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST03_TIME source=<SID>
| stats latest(DIASTEPCNT) as steps latest(RESPMT) as resp latest(WAITMT) as wait
    latest(CPUMT) as cpu latest(DBMT) as db latest(ROLLWAITMT) as rollwait by INSTANCE_NAME TASKTYPETEXT TIME
| sort TASKTYPETEXT TIME
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "ST03_TIME" and log.source == "<SID>"
| sort timestamp asc
| summarize {steps = takeLast(diastepcnt), resp = takeLast(respmt), wait = takeLast(waitmt), cpu = takeLast(cpumt),
    db = takeLast(dbmt), rollwait = takeLast(rollwaitmt)}, by: {instance_name, tasktypetext, time}
```
3. **Top consumers and their split.** On `STATS` filter `MAIN` (on `STAD`
   also `MAIN`, with `RESPTI`, `QUEUETI`, `CPUTI`, `DBCALLTI`, `ROLLTI`,
   `CPICTI` by `TCODE`, `TASKTYPE`). Rank by total time, not by average
   alone. Group by user or program for "who"; filter one transaction to drill.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=STATS EVENT_SUBTYPE=MAIN source=<SID>
| fillnull value="(none)" TRANSACTION
| eval resp=tonumber(RESPONSE_TIME), cpu=tonumber(CPU_TIME), db=tonumber(TOTAL_REQUEST_TIME),
    wait=tonumber(WAIT_TIME), roll=tonumber(ROLL_WAIT_TIME), rfc=tonumber(RFC_CPIC_TIME)
| stats count as steps sum(resp) as total perc95(resp) as p95
    avg(wait) as wait avg(cpu) as cpu avg(db) as db avg(roll) as roll avg(rfc) as rfc by TRANSACTION TASK_TYPE
| sort - total | head 30
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "STATS"
    and dt.source_entity_type == "MAIN" and log.source == "<SID>"
| summarize {steps = count(), total = sum(toDouble(response_time)), p95 = percentile(toDouble(response_time), 95),
    wait = avg(toDouble(wait_time)), cpu = avg(toDouble(cpu_time)), db = avg(toDouble(total_request_time)),
    roll = avg(toDouble(roll_wait_time)), rfc = avg(toDouble(rfc_cpic_time))}, by: {transaction, task_type}
| sort total desc | limit 30
```
4. **Work process shortage.** Waiting requests per queue, one value per
   poll, then the worst poll. Read busy against total from `SM51_STATE`.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM51_QUEUE source=<SID>
| stats max(eval(tonumber(REQ_WAIT))) as max_wait dc(CURRENT_TIMESTAMP) as polls by INSTANCE_NAME REQ_TYPE
| where max_wait>0
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM51_QUEUE" and log.source == "<SID>"
| summarize {max_wait = max(toLong(req_wait)), polls = countDistinct(current_timestamp)}, by: {instance_name, req_type}
| filter max_wait > 0
```
5. **Correlate and hand off** by the dominant component (next table). Follow
   one step by `TRANSACTION_ID` into its sub-records and into `ST22`.

On any other backend, translate the intent with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Wait time dominates, `REQ_WAIT` > 0 for `DIA` | not enough free dialog work processes, or a few long steps block them | `SM51` work process list; long runners in step 3 |
| CPU dominates | across many transactions: saturated host; for one program: expensive ABAP | [os-resources.md](os-resources.md); or name the program for its owner |
| Database time dominates | slow statements, locks or DB resource shortage | [database-health.md](database-health.md) |
| Roll-wait or RFC time dominates | step waits on a remote call or the GUI | [rfc-and-queues.md](rfc-and-queues.md), `ST03_RFCC` |
| Enqueue time dominates | lock contention | [locks-and-updates.md](locks-and-updates.md) |
| Load / generation time high after a transport | program buffer reloads | [change-tracking.md](change-tracking.md) |
| Step counts doubled | KB 189 duplicates (SP 7.03) or sub-records counted | filter subtype; distinct count on `TRANSACTION_ID` + `DIALOG_STEP_NUMBER` |
| No statistics data, or only from some instances | kernel 753 transaction-id defect (KB 67), agent defect on SP 7.01–7.03 (KB 186 / 187), or the metric filter | check `TRANSACTION_ID`; [extractor-config-advisor.md](extractor-config-advisor.md) |

Starting points to tune: dialog mean response above 1 s, wait above 10 % and database above 40 % of it.

## What to tell the user

- The split in numbers for the window, the dominant component and the top
  three transactions, users or programs behind it.
- The scope: system-wide (`ST03_TIME`) or filtered sample (`STAD`/`STATS`).
- Where to verify (ST03N, STAD, SM50/SM66, ST06, ST04), the owner by
  component, and what you could not see.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `REQ_WAIT` != 0 for `DIA` or `BTC` | `SM51_QUEUE` | shipped Dynatrace alerts `davis.sap.sm51_queue.dia_wait`, `.btc_wait`; add a duration to cut noise |
| dialog mean response above baseline for 3 buckets | `ST03_TIME` | baseline per instance and hour of week |
| p95 response of a critical transaction above target | `STATS` / `STAD` | requires that transaction in the metric filter |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform alert.

## Documentation

- STAD, STATS — `stad-sap-performance-monitor-statistics-records`,
  `stats-sap-performance-monitor-statistics-records-n`
- ST03, WPER — `st03_rfcc`, `st03_rfcs`, `st03_time_dist-st03-response-time-distribution`, `wper`
- Snapshots — `sdf_mon-sap-performance-snapshot-monitoring`, `sdf_smon-new-sap-performance-snapshot-monitoring`
- KB 67, 150, 182 — `kb-67-missing-transaction-id-for-kernel-753`, `kb-150-no-result-found-in-st03-user-profile-dashbo`, `kb-182-stats-missing-user-name-value`
- KB 186, 187, 189 — `kb-186-stad-extractor-does-not-collect-metrics-fro`, `kb-187-stats-extractor-does-not-collect-metrics-fr`, `kb-189-stad-extractor-sends-duplicated-events`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
