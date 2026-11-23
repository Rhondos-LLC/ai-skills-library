# Change tracking — what changed, when, and by whom

**Use when:** "X broke at 14:10 — what changed before that?", "which
transports went into PRD last night?", "did a profile parameter change?",
"who edited table T in SE16N?", "HANA ini changes?", "new ATC findings?".
**Not for:** user, role and authorization changes →
[user-and-authorization-review.md](user-and-authorization-review.md);
who did it and from where (audit trail) → [security-audit.md](security-audit.md);
certificate expiry → [certificates-and-licenses.md](certificates-and-licenses.md).

The core insight: **a change is either logged or has to be inferred, and
the two need different queries.** Change-log types (transports, parameter
logs, table logs) emit a record when something changed; count them in the
window. Configuration types (`RZ10`, `SCC4`, `SE06`) are snapshots re-sent
on every poll whether or not anything changed, so their presence in the
window means nothing: a change shows only as two different values for the
same key. Some logs stay empty until a metric filter is set (`CDPOS`,
`SCU3`), so an empty sweep means "nothing logged that we collect".

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `STMS` | ABAP | event stream; subtypes empty (import steps), `COFILE`, `QUEUE`, `TPALOGS_DETAILS` | transport imports with return code, queue, logs | yes |
| `STMS_TPLOG` | ABAP | event stream | tp call log (ULOG): requests added to or removed from the queue | yes |
| `STMS_ALERT` | ABAP | event stream | TMS alerts: export, import, communication, CTS configuration errors | check |
| `E070` | ABAP | event stream; subtypes empty (header from E070/E07T/E070M), `E071` (objects) | which objects a request contains, owner, status | yes |
| `RZ10` | ABAP | snapshot | profile parameters and values per instance | yes |
| `RZ10_LOG`, `TU02` | ABAP | event stream | static profile changes; parameter change history with old and new value | yes |
| `SM21_LOG` | ABAP | event stream | dynamic parameter changes, SM59 changes (see [system-log.md](system-log.md)) | yes |
| `SCC4`, `SE06` | ABAP | snapshot; SE06 subtypes `COMP`, `NMSP` | client settings (role, change options, locks); component and namespace change option | yes |
| `SCU3` | ABAP | event stream; subtype = table name | table logging (DBTABLOG) for the tables in its filter | yes, empty until filter set |
| `CDPOS` | ABAP | header + detail; subtypes empty (CDHDR), `CDPOS` | change documents for the objects in its filter | yes, empty until filter set |
| `SE16N_CD`, `S416N_CD` | ABAP | event stream; SE16N_CD subtype `SE16N_EDIT` seen | table data edited by hand in SE16N / S416N | yes |
| `HDB_DBCC_INIHST`, `HDB_DBCC_INI` | ABAP (HANA) | event stream; snapshot | HANA ini change history; current ini values | yes |
| `STRUST_HISTORY` | ABAP | event stream | certificate changes — details in [certificates-and-licenses.md](certificates-and-licenses.md) | yes |
| `ATC` | ABAP | header + detail; subtypes empty (run), `CONTENTS`, `CONTENTS_DETAIL`, `CONTENTS_TEXT` | ABAP Test Cockpit runs and findings | yes |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `TRKORR` (STMS) | transport request | `ALL` appears for import-all steps | sample (Dynatrace) |
| `RETCODE` | tp return code of the step | `0000` ok, `0004` warning, `0008` error, `0012`+ fatal (meanings: SAP) | sample (Dynatrace) |
| `TRSTEP`, `TRTIME` | import step code; step time `yyyymmddhhmmss`, system-local | `QUEUE` records carry an empty `TRSTEP`, `COFILE` records none (and `TRTIME` as `hhmmss` with `TRDATE`): require a non-empty `TRSTEP` to select import steps | sample (Dynatrace) |
| `TRUSER`, `ADMIN`, `TARSYSTEM`, `TRCLI`, `DOMAIN` | who imported, target system and client, transport domain | `TRUSER` is often empty; fall back to `ADMIN` | sample (Dynatrace) |
| `sod_violation` (STMS) | pipeline flag | Dynatrace-derived; meaning not documented | sample (Dynatrace) |
| `PAR_NAME`, `INSTANCE_NAME` (RZ10) | parameter and instance: the entity key | | sample (Dynatrace) |
| `PAR_USER_WERT`, `PAR_PRF_INST_VALUE`, `PAR_PRF_DEF_VALUE`, `PAR_DEFAULT_WERT1` | current value; instance-profile, default-profile and kernel-default values (roles inferred from SAP naming) | | sample (Dynatrace) |
| `IS_DYNAMIC`, `RECOM_VALUE`, `RECOM_NOTE`, `VALUE_ORIGIN` | dynamically switchable; SAP recommendation; origin code | | sample (Dynatrace) |
| `AS4USER`, `AS4DATE`, `TRSTATUS`, `TRFUNCTION`; `PGMID`, `OBJECT`, `OBJ_NAME` (E070 / E071) | owner, date, status, type; object entries | | SAP |
| `USERNAME`, `UDATE`, `UTIME`, `TCODE`, `OBJECTCLAS`, `OBJECTID`, `CHANGENR`, `MANDANT`; `TABNAME`, `TABKEY`, `FNAME`, `CHNGIND`, `F_OLD`, `F_NEW` (CDPOS) | change document header (subtype empty) and items (subtype `CDPOS`); join on `CHANGENR` | client is `MANDANT`, not `MANDT`; items repeat user, date and time | sample (Dynatrace) |
| `PARNAME`, `OLDVALUE`, `NEWVALUE`, `PARDATE`, `PARTYPE`, `HOSTNAME` (TU02) | parameter, old and new value, change date, type, host | no user field in the sample | sample (Dynatrace) |
| `MANDT`, `CCCATEGORY`, `CCCORACTIV`, `CCNOCLIIND`, `CCCOPYLOCK`, `CHANGEUSER`, `CHANGEDATE` (SCC4) | client: the entity key; role, change options, protection, last changer | `_METRICS_` KPI records share the type: require a non-empty `MANDT` | sample (Dynatrace) |
| `DLVUNIT`, `CHANGEABLE`, `EXTENDABLE` (SE06 `COMP`); `NAMESPACE`, `PREFIX`, `CHANGEABLE` (SE06 `NMSP`) | change option per software component and per namespace | two subtypes with different keys | sample (Dynatrace) |
| `CRNAME`, `CRDATE`, `CRTIME`, `MANDT` (SE16N_CD) | who edited, when (system-local), client | subtype seen: `SE16N_EDIT`; no table name on it | sample (Dynatrace) |
| `USERNAME`, `SYDATE`, `SYTIME`, `CMDSTRING`, `RETCODE` (STMS_TPLOG); `SYSNAM`, `FUNCTION`, `ERROR`, `SEVERITY`, `TEXT`, `CURDATE`, `CURTIME`, `CURUSER` (STMS_ALERT) | tp command with return code; TMS alert with function, error id and text | | sample (Dynatrace) |
| RZ10_LOG, SCU3, S416N_CD, HDB_DBCC_INIHST, ATC fields | | no record seen; sample one record first | unconfirmed |

## Investigation sequence

Fix the window first. The user's "T" is usually wall-clock time in their
own zone; convert it, then start with T − 6 h to T (24 h if nothing is
found: changes often bite at the next restart or job run, not at once).

1. **Sweep every change log in the window**: counts by type and subtype
   show which kinds of change happened and which feeds exist at all.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (STMS,STMS_TPLOG,STMS_ALERT,E070,RZ10_LOG,TU02,SCU3,CDPOS,SE16N_CD,S416N_CD,HDB_DBCC_INIHST,STRUST_HISTORY,SUIM,SM69,SECPOL_LOG,UCON_LOG)
| stats count min(_time) as first max(_time) as last by source EVENT_TYPE EVENT_SUBTYPE
| sort source first
```
```dql
fetch logs, from: <T_MINUS_6H>, to: <T>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"STMS", "STMS_TPLOG", "STMS_ALERT", "E070", "RZ10_LOG", "TU02", "SCU3", "CDPOS", "SE16N_CD", "S416N_CD", "HDB_DBCC_INIHST", "STRUST_HISTORY", "SUIM", "SM69", "SECPOL_LOG", "UCON_LOG"})
| summarize {events = count(), first = min(timestamp), last = max(timestamp)}, by: {log.source, dt.source_entity_name, dt.source_entity_type}
| sort first asc
```

   Platform time is extraction time, normally minutes after the change
   but hours late after a collector outage or historical load. Confirm
   each hit against its own time fields (`TRTIME`, `UDATE` + `UTIME`).
2. **Sample one record** of each type the sweep returned.
3. **Transports imported in the window**, one row per request:

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=STMS TRSTEP=*
| stats max(RETCODE) as max_rc values(TRSTEP) as steps max(TRTIME) as last_step latest(TRUSER) as user by source TARSYSTEM TRKORR
| sort - last_step
```
```dql
fetch logs, from: <T_MINUS_6H>, to: <T>
| filter service.name == "sap:abap" and dt.source_entity_name == "STMS" and isNotNull(trstep) and trstep != ""
| summarize {max_rc = max(toLong(retcode)), steps = collectDistinct(trstep), last_step = max(toLong(trtime)), user = takeAny(truser)}, by: {log.source, tarsystem, trkorr}
| sort last_step desc
```

   Then read `E070` subtype `E071` for the suspicious request and match
   its objects against what broke (dump program, failing job's table).

4. **Configuration drift from snapshots.** Use a window that starts before
   the suspected change and ends at T. Any key with more than one value
   changed inside it. The same pattern works for `SCC4` (key `MANDT`,
   non-empty to skip `_METRICS_` records) and `SE06` (key `DLVUNIT` or
   `NAMESPACE` per subtype, value `CHANGEABLE`).

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=RZ10 PAR_NAME=*
| stats dc(PAR_USER_WERT) as versions values(PAR_USER_WERT) as seen by source INSTANCE_NAME PAR_NAME
| where versions > 1
```
```dql
fetch logs, from: <T_MINUS_24H>, to: <T>
| filter service.name == "sap:abap" and dt.source_entity_name == "RZ10" and isNotNull(par_name)
| summarize {versions = countDistinct(par_user_wert), seen = collectDistinct(par_user_wert)}, by: {log.source, instance_name, par_name}
| filter versions > 1
```

   `RZ10_LOG` and `TU02` give who and when. A static parameter takes
   effect only at the next restart; see [system-availability.md](system-availability.md).

5. **Data and customizing changes.** For `SCU3`, `CDPOS`, `SE16N_CD` and
   `S416N_CD`, list by table, user and time; report the fact of the
   change, not old and new business values, unless the user asks.
6. **Correlate with the symptom.** Line the changes up against the first
   dump (`ST22`), failed job (`SM37`) or error (`SM21_LOG`). A change
   after the first symptom is not the cause.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Sweep returns nothing | nothing logged, or feeds missing or unfiltered | check each type exists over 7 days before saying "no change" |
| Transport with `RETCODE` ≥ 8 shortly before T | failed or partial import | read `STMS` subtype `TPALOGS_DETAILS`; owner re-imports or corrects |
| Clean import, then dumps in a program it contained | code change is the likely cause | confirm via `E071` objects vs the dump's program |
| `RZ10` value differs across polls, no restart | dynamic change, or profile edit not yet active | check `IS_DYNAMIC` and `SM21_LOG` |
| `CDPOS` empty for business partners only | KB 138 time-zone issue for BUPA objects | set the filter's Timezone column to UTC |
| `SE16N_CD` / `S416N_CD` record on production | direct table edit | escalate; this bypasses transports |

## What to tell the user

- A timeline: each change with type, object, system, time (say whether
  system-local or UTC) and who made it, ending at the first symptom.
- Which change types you checked and found empty, and which are not
  collected or not filtered, so the user knows the blind spots.
- Where a human verifies: STMS import history, SE01/SE09, RZ10/RZ11,
  TU02, SCC4, SE06, SCU3, DBACOCKPIT (INI change history), ATC.
- The owner (transport or parameter owner) reviews or reverts; you never do.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Import with return code ≥ 8 | `STMS` | compare as number |
| Request added to or removed from the import queue by hand | `STMS_TPLOG` | shipped in Splunk ES |
| Static or dynamic profile parameter changed | `RZ10_LOG`, `SM21_LOG` | shipped in Splunk ES |
| Client opened for change; new client; namespace opened | `SCC4`, `SE06` | shipped in Splunk ES; snapshot diff elsewhere |
| Manual table edit on production | `SE16N_CD`, `S416N_CD` | every record qualifies |
| HANA ini parameter changed | `HDB_DBCC_INIHST` | filter on critical sections |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `stms`, `stms_alert-transport-management-system-tms-alerts`,
  `stms_tplog-tp-call-log-ulog`, `e070`
- `rz10`, `tu02-parameter-changes-in-sap-system`,
  `scc4-sap-clients-overview`
- `scu3-analysis-of-logged-customizing-objects-and-ta`, `cdpos`,
  `se16n_cd-se16n-change-documents`, `s416n_cd-s416n-change-documents`
- `hdb_dbcc_inihst-hana-database-ini-files-change-his`,
  `hdb_dbcc_ini-hana-ini-files`, `atc-abap-test-cockpit-results`,
  `kb-138-cdpos-extractor-does-not-collect-change-doc`, `list-of-correlation-searches`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
