# IDocs — failures, backlog, volume, one IDoc

**Use when:** IDocs fail or are stuck, a partner reports missing documents,
or someone asks for IDoc volume or the history of one IDoc number.
**Not for:** tRFC/qRFC transport errors behind an outbound IDoc →
[rfc-and-queues.md](rfc-and-queues.md); PI/PO or CPI message failures →
[integration-messages.md](integration-messages.md); the posted business
document → [business-process.md](business-process.md).

The core insight: **`WE02` is a stream of control records, one per status
change, so an IDoc's state is its latest record per `MANDT` + `DOCNUM`.**
Counting rows counts transitions: an IDoc that failed and was reprocessed
shows as both failed and successful. Reduce to the latest record first.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `WE02` | ABAP | event stream | control record (EDIDC) with current status, partners, message type | yes |
| `BD87_DYN` | ABAP | header + detail | `""` control record, `SGLG` status records with log text, `SGFV` chosen segment fields | yes, but sends nothing until its metric filter is filled |
| `BD87` | ABAP | event stream | older IDoc status feed named by some shipped dashboards | check by count |

Metric filters decide what you can see. `WE02` has one from PowerConnect
9.01 (Administrator → Metric Filters → Interfaces → WE02 filter);
`BD87_DYN` extracts only message type + basic type pairs listed in its
filter. An absent message type is "not collected", not "no IDocs".

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `DOCNUM` (+ `MANDT`) | IDoc number, the entity key | | sample (Dynatrace) |
| `STATUS` | two-digit status code | outbound 01–49, inbound 50–75 | sample (Dynatrace, in raw JSON only — see note) |
| `STATUS_GROUP` | PowerConnect's own grouping of the code | list its values first; a record with code `62` carried `Successful`, so it is not the WE02 traffic light | sample (Dynatrace) |
| `STATNM`, `STATXT` | status name; last status message text | | sample (Dynatrace) |
| `DIRECT`, `DIRECTTEXT` | direction | `1` outbound (`Outbox`), `2` inbound | sample (Dynatrace); `2` = SAP |
| `MESTYP`, `IDOCTP` | message type, basic type | | sample (Dynatrace) |
| `SNDPRN`, `RCVPRN`, `SNDPOR`, `RCVPOR` | sender / receiver partner and port | | sample (Dynatrace) |
| `CREDAT`+`CRETIM`, `UPDDAT`+`UPDTIM` | created / last changed, system-local | | sample (Dynatrace) |
| `TRFC_TID`, `TRFC_STATE` | tRFC transaction id and state of an outbound IDoc | join key to SM58 / SMQ1 | sample (Dynatrace) |
| `BD87_DYN` fields | EDIDC / EDIDS names: `DOCNUM`, `STATUS`, `STATXT`, `COUNTR`, `LOGDAT`, `LOGTIM`, `STATYP`, `STAMID`, `STAMNO`, `SEGNUM`, `UNAME`, `STATUS_GROUP` | `STATUS` again only as `data.status` on Dynatrace | sample (Dynatrace, `SGLG`); `SGFV` not sampled |

**Dynatrace:** top-level `status` is the platform's log status (`NONE`,
`ERROR`), not the IDoc status; the code survives only as `data.status`.

Status codes (SAP standard meanings; tune per interface). Outbound: error
`02 04 05 25 26 27 29 37`; waiting `30` (ready for dispatch), `03` (passed
to port, handed to tRFC but not confirmed); done `12 41`. Inbound: error
`51 56 60 61 63 65`; waiting `64` (ready for application), `66` (waiting
for predecessor), `62` (passed to application); done `53`. `31` and `68`
are errors closed by hand.

## Investigation sequence

1. **Confirm the feed, sample one WE02 record.** A quiet stream can be normal.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (WE02, BD87_DYN, BD87)
| stats count max(_time) as newest by EVENT_TYPE EVENT_SUBTYPE
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"WE02", "BD87_DYN", "BD87"})
| summarize {events = count(), newest = max(timestamp)}, by: {dt.source_entity_name, dt.source_entity_type}
```

2. **Current state and backlog** — latest record per IDoc, then count by
   direction and status. Rows with a waiting code are the backlog;
   `oldest_created` is system-local, so compare it with
   `CURRENT_TIMESTAMP`, not with the platform clock.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=WE02
| stats latest(STATUS) as STATUS latest(STATUS_GROUP) as GRP latest(DIRECT) as DIRECT latest(CREDAT) as CREDAT by MANDT DOCNUM
| stats count as idocs min(CREDAT) as oldest_created by DIRECT GRP STATUS
| sort - idocs
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "WE02"
| sort timestamp asc
| summarize {code = takeLast(data.status), grp = takeLast(status_group), direct = takeLast(direct), credat = takeLast(credat)}, by: {mandt, docnum}
| summarize {idocs = count(), oldest_created = min(credat)}, by: {direct, grp, code}
| sort idocs desc
```

3. **Group the failures** by message type, partner and status, with one
   example text. Adjust the code list to the direction in question.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=WE02
| stats latest(STATUS) as STATUS latest(STATXT) as STATXT latest(MESTYP) as MESTYP latest(SNDPRN) as SNDPRN latest(RCVPRN) as RCVPRN by MANDT DOCNUM
| search STATUS IN ("02","04","05","25","26","27","29","37","51","56","60","61","63","65")
| stats count as idocs latest(STATXT) as example by MESTYP SNDPRN RCVPRN STATUS
| sort - idocs
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "WE02"
| sort timestamp asc
| summarize {code = takeLast(data.status), text = takeLast(statxt), mestyp = takeLast(mestyp), sndprn = takeLast(sndprn), rcvprn = takeLast(rcvprn)}, by: {mandt, docnum}
| filter in(code, {"02","04","05","25","26","27","29","37","51","56","60","61","63","65"})
| summarize {idocs = count(), example = takeAny(text)}, by: {mestyp, sndprn, rcvprn, code}
| sort idocs desc
```

4. **Trace one IDoc** — every record for the number, in order. If
   `BD87_DYN` is collected, repeat with it and `EVENT_SUBTYPE=SGLG` for the
   full status log.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=WE02 DOCNUM=<DOCNUM>
| sort 0 _time
| table _time STATUS STATNM STATXT UPDDAT UPDTIM TRFC_TID TRFC_STATE
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "WE02" and docnum == "<DOCNUM>"
| sort timestamp asc
| fields timestamp, data.status, statnm, statxt, upddat, updtim, trfc_tid, trfc_state
```

5. **Correlate.** Outbound IDoc at `03` or `30` with a `TRFC_TID`: look
   for that id and the receiver's destination in `SM58` and `SMQ1`
   ([rfc-and-queues.md](rfc-and-queues.md)). An inbound `51` burst on one
   message type: check locks (`SM12`) and dumps at the same time.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Many rows, few distinct `DOCNUM` | reprocessing loops | report IDocs, not rows; find the repeating `STATXT` |
| Outbound stuck at `03` / `30` | tRFC not delivered or dispatch job not running | SM58 / SMQ1 for the destination; RSEOUT00 job in SM37 |
| Inbound `64` growing | inbound processing job not running or overloaded | RBDAPP01 job; work process shortage |
| Inbound `51` on one `MESTYP` and partner | application or master-data error | read `STATXT`; owner is the functional team |
| `BD87_DYN` silent, application log says "maximum possible size of the structure is exceeded" | too many segment fields flagged "to main" (KB 228, SP 8.04+) | reduce the fields in the segment filter |
| Splunk "Segment Details" panel empty on app 7.1.0 / 7.2.0 | hard-coded system in the panel query (KB 171) | dashboard fix, not a data gap |

## What to tell the user

- Distinct IDocs by direction and current status, with the failing
  message types, partners and one example status text.
- Verify in WE02 or BD87; reprocessing in BD87 is a human decision.
  Application errors belong to the functional team; port, partner-profile
  and tRFC errors to Basis or the integration team.
- Not visible: message types excluded by the metric filter, IDocs last
  changed before the window, payload unless `BD87_DYN` `SGFV` is set up.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Latest status of an IDoc in an error code | `WE02` | group per `MESTYP` + partner to avoid one alert per IDoc |
| Waiting IDocs (`30`, `64`) above a tuned count or age | `WE02` | starting point: older than 30 minutes |
| No IDocs for a critical `MESTYP` in business hours | `WE02` | baseline per interface; event streams have no fixed cadence |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- WE02 — `we02`; BD87_DYN — `bd87_dyn`
- KB 171, KB 228 — `kb-171-no-results-shown-in-segment-details-panel-o`,
  `kb-228-bd87_dyn-the-maximum-possible-size-of-the-s`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
