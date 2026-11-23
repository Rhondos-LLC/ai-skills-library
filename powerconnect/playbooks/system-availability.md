# System availability — is the system or an application server up

**Use when:** "is <SID> up", "did an application server go down or
restart", "which instances are active", "is the ICM / message server
running", "what was the availability last week".
**Not for:** every feed is quiet or a dashboard is empty →
[feed-health.md](feed-health.md); the system is up but slow →
[performance-triage.md](performance-triage.md); host CPU, memory or disk →
[os-resources.md](os-resources.md); Java instance processes →
[java-stack.md](java-stack.md).

The core insight: **the ABAP agent runs inside the system it reports on, so
a dead instance does not send a "down" record; it simply stops sending.**
Silence of the snapshot feeds from one instance, while other instances and
the collector's own telemetry keep arriving, is the availability signal.
Silence from every instance at once is either a full outage or a collector
outage, and only the independent NIPING probe can tell the two apart.
Decide which case you are in before you say "down".

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM51_STATE` | ABAP | snapshot | one row per application server known to the message server: state, services, start time, work process totals and busy counts | no |
| `SM51`, `SM51_CBLCK` | ABAP | snapshot | work process list per instance, with detail subtypes (`CALLSTACK` seen); communication blocks overview (no documentation page) | yes |
| `SM51_QUEUE` | ABAP | snapshot | dispatcher request queue per instance and request type; a reliable per-instance heartbeat | yes |
| `CCMS` | ABAP | collector batch | RZ20 monitoring tree values, including the instance availability node | yes |
| `SMMS` | ABAP | snapshot | message server view; subtype `""` = server list, `PTCL` = protocols | yes |
| `SMICM` | ABAP | snapshot | ICM monitor; several subtypes (`PARM` seen: one parameter per record) | yes |
| `SYSTEM_STATUS` | ABAP | inventory | product, kernel and component lists (subtypes `SYSTEM_STATUS`, `KERNEL_INFO`, `COMPONENT_LIST`, `PRODUCT_INFO`); proves the feed is alive, says nothing about health | yes |
| `SYSTEM_TIME` | ABAP | snapshot | system, UTC, DB and enqueue time per server plus a mismatch flag | yes |
| `ni_ping` | external | probe | NIPING result per target host, sent by a standalone script that does not depend on the agent | separate install |

`ni_ping` is the only source that survives a collector outage. Without it,
say that a full outage and a collector outage cannot be told apart from
this data. There is no SM50 or SM66 extractor; work processes are `SM51`.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `NAME` (SM51_STATE) | instance name `<host>_<SID>_<nr>` | entity key | sample (Dynatrace) |
| `STATE` (SM51_STATE) | server state code | `1` = active; `2`, `4` = inactive (shipped alert) | sample (Dynatrace), docs |
| `STATUS` (SM51_STATE) | state as text | `Active` in the raw record; in Dynatrace the top-level `status` is the platform's log status, so filter on `state` | sample (Dynatrace) |
| `SERVICES` | services the instance offers | text list (Dialog, Batch, Update, Spool, ICM ...) | sample (Dynatrace) |
| `START_TIMESTAMP`, `START_DATE`, `START_TIME` | instance start, system-local | a change means a restart | sample (Dynatrace) |
| `WP_DIA_TOTAL`, `WP_DIA_BUSY`, `WP_BTC_*`, `WP_UP1_*`, `WP_UP2_*`, `WP_ENQ_*`, `WP_SPO_*` | work processes configured and busy | strings; convert | sample (Dynatrace) |
| `INSTANCE_NAME` (SM51, SM51_QUEUE, SMICM) | instance that produced the record | heartbeat key; SM51 subtype `""` is the work process list (`WP_NO`, `WP_TYP`, `WP_STATUS`, `WP_PID`) | sample (Dynatrace) |
| `REQ_TYPE`, `REQ_WAIT` (SM51_QUEUE) | queue type and waiting requests | `DIA`, `BTC`, `NOWP` | sample (Dynatrace), docs |
| `PATH`, `TEXT` (CCMS) | RZ20 node path and displayed value | availability node contains `InstanceAsTask\Availability` | sample (Dynatrace), docs |
| `DATE`, `TIME` (CCMS) | when CCMS last measured the node | can be far older than the extraction time | sample (Dynatrace) |
| `ccms_avail_perc` | availability percentage, Dynatrace-derived (numeric) | shipped alert fires below 50 | sample (Dynatrace), docs |
| `LINES` (SMICM `PARM`) | one ICM parameter line | text | sample (Dynatrace) |
| SMMS, SYSTEM_TIME, SM51_CBLCK, `ni_ping` fields | not sampled | sample one record before filtering | unconfirmed |
| `HOST` | application server | missing on several sampled Dynatrace records; group by `NAME` or `INSTANCE_NAME` instead | sample (Dynatrace) |

## Investigation sequence

1. **Separate instance, system and collector.** Count and newest record
   per instance for the heartbeat types and the collector's own telemetry,
   over the two hours before `T_END`. One instance stale and the rest
   fresh: that instance is the finding. Everything stale including
   `PC_HEALTH`: go to [feed-health.md](feed-health.md) and to step 4.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (SM51_QUEUE, SM51_STATE, PC_HEALTH)
| eval inst=coalesce(INSTANCE_NAME, NAME, host)
| stats count max(_time) as newest by source EVENT_TYPE inst
| eval age_min=round((<T_END>-newest)/60,0) | sort source EVENT_TYPE
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"SM51_QUEUE", "SM51_STATE", "PC_HEALTH"})
| fieldsAdd inst = coalesce(instance_name, name, host.name)
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name, inst}
| sort newest asc
```
2. **Read the server list.** Latest state per instance. A surviving
   instance may report a dead one with a non-active state, or the dead one
   may vanish from the list; check both. `starts` above 1 means a restart
   inside the window; the start time and the gap bound the downtime.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM51_STATE
| stats latest(STATE) as state latest(SERVICES) as services
    latest(START_TIMESTAMP) as started dc(START_TIMESTAMP) as starts latest(_time) as seen by source NAME
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM51_STATE"
| sort timestamp asc
| summarize {state = takeLast(state), services = takeLast(services), started = takeLast(start_timestamp),
    starts = countDistinct(start_timestamp), seen = max(timestamp)}, by: {log.source, name}
```
3. **Measure the gap.** For a suspect instance, count distinct polls per
   15 minutes on `SM51_QUEUE`. An even comb is the cadence; the hole is the
   outage. Compare with a healthy instance of the same system.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM51_QUEUE source=<SID>
| timechart span=15m dc(CURRENT_TIMESTAMP) as polls by INSTANCE_NAME
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM51_QUEUE" and log.source == "<SID>"
| summarize polls = countDistinct(current_timestamp), by: {slot = bin(timestamp, 15m), instance_name}
| sort slot asc
```
4. **Ask the independent sources.** CCMS availability per instance, then
   `ni_ping` (sample one record first; its fields are not documented).
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=CCMS PATH="*InstanceAsTask\\Availability*"
| stats latest(TEXT) as value latest(DATE) as d latest(TIME) as t by source PATH
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "CCMS"
    and matchesPhrase(path, "InstanceAsTask\\Availability")
| sort timestamp asc
| summarize {value = takeLast(text), avail = takeLast(ccms_avail_perc), seen = max(timestamp)}, by: {log.source, path}
```
5. **ICM and message server.** Sample one record per subtype of `SMICM`
   and `SMMS` (no confirmed field list), then apply the pattern of step 2.
   No `SMICM` records from an instance whose `SERVICES` lists ICM is a
   signal in itself.
6. **Correlate.** Around the last record of the dead instance read
   `SM21_LOG` ([system-log.md](system-log.md)), `ST22`
   ([abap-dumps.md](abap-dumps.md)) and [os-resources.md](os-resources.md).

On any other backend, translate the intent with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| One instance silent, others and `PC_HEALTH` fresh | that instance is down or cut off | steps 2–3, then SM21_LOG of the others |
| All SAP feeds silent, `ni_ping` still succeeds | collector or delivery path is down, system is up | [feed-health.md](feed-health.md) |
| All silent and `ni_ping` fails | system or network outage | report outage window; humans check sapcontrol / OS |
| `STATE` 2 or 4 for an instance | server registered but not active (shutdown, starting, passive) | confirm with step 3 |
| `starts` > 1 | restart inside the window | bound it with the gap; look for a planned change in [change-tracking.md](change-tracking.md) |
| Splunk Availability panel above 100 % | known dashboard defect (KB 160) | trust the query, cite the KB |

## What to tell the user

- Verdict per instance: up, down (from–to, system-local and UTC), restarted
  or unknown, with event type, window and the last record seen.
- Whether the collector was healthy then, whether an independent probe
  exists, and where to verify (SM51, RZ20, SMICM, SMMS, sapcontrol).

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `STATE` is 2 or 4 | `SM51_STATE` | shipped Dynatrace alert `davis.sap.sm51_state.inactive_app_servers` |
| availability below 50 % | `CCMS` | shipped Dynatrace alert `davis.sap.ccms.sys_avail` |
| no `SM51_QUEUE` record from an instance for 3× its cadence | `SM51_QUEUE` | absence alert; pair with a collector-health condition to avoid false alarms |
| NIPING failure | `ni_ping` | the only alert that works when the agent is down |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform alert.

## Documentation

- Event types — `sm51`, `sm51_state`, `ccms`, `smms`, `system_status`,
  `system_time-time-diagnosis-information`
- NIPING setup — `7-0-0-standalone-niping-utility-setup-guide` (Splunk),
  `niping-utility-setup-guide-dynatrace`
- KB 70, 159 (NIPING in the Splunk app) — `kb-70-niping-utility-sap-system-availability-check`,
  `kb-159-splunk-niping-built-in-data-collection-not-`
- KB 160, 199 (Splunk dashboard defects) — `kb-160-availability-panel-showing-wrong-result-in-`,
  `kb-199-application-servers-overview-error`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
