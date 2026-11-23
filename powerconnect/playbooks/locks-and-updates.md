# Locks and updates — SM12, SM13, enqueue server

**Use when:** "are there old lock entries", "who is locking table X",
"users get 'locked by' messages", "are there failed or stuck updates", "is
the update task active", "is the enqueue server / replicator running".
**Not for:** database-level locks and lock waits →
[database-health.md](database-health.md); qRFC / tRFC entries waiting on a
lock → [rfc-and-queues.md](rfc-and-queues.md); the dump behind a failed
update → [abap-dumps.md](abap-dumps.md).

The core insight: **SM12 is a snapshot, so a lock seen 40 times is one lock
polled 40 times, and a lock missing from the newest poll has been
released.** Reduce to the latest record per lock (client, user, table,
argument) inside a window of about two poll intervals ending at `T_END`
before you count or age anything. Summing rows over a day turns one
long-lived lock into hundreds; reading an old poll reports locks that no
longer exist. Age comes from the record (`LOCK_TIME`), not from your window.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM12` | ABAP | snapshot | one record per enqueue lock entry per poll: table, argument, mode, owner, origin, age | yes |
| `SM12_STATS` | ABAP | snapshot | lock statistics (no documentation page) | yes |
| `SM13` | ABAP | snapshot / stream | update records with header and details: state, user, transaction | yes |
| `SM13_STATE` | ABAP | snapshot | whether updating is active or deactivated per application server | yes |
| `SMENQ_SERVER` | ABAP | snapshot | enqueue server administration data: running, instance, kernel, trace level, lock table fill level | yes |
| `SMENQ_REPLICATOR` | ABAP | snapshot | the same for the enqueue replicator; only where replication is configured | no |

An empty `SM12` poll on a quiet system is normal. An empty `SM13` result is
normal too: update records exist only while pending or failed. Neither is a
coverage gap if the feed's newest record is fresh.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `GNAME` | locked table | group key for "what" | sample (Dynatrace) |
| `GARG` | lock argument (the locked key) | may contain business keys; quote sparingly | sample (Dynatrace) |
| `GMODE` | lock mode | `E` exclusive, `S` shared, `X` exclusive non-cumulative, `O` optimistic | sample (Dynatrace), SAP |
| `GOBJ` | lock object | | sample (Dynatrace) |
| `GUNAME`, `GCLIENT`, `GTCODE` | owner user, client, transaction | `GTCODE` empty for background and RFC | sample (Dynatrace) |
| `GTHOST`, `GTSYSNR`, `GTWP` | host, instance number and work process that set the lock | | sample (Dynatrace) |
| `GTDATE`, `GTTIME` | lock set date and time, system-local | in Dynatrace only as `data.gtdate`, `data.gttime`, not top-level | sample (Dynatrace) |
| `LOCK_TIME` | lock age in seconds at extraction | string; convert. On a sampled system it was short by the UTC offset and negative for fresh locks; cross-check with `GTDATE` + `GTTIME` | sample (Dynatrace) |
| `GUSE`, `GUSEVB` | owner counters: dialog owner and update-task owner | `GUSEVB` above 0 = lock was handed to the update task | sample (Dynatrace), SAP |
| `lock_start_ts` | lock start as a timestamp, Dynatrace-derived | in the sample it held the system-local `GTDATE` + `GTTIME` labelled as UTC | sample (Dynatrace) |
| `older_than_24h` | aged-lock flag, Dynatrace-derived, used by the shipped alert | `1` = aged. It read `0` on sampled locks more than 70 hours old, so cross-check with `LOCK_TIME` | sample (Dynatrace), docs |
| `VBSTATE` (SM13) | update record state | `253`, `255` = error (shipped alert) | docs |
| `VBKEY`, `VBUSR`, `VBTCODE`, `VBDATE`, `VBREPORT`, `VBMANDT` (SM13) | update key, user, transaction, date, program, client | no SM13 record existed in the sampled tenant | SAP |
| `SERVER`, `STATE`, `STATUSTEXT`, `TYPETEXT`, `RQ_V1_CNT`, `RQ_V2_CNT` (SM13_STATE subtype `SERVER` or `""`); `VB_STATE` (subtype `GLOBAL`) | update server, its state code and text (`2` / `Active` seen), update types, request counts; system-wide update state (`1` seen while active) | subtypes differ by release; meaning of other codes unconfirmed | sample (Dynatrace) |
| `NAME`, `VALUE` (SM12_STATS; SMENQ_SERVER subtype `OVERVIEW`) | one statistic or administration value per record (`Enqueue Requests`, `Server Instance Number` ...) | list the distinct `NAME` values first; `SMENQ_REPLICATOR` not sampled | sample (Dynatrace) |

## Investigation sequence

1. **Confirm the feeds and the cadence.** Count, distinct polls and newest
   record per type. The poll cadence sets the window for steps 2 and 3.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (SM12, SM12_STATS, SM13, SM13_STATE, SMENQ_SERVER, SMENQ_REPLICATOR) source=<SID>
| stats count dc(CURRENT_TIMESTAMP) as polls max(_time) as newest by EVENT_TYPE
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"SM12",
    "SM12_STATS", "SM13", "SM13_STATE", "SMENQ_SERVER", "SMENQ_REPLICATOR"})
| filter log.source == "<SID>"
| summarize {events = count(), polls = countDistinct(current_timestamp),
    newest = max(timestamp)}, by: {dt.source_entity_name}
```
2. **Aged locks now.** Window = two poll intervals ending at `T_END`.
   Latest record per lock, then age. Keep only locks seen in the newest
   poll (`seen` equal to the newest `SM12` time from step 1).
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM12 source=<SID>
| stats latest(LOCK_TIME) as age_s latest(GMODE) as mode latest(GTCODE) as tcode
    latest(GTHOST) as host latest(GUSEVB) as upd_owner latest(_time) as seen by GCLIENT GUNAME GNAME GARG
| eval age_h=round(tonumber(age_s)/3600,1) | where age_h>=24 | sort - age_h | head 30
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM12" and log.source == "<SID>"
| sort timestamp asc
| summarize {age_s = takeLast(toLong(lock_time)), mode = takeLast(gmode),
    tcode = takeLast(gtcode), host = takeLast(gthost), upd_owner = takeLast(gusevb), seen = max(timestamp)},
    by: {gclient, guname, gname, garg}
| fieldsAdd age_h = age_s / 3600.0
| filter age_h >= 24 | sort age_h desc | limit 30
```
   24 hours matches the shipped alert; for dialog locks a few hours is
   already worth a look. Tune per system.
3. **Who and what holds the most.** Same window; distinct locks per owner
   and table. A single user with thousands of locks on one table is a mass
   job, not thousands of problems.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM12 source=<SID>
| stats dc(GARG) as locks max(eval(tonumber(LOCK_TIME))) as oldest_s values(GTCODE) as tcodes by GUNAME GNAME
| sort - locks | head 20
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM12" and log.source == "<SID>"
| summarize {locks = countDistinct(garg), oldest_s = max(toLong(lock_time))}, by: {guname, gname}
| sort locks desc | limit 20
```
4. **Lock volume over time.** Count rows per `CURRENT_TIMESTAMP` (one value
   per poll) over a longer window and plot that series. Never sum polls.
5. **Failed updates.** Sample one `SM13` record first; the key and owner
   names below are SAP's and unconfirmed. Count distinct update keys,
   because a failed record is re-sent while it stays in the list.
```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SM13 source=<SID> VBSTATE IN (253, 255)
| stats dc(VBKEY) as failed_updates values(VBTCODE) as tcodes max(_time) as seen by VBUSR VBSTATE | sort - failed_updates
```
```dql
fetch logs, from: <T_START>, to: <T_END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SM13" and log.source == "<SID>"
| filter in(vbstate, {"253", "255"})
| summarize {failed_updates = countDistinct(vbkey), seen = max(timestamp)}, by: {vbusr, vbstate} | sort failed_updates desc
```
6. **Update and enqueue service state.** `SM13_STATE`: latest
   `STATUSTEXT` per `SERVER`. `SMENQ_SERVER` (and `SMENQ_REPLICATOR` where
   configured): latest `VALUE` per `NAME`, including the lock table fill
   level. A deactivated update explains growing `SM13` and `SM12`.
7. **Correlate.** Owner and start time of an aged lock against `SM37` (a
   job of that user, [background-jobs.md](background-jobs.md)), `ST22` for
   that user ([abap-dumps.md](abap-dumps.md)), `SM21_LOG` for update or
   enqueue messages ([system-log.md](system-log.md)) and `SM04` / `AL08` for
   whether the owner is still logged on ([user-activity-and-fiori.md](user-activity-and-fiori.md)).

On any other backend, translate the intent with the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Aged lock, `GUSEVB` above 0 | lock inherited by an update that has not completed | step 5 for the same user; SM13 |
| Aged lock, dialog `GTCODE`, owner still logged on | user left a transaction open in change mode | owner's team asks the user to leave it |
| Aged lock, owner not logged on, no job | orphaned lock after an abort | Basis verifies in SM12 before any deletion |
| Thousands of locks, one user and table | mass processing; risk of lock table overflow | fill level in `SMENQ_SERVER`; job owner |
| `VBSTATE` 253 / 255 records | update terminated with error; across many users at once: database or update work process problem | SM13 detail, matching `ST22` dump; [database-health.md](database-health.md), `SM13_STATE` |
| Update deactivated on a server | system stopped updating after a serious DB error | urgent: Basis, SM14 |
| `SMENQ_SERVER` silent while other feeds are fresh | extractor issue or enqueue server problem | [system-availability.md](system-availability.md) |

## What to tell the user

- Aged locks from the newest poll: table, owner, client, transaction, age,
  poll time and count. Give the lock argument only if the user needs it.
- Failed updates: distinct count by user and transaction, state values.
- Where to verify: SM12, SM13, SM14 (update administration), SMENQ.
- Never suggest deleting a lock or update record unless the owner and
  Basis have confirmed it is orphaned.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `older_than_24h` = 1 | `SM12` | shipped Dynatrace alert `davis.sap.sm12.aged_locks`; elsewhere compute from `LOCK_TIME` > 86400 |
| `VBSTATE` 253 or 255 | `SM13` | shipped Dynatrace alert `davis.sap.sm13.failed_update` |
| locks per poll above the system's normal peak | `SM12` | per-poll count; lock table overflow precursor |
| update deactivated; enqueue server or replicator not running | `SM13_STATE`, `SMENQ_SERVER`, `SMENQ_REPLICATOR` | confirm the state field by sample |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform alert.

## Documentation

- SM12, SM13, SM13_STATE — `sm12`, `sm13`, `sm13_state`
- Enqueue — `smenq_server-enqueue-server-admin-data`, `smenq_replicator-enqueue-replicator-admin-data`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
