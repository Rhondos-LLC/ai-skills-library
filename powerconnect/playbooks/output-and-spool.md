# Output and spool — printers, spool requests, mail, ADS

**Use when:** the user asks whether printing works, which output devices
are down, which spool requests failed or are stuck, what a spool request
contained, whether outbound mail (SAPconnect) is going out or backing up,
whether an expected inbound mail arrived, or whether Adobe Document
Services is available.
**Not for:** the job that produced the spool →
[background-jobs.md](background-jobs.md) (job spool is `SM37` subtype
`SPOOL`; if missing, see KB 140 below) · the RFC destination behind ADS
→ [rfc-and-queues.md](rfc-and-queues.md) · a stopped feed →
[feed-health.md](feed-health.md)

The core insight: **a status here is rarely a plain up/down.** In
`SPAD_STATUS` a device whose check returns "not supported" is not a
device that is down; the check only works for some access methods. In
`SOST` a request waiting since last year is reported again on every
extraction, so the event time says when it was read, not when it was
sent. Always reduce to the latest record per device or request, and age
requests by their own date fields.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SPAD_STATUS` | ABAP | snapshot | output device definition plus connection check result | no; from 8.04 the SPAD dest. filter is mandatory |
| `SP01` | ABAP | collector batch, one record per spool request; a request can be sent again on later polls | spool request header and output-request counters | yes |
| `SP01_CONTENT` | ABAP | event stream, one record per line | text lines of spool requests | no |
| `SOST` | ABAP | snapshot-like, one record per send request and recipient | SAPconnect send requests with status and message | yes; SOST filter may narrow it |
| `SOIN` | ABAP | event stream | inbound SMTP requests | yes |
| `ADS_CHECK` | ABAP | snapshot (periodic test) | result of the ADS destination check | yes |
| `SCOT` | ABAP | snapshot | SAPconnect node settings | yes |

`SP01_CONTENT` reads at most 5 pages per request and skips requests over
20 pages (defaults of `READ_MAXPAGES` / `PAGELIMIT_TO_IGNORE`), so a
missing or truncated request is expected. Waiting mail in table SOSC is
only extracted when the SOST metric configuration is set to `X`. Spool
content and mail subjects are business data: count and search them, and
quote a line only when the user asked about that request.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `SPAD_STATUS`: `PADEST` (also `NAME`) | output device, the entity key | | sample (Dynatrace) |
| `SPAD_STATUS`: `RCCODE`, `RCTEXT` | check return code and text | seen `-1` = "Printer check is not supported", `9` = "Not reachable"; list the others by grouping | sample (Dynatrace) |
| `SPAD_STATUS`: `PAMETHOD`, `PATYPE`, `PALPDHOST`, `PAMSSERVER`, `PADISABLED`, `PASTANDORT` | access method, device type, target host, spool server, disabled flag, location | | sample (Dynatrace) |
| `SP01`: `RQIDENT`, `RQCLIENT` | spool request number and client, the entity key | | sample (Dynatrace) |
| `SP01`: `RQOWNER`, `RQDEST`, `RQ2NAME`, `RQTITLE_V`, `RQDOCTYPE`, `PAGE_COUNT` | owner, device, name, title, type, pages | | sample (Dynatrace) |
| `SP01`: `RQPJREQ`, `RQPJDONE`, `RQPJSERR`, `RQPJHERR` | output requests: created, completed, with minor problems, with severe errors | strings; all `0` = never sent to a device | names: sample (Dynatrace); meaning: SAP (TSP01) |
| `SP01`: `RQSTATUS_V`, `RQERROR`, `RQCRETIME`, `RQDELDATE` | display status, error flag, creation time (`yyyymmddhhmmss`), deletion date | seen status `-` (no output request) | sample (Dynatrace) |
| `SP01_CONTENT`: `RQIDENT`, `TABIX`, `LINE` | request, line number, line text | join to `SP01` on `RQIDENT` | sample (Dynatrace) |
| `SOST`: `SNDREQ_SOOS`, `MANDT`, `RECEIVER`, `SENDER` | send request id, client, addresses | addresses are personal data | sample (Dynatrace) |
| `SOST`: `MSGTY_SOST`, `MSGID_SOST`, `MSGNO_SOST`, `MSGTXT_SOST`, `MSGV1_SOST` | status message of the request | seen type `W` with "Waiting for communications service" | sample (Dynatrace) |
| `SOST`: `STATUS_SOES`, `MAILSTATUS_SOES`, `MSGTY_SOES`, `MSGV1_SOES` | recipient-level status and message | seen `E` | sample (Dynatrace) |
| `SOST`: `ENTRY_DATE_SOST`, `ENTRY_TIME_SOST`, `SNDDAT_SOES`, `SNDTIM_SOES`, `OBJDES_SOOD` | when the status was set, when sent, subject | local `yyyymmdd` / `hhmmss` | sample (Dynatrace) |
| `ADS_CHECK`: `DESTINATION`, `TEST_RESULT`, `TEST_RESULT_MSG` | destination tested, outcome, message | seen `Error`; confirm the success value by grouping | sample (Dynatrace) |
| `SCOT`: `NODE`, `MANDT`, `RFCDEST`, `SERVICE`, `WAITING`, `ERROR`, `SENT`, `BUSY` | node, client, destination, service, request counters (strings) | payload `STATUS` (`active` seen) collides with the log status on Dynatrace: read `data.status`. Subtype `ROUTE` holds routing rules | sample (Dynatrace) |

`SOIN` returned no data when sampled; its fields are unconfirmed.

## Investigation sequence

1. **Confirm the feeds.** Count and newest record per type. No
   `SPAD_STATUS` on agent 8.04+ usually means the filter list was never
   activated: a coverage gap, not "all printers fine".
2. **Sample one record** of each type you will filter on.
3. **Device status.** Latest record per device, grouped by check result.
   Read the `RCCODE` / `RCTEXT` pairs before calling anything down.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SPAD_STATUS
| stats latest(RCCODE) as rc latest(RCTEXT) as text latest(PAMETHOD) as method by source PADEST
| stats count as devices by source rc text method
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SPAD_STATUS"
| sort timestamp asc
| summarize {rc = takeLast(rccode), text = takeLast(rctext), method = takeLast(pamethod)}, by: {log.source, padest}
| summarize devices = count(), by: {log.source, rc, text, method}
| sort devices desc
```

4. **Failed or stuck spool requests.** Latest record per request, then
   classify from the output-request counters and group by device.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SP01
| stats latest(RQPJREQ) as req latest(RQPJDONE) as done latest(RQPJHERR) as herr latest(RQDEST) as dest by source RQCLIENT RQIDENT
| eval req=tonumber(req), done=tonumber(done), herr=tonumber(herr)
| eval state=case(herr>0,"error", req>done,"not finished", req==0,"not sent to device", true(),"done")
| stats count as requests by source dest state
| sort - requests
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SP01"
| sort timestamp asc
| summarize {req = takeLast(toLong(rqpjreq)), done = takeLast(toLong(rqpjdone)), herr = takeLast(toLong(rqpjherr)), dest = takeLast(rqdest)}, by: {log.source, rqclient, rqident}
| fieldsAdd state = if(herr > 0, "error", else: if(req > done, "not finished", else: if(req == 0, "not sent to device", else: "done")))
| summarize requests = count(), by: {log.source, dest, state}
| sort requests desc
```

   "Not finished" is stuck only if it stays so: compare with `RQCRETIME`
   (start with 30 minutes). Drill into at most five `RQIDENT`s.
5. **Mail backlog by status.** Latest record per send request, grouped
   by status message, counting those entered before a cut-off date
   (`yyyymmdd`; string comparison is safe for this format).

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SOST
| stats latest(MSGTY_SOST) as type latest(MSGNO_SOST) as msgno latest(MSGTXT_SOST) as text latest(ENTRY_DATE_SOST) as entered by source MANDT SNDREQ_SOOS
| stats count as requests sum(eval(if(entered<"<CUTOFF_YYYYMMDD>",1,0))) as older min(entered) as oldest by source type msgno text
| sort - requests
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "SOST"
| sort timestamp asc
| summarize {type = takeLast(msgty_sost), msgno = takeLast(msgno_sost), text = takeLast(msgtxt_sost), entered = takeLast(entry_date_sost)}, by: {log.source, mandt, sndreq_soos}
| summarize {requests = count(), older = countIf(entered < "<CUTOFF_YYYYMMDD>"), oldest = min(entered)}, by: {log.source, type, msgno, text}
| sort requests desc
```

   A backlog is a growing count of waiting or error requests with recent
   entry dates; a flat pile of old ones is housekeeping, not an outage.
   An entry date of `00000000` means "not set"; ignore it as `oldest`.
6. **ADS availability.** Same idiom on `ADS_CHECK`: per `DESTINATION`
   and `TEST_RESULT`, count checks with first and last time and the
   latest `TEST_RESULT_MSG`. Report the first failing check and whether
   it has recovered.
7. **Correlate.** Device errors → its spool server (`PAMSSERVER`) in
   [system-availability.md](system-availability.md) and `SM21_LOG` in
   [system-log.md](system-log.md); waiting mail → the SAPconnect send job
   in [background-jobs.md](background-jobs.md) and the SMTP node (`SCOT`).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Most devices return "check is not supported" | access method without a status query (front-end or command printing) | exclude from "down" counts; say they cannot be checked |
| One device with a real error code, spool errors on the same `RQDEST` | printer or its host is unreachable | SPAD → output device → check; network team |
| Errors across all devices of one `PAMSSERVER` | spool server or spool work process problem | SM51 / SM50 on that server |
| Mail type `W` "Waiting for communications service" growing | send job not running or SMTP node down | SOST, SCOT, job `RSCONN01` (SAP standard name; confirm) |
| `ADS_CHECK` `Error` with a usage or destination message | destination missing or misnamed, not ADS itself | check the destination name in Metric Configuration, then `FP_CHECK_DESTINATION_SERVICE` |
| `SM37` has no `SPOOL` records although the job filter asks for them | collector user lacks spool authorizations | KB 140: `S_ADMI_FCD` (SP01, SP0R), `S_SPO_ACT` |

## What to tell the user

- Devices by check result, including how many cannot be checked.
- Spool requests in error or unfinished per device, oldest age, up to
  five request numbers; mail requests by status, oldest entry date, and
  whether the count grows; ADS last result and first failure time.
- Where to verify: SPAD, SP01, SOST, SOIN, SCOT,
  `FP_CHECK_DESTINATION_SERVICE`.
- What you could not see: devices outside the filter, content beyond the
  page limits, types not collected.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Device check result changes to an error code | `SPAD_STATUS` | snapshot: latest per `PADEST`; exclude "not supported"; throttle per device |
| Waiting or error mail requests entered today above threshold | `SOST` | filter on `ENTRY_DATE_SOST`, not event time |
| ADS check not successful for two consecutive polls | `ADS_CHECK` | throttle per destination |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform
alert.

## Documentation

- SPAD_STATUS — `spad_status`
- SP01_CONTENT — `sp01_content-spool-request-contents`
- SOST — `sost-send-requests-overview`
- SOIN — `soin-inbound-messages-smtp`
- ADS_CHECK — `ads_check-adobe-document-service-ads-availability-`
- KB 140, SM37 does not collect spool data —
  `kb-140-sm37-extractor-does-not-collect-spool-data`

`SP01` and `SCOT` have no documentation page of their own. Slugs resolve
as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
