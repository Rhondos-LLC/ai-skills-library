# Feed health — data missing, stale, or PowerConnect stopped sending

**Use when:** "the SAP data is stale", "the dashboard is empty", "searches
return nothing", "PowerConnect stopped sending", "one extractor is
missing", "the send queue is growing", or Step 0 found the scope empty.
**Not for:** an inventory of what is collected → [explorer.md](explorer.md).
Choosing extractors or intervals →
[extractor-config-advisor.md](extractor-config-advisor.md). SAP itself
down → [system-availability.md](system-availability.md).

Establishes where the feed broke: platform, one system, one extractor, or
the collector. The core insight: **the platform can only show a failure it
still receives.** `PC_HEALTH` is produced by the Extractor job, so it keeps
arriving when the Uploader job is stopped; but when the endpoint,
certificate or batch user fails, nothing arrives at all and the cause is
visible only in SAP. Total silence therefore ends with SAP-side checks for
a human, never with "no errors found".

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `PC_HEALTH` (`STAT`, `ERROR`, `INFO`) | ABAP | snapshot per upload target; error stream; agent info | send queue, error texts, version | yes |
| `PC_SCHEDULE` | ABAP | snapshot per extractor | last and next run, interval, active flag | yes |
| `PC_SENT_STATS` | ABAP | counter per extractor and day | bytes sent | yes |
| `PC_AUDIT` | ABAP | stream | who started or stopped jobs, changed configuration | yes |
| `PC_TRACE` | ABAP | stream | run time per extractor; only when global parameter `EXTRACT_TRACE` is on | yes |
| `agent_health` | Java, Cloud | stream of agent metrics | agent alive | yes |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `TRGNAME`, `TRGID` (PC_HEALTH STAT) | upload target; one row per target | | sample (Dynatrace) |
| `TOTAL_TO_SEND`, `TO_SEND`, `IN_ERROR` | metrics waiting (overall / this target); metrics in error | near 0 when healthy | sample (Dynatrace); docs |
| `SENT`, `SENT_TOTAL`, `LAST_SENT_DATE`+`LAST_SENT_TIME`, `LAST_METRIC_DATE`+`LAST_METRIC_TIME` | send counters; last successful send; last metric queued | old last-sent date = dead target | sample (Dynatrace) |
| `MESSAGE_PATTERN`, `MESSAGE_CODE`, `MESSAGE_COUNT`, `FIXED` (PC_HEALTH ERROR) | error text as under Administrator → Check Errors | target name and HTTP status in the text | sample (Dynatrace) |
| `RELEASE_NO`, `RELEASE_DATE`, `DB_SYS`, `OPSYS` (PC_HEALTH INFO) | PowerConnect version and its release date (`yyyymmdd`), database type, operating system | version as `major.minor` string | sample (Dynatrace) |
| `LICENCE_EXP`, `LICENCE_EOM`, `LICENCE_KIND`, `USERS_GUI`, `USERS_RFC`, `USERS_PLG` (PC_HEALTH INFO) | licence expiry (`yyyymmdd`; `LICENCE_EOM` and `LICENCE_KIND` not documented); logged-on users by GUI, RFC and plug-in type | `99991231` = no expiry date | sample (Dynatrace), meaning partly unconfirmed |
| Cloud `agent_health` fields | not seen in a record | sample first | unconfirmed |
| `GROUP_DEF`, `ACTIVE`, `COLL_INTERVAL` (PC_SCHEDULE) | extractor (= event type), on/off, interval in seconds (zero-padded string) | `ACTIVE=X` | sample (Dynatrace) |
| `LAST_RUN`, `NEXT_RUN` | `yyyymmddhhmmss`, UTC in the sample like `CURRENT_TIMESTAMP`; `LAST_DATE`+`LAST_TIME`, `NEXT_DATE`+`NEXT_TIME` are the local pairs | compare like with like | sample (Dynatrace) |
| `MTGRP`, `SBGRP`, `UDATE`, `BYTES` (PC_SENT_STATS) | extractor, subgroup, day, bytes | | sample (Dynatrace) |
| `ATEXT`, `UNAME`, `MAREA`, `OBJCT`, `SDATE`+`STIME` (PC_AUDIT) | readable action, who, area, object, local time | `MAREA=JOB`, `OBJCT=/BNWVS/BC_*` | sample (Dynatrace) |
| `OBJECT`, `RUNTIME`, `SERVER` (PC_TRACE) | extractor, seconds, instance | | sample (Dynatrace) |
| `mbean_name`, `Count`, `Mean`, `instance_id` (Java `agent_health`) | agent metric and values; Java fields keep this casing | `io.powerconnect.java:name=...` | sample (Dynatrace) |

## Investigation sequence

Work down the tree; stop at the first branch that explains the symptom.

**1. Is anything arriving, and from whom?** Run the adapter's Step 0 over
24 hours and compare SIDs and stacks with the profile.

| Result | Go to |
|---|---|
| Nothing in scope | platform first: right index / bucket, role or token can read it, ingest token valid; Splunk data present but dashboards empty = KB 165. Then step 6 |
| Every SID stale since the same minute | shared path (endpoint, proxy, certificate): step 4, then 6 |
| One SID stale | that system's collector: step 4, then 6 |
| SIDs fresh, one topic missing | step 2 |

**2. Which extractors are silent for the SID?** Run the adapter's "count
and freshness per type" idiom for that SID over 24 hours (the census query
of [explorer.md](explorer.md), Step 2). Judge each age against its record
shape; a quiet event stream is not a broken feed.

**3. Does the collector think it is extracting it?** Latest schedule row
per extractor; `NEXT_RUN` earlier than the snapshot time means overdue
(seconds are normal: the extractor loop wakes every 15 s by default). The
DQL compares the two `yyyymmddhhmmss` strings, which order correctly.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_SCHEDULE source=<SID>
| stats latest(ACTIVE) as active latest(COLL_INTERVAL) as interval_s latest(LAST_RUN) as last_run latest(NEXT_RUN) as next_run latest(CURRENT_TIMESTAMP) as seen by GROUP_DEF
| eval interval_s=tonumber(interval_s), overdue_s=strptime(seen,"%Y%m%d%H%M%S")-strptime(next_run,"%Y%m%d%H%M%S")
| sort - overdue_s
```

```dql
fetch logs, from: now() - 2h
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_SCHEDULE"
| filter log.source == "<SID>"
| sort timestamp asc
| summarize {active = takeLast(active), interval_s = takeLast(coll_interval), last_run = takeLast(last_run), next_run = takeLast(next_run), seen = takeLast(current_timestamp)}, by: {group_def}
| fieldsAdd overdue = next_run < seen
| sort next_run asc
| limit 50
```

**4. Is the send queue draining?** One series per upload target, on the
per-target `TO_SEND` (`TOTAL_TO_SEND` repeats the same overall figure on
every target row). A system can have several targets; match `TRGNAME` to
the platform you are querying before blaming an error for the gap.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_HEALTH EVENT_SUBTYPE=STAT source=<SID>
| eval to_send=tonumber(TO_SEND), in_error=tonumber(IN_ERROR)
| timechart span=15m max(to_send) as to_send max(in_error) as in_error by TRGNAME
```

```dql
fetch logs, from: now() - 24h
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_HEALTH"
| filter dt.source_entity_type == "STAT" and log.source == "<SID>"
| makeTimeseries {to_send = max(toLong(to_send)), in_error = max(toLong(in_error))}, interval: 15m, by: {trgname}
```

Then read the error texts: the same selection with subtype `ERROR`,
counted and latest time by `MESSAGE_CODE`, `MESSAGE_PATTERN`.

**5. Did someone stop it?** `PC_AUDIT` records job starts, stops and
configuration changes with the user.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_AUDIT source=<SID>
| sort - _time
| head 30
| table _time MAREA OBJCT UNAME ATEXT
```

```dql
fetch logs, from: now() - 3d
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_AUDIT"
| filter log.source == "<SID>"
| sort timestamp desc
| limit 30
| fields timestamp, marea, objct, uname, atext
```

Java and Cloud agents have no schedule event: run step 2 on `sap:java` /
`sap:cloud` by `HOST` and check `agent_health` still arrives;
the logs to collect are on `java-troubleshooting`, `cloud-troubleshooting`.
Other backends: translate each step with the profile's idioms
(see [../backends/other.md](../backends/other.md)).

**6. SAP-side checks a human runs** in `/n/BNWVS/MAIN`, productive client:

| Check | Where | If it fails |
|---|---|---|
| Three jobs green: Check `/BNWVS/BC_CHECK_JOB`, Extractor `/BNWVS/BC_DATA_EXTRACT`, Uploader `/BNWVS/BC_DATA_TRANSFER` | main screen; SM37 `/BNWVS/*` | start them: KB 169; roles and restart behaviour: KB 178 |
| Metric errors | Administrator → Check Errors | read the text; after the fix mark Fixed: KB 113 |
| Batch user locked | SU01, the job user | unlock, mark errors Fixed, restart jobs: KB 116 |
| Connection test | Administrator → Connection Setup → Upload Scheme → endpoint → Test (older: Splunk Setup) | HTTP error = URL, index or token; SSL error = certificate or firewall: KB 197 |
| Batch user authorizations | SU53 as that user | update roles, especially after upgrades: KB 197, KB 131, KB 140 |
| Extractor active | Administrator → Setup Group Def | activate: `abap-troubleshooting` |
| Dumps, job failures | red icons top right; ST22, SM37 | troubleshooting package for support: KB 97 (dump while creating it: KB 183) |

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| `PC_HEALTH` fresh, everything else stale | Uploader job stopped (PC_HEALTH bypasses it) | step 5 for who; KB 169 |
| `TOTAL_TO_SEND` climbing, `IN_ERROR` flat | target slow or throttling | "503 Server is busy" = KB 135; data is kept and resent |
| `IN_ERROR` climbing | sends rejected | error text; connection test; KB 197 |
| Queue fine, then total silence | endpoint, certificate, proxy or batch user | step 6; SSL to Splunk KB 44; Dynatrace SaaS KB 247 |
| Many extractors overdue together | Extractor job down or user locked (it blocks itself) | KB 116, KB 169 |
| Extractor absent from `PC_SCHEDULE`, or `ACTIVE` empty | not configured / switched off | [extractor-config-advisor.md](extractor-config-advisor.md) |
| Extractor active and on time, no data | nothing to report, metric filter, or authorization | KB 131 (LOGS), KB 140 (SM37 spool); version bugs KB 201 (SM59), KB 192 (STRUST_HISTORY), KB 193 (LTRC), KB 139 (AL11) |
| Unsent 0 and nothing arrives, SP 7.03 with a Target Group | known defect | KB 184 |
| `/BNWVS/MTR` table or `/BNWVS/` application log growing | unsent backlog held by retention; invalid target | KB 2; KB 190 |
| "RFC-timeout: Dest ..." in the PowerConnect log | an app server was unreachable | KB 155; informational |

## What to tell the user

- The branch that explains it, with event type, window, counts, `SID`,
  target name, and first and last timestamps of the gap.
- The SAP-side check to run and its KB. Network and certificate work is
  for the network and Basis teams; support incidents need the KB 97 package.
- On total silence, say the cause is not observable from the platform. On
  ECS/RISE apply [ecs-overlay.md](ecs-overlay.md): firewall, proxy and
  profile-parameter fixes are service requests.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| No records for a SID for 30 min | any `sap:abap` | from KB 247; the only alert that catches total silence |
| `TOTAL_TO_SEND` above its normal ceiling for 30 min | `PC_HEALTH` STAT | starting point: 5× the daytime median, per target |
| `IN_ERROR` increasing | `PC_HEALTH` STAT | against the previous hour |
| Active extractor overdue by more than 2× its interval | `PC_SCHEDULE` | starting point |
| Job stopped by a user | `PC_AUDIT` | `MAREA=JOB`; match the stop text seen in a sample |
| `agent_health` silent for 15 min | Java / Cloud | per host; starting point |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform
alert; the two generic feed alerts are in [explorer.md](explorer.md).

## Documentation

- `pc_health`, `pc_schedule`, `pc_audit`, `abap-troubleshooting`, `java-troubleshooting`, `cloud-troubleshooting`
- `kb-197-powerconnect-data-from-abap-system-not-flow`, `kb-165-out-of-the-box-dashboards-not-populating-da`, `kb-169-start-stop-powerconnect-abap-application-ba`, `kb-178-powerconnect-jobs-overview`
- `kb-116-locked-user-stopping-powerconnect-data-extr`, `kb-113-send-metrics-in-error-after-root-cause-is-f`, `kb-135-target-503-service-unavailable-server-is-bu`, `kb-155-rfc-timeout-dest-rfc-destination`, `kb-184-metrics-are-not-uploaded-to-load-balanced-t`
- `kb-44-ssl-handshake-error`, `kb-247-ssl-handshake-error-to-dynatrace-saas-ssslerr_peer_cert_untrusted`, `kb-2-table-bnwvs-mtr-is-growing-rapidly`, `kb-190-application-logs-are-growing-excessively`
- `kb-97-troubleshooting-information`, `kb-183-troubleshooting-information-dump`, `kb-131-logs-extractor-does-not-collect-necessary-d`, `kb-140-sm37-extractor-does-not-collect-spool-data`
- `kb-201-sm59-events-are-not-collected`, `kb-192-strust_history-events-are-not-collected`, `kb-193-ltrc-events-are-not-collected`, `kb-139-al11-does-not-collect-file-information`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
