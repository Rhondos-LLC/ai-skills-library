# Integration messages — ABAP PI, PI/PO, Cloud Integration (CPI)

**Use when:** PI/PO or CPI messages fail or hang, an iFlow or channel is in
error, an Adapter Engine queue is stopped, or one message must be followed
across ABAP, PO and CPI.
**Not for:** IDocs → [idocs.md](idocs.md); qRFC queues and destinations
under the Integration Engine → [rfc-and-queues.md](rfc-and-queues.md);
JVM health of PO → [java-stack.md](java-stack.md); other BTP services →
[cloud-services.md](cloud-services.md).

The core insight: **three collectors, three vocabularies, none a complete
ledger.** `pi_message` is capped (100 messages per interval, per filter,
per instance by default) and re-sends a message while it is in flight;
`SXMB_MONI` sends nothing for an interface missing from its metric filter.
Take the latest record per message id, treat counts as a floor, and never
reconcile with them (KB 221). On Dynatrace the top-level `status` is the
platform's log status, not the message status.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SXMB_MONI` | ABAP | header + detail | Integration Engine messages; `PAYLOAD` subtype = one record per payload element | no; needs an SXMB filter row per interface |
| `pi_message` | Java | event stream | Adapter Engine messages with optional logs and staged payload | no (PI plug-in) |
| `channel_status` | Java | snapshot | channel state, activation state, short and process log | no (Channel plug-in) |
| `pi_queues`, `pi_performance` | Java | snapshot / batch | Adapter Engine queue size, threads, started state; performance aggregates | check by count; KB 210 |
| `cpi_message` | Cloud | event stream | message processing logs per iFlow, optional message store | input must exist |
| `cpi_artifact`, `cpi_inventory`, `cp_audit_log` | Cloud | snapshot / stream | deployed artifacts and status (`iflow_status` `ERROR` in the shipped alert); packages and endpoints; BTP audit log | input must exist |
| `SRT_LOG`, `SOA_PING`, `AIF_ERROR` | ABAP | stream / snapshot / stream | web-service error log, consumer-proxy ping, AIF errors | `SRT_LOG` yes; others no |

## Fields that matter

Java and Cloud fields are lowercase on both backends. Java records carry
`event_type`; Cloud records of one sampled system did, of another did not:
confirm the tag on Splunk.

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `message_id`, `message_key` | PO message id (UUID); id + direction + node | entity key | sample (Dynatrace) |
| `status` (pi_message) | PO status (`data.status` on Dynatrace) | `success`, `toBeDelivered`, `waiting`, `delivering`, `systemError` seen; `holding`, `canceled` docs | sample (Dynatrace) + docs |
| `msg_state`, `pi_message_status` | Dynatrace-derived: normalised state; raw status | `Success`, `System Error`, `Waiting`, `To Be Delivered`, `Delivering` seen; alerts also use `Holding` | sample (Dynatrace) + docs |
| `direction`, `qos` | `INBOUND` / `OUTBOUND`; quality of service | `EO` seen; `EOIO`, `BE` = SAP | sample (Dynatrace) |
| `sender_name`, `sender_interface`, `receiver_name`, `receiver_interface`, `integration_scenario` | who talks to whom, and the ICO | group-by keys | sample (Dynatrace) |
| `start_time`, `end_time`, `duration`, `logs`, `payload_staged` | ISO UTC times; ms; audit log; payload | payload is sensitive | sample (Dynatrace) |
| `passport_tid`, `trace_id` | SAP passport transaction id | correlation key | sample (Dynatrace) |
| `channel_id`, `channel_name`, `component_name`, `channel_state`, `activation_state` | channel identity; runtime and admin state | `OK`, `ERROR`, `STARTED` seen; alerts also use `STOPPED` | sample (Dynatrace) + docs |
| `pi_queue_stopped`, `pi_queue_thread_util` | Dynatrace-derived queue flags | `"1"`; `>= 100` | docs (alert) |
| `message_guid`, `correlation_id`, `application_message_id`, `integration_artifact_name` | CPI message id; id shared by chained flows; sender-set id; iFlow | entity and group-by keys | sample (Dynatrace) |
| `status` / `custom_status` (cpi_message) | processing status (`data.status` on Dynatrace); the two can differ on one record | `FAILED`, `COMPLETED` seen; `RETRY` docs | sample (Dynatrace) |
| `error_msg`, `error_step_id`, `log_start`, `log_end`, `custom_headers`, `message_store` | error text, failing step, ISO UTC times; iFlow-defined keys; persisted payloads (KB 208) | payloads are sensitive | sample (Dynatrace) |
| `MSGGUID`, `PAYLOAD_NAME`, `PATH`, `VALUE` | SXMB_MONI `PAYLOAD` records; header fields (status, interface, times; SXMSPMAST names such as `MSGSTATE` expected) were not seen | | sample (Dynatrace); header = SAP, sample first |

## Investigation sequence

1. **Confirm the feeds** per stack (adapter idiom "count and freshness per
   type"), then sample each type in play. Message times are ISO UTC.

2. **PO: failed and stuck messages by interface** — latest record per
   message, then keep the non-final and error states.

```spl
index=<IDX> sourcetype=sap:java event_type=pi_message
| stats latest(status) as status latest(sender_name) as sender latest(receiver_name) as receiver latest(receiver_interface) as interface by message_id
| search status IN ("systemError", "waiting", "holding", "toBeDelivered")
| stats count as messages by sender receiver interface status
| sort - messages
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:java" and dt.source_entity_name == "pi_message"
| sort timestamp asc
| summarize {state = takeLast(msg_state), sender = takeLast(sender_name), receiver = takeLast(receiver_name), interface = takeLast(receiver_interface)}, by: {message_id}
| filter in(state, {"System Error", "Waiting", "Holding", "To Be Delivered"})
| summarize messages = count(), by: {sender, receiver, interface, state}
| sort messages desc
```

3. **PO: channels not healthy** — latest state per channel. For a stopped
   or saturated Adapter Engine queue, sample `pi_queues` the same way.

```spl
index=<IDX> sourcetype=sap:java event_type=channel_status
| stats latest(channel_state) as channel_state latest(activation_state) as activation_state latest(_time) as seen by channel_id channel_name component_name
| where channel_state!="OK" OR activation_state="STOPPED"
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:java" and dt.source_entity_name == "channel_status"
| sort timestamp asc
| summarize {channel_state = takeLast(channel_state), activation_state = takeLast(activation_state), seen = max(timestamp)}, by: {channel_id, channel_name, component_name}
| filter channel_state != "OK" or activation_state == "STOPPED"
```

4. **CPI: failed messages by iFlow**, with the failing step and one error
   text. On Dynatrace use `custom_status` (the shipped alert's field).

```spl
index=<IDX> sourcetype=sap:cloud event_type=cpi_message
| stats latest(status) as status latest(integration_artifact_name) as iflow latest(error_step_id) as step latest(error_msg) as error by message_guid
| search status IN ("FAILED", "RETRY")
| stats count as messages latest(error) as example by iflow step status
| sort - messages
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:cloud" and dt.source_entity_name == "cpi_message"
| sort timestamp asc
| summarize {state = takeLast(custom_status), iflow = takeLast(integration_artifact_name), step = takeLast(error_step_id), error = takeLast(error_msg)}, by: {message_guid}
| filter in(state, {"FAILED", "RETRY"})
| summarize {messages = count(), example = takeAny(error)}, by: {iflow, step, state}
| sort messages desc
```

5. **Trace one message.** Filter its type on the id you have (`MSGGUID`,
   `message_id` or `message_guid`), sort by time and project state, times
   and error text; then walk outward with these keys.

| Hop | Join | How sure |
|---|---|---|
| ABAP proxy ↔ PO | `MSGGUID` (32 hex, upper case) ↔ `message_id` (same id with dashes, lower case) | SAP XI behaviour; verify on one known message |
| PO ↔ ABAP / Java workload | `passport_tid` / `trace_id` ↔ `dsr`, STAD / STATS passport | shipped "Java PI - ABAP Correlation" dashboard |
| CPI flow ↔ CPI flow | `correlation_id` | sample |
| CPI ↔ S/4 | `cpi_message` ↔ STAD3 / STATS | shipped "CPI - S/4 HANA Correlation" dashboards; confirm the join field by sample |
| CPI ↔ PO | no shared id by default: `application_message_id`, a `custom_headers` key, or endpoint + time from `error_msg` | weak; say so |

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Exactly 100 `pi_message` per poll; `BE` messages missing | cap reached; logged (not staged) messages purged before the poll (KB 99) | `agent_health` MBean `po-ws.message-list.limit-reached`; narrow filters |
| Failures missing while "only faulty" is set | retries sit in `waiting` and are filtered (PI/PO Messages page) | lag setting or exclude filter |
| `cpi_message` `FAILED` at one `error_step_id` | receiver or mapping error | open `alternate_web_link` (human) |
| No `SXMB_MONI` for an interface | not in the SXMB filter; payload missing before SP 7.03 if not named `MainDocument` (KB 175) | metric filter |
| No `pi_message` on an HTTPS-only PO; PO threads blocked with `pi_performance` on | localhost certificate mismatch (KB 223); SAP servlet bug, Note 3442208 (KB 210) | local HTTP or EJB connection type (8.3); patch or disable the extractor |

## What to tell the user

- Distinct messages by interface or iFlow and state, the failing step,
  one error text and the ids; verify in SXMB_MONI, the PO message and
  channel monitors or the CPI monitor. Restart or cancel is a human call.
- State the limits: capped collection, filters, payloads not collected.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `msg_state` `System Error`; `Waiting` / `Holding` | `pi_message` | shipped `davis.sap.java.pi_message.system_error`, `.stuck` |
| `channel_state` `ERROR`; `activation_state` `STOPPED`; `pi_queue_stopped` `1`; `pi_queue_thread_util >= 100` | `channel_status`, `pi_queues` | shipped `davis.sap.java.channel_status.error`, `.stopped`, `davis.sap.java.pi_queues.stopped`, `.saturated` |
| `custom_status` `FAILED`; `iflow_status` `ERROR` | `cpi_message`, `cpi_artifact` | shipped `davis.sap.cloud.cpi_message.failed`, `.cpi_artifact.error` |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `sxmb_moni`, `pi-po-messages`, `sap-cpi-messages`, `runtime-artifacts`,
  `sap-cloud-platform-integration-cpi`, `srt_log-web-services-error-log`,
  `soa_ping-soamanager-consumer-proxy-ping`
- KB articles: `kb-99-sap-pi-po-missing-messages`,
  `kb-175-sxmb_moni-message-payload-is-not-collected`,
  `kb-69-powerconnect-java-disabling-pi-message-colle`,
  `kb-91-powerconnect-java-advanced-pi-filter-configu`,
  `kb-208-capturing-sap-cpi-payloads-using-powerconne`,
  `kb-210-performance-issues-related-to-po-performanc`,
  `kb-221-using-the-powerconnect-java-agent-for-pi-po`,
  `kb-223-po-connection-test-fails-with-chainverifier`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
