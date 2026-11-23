# PowerConnect footprint — is the collector loading the SAP system?

**Use when:** "PowerConnect is raising dumps", "PowerConnect jobs are
queueing / filling the job overview", "the extractor hits TIME_OUT",
"PowerConnect ran out of memory", "is PowerConnect causing this slowdown",
"prove PowerConnect did not cause the incident", "what does PowerConnect
cost the system".
**Not for:** data not arriving → [feed-health.md](feed-health.md); changing
what is collected → [extractor-config-advisor.md](extractor-config-advisor.md);
a slow system with no suspicion on the collector →
[performance-triage.md](performance-triage.md).

The core insight: **PowerConnect's own work is identifiable, so measure its
share before blaming or clearing it.** Everything it runs lives in the
`/BNWVS/` namespace (jobs, programs, classes) and runs under its batch
user, and the system's own telemetry (ST22, SM37, SM51, STAD) records it
like any other workload. An absolute number ("788 dumps", "40 jobs") says
nothing until it is set against the system total and against which
extractor produced it. Second trap: extraction runs in **dialog** work
processes through parallel RFC, capped by the global parameter
`MAX_PARALLEL_PROCESS` (default 10% of dialog tasks), so its pressure shows
in dialog queues, not only in background jobs.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `ST22` subtype `""` | ABAP | event stream | dumps in `/BNWVS/` programs | yes |
| `SM37` subtype `""` | ABAP | header + detail | PowerConnect's jobs, their state and volume | yes |
| `SM51` subtype `""` | ABAP | snapshot | work processes occupied by `/BNWVS/` programs | yes |
| `STAD` subtype `MAIN` (or `STATS`) | ABAP | event stream | time and CPU consumed under the batch user; subject to the STAD metric filter | yes |
| `PC_TRACE` | ABAP | event stream | run time per extractor; only when global parameter `EXTRACT_TRACE` is on | no |
| `PC_SCHEDULE`, `PC_HEALTH` | ABAP | snapshot | interval per extractor; send queue and errors; version | yes |

PowerConnect's standard jobs (KB 178): `/BNWVS/BC_CHECK_JOB` (watchdog,
every 5 min, under 5 min), `/BNWVS/BC_DATA_EXTRACT` and
`/BNWVS/BC_DATA_TRANSFER` (dispatchers, run about 24 h, do no heavy work),
`/BNWVS/DISTRIBUTE_PARALLEL` (send jobs, under 5 min, count capped by
`UPLOAD_JOB_COUNT`), `/BNWVS/BC_DATA_ARCHIVE` (hourly, under 20 min). A
dispatcher that has run for hours is normal, not a hung job.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `PROGRAMNAME`, `SRC_MAIN_PROGRAM` (ST22) | terminated program and its main program | contain `/BNWVS/` for collector dumps; the class name tells the extractor (`/BNWVS/CL_EXT_<TYPE>`) | sample (Dynatrace) |
| `DUMPID`, `DATUM`, `UZEIT`, `UNAME` (ST22) | runtime error, local date and time, user | | sample (Dynatrace) |
| `JOBNAME`, `JOBCOUNT`, `JOBSTATE` (SM37 header) | job, run, state text | `Aborted/Failed`, `Finished`, `Running`, `Ready`, `Scheduled` | sample (Dynatrace) |
| `AUTHCKNAM` (SM37 `STEP`) | step user = the PowerConnect batch user | customer-specific; read it once and reuse it below as `<PC_USER>` | sample (Dynatrace) |
| `WP_REPORT`, `WP_BNAME`, `WP_TYP`, `WP_STATUS`, `INSTANCE_NAME` (SM51) | program, user, type and state of each work process | idle processes show `Waiting` | sample (Dynatrace) |
| `REPORT`, `ACCOUNT`, `RESPTI`, `CPUTI`, `DBCALLTI` (STAD `MAIN`) | program, user, response, CPU and DB time in ms | | sample (Dynatrace) |
| `OBJECT`, `RUNTIME`, `SERVER` (PC_TRACE) | extractor, seconds, instance | | sample (Dynatrace) |
| `GROUP_DEF`, `INTERVAL`, `ACTIVE` (PC_SCHEDULE) | extractor, run interval, on/off | | sample (Dynatrace) |
| `RELEASE_NO` (PC_HEALTH `INFO`) | installed PowerConnect version | needed for every KB check | sample (Dynatrace) |

## Investigation sequence

1. **Fix the window and the identity.** Take the incident window from the
   user, or one hour ending at `T_END`. Read the batch user from one SM37
   `STEP` record of a `/BNWVS/` job and the version from PC_HEALTH `INFO`.
2. **Dumps: collector share and signature.** Group collector dumps by
   runtime error and program, and count all dumps beside them.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST22 source=<SID> DUMPID=*
| eval pc=if(like(PROGRAMNAME,"%/BNWVS/%") OR like(SRC_MAIN_PROGRAM,"%/BNWVS/%"),"PowerConnect","other")
| eval dump=DATUM.UZEIT.UNAME.MODNO
| stats dc(dump) as dumps min(DATUM) as first max(DATUM) as last by pc DUMPID PROGRAMNAME | sort - dumps
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "ST22" and dt.source_entity_type == "" and log.source == "<SID>"
| filter isNotNull(dumpid) and dumpid != ""
| fieldsAdd pc = if(contains(programname, "/BNWVS/") or contains(src_main_program, "/BNWVS/"), "PowerConnect", else: "other")
| summarize {dumps = countDistinct(concat(datum, uzeit, uname, modno)), first = min(datum), last = max(datum)}, by: {pc, dumpid, programname}
| sort dumps desc | limit 30
```
3. **Jobs: volume and failures.** Latest state per run of every `/BNWVS/`
   job. Many `DISTRIBUTE_PARALLEL` runs in `Ready` or `Scheduled` state is a
   send backlog, not an extraction problem.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM37 source=<SID> JOBNAME="/BNWVS/*" NOT EVENT_SUBTYPE IN (STEP, LOGS, SPOOL, SPOOLID, VARIANT)
| stats latest(JOBSTATE) as state by JOBNAME JOBCOUNT | stats count as runs by JOBNAME state | sort JOBNAME - runs
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM37" and dt.source_entity_type == "" and log.source == "<SID>"
| filter startsWith(jobname, "/BNWVS/")
| sort timestamp asc
| summarize {state = takeLast(jobstate)}, by: {jobname, jobcount}
| summarize {runs = count()}, by: {jobname, state} | sort jobname asc, runs desc
```
4. **Work processes: occupancy per slot.** Count distinct work processes
   seen busy in each 5-minute slot, then take the peak. A slot holds
   several polls, so counting rows would multiply the figure.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM51 source=<SID> WP_NO=* WP_STATUS!="Waiting"
| eval pc_wp=if(like(WP_REPORT,"/BNWVS/%") OR WP_BNAME="<PC_USER>",WP_NO,null())
| bin _time span=5m | stats dc(pc_wp) as pc_busy dc(WP_NO) as busy by _time INSTANCE_NAME WP_TYP
| stats max(pc_busy) as pc_peak max(busy) as busy_peak avg(pc_busy) as pc_avg by INSTANCE_NAME WP_TYP
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM51" and dt.source_entity_type == "" and log.source == "<SID>"
| filter isNotNull(wp_no) and wp_no != "" and wp_status != "Waiting"
| fieldsAdd pc_wp = if(startsWith(wp_report, "/BNWVS/") or wp_bname == "<PC_USER>", wp_no)
| summarize {pc_busy = countDistinct(pc_wp), busy = countDistinct(wp_no)}, by: {slot = bin(timestamp, 5m), instance_name, wp_typ}
| summarize {pc_peak = max(pc_busy), busy_peak = max(busy), pc_avg = avg(pc_busy)}, by: {instance_name, wp_typ}
```
5. **Workload share.** Sum response, CPU and DB time of statistics records
   under `<PC_USER>` or a `/BNWVS/` program against the system total for the
   same window. If the STAD metric filter excludes the batch user, the
   share reads zero; say so instead of reporting "no load".
6. **Which extractor.** With `PC_TRACE` on, rank `OBJECT` by total and
   maximum `RUNTIME`. Without it, use the class name in the dump
   (`/BNWVS/CL_EXT_<TYPE>`) and the job step, then read that extractor's
   `INTERVAL` in PC_SCHEDULE: a heavy extractor on a short interval is the
   usual cause.
7. **Queue and storage.** PC_HEALTH `STAT`: rising `TO_SEND` or `IN_ERROR`
   means unsent metrics are accumulating in PowerConnect's tables, which
   is what leads to memory dumps and table growth (see feed-health).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| `TIME_OUT` in `/BNWVS/CL_EXT_<TYPE>` | one extractor reads too much per run (authorization and user extractors on large systems are typical) | lengthen its interval or narrow it with a metric filter; extractor-config-advisor |
| "No more storage space" / `TSV_TNEW_PAGE_ALLOC_FAILED` in a `/BNWVS/` program | result set or send queue too large for work process memory | check the queue (step 7); KB 2; reduce volume before raising memory |
| Dump in `/BNWVS/SAPLPARALLEL_PROCESSING` | known issue | KB 38 |
| `ITAB_ILLEGAL_SORT_ORDER` (SUIM), `DBSQL_SQL_ERROR` on ASE, `ITAB_DUPLICATE_KEY` in SLM | known issues | KB 203, KB 176, KB 224 |
| Dumps or failed jobs start right after an upgrade or role import | missing authorizations for the batch user | KB 162, KB 110; change-tracking for the transport time |
| Hundreds of `DISTRIBUTE_PARALLEL` runs | target slow or rejecting, uploads piling up | feed-health; `UPLOAD_JOB_COUNT` in KB 178 |
| PowerConnect holds a large share of dialog processes at peak | `MAX_PARALLEL_PROCESS` too generous for this system, or many extractors aligned on the same minute | KB 84; stagger with KB 180 |
| Collector share is small in every measure | PowerConnect is not the cause | say so with the numbers; continue in performance-triage |
| Identical dump re-sent every poll | the feed re-sends the record | count distinct dumps, as the queries do |

## What to tell the user

- PowerConnect's share in numbers: dumps, job runs, peak work processes
  and, where available, response and CPU time, each against the system
  total for the same window.
- The extractor responsible, its interval, and the KB that matches.
- The recommended change and where it is made (`/BNWVS/MAIN` →
  Administrator), for a Basis administrator to carry out.
- What to attach if a support ticket is still needed: PowerConnect version
  and the troubleshooting dump (KB 97, KB 183).
- What you could not see: `PC_TRACE` off, STAD filter excluding the batch
  user, SM51 poll interval longer than the spike.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Distinct dumps in `/BNWVS/` programs above 10 per hour | `ST22` | starting point; alert on the count, not on each dump |
| A `/BNWVS/` job in `Aborted/Failed` state | `SM37` header | the watchdog restarts dispatchers, so alert on repeats |
| PowerConnect holds more than a set share of dialog processes for 15 min | `SM51` | derive the share from this system's history |
| An extractor's `RUNTIME` exceeds its `INTERVAL` | `PC_TRACE`, `PC_SCHEDULE` | needs `EXTRACT_TRACE` |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- KB 178 - PowerConnect jobs overview — `kb-178-powerconnect-jobs-overview`
- KB 84 - Global configuration parameters — `kb-84-global-configuration-parameters`
- KB 180 - Add Delay to Data Extraction — `kb-180-add-delay-to-data-extraction`
- KB 2 - Table BNWVS MTR is Growing Rapidly — `kb-2-table-bnwvs-mtr-is-growing-rapidly`
- KB 38, KB 176, KB 203, KB 224 (dumps) — `kb-38-abap-dump-in-bnwvs-saplparallel_processing`, `kb-176-dbsql_sql_error-abap-dumps-sybase`, `kb-203-itab_illegal_sort_order-abap-dumps-suim`, `kb-224-itab_duplicate_key-dump-in-slm-control-pane`
- KB 162, KB 110 (authorizations) — `kb-162-authorization-objects-related-issues`, `kb-110-new-batch-user-profile-when-upgrading-to-po`
- KB 97, KB 183 (troubleshooting dump) — `kb-97-troubleshooting-information`, `kb-183-troubleshooting-information-dump`
- ABAP Troubleshooting — `abap-troubleshooting`
