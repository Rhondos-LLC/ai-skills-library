# Alert builder — turn a condition into a platform alert

**Use when:** the user wants an alert, KPI threshold or detection on SAP
data ("alert me when ...", "tune this alert", "why does it fire so
often"), or another playbook's "Alert ideas" need to become a definition.
**Not for:** investigating the condition itself → the topic playbook from
[../SKILL.md](../SKILL.md) · what a shipped security detection means →
[security-audit.md](security-audit.md) · no data to alert on →
[feed-health.md](feed-health.md) · source-side KPI or event definitions in
the agent → [extractor-config-advisor.md](extractor-config-advisor.md)

The core insight: **an alert is a query that runs forever, so the record
shape decides whether it is correct.** A snapshot type repeats the same
bad state on every poll and a stream type reports each occurrence once.
An alert written as "any record with state X" on a snapshot fires every
five minutes for as long as the state lasts; on Dynatrace, where shipped
alerts match single records with no aggregation, that is one event per
record. Design the entity key and the suppression before the threshold,
and prove the firing rate against history before handing anything over.

Hand the definition to the user as text. Do **not** create, enable or
change an alert, saved search, pipeline processor or KPI unless the user
explicitly asks for that and a tool for it exists.

## Where alerts live

| Platform | Mechanism | Use it for | Source |
|---|---|---|---|
| Splunk | **Alert Manager** in the PowerConnect app (9.1.0+): alerts built from templates filtered by category; fields are name, description, template, systems (from the `pc_sap_systems` lookup), search (unlockable), app, frequency or cron, time range, trigger condition, throttling; actions are alert log event, email, triggered alerts | first choice when the app is installed | `creating-custom-alerts` |
| Splunk | **Panel alerts** (alerting framework): a bell icon in a panel's toolbar creates an alert from that panel's search | when a panel already shows the condition | KB 181 |
| Splunk | **KPI Engine** (9.2.0+, KPI Configuration under Events and Alerts): 35 ABAP metrics evaluated against static or dynamic thresholds (baseline over 7, 30 or 90 days, in standard deviations), per system or global, with maintenance windows | metric thresholds and baselines; not event conditions | `kpi-engine` |
| Splunk | plain **saved search alert** | fallback without the app, or for logic no template covers | Splunk platform |
| Splunk ES | **correlation searches** from the content pack | security detections; see [../reference/detections-splunk-es.md](../reference/detections-splunk-es.md) | `list-of-correlation-searches` |
| Dynatrace | **Davis alerts**: event processors in the PowerConnect OpenPipeline, each with a DQL matcher; a match raises a `CUSTOM_ALERT` Davis event on the SAP instance entity. Enabled by default; listed with fire counts in the app's Alerts section; own ones under Custom Alerts | any per-record condition | `davis-alerts`, `list-of-alerts-dynatrace` |
| Agent | **KPI / Event Definitions** (8.03+ / 8.04+) emit `_METRICS_` / `_EVENTS_` records from data already extracted | when the platform should receive a ready-made metric | KB 214, KB 225 |
| Other | scheduled query + threshold + suppression key | generic recipe below | — |

## Matcher syntax (Dynatrace), from the shipped alerts

A matcher is one boolean DQL expression evaluated against each ingested
record. It cannot aggregate, count or look back.

```dql
matchesValue(service.name, "sap:abap") and matchesValue(dt.source_entity_name, "SM13") and (matchesValue(vbstate, "253") or matchesValue(vbstate, "255"))
matchesValue(dt.source_entity_name, "ST06") and isNotNull(free_mem) and free_mem < 10
matchesValue(dt.source_entity_name, "SM12") and matchesValue(older_than_24h, "1")
matchesValue(dt.source_entity_name, "CCMS") and matchesPhrase(path, "InstanceAsTask\\Availability") and ccms_avail_perc < 50
```

Patterns to copy: start with `service.name` and `dt.source_entity_name`
(add `dt.source_entity_type` for subtypes); states with `matchesValue`,
free text with `matchesPhrase`; guard optional fields with `isNotNull`;
numeric tests only on fields that arrive numeric (`ccms_avail_perc`,
`free_mem`). A string field, including the derived flag `older_than_24h`,
needs `matchesValue` or a derived numeric field first; a backslash inside
a string literal is written `\\`. All shipped matchers:
[../reference/alerts-dynatrace.md](../reference/alerts-dynatrace.md).
The documentation recommends duplicating a shipped alert and editing the
copy; an OpenPipeline configuration update re-enables the shipped ones.

## Building sequence

1. **Check whether a shipped alert already covers it.** Dynatrace: search
   `reference/alerts-dynatrace.md` by event type. Splunk: ask which app
   version is installed and whether Alert Manager has a template for the
   category; for security, search `detections-splunk-es.md`. If one
   exists, the work is tuning, not building. Two shipped Dynatrace alerts
   are disabled by default because they raise one event per record
   (blocked threads, IAS users without MFA); your design has that risk.
2. **Define the condition from the data's own history.** Read the topic
   playbook, sample one record, and fix four things in writing:
   - *entity key* — what one alert instance is about (job, queue,
     device, interval, destination), plus `SID`;
   - *state or measure* — field and bad values, confirmed by sample,
     converted to a number if compared;
   - *window* — snapshots: at least two poll intervals; streams: the
     period over which occurrences are counted;
   - *threshold* — from a shipped alert or the documentation if one
     exists; otherwise from the 7–30 day distribution (for example a
     value exceeded on under 1 % of polls), as a starting point to tune.
3. **Write the query for the record shape.**
   - *Snapshot* (queues, locks, sessions, devices, periodic checks):
     latest record per entity in the window, then test the state;
     suppress per entity for as long as the state normally lasts.
   - *Event stream* (dumps, audit messages, failed messages): count
     occurrences per entity in the window, compare, throttle per entity.
   - *Header + detail*: filter the subtype, count distinct run ids.
   - *Absence* ("no orders", "job did not run"): needs a schedule and a
     window; a per-record matcher cannot express it.
   Worked example, a periodic check that must not fire on every poll
   (`ADS_CHECK`, fields and the failing value `Error` seen in a sample):

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ADS_CHECK
| stats latest(TEST_RESULT) as result latest(TEST_RESULT_MSG) as msg by source DESTINATION
| where result="Error"
```

   Schedule every 10 minutes over the last 20, trigger when results > 0,
   throttle 4 hours on `source, DESTINATION`. The Dynatrace equivalent is
   a matcher, which fires for every failing record; whether Davis merges
   repeats on the same entity into one problem is platform behaviour to
   confirm in the tenant:

```dql
matchesValue(service.name, "sap:abap") and matchesValue(dt.source_entity_name, "ADS_CHECK") and matchesValue(test_result, "Error")
```

4. **Back-test, read-only, over history.** Run the condition over 7–30
   days anchored on `T_END`; report how many evaluation periods would
   have fired and on how many entities. A Dynatrace matcher is a filter:

```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "ADS_CHECK"
| filter matchesValue(test_result, "Error")
| summarize {matching_records = count(), entities = countDistinct(destination)}, by: {day = bin(timestamp, 24h), log.source}
| sort day asc
```

   For a scheduled Splunk alert, replay the schedule in time buckets the
   size of the alert interval:

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ADS_CHECK
| bin _time span=10m
| stats latest(TEST_RESULT) as result by _time source DESTINATION
| where result="Error"
| bin _time span=1d
| stats count as firing_periods dc(DESTINATION) as entities by _time source
```

   Zero firings in 30 days may mean a loose threshold or a condition
   that never occurs; dozens per day means nobody will read it. Adjust
   and re-run before proposing.
5. **Hand over the definition as text**, in the form of the target
   mechanism:
   - Splunk: name, description, template (if any), systems, search,
     schedule, time range, trigger condition, throttle fields and period,
     action. Email needs Splunk mail settings.
   - Dynatrace: alert name, matcher, the entity key fields to show in
     the event, whether it duplicates a shipped alert, and that it fires
     per matching record.
   - Other backends: query (idioms from the profile, see
     [../backends/other.md](../backends/other.md)), schedule, comparison,
     suppression key and period, notification target.
   Always add the back-test numbers, the fields confirmed by sample, and
   what the alert does not cover (systems, filtered-out records).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Back-test fires on every poll for hours | snapshot condition without suppression | latest-per-entity plus throttle; on Dynatrace accept merging or move to an aggregated detector |
| Back-test never fires, but the user saw the problem | wrong field, wrong value, or the record was filtered at source | sample a record from the incident time |
| Condition needs a count, a rate or an absence on Dynatrace | beyond a per-record matcher | propose a scheduled DQL-based detector in the platform (a Dynatrace feature, not documented by PowerConnect) or an agent KPI definition |
| No bell icon on newer panels (Splunk app 7.3.0) | alert framework KV store not initialised | KB 181; the fix runs `outputlookup`, so a Splunk admin runs it, not you |
| ES correlation searches enabled but no notables | searches are orphaned | KB 174 (slug starts `kb-147-splunk-orphaned`) |
| KPI events during planned downtime | no maintenance window defined | KPI Engine → Maintenance Windows |

## What to tell the user

- Whether a shipped alert or template already covers the need.
- The definition, ready to paste, and the back-test: window, firing
  periods, distinct entities, noisiest one.
- Thresholds marked as shipped, documented or "starting point".
- Who creates it and where; that you have not created anything.

## Documentation

- Splunk: `creating-custom-alerts`, `kpi-engine`,
  `kb-181-initializing-new-alerting-framework-searche`,
  `list-of-correlation-searches`,
  `kb-147-splunk-orphaned-correlation-searches-in-es-` (KB 174)
- Dynatrace: `davis-alerts`, `list-of-alerts-dynatrace`
- Agent KPI and event definitions:
  `kb-214-how-to-generate-and-send-kpis-metrics`,
  `kb-225-how-to-generate-and-send-events`

`alert-notification-service` is a Cloud agent input for SAP BTP alerts,
not an alerting mechanism ([cloud-services.md](cloud-services.md)).
Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
