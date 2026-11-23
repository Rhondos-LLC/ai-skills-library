# User activity and Fiori — who is logged on, what they use, what fails

**Use when:** the user asks who is logged on, how many concurrent users
there are and how that trends, sessions by client, terminal or SAP GUI
version, what a user or group of users is doing, which Fiori apps and
OData services are used, or which gateway errors users are hitting.
**Not for:** slow transactions → [performance-triage.md](performance-triage.md)
· suspicious logons, public ICF services →
[security-audit.md](security-audit.md) · dormant users, roles →
[user-and-authorization-review.md](user-and-authorization-review.md) ·
licensed user counts (KB 152, RSUSR200) →
[certificates-and-licenses.md](certificates-and-licenses.md) · Java
portal and web sessions in depth → [java-stack.md](java-stack.md)

The core insight: **`AL08` and `SM04` are snapshots, so every poll lists
every session again.** Counting rows gives sessions × polls, which looks
like thousands of users. Reduce each poll to one number first (distinct
users in that poll), then trend that number. Also, a session list is not a
list of people: it contains batch, RFC and system sessions, so decide
which session types count as "users" before you report a figure.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `AL08` | ABAP | snapshot | logged-on users across all instances, current transaction | yes |
| `SM04` | ABAP | snapshot | sessions per application server with type, terminal, GUI version, memory | yes |
| `STATS` | ABAP | header + detail | per-step statistics on NetWeaver 7.50+; subtype = subrecord name | no; STATS record filter |
| `STAD` | ABAP | header + detail | per-step statistics, `MAIN` / `SUB*` | yes; filter-limited |
| `FLP_MONITOR` | ABAP | event stream | Fiori launchpad usage from the PowerConnect plugin | plugin and role needed (KB 134) |
| `GW_ERROR_FND`, `GW_ERROR_BEP` | ABAP | event stream | gateway hub and backend error log | yes |
| `GW_TRACE_STATS`, `ODATA_TRACE` | ABAP | event stream | gateway and OData call statistics | varies |
| `ODATA_SERVICE` | ABAP | configured | rows read *from* an OData entity set | no; OData Service filter |
| `SM05` | ABAP | snapshot | HTTP security sessions and logon method | check; not in the bundled catalog |
| `SICFCHK` | ABAP | snapshot or delta | public ICF services, services with logon data | yes |
| `portal_activity_log`, `web_session` | Java | stream / snapshot | portal page hits; Java web sessions | KB 41 setup for portal |

Two traps. `ODATA_SERVICE` is a data reader like `TREAD_DYN` (see
[business-process.md](business-process.md)); it says nothing about who
calls OData services. `FLP_MONITOR` only sees users assigned the
monitoring catalog role, so its user count is a lower bound.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `AL08`: `USERNAME`, `MANDT`, `TCODE`, `TERM_NAME`, `INSTANCE_NAME` | user, client, current transaction, terminal, instance | | sample (Dynatrace) |
| `AL08`: `EXT_SESSION`, `INT_SESSION`, `DIALOG_TIME` | session counters, time of last dialog step (`hhmmss`) | | sample (Dynatrace) |
| `SM04`: `BNAME` (also `USER_NAME`), `MANDT`, `TCODE`, `TERM`, `HOSTADDR` | user, client, transaction, terminal, client IP | `HOSTADDR` seen as `0.0.0.0` on a batch session | sample (Dynatrace) |
| `SM04`: `SESSION_TYPE`, `EXT_STYPE`, `EXT_TYPE`, `TYPE`, `RFC_TYPE` | what kind of session | seen: `SESSION_TYPE` `GUI`, `RFC`, `BATCH`, `Background`, `SYSTEM`, `BGRFC Scheduler` or empty (spelling varies by release), `EXT_TYPE` `System`; list the rest by grouping | sample (Dynatrace) |
| `SM04`: `GUIVERSION`, `PROTOCOL`, `APPLICATION` | SAP GUI version, protocol, application | empty on non-GUI sessions | sample (Dynatrace) |
| `SM04`: `INSTANCE_NAME`, `SESSION_KEY`, `LOGON_ID`, `SESSIONS` | entity key = instance + session key | | sample (Dynatrace) |
| `SM04`: `ZEIT`, `EXT_TIME`, `ACT_PROGRAM`, `APPL_INFO`, `TOTAL_MEM_KB` | last activity, running program, session memory | numbers are strings | sample (Dynatrace) |
| `STATS`: `USER_NAME`, `TOTAL_REQUEST_TIME`, `HANA_PROCESSING_TIME` | user and timings | `USER_NAME` = `-- ? --` when the collector user lacks authorization (KB 182); the HANA field is absent on S/4HANA 2020 and older (KB 158) | docs |
| `GW_ERROR_*`: `ERROR_CONTEXT` | optional XML context, off unless configured | payload; do not quote | docs |
| `SM05`: `MAX_ENTRIES`, `USED_ENTRIES`, `PERCENTAGE`, `STAT_TEXT` | security session cache size, entries used, percent used, the same as text | only subtype `STATISTICS` seen; no per-session records | sample (Dynatrace) |
| `SICFCHK`: `ICF_NAME`, `IO_PATH_FROM`, `ICFACTIVE`, `ICF_USER`, `ICF_MANDT`, `PROTSEC` | service node, its path, active flag, stored logon user and client, security setting | subtypes seen: empty and `WITH_LOGON` (services with logon data) | sample (Dynatrace) |

`GW_ERROR_*`, `ODATA_SERVICE` and `FLP_MONITOR` returned no data when
sampled; the Java types were not sampled. Their field names are
unconfirmed: use the names you find in a record.

## Investigation sequence

1. **Confirm the feeds.** Count and newest record for the types above.
   `AL08` / `SM04` silent = broken feed; `GW_ERROR_*` silent may simply
   mean no errors, so check that it has history at all.
2. **Sample one `AL08` and one `SM04` record** and note the poll cadence
   (gap between consecutive `CURRENT_TIMESTAMP` values).
3. **Concurrent users over time.** Bucket at the poll cadence so each
   bucket holds one poll, count distinct users, then trend the peak.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=AL08
| bin _time span=<CADENCE>
| stats dc(USERNAME) as users by _time source
| bin _time span=1h
| stats max(users) as peak avg(users) as typical by _time source
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "AL08"
| summarize users = countDistinct(username), by: {poll = bin(timestamp, 5m), log.source}
| summarize {peak = max(users), typical = avg(users)}, by: {hour = bin(poll, 1h), log.source}
| sort hour asc
```

   Use the observed cadence for `5m` / `<CADENCE>`; a bucket wider than
   one poll counts everyone seen in it and overstates concurrency.
4. **Sessions right now, by client, type and GUI version.** Look back two
   poll intervals, keep the latest record per session, then group.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM04
| stats latest(MANDT) as client latest(SESSION_TYPE) as stype latest(GUIVERSION) as gui latest(BNAME) as user by source INSTANCE_NAME SESSION_KEY
| fillnull value="(none)" gui stype
| stats count as sessions dc(user) as users by source client stype gui
| sort - sessions
```
```dql
fetch logs, from: "<T_END - 2 polls>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SM04"
| sort timestamp asc
| summarize {client = takeLast(mandt), stype = takeLast(session_type), gui = takeLast(guiversion), user = takeLast(bname)}, by: {log.source, instance_name, session_key}
| summarize {sessions = count(), users = countDistinct(user)}, by: {log.source, client, stype, gui}
| sort sessions desc
```

   For terminals, group by `TERM` or `HOSTADDR` and report counts only.
5. **What users do** (activity, not speed). Use `STATS` where it exists,
   else `STAD`. Sample first to find the subtype of the main record and
   the transaction field, then count steps and distinct transactions per
   `USER_NAME`, excluding `-- ? --`. Statistics are filter-limited: a
   user missing here may be outside the record filter, not inactive.
6. **Fiori usage and gateway errors.** Usage: count `FLP_MONITOR`
   records by the app field found in a sample. Errors: group the error
   log by service and error text, with first and last occurrence. To tie
   a hub (`FND`) entry to its backend (`BEP`) entry, look for a request
   or transaction id present in both samples; do not assume its name.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (GW_ERROR_FND, GW_ERROR_BEP)
| stats count min(_time) as first max(_time) as last dc(<USER_FIELD>) as users by source EVENT_TYPE <SERVICE_FIELD> <ERROR_TEXT_FIELD>
| sort - count
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"GW_ERROR_FND", "GW_ERROR_BEP"})
| summarize {errors = count(), first = min(timestamp), last = max(timestamp), users = countDistinct(<user_field>)}, by: {log.source, dt.source_entity_name, <service_field>, <error_text_field>}
| sort errors desc
```

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| "Users" far above the headcount | rows counted across polls, or system sessions included | redo with step 3; filter session types |
| `AL08` and `SM04` disagree | `AL08` is system-wide per user, `SM04` per server per session | state which one you used |
| Many sessions with empty `GUIVERSION` | RFC, HTTP or batch sessions | split by `SESSION_TYPE` before judging GUI versions |
| `USER_NAME` = `-- ? --` | collector user lacks `S_TOOLS_EX` / `S_ADMI_FCD` `STAU` | KB 182; cannot attribute activity until fixed |
| `STATS` absent | system below NetWeaver 7.50 or filter empty | use `STAD` |
| Few Fiori users in `FLP_MONITOR` | role not assigned to everyone, or ICF nodes inactive | KB 134 |
| One gateway error text dominates | a single service or app is failing | `/IWFND/ERROR_LOG`, `/IWBEP/ERROR_LOG`; check dumps and backend RFC |
| "HTTP security context cache is full" in the system log | session cache exhausted | `SM05` free-session percentage; SM05 |

## What to tell the user

- Peak and typical figures, how they were reduced (per poll, which
  session types) and the window; named users only if the question needs
  them.
- Where to verify: AL08, SM04, SM05, STAD, `/IWFND/ERROR_LOG`.
- What you could not see: unsampled types, filter-limited statistics,
  Fiori users without the monitoring role.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Concurrent users above or far below the weekday baseline | `AL08` | snapshot: evaluate per poll, baseline from history |
| Gateway errors per service above baseline | `GW_ERROR_FND` / `GW_ERROR_BEP` | stream: throttle per service |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform
alert.

## Documentation

- Sessions: `al08`, `sm04`, `sm05-http-security-session-monitoring`
- STATS: `stats-sap-performance-monitor-statistics-records-n`,
  `kb-182-stats-missing-user-name-value`,
  `kb-158-splunk-overall-statistics-table-not-renderi`,
  `kb-157-splunk-user-filter-not-working-in-fiori-sta`
- Gateway and OData: `gw_error_fnd-sap-gateway-frontend-error-log`,
  `gw_error_bep-sap-gateway-backend-error-log`, `odata_service`,
  `sicfchk-sicf-sap-internet-communication-framework-`
- Setup and licensing: `kb-134-sap-fiori-user-monitoring`,
  `kb-41-enabling-portal-activity-data-collector`,
  `kb-152-determine-active-user-count-for-powerconnec`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
