# ABAP dumps — ST22 short dumps

**Use when:** "are there dumps", "why so many dumps today", "what is this
runtime error", "which program / user / job is dumping", "did the dumps
start after the transport".
**Not for:** the job that cancelled → [background-jobs.md](background-jobs.md);
system log messages around it → [system-log.md](system-log.md); what was
transported → [change-tracking.md](change-tracking.md); Java exceptions →
[java-stack.md](java-stack.md).

The core insight: **a dump count is not an incident count.** One failing
job step, interface or user retry loop writes hundreds of identical dumps,
while a single new signature in a quiet program can be the real incident.
Always reduce to signatures (runtime error + program) first, then separate
a storm (a signature far above its own history) from the steady background
every system carries. And **project fields on every query**: an ST22 record
is 5–10 KB because it carries the source excerpt and long texts.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `ST22` | ABAP | event stream | one record per short dump (subtype `""`): runtime error, program, include and line, user, client, instance, job, texts, source excerpt. Detail subtypes (`DBI_ERROR` seen) repeat the dump key without `DUMPID`; filter the empty subtype | yes |
| `SM37` | ABAP | header + detail | the job run a dump belongs to (`JOBNAME` + `JOBCOUNT`) | yes |
| `SM21_LOG` | ABAP | event stream | system log around the dump time | yes |
| `E070`, `STMS` | ABAP | event stream | transports imported before the first dump of a signature | yes |

ST22 is an event stream: a quiet feed can be healthy. Judge freshness
against the system's own history, and if `ST22` has never arrived say it is
a coverage gap.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `DUMPID` | runtime error name | e.g. `TIME_OUT`, `MESSAGE_TYPE_X`, `TSV_TNEW_PAGE_ALLOC_FAILED`, `DBSQL_SQL_ERROR` (SAP names) | sample (Dynatrace), docs |
| `EXCEPTION` | exception class, if one was raised | may be empty | sample (Dynatrace) |
| `PROGRAMNAME`, `INCLUDENAME`, `LINENUMBER` | terminated program, include and line | signature = `DUMPID` + `PROGRAMNAME` | sample (Dynatrace) |
| `SRC_MAIN_PROGRAM`, `SRC_APP_COMP`, `SRC_DEV_CLASS` | main program, application component, package | component names the SAP support queue or the custom owner | sample (Dynatrace) |
| `DATUM`, `UZEIT` | dump date and time, system-local | the record's event time can be the extraction time (it was in the sample); use these for "when" | sample (Dynatrace) |
| `UNAME`, `MANDT` | user and client | | sample (Dynatrace) |
| `AHOST`, `INSTANCE_NAME` | application server instance | | sample (Dynatrace) |
| `MODNO` | internal mode number; with `DATUM`, `UZEIT`, `AHOST`, `UNAME`, `MANDT` it identifies one dump | | sample (Dynatrace) |
| `JOBNAME`, `JOBCOUNT` | background job run, empty for dialog | join key to SM37 | sample (Dynatrace) |
| `TRX_TRANSACTION`, `TRX_TRANSACTION_ID`, `TRX_ROOT_CONTEXT_ID` | transaction code and passport ids | join to `STATS` / `STAD` | sample (Dynatrace) |
| `CATEGORY_TEXT`, `TXT_SHORT_DESCRIPTION` | category and one-line description | short enough to return | sample (Dynatrace) |
| `TXT_WHAT_HAPPEND`, `TXT_ERROR_ANALYSIS`, `SRC_SOURCE`, `BS_INT_HINT` | long texts and source excerpt | large; fetch for one dump only | sample (Dynatrace) |
| `RFC_*` (`RFC_DST`, `RFC_FUN`, `RFC_WHO` ...) | RFC context | `???` or `-` when the dump was not in an RFC | sample (Dynatrace) |

## Investigation sequence

1. **Confirm the feed.** Count and newest `ST22` record; widen to seven
   days before calling it absent, since hours without a dump are normal.
2. **Reduce to signatures** (runtime error + program) with a distinct dump key, which guards against re-sent records.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST22 source=<SID>
| eval dump=DATUM.UZEIT.coalesce(AHOST,"").coalesce(UNAME,"").coalesce(MODNO,"")
| stats dc(dump) as dumps dc(UNAME) as users dc(JOBNAME) as jobs
    min(DATUM) as first_day max(DATUM) as last_day by DUMPID PROGRAMNAME
| sort - dumps | head 30
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "ST22" and dt.source_entity_type == "" and log.source == "<SID>"
| fieldsAdd dump = concat(datum, uzeit, ahost, uname, modno)
| summarize {dumps = countDistinct(dump), users = countDistinct(uname),
    first_day = min(datum), last_day = max(datum)}, by: {dumpid, programname}
| sort dumps desc | limit 30
```
3. **Storm or background.** Run step 2 over a baseline (the seven days
   before the window) and compare per signature. A signature absent from
   the baseline is new; one at many times its daily baseline is a storm;
   the rest is background. For the shape of a storm, bucket by dump hour:
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST22 source=<SID> DUMPID=<DUMPID>
| eval dump=DATUM.UZEIT.coalesce(AHOST,"").coalesce(UNAME,"").coalesce(MODNO,""), hour=DATUM." ".substr(UZEIT,1,2)
| stats dc(dump) as dumps dc(UNAME) as users by hour | sort hour
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "ST22" and dt.source_entity_type == "" and log.source == "<SID>"
| filter dumpid == "<DUMPID>"
| fieldsAdd dump = concat(datum, uzeit, ahost, uname, modno),
    hour = concat(datum, " ", substring(uzeit, from: 0, to: 2))
| summarize {dumps = countDistinct(dump), users = countDistinct(uname)}, by: {hour}
| sort hour asc
```
4. **Drill into one signature.** A handful of records, narrow projection.
   Fetch the long texts for a single dump only if the short description
   does not explain it.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST22 source=<SID> DUMPID=<DUMPID> PROGRAMNAME=<PROGRAM>
| fields DATUM UZEIT UNAME MANDT INSTANCE_NAME INCLUDENAME LINENUMBER EXCEPTION
    JOBNAME JOBCOUNT TRX_TRANSACTION SRC_APP_COMP TXT_SHORT_DESCRIPTION
| sort - DATUM - UZEIT | head 10
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "ST22" and dt.source_entity_type == "" and log.source == "<SID>"
| filter dumpid == "<DUMPID>" and programname == "<PROGRAM>"
| fields datum, uzeit, uname, mandt, instance_name, includename, linenumber,
    exception, jobname, jobcount, trx_transaction, src_app_comp, txt_short_description
| sort datum desc, uzeit desc | limit 10
```
5. **Correlate.**
   - **Jobs:** when `JOBNAME` is populated, look up the same `JOBNAME` +
     `JOBCOUNT` in `SM37` ([background-jobs.md](background-jobs.md)). A
     cancelled run with a dump at its end time is cause and effect.
   - **System log:** `SM21_LOG` on the same instance within a minute of
     `DATUM` + `UZEIT` ([system-log.md](system-log.md)); both are
     system-local, so compare them directly.
   - **Change:** if a signature is new, find its first `DATUM` + `UZEIT`
     and look for transports imported shortly before it
     ([change-tracking.md](change-tracking.md)). Name the package or
     component from the dump so the search is narrow.
   - **Memory dumps** (`TSV_TNEW_PAGE_ALLOC_FAILED`, `SYSTEM_NO_ROLL`):
     continue in [os-resources.md](os-resources.md);
     **`DBSQL_*` / `DBIF_*`**: [database-health.md](database-health.md).

On any other backend, translate the intent with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| One signature, one user or job, hundreds of dumps | retry loop or a periodic job failing every run | step 5 jobs; stop the loop at its source |
| One signature, many users, sudden start | system-wide cause: transport, DB or memory problem | step 5 change and system log |
| Many signatures rising together | shared resource exhausted | [os-resources.md](os-resources.md), [database-health.md](database-health.md) |
| Signature present every day at a flat rate | background noise, known defect | report as chronic; owner by `SRC_APP_COMP` |
| `TIME_OUT` in dialog | long-running step hit `rdisp/max_wprun_time` | [performance-triage.md](performance-triage.md) |
| Program or include starts with `/BNWVS/` | PowerConnect's own code | match against KB 38, 176, 203, 224 and the agent version; [docs-qa.md](docs-qa.md) |
| `DATUM` far older than the record's event time | re-sent or historical load | use `DATUM`/`UZEIT`, not event time |

Known PowerConnect dumps: `UNCAUGHT_EXCEPTION` in
`/BNWVS/SAPLPARALLEL_PROCESSING` (KB 38, stale shared memory);
`DBSQL_SQL_ERROR` on Sybase ASE, agent 6.00–7.00 (KB 176);
`ITAB_ILLEGAL_SORT_ORDER` in `/BNWVS/CL_SUIM_TOOLS_MC`, 7.03–8.01, CUA
systems (KB 203); `ITAB_DUPLICATE_KEY` in `/BNWVS/CL_SLM_LANDSCAPE`,
8.00–8.04 (KB 224).

## What to tell the user

- Signatures ranked by distinct dumps, each tagged new, storm or chronic,
  with window, counts, first and last dump time and affected users or jobs.
- Program, include, line and application component of the leading one.
- Where to verify: ST22 (same date, user, program); SM37 for the job.
- The owner (custom code team, SAP component, Basis) and the next action.
- What you could not see: long texts not fetched, no baseline, no SM37.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| any dump (`DUMPID` not null) | `ST22` | shipped Dynatrace alert `davis.sap.st22.dump`; noisy on busy systems |
| distinct dumps per signature above N in 15 min | `ST22` | storm alert; start with N = 20 and tune |
| signature not seen in the previous 7 days | `ST22` | new-signature alert; best after releases |
| dump with `JOBNAME` of a critical job | `ST22` | pair with the job-failed alert |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform alert.

## Documentation

- ST22 — `st22`
- KB 38 dump in /BNWVS/SAPLPARALLEL_PROCESSING — `kb-38-abap-dump-in-bnwvs-saplparallel_processing`
- KB 176 DBSQL_SQL_ERROR (Sybase) — `kb-176-dbsql_sql_error-abap-dumps-sybase`
- KB 203 ITAB_ILLEGAL_SORT_ORDER (SUIM) — `kb-203-itab_illegal_sort_order-abap-dumps-suim`
- KB 224 ITAB_DUPLICATE_KEY (SLM) — `kb-224-itab_duplicate_key-dump-in-slm-control-pane`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
