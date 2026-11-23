# RFC destinations, tRFC / qRFC / bgRFC queues, gateway

**Use when:** an RFC destination fails, tRFC calls hang in SM58, a qRFC
queue is stuck or growing (SMQ1 / SMQ2), bgRFC units fail, or someone asks
what is connected through the gateway.
**Not for:** RFC response time and call volume (`ST03_RFCC`, `ST03_RFCS`)
→ [performance-triage.md](performance-triage.md); the IDoc on the queue →
[idocs.md](idocs.md); PI/PO and CPI messages →
[integration-messages.md](integration-messages.md).

The core insight: **queue and destination data are snapshots re-sent on
every poll.** A queue stuck for a week produces thousands of rows: count
distinct queues by latest state and never sum depths across polls. Second
trap: **`SM59` tests only destinations included in its metric filter**
(since SP 8.04), so a destination with no records is untested, not healthy.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM58` | ABAP | snapshot | tRFC error entries; subtype `STATISTICS` = counts per destination, function, state, user (8.0+). Metric configuration `STATISTICS_ONLY = X` (also SMQ1 / SMQ2) leaves only that subtype | yes |
| `SMQ1` / `SMQ2` | ABAP | snapshot | outbound / inbound qRFC queues; subtype `STATISTICS` = counts per state and client | yes |
| `SMQS` (`SMQR`) | ABAP | snapshot | registered outbound destinations (inbound queue registration) | yes |
| `BGRFC_MON`, `BGRFC_PERFMON` | ABAP | snapshot | bgRFC units per destination and queue (subtypes `INB_` / `OUTB_` + `DEST`, `QUEUE`, `UNITS`); totals, SYSFAIL units, longest-running unit | `_MON` no (filter rows mandatory from 8.03); `_PERFMON` yes |
| `SM59` | ABAP | snapshot | result of a connection test per destination and server | yes, for included destinations |
| `SM59_RFCDES` | ABAP | snapshot | destination definitions (the SM59 tabs) | yes |
| `SMGW` | ABAP | snapshot | gateway: `""` connections, `LOG_CLNT` logged-on clients, `REM_GW` remote gateways, `GWADM` summary | yes |
| `SMGW_SEC` | ABAP | snapshot | `SEC` secinfo and `REG` reginfo contents | yes |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `QNAME`, `DEST`, `MANDT` | queue, destination, client (SMQ1 / SMQ2 key) | | sample (Dynatrace) |
| `QSTATE` | queue state | shipped alerts fire on `CPICERR`, `SYSFAIL`, `VBERROR`, `SENDED`; `STOP` seen; `READY`, `RUNNING`, `WAITING`, `RETRY`, `NOSEND` are SAP standard | sample (Dynatrace) + docs |
| `QDEEP` | entries in the queue (`ENTRIES` on some feeds) | string; convert | sample (Dynatrace); `ENTRIES` = docs |
| `FDATE`+`FTIME` | date / time of the first (oldest) entry, system-local | | sample (Dynatrace) |
| `ERRMESS` | error text of the blocking entry | | sample (Dynatrace) |
| `FIRSTTID`, `WQNAME` | TID of the first LUW; queue this one waits for | join to WE02 `TRFC_TID` | sample (Dynatrace) |
| `ARFCDEST`, `ARFCFNAM`, `ARFCSTATE`, `ARFCUSER`, `ARFCTCODE`, `COUNT` | SM58 `STATISTICS`: destination, function, state, user, tcode, entries | `CPICERR` seen; `SYSFAIL`, `RECORDED`, `SENDED` = SAP | sample (Dynatrace) |
| `RFC_TID`, `ARFCDATUM`+`ARFCUZEIT`, `ARFCMSG`, `ARFCRETRYS`, `ARFCRHOST`, `ARFCIPID` | SM58 detail (`""` subtype): TID, date / time, error text, retries, host; plus `ARFCDEST`, `ARFCFNAM`, `ARFCSTATE`, `ARFCUSER`, `ARFCTCODE` | `RFC_TID` joins to WE02 `TRFC_TID` | sample (Dynatrace) |
| `RFCDEST`, `RFCTYPE`, `SAP_SERVER` | destination, type, server that ran the test (the sample had no `HOST`; keep `SAP_SERVER` in the key, one server can pass while another fails) | `RFCTYPE` `3` ABAP, `T` TCP/IP, `G` / `H` HTTP (SAP) | sample (Dynatrace) |
| `SUCCESS`, `REASON` | test result; error text when it failed | `0` = failed (shipped alert); `REASON` empty on success | sample (Dynatrace) + docs |
| `SM59_RFCDES`, `SMQS`, `BGRFC_*`, `SMGW*` fields | not in the documentation | | unconfirmed — sample first |

## Investigation sequence

1. **Confirm the feeds, then sample one record per type.** These are
   snapshots: a type quiet for more than a few polls is a broken feed.
   For SMQ1 / SMQ2 check whether depth is `QDEEP` or `ENTRIES`.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (SM58, SMQ1, SMQ2, SMQS, SM59, SM59_RFCDES, BGRFC_MON, BGRFC_PERFMON, SMGW)
| stats count max(_time) as newest by EVENT_TYPE EVENT_SUBTYPE
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"SM58", "SMQ1", "SMQ2", "SMQS", "SM59", "SM59_RFCDES", "BGRFC_MON", "BGRFC_PERFMON", "SMGW"})
| summarize {events = count(), newest = max(timestamp)}, by: {dt.source_entity_name, dt.source_entity_type}
```

2. **Failing destinations** — latest test per destination and server.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM59
| stats latest(SUCCESS) as SUCCESS latest(REASON) as REASON latest(RFCTYPE) as RFCTYPE latest(_time) as seen by RFCDEST SAP_SERVER
| where SUCCESS="0"
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SM59"
| sort timestamp asc
| summarize {success = takeLast(success), reason = takeLast(reason), rfctype = takeLast(rfctype), seen = max(timestamp)}, by: {rfcdest, sap_server}
| filter success == "0"
```

3. **Queues in trouble** — latest state per queue, then keep error states
   and deep queues. Run for `SMQ1` (outbound) and `SMQ2` (inbound); the
   depth threshold is a starting point. To tell stuck from slow, list one
   queue's records over time: flat depth with an old `FDATE` is stuck.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SMQ1 EVENT_SUBTYPE=""
| stats latest(QSTATE) as QSTATE latest(QDEEP) as QDEEP latest(FDATE) as FDATE latest(ERRMESS) as ERRMESS by MANDT QNAME DEST
| eval depth=tonumber(QDEEP)
| where QSTATE IN ("CPICERR","SYSFAIL","VBERROR","SENDED","STOP") OR depth > 1000
| sort - depth
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SMQ1" and dt.source_entity_type == ""
| sort timestamp asc
| summarize {qstate = takeLast(qstate), depth = takeLast(toLong(qdeep)), fdate = takeLast(fdate), errmess = takeLast(errmess)}, by: {mandt, qname, dest}
| filter in(qstate, {"CPICERR", "SYSFAIL", "VBERROR", "SENDED", "STOP"}) or depth > 1000
| sort depth desc
```

4. **tRFC errors by destination.** `COUNT` in `STATISTICS` is already a
   total: take the latest value per group; summing across polls multiplies
   the backlog. Groups whose `seen` predates the last poll have cleared.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM58 EVENT_SUBTYPE=STATISTICS
| stats latest(COUNT) as entries latest(_time) as seen by ARFCDEST ARFCFNAM ARFCSTATE
| eval entries=tonumber(entries)
| sort - entries
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SM58" and dt.source_entity_type == "STATISTICS"
| sort timestamp asc
| summarize {entries = takeLast(toLong(`count`)), seen = max(timestamp)}, by: {arfcdest, arfcfnam, arfcstate}
| sort entries desc
```

5. **Correlate.** A failing `RFCDEST` in `SM59` equal to `DEST` (SMQ1) or
   `ARFCDEST` (SM58) explains the queue: fix the destination first.
   `CPICERR` on many destinations at once points to the network or the
   target ([system-availability.md](system-availability.md)); `SYSFAIL`
   to the application in the target (read `ERRMESS`). An `SMQ2` error is
   processed here: check dumps and locks at the same time. bgRFC: read
   `BGRFC_PERFMON` totals, then `BGRFC_MON` units if its filter is kept.
   "Who is connected": `SMGW` `LOG_CLNT` / `REM_GW`; ACLs: `SMGW_SEC`.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| `SUCCESS` `0` with "Error when opening an RFC connection" | target down, wrong host / port, or network | SM59 connection test; target availability |
| Queue `SYSFAIL` with old `FDATE` | first LUW fails in the target and blocks the rest | SMQ1 / SMQ2: read the error, fix, then restart (human) |
| Queue `STOP` | stopped by hand or by a stop mark | ask who stopped it; do not assume a fault |
| Queue `READY` with rising depth | scheduler not registered or no free work processes | SMQS / SMQR registration |
| No SM59 records at all on 7.0–8.1 after install | filter bug (KB 201) | re-save an entry in the SM59 dest. filter |
| "RFC-timeout: Dest ..." in the PowerConnect log | PowerConnect could not reach a server to extract (KB 155) | informational; check that server |

## What to tell the user

- Distinct failing destinations and distinct queues in error, with state,
  depth, age of the oldest entry and the error text.
- Verify in SM59 (connection test), SM58, SMQ1 / SMQ2, SMQS, SBGRFCMON.
- Owner: Basis for destinations, gateway and registration; the interface
  owner for `SYSFAIL`. Restarting or deleting entries is a human decision.
- Not visible: destinations outside the SM59 filter, detail records under
  `STATISTICS_ONLY`, bgRFC units without filter rows.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `SUCCESS == "0"` | `SM59` | shipped Dynatrace alert `davis.sap.sm59.failed_rfc_dest` |
| `QSTATE` in `CPICERR`, `SYSFAIL`, `VBERROR`, `SENDED` | `SMQ1`, `SMQ2` | shipped alerts `davis.sap.smq1.outbound_queue_failures`, `davis.sap.smq2.inbound_queue_failures`; fire per poll, so deduplicate per queue |
| Depth above a tuned value, or oldest entry older than 1 hour; tRFC entries above a tuned count | `SMQ1`, `SMQ2`, `SM58` | starting points; baseline per queue or destination |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `sm58`, `sm59`, `sm59_rfcdes`, `smq1`, `smq2`, `smgw`, `smgw_sec`,
  `smqs-outbound-qrfc-monitor`, `bgrfc_mon-background-rfc-monitor`,
  `bgrfc_perfmon-background-rfc-performance-monitor`
- KB 155, KB 201 — `kb-155-rfc-timeout-dest-rfc-destination`,
  `kb-201-sm59-events-are-not-collected`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
