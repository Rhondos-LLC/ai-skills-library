# System log and application log — SM21, SLG1, log files

**Use when:** "what errors are in the system log", "anything unusual in
SM21 since the change", "application log errors for object X", "what does
the work process trace / gateway log say", "is this message new".
**Not for:** security audit log (SM20) → [security-audit.md](security-audit.md);
short dumps → [abap-dumps.md](abap-dumps.md); Java traces and logs →
[java-stack.md](java-stack.md); gateway connectivity and RFC errors →
[rfc-and-queues.md](rfc-and-queues.md); PowerConnect's own runtime log as a
collector symptom → [feed-health.md](feed-health.md).

The core insight: **what arrives is what the metric filter lets through, so
read the filter before you read the log.** SM21_LOG sends every message
unless an administrator excluded some; SLG1 and the file-based LOGS
extractor send nothing at all until a filter names an object or a file. An
empty SLG1 result therefore means "not collected" far more often than "no
errors". Second rule: **group by message id, not by text.** Texts carry
variable parts (work process numbers, job names, users), so every line looks
unique; the id shows that 4,000 lines are one chronic message and three are new.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM21_LOG` | ABAP | event stream | system log entries per instance: message id, text, user, program, transaction | yes; optional include/exclude filter |
| `SLG1` | ABAP | event stream | application log messages with their log header: object, subobject, message class and number | extractor on, but sends only what the SLG1 filter names |
| `LOGS` | ABAP | event stream | lines of any text file on the application server (work process traces, `gw_log-*`, HTTP logs) | extractor on, but sends only files named in the Logs file filter |
| Gateway server logs | Java | event stream | gateway log lines read by the Java agent from the central services host | off; needs a Java node on the SCS host |

Filters live in `/BNWVS/MAIN` → Administrator → Metric Filters: "SM21
Sys.Log Filter" (instance, client, user, message group and sub-name, text),
"SLG1 filter" (object, subobject, user, mode, message type, class, number,
external id, time zone) and "Logs file filter" (instance, path, file name,
log format). A quiet event stream can be healthy; judge it on its history.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `AREA`, `SUBID` (SM21_LOG) | message area and sub-id; together the three-character message id | group key | sample (Dynatrace) |
| `TEXT`, `SLGDATA` | message text and its variable data | variable; use for reading, not grouping | sample (Dynatrace) |
| `DATE_INT`, `DATE`, `TIME` | entry date and time, system-local | drifts by release: some feeds send `DATE_INT` = `yyyymmdd` plus `DATE` = `dd.mm.yyyy`, others only `DATE` = `yyyymmdd`; coalesce the two | sample (Dynatrace) |
| `INSTID`, `MAND`, `USER`, `TERMINAL` | instance, client, user, terminal | | sample (Dynatrace) |
| `TRANSCODE`, `REPNA`, `DEVCLASS`, `TSKNA`, `TSKNU` | transaction, program, package, work process type and number | | sample (Dynatrace) |
| `SEVERITY`, `CLASID`, `MONKAT`, `MONBEW`; `PRIORITY` | severity and classification codes; priority text (`HIGH PRIORITY` ...), Dynatrace-derived | in Dynatrace `SEVERITY` is only at `data.severity`, not top-level | sample (Dynatrace) |
| `OBJECT`, `SUBOBJECT` (SLG1) | application log object and subobject | `/BNWVS/` = PowerConnect's own log | sample (Dynatrace), docs |
| `LOGNUMBER`, `EXTNUMBER` | log number (one log, many messages) and external id | count logs with distinct `LOGNUMBER` | sample (Dynatrace) |
| `MSGTY` | message type | `A` abort, `E` error, `W` warning, `I` information, `S` success; Dynatrace adds decoded `MSGTY_STR`, `ALMODE_STR` | sample (Dynatrace), docs |
| `MSGID`, `MSGNO`, `MSGV1`–`MSGV4`, `MESSAGE_TEXT` | message class, number, variables, rendered text | group key = `MSGID` + `MSGNO` | sample (Dynatrace) |
| `ALDATE`, `ALTIME`, `ALUSER`, `ALTCODE`, `ALPROG`, `ALMODE`, `PROBCLASSH`, `MANDANT` | log date, time, user, transaction, program, creation mode, problem class, client | mode codes `D`, `I`, `B`; quote the decoded `ALMODE_STR` | sample (Dynatrace), docs |
| `FILE_NAME`, `FILE_PATH`, `FILE_DATA`, `SEQ_NUM`, `INSTANCE_NAME` (LOGS) | file, directory, a block of lines, block order, instance | `EVENT_SUBTYPE` is the file name too (`dev_w0`, `dev_icm`, `gw_log-*`); `FILE_DATA` is large, project it for few records only | sample (Dynatrace) |
| Gateway log fields | not sampled; the gateway header defaults to `type,timestamp,message` | sample one record first | unconfirmed, docs |

## Investigation sequence

1. **Confirm the feed and what the filter admits.** One instance or one
   object only is a filter fingerprint; report it as scope, not as health.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (SM21_LOG, SLG1, LOGS) source=<SID>
| stats count max(_time) as newest dc(eval(coalesce(INSTID, INSTANCE_NAME))) as instances dc(OBJECT) as objects by EVENT_TYPE
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"SM21_LOG", "SLG1", "LOGS"})
| filter log.source == "<SID>"
| summarize {events = count(), newest = max(timestamp),
    instances = countDistinct(coalesce(instid, instance_name)), objects = countDistinct(object)}, by: {dt.source_entity_name}
```
2. **System log by message id: new or chronic.** Run over a baseline plus
   the incident window (for example seven days ending at `T_END`) and split
   at the incident start. An id with `before` = 0 is first-seen.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM21_LOG source=<SID>
| eval msg=AREA.SUBID, phase=if(_time>=<T_INCIDENT_START>,"now","before")
| stats count(eval(phase="now")) as now count(eval(phase="before")) as before
    dc(INSTID) as instances latest(TEXT) as example by msg
| where now>0 | eval class=if(before=0,"first-seen","chronic") | sort - now | head 40
```
```dql
fetch logs, from: <T_BASELINE_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM21_LOG" and log.source == "<SID>"
| fieldsAdd msg = concat(area, subid)
| summarize {now = countIf(timestamp >= toTimestamp("<T_INCIDENT_START>")),
    before = countIf(timestamp < toTimestamp("<T_INCIDENT_START>")),
    instances = countDistinct(instid), example = takeAny(text)}, by: {msg}
| filter now > 0 | sort now desc | limit 40
```
   For a chronic id compare rates, not presence: a message that tripled
   is still a finding. The split uses event time; if the entry date is far
   from it (historical load or replay), split on entry date + `TIME` instead.
3. **Application log by object and message.** Errors and aborts per
   object, subobject and message. Separate PowerConnect's own log.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SLG1 source=<SID> MSGTY IN (A, E)
| fillnull value="-" SUBOBJECT
| stats count dc(LOGNUMBER) as logs dc(ALUSER) as users latest(MESSAGE_TEXT) as example by OBJECT SUBOBJECT MSGID MSGNO
| sort - logs | head 40
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SLG1" and log.source == "<SID>" and in(msgty, {"A", "E"})
| summarize {messages = count(), logs = countDistinct(lognumber),
    users = countDistinct(aluser), example = takeAny(message_text)}, by: {object, subobject, msgid, msgno}
| sort logs desc | limit 40
```
4. **Drill into one message.** A handful of records, narrow projection,
   newest first.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM21_LOG source=<SID> AREA=<AREA> SUBID=<SUBID>
| eval DAY=coalesce(DATE_INT, DATE) | fields DAY TIME INSTID MAND USER TRANSCODE REPNA TSKNA TSKNU TEXT SLGDATA
| sort - DAY - TIME | head 10
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM21_LOG" and log.source == "<SID>"
| filter area == "<AREA>" and subid == "<SUBID>"
| fieldsAdd day = coalesce(date_int, date)
| fields day, time, instid, mand, user, transcode, repna, tskna, tsknu, text, slgdata
| sort day desc, time desc | limit 10
```
5. **Files and gateway logs.** For `LOGS`, count records per `FILE_NAME`
   and `INSTANCE_NAME` before reading any `FILE_DATA`. Only files in a format the extractor recognises carry their
   own line timestamps; others get the extraction time, so build no
   timeline from them. Gateway server logs come from the Java agent
   (`STACK` = `sap:java`); confirm the event type name by sample.
6. **Correlate.** Dumps at the same second ([abap-dumps.md](abap-dumps.md));
   the job named in `SLGDATA` ([background-jobs.md](background-jobs.md));
   instance stops and starts ([system-availability.md](system-availability.md));
   database errors ([database-health.md](database-health.md)); a first-seen
   id right after an import ([change-tracking.md](change-tracking.md)).

On any other backend, translate the intent with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| First-seen id | on one instance: local problem on that server; on all at once: shared cause (database, enqueue, message server, transport) | drill, then correlate by time |
| No `SLG1`, or only object `/BNWVS/` | SLG1 filter empty (or only PowerConnect's own log), or the log is written in a user time zone the filter does not name | say business logs are not covered; [extractor-config-advisor.md](extractor-config-advisor.md) |
| `/BNWVS/` errors growing fast, nothing uploaded | invalid upload target (KB 190, up to 7.03) or log deletion defect (KB 167, SP 7.01) | [feed-health.md](feed-health.md) |
| `LOGS` configured, no data | missing S_DATASET authorization (KB 131), deadlock on SP 7.01 (KB 168), new files not picked up on 8.02–8.05 (KB 230) | cite the KB with the agent version |
| Splunk "SAP Logs Search" panels empty on app 8.0.1 | dashboard token defect (KB 194) | trust the query, cite the KB |

## What to tell the user

- Message ids ranked by count in the window, each tagged first-seen or
  chronic, with instances affected and one example text.
- For SLG1: object, subobject, message class and number, distinct logs;
  and the filter scope you observed, so absence is not read as health.
- Where to verify: SM21, SLG1 (object, subobject), AL11 for files.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| message id not seen in the previous 7 days | `SM21_LOG` | new-message alert; low noise, high value |
| `MSGTY` `A` or `E` for a named object / subobject | `SLG1` | the object must be in the SLG1 filter |
| error pattern in a named file | `LOGS` | the file must be in the Logs file filter |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform alert.

## Documentation

- Event types — `sm21_log`, `slg1`, `logs`, `gateway-server-logs`
- KB 131, 168, 230 (LOGS extractor) — `kb-131-logs-extractor-does-not-collect-necessary-d`,
  `kb-168-logs-extractor-deadlock`, `kb-230-logs-extractor-does-not-pick-up-new-files`
- KB 167, 190, 194 — `kb-167-application-logs-cannot-be-deleted`, `kb-190-application-logs-are-growing-excessively`, `kb-194-panel-data-not-populating-on-sap-logs-searc`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
