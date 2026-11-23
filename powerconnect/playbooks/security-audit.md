# Security audit — SM20 audit log, suspicious logons, privileged activity

**Use when:** "who logged on as SAP* or DDIC?", "failed logons on PRD",
"was the audit log deleted or switched off?", "who downloaded data?",
"was anyone debugging in production?", "one user from many terminals", "is
Read Access Logging collected?", or a security detection needs checking.
**Not for:** roles, authorizations, default passwords →
[user-and-authorization-review.md](user-and-authorization-review.md);
transports, parameters, table changes → [change-tracking.md](change-tracking.md);
who is logged on, for operations →
[user-activity-and-fiori.md](user-activity-and-fiori.md); general SM21
errors → [system-log.md](system-log.md).

The core insight: **SM20 holds only what two filters let through.** SAP
writes an audit event only if the SM19 audit configuration selects it, and
PowerConnect forwards it only if the SM20 metric filter allows it. "No
failed logons found" proves nothing until you have shown that the event
class is audited (SM19) and that other SM20 events arrive from the same
system and client. Check the configuration before reporting a clean result.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM20` | ABAP | event stream | security audit log messages | yes |
| `SM19` | ABAP | snapshot | audit configuration: which messages are selected | yes |
| `SM04`, `AL08` | ABAP | snapshot | sessions: user, terminal, address (logon context) | yes |
| `SM21_LOG` | ABAP | event stream | system log; debug, dynamic parameter and SM59 changes | yes |
| `SE37_LOG` | ABAP | event stream | function modules run manually in SE37 | yes |
| `SM69` | ABAP | event stream (delta) | external OS command definitions changed | yes |
| `SBDLOG` | ABAP | snapshot | RFC function and SICF service usage (S/4HANA 2022+) | yes |
| `DEVACCESS` | ABAP | snapshot | users holding developer keys | yes |
| `SM05` | ABAP | snapshot | HTTP security sessions and logon method | check |
| `SRAL` | ABAP | event stream | Read Access Logging records | yes, but empty until RAL is configured (KB 132) |

`SM69` sends only commands changed since the last run unless its metric
parameter `SNAPSHOT` is set. `SRAL` stays empty until logging purposes,
recordings and a configuration exist in `SRALMANAGER`, enabled per client.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `MSG` (SM20) | audit message id = `ALGAREA` + `ALGSUBID` | `AU1` dialog logon ok, `AU2` dialog logon failed, `AU5` RFC/CPIC logon ok, `AU6` RFC/CPIC logon failed, `AUM` user locked after failed logons, `AU3`/`AU4` transaction start ok/failed, `AUY` download, `AUE` audit configuration changed | field: sample (Dynatrace); ids other than `AU5`: SAP |
| `ALGUSER`, `ALGCLIENT` | user and client of the event | | sample (Dynatrace) |
| `ALGLTERM`, `IPADDRESS` | terminal (often an address) and IP | `IPADDRESS` may be empty | sample (Dynatrace) |
| `ALGTCODE`, `ALGREPNA`, `ALGTEXT` | transaction, program, resolved message text | | sample (Dynatrace) |
| `TXSUBCLSID`, `TXSEVERITY` | audit class and severity as text | `RFC/CPIC Logon`, `Low` | sample (Dynatrace) |
| `ALGDATE`, `ALGTIME`, `ALGINST`, `PARAM1`..`PARAM4` | system-local date and time, instance, message variables (logon type, method) | `category` = copy of `MSG`, Dynatrace-derived | sample (Dynatrace) |
| `RSLGNO`, `SELREC`, `SECCLASS`, `SEVERITYC`, `TXT` (SM19) | message id, selected flag, class, severity, text per filter | `SELREC` = `X` selected; subtypes seen: `DYNAMIC_F1`, `DYNAMIC_F2`, `STATIC_F1`, `STATIC_F2` (one per filter slot; docs also name `PROFILE`, `FILTERS`) | sample (Dynatrace) |
| `BNAME`, `MANDT`, `TERM`, `HOSTADDR`, `SESSION_TYPE`, `INSTANCE_NAME` (SM04) | user, client, terminal, address, session kind, server | background sessions have empty `TERM` | sample (Dynatrace) |
| `TEXT`, `USER`, `TERMINAL`, `TRANSCODE`, `REPNA`, `MAND`, `DATE`, `TIME`, `INSTID` (SM21_LOG) | message text, user, terminal, transaction, program, client, system-local date and time, instance | | sample (Dynatrace) |
| `UNAME`, `DATA_SOURCE`, `DATA_CLIENT` (DEVACCESS) | user holding a developer key, where the entry comes from | | sample (Dynatrace) |
| `USERNAME`, `CLIENT`, `CHANNEL_ID`, `LOG_ID`, `READ_STATUS`, `REMOTE_IP`, `CREATED_AT` (SRAL) | who read what through which channel; `LOG_ID` joins the detail subtypes | subtypes seen: empty (header), `DATA`, `ENVT` (`NAME`, `VALUE`) | sample (Dynatrace) |
| `MAX_ENTRIES`, `USED_ENTRIES`, `PERCENTAGE`, `STAT_TEXT` (SM05) | security session cache size and usage | only subtype `STATISTICS` seen; no per-session records | sample (Dynatrace) |
| SE37_LOG, SM69, SBDLOG fields | | no record seen; sample one record first | unconfirmed |

## Investigation sequence

1. **Confirm the feed and its limits.** Count SM20 by system and client,
   then check that SM19 selects the message you are about to search for.
   SM20 is an event stream, so judge quietness against its own history.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM19
| stats latest(SELREC) as selected latest(TXT) as text by source EVENT_SUBTYPE RSLGNO
| search RSLGNO IN ("AU1","AU2","AU5","AU6","AUM","AUY","AUE")
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM19"
| filter in(rslgno, {"AU1", "AU2", "AU5", "AU6", "AUM", "AUY", "AUE"})
| sort timestamp asc
| summarize {selected = takeLast(selrec), text = takeLast(txt)}, by: {log.source, dt.source_entity_type, rslgno}
```

2. **Profile what the audit log contains** before filtering on any id:
   the same selection on `SM20` with `| stats count dc(ALGUSER) by MSG
   TXSUBCLSID TXSEVERITY` (DQL: `summarize count(), by: {msg, txsubclsid,
   txseverity}`). It shows the ids and classes present on this release.
3. **Run the detection family the question is about.** On Splunk with the
   Enterprise Security content pack installed, the shipped correlation
   search and its notable events are the preferred source: they carry the
   customer's tuning and the "Next Steps" text. Use the generic patterns
   below when the pack is absent, on Dynatrace, or to verify a notable.

| Family | Event type | Generic pattern | Shipped correlation search |
|---|---|---|---|
| Failed logons | `SM20` | `MSG` in `AU2`, `AU6`, `AUM`; count by user and terminal | Account Multiple Login Failures |
| Privileged logon | `SM20` | logon ids with `ALGUSER` exactly `SAP*` or `DDIC` | Privileged Account Login |
| Audit log deleted or reconfigured | `SM20`, `SM19` | `ALGTEXT="*audit*"` / `contains(lower(algtext), "audit")` by user, `MSG`, text; `SM19` `SELREC` changes | Audit Log Deletion |
| Downloads | `SM20` | `MSG` = `AUY` or `ALGTEXT` containing "download" | File Downloads |
| Debug mode | `SM21_LOG` (also `SM20` `ALGTEXT` "debug") | `TEXT` containing "debug" | Debug Mode Execution |
| OS commands | `SM69` | every record is a created or changed command | OS Command Change |
| Many terminals / geos | `SM04` | `TERM` not empty; distinct `TERM` / `HOSTADDR` by `BNAME`, `MANDT` > 1; reverse for users per terminal | One Account Many Terminals, Many Accounts One Terminal, One Account Many Geos |
| Transaction failures; manual function modules | `SM20`; `SE37_LOG` | `MSG` = `AU4` by user; count by user and function module | Account High Transaction Failure; Manual Function Module Execution |

   Failed logons (threshold 5 is a starting point to tune):

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM20 MSG IN ("AU2","AU6","AUM")
| stats count dc(ALGLTERM) as terminals max(_time) as last by source ALGCLIENT ALGUSER
| where count >= 5
| sort - count
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM20"
| filter in(msg, {"AU2", "AU6", "AUM"})
| summarize {failures = count(), terminals = countDistinct(alglterm), last = max(timestamp)}, by: {log.source, algclient, alguser}
| filter failures >= 5
| sort failures desc
```

   For the other families apply the pattern from the table with the same
   skeleton. Two traps: match privileged users literally
   (`| where ALGUSER="SAP*" OR ALGUSER="DDIC"`; `alguser == "SAP*"` in
   DQL) because `SAP*` as an SPL search term is a wildcard that also
   matches every user starting with SAP; and SM04 is a snapshot, so
   distinct terminals per user over a window means "seen in the window",
   not simultaneous, unless you also group by `CURRENT_TIMESTAMP`.

4. **Drill** into at most a handful of events for one user: project time,
   `MSG`, `ALGTEXT`, `ALGTCODE`, `ALGLTERM`, `ALGINST`. Build the timeline
   from `ALGDATE` + `ALGTIME` (system-local), not from the platform time.
5. **Correlate** on user + client + system-local time: `SM04` (session
   open, from where), `STAD` (sensitive transactions), `SUIM` (role granted
   just before), `SM21_LOG` (debug and parameter messages).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| No SM20 rows for a family | not audited, or filtered by PowerConnect | Step 1; ask for the SM20 metric filter (`/BNWVS/MAIN` → Metric Filters → SM20 Audit log filter) |
| SM20 present, only RFC logons | dialog classes not selected in SM19 | report as an audit coverage gap |
| Failures across many users from one terminal | password spraying or a broken shared client | escalate to security with terminal and window |
| Audit-configuration message, then silence | audit switched off or filters reduced | compare `SM19` before and after; escalate |
| Collector user dominates counts | PowerConnect's own RFC logons | exclude that user explicitly and say so |

## What to tell the user

- The finding with event type, window, counts, system and client, and the
  message ids matched. State which SM19 selection you verified.
- Name users, terminals and addresses only as far as the question needs;
  for a posture question give counts and the top few. Never paste records.
- Where a human verifies it: SM20 (or RSAU_READ_LOG), SM19 (RSAU_CONFIG on
  S/4HANA), SM04, SM69.
- What you could not see: unaudited classes, filtered messages, feeds off.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| ≥ 5 failed logons per user in 15 min | `SM20` | tune per system; exclude interface users separately |
| Any dialog logon by `SAP*` / `DDIC` | `SM20` | literal match |
| Audit configuration changed or `SELREC` cleared | `SM20`, `SM19` | high severity |
| New or changed external command | `SM69` | every record qualifies in delta mode |

Hand these to [alert-builder.md](alert-builder.md). On Splunk ES, enable
the shipped search instead of rebuilding it; the 1.3.0 release notes say to
leave the two SM59 destination searches disabled.

## Documentation

- `sm20`, `sm19`, `sm04`, `al08`, `sm21_log`, `devaccess`,
  `se37_log-se37-fm-execution-log`, `sm69-external-os-commands-logs`,
  `sbdlog-sap-secure-by-default-logs`, `sm05-http-security-session-monitoring`
- Detections — `list-of-correlation-searches`,
  `enterprise-security-content-pack`, `list-of-cim-compliant-event-types`,
  `sap-powerconnect-content-pack-for-splunk-enterpr-3` (v1.3.0 notes)
- KB 132 Read Access Logging — `kb-132-how-to-enable-read-access-logging`;
  KB 164 CIM mapping — `kb-164-strust-data-not-mapping-to-cim-ssl-dataset`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
