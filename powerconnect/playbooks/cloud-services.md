# Cloud services — BTP, IAS, SuccessFactors, Ariba and other SAP cloud data

**Use when:** the question is about data from the PowerConnect Cloud
agent: BTP audit logs, Cloud Foundry logs, BTP alerts, subaccount cost,
IAS, SuccessFactors, Ariba, Fieldglass, CPQ, SAP Analytics Cloud, API
Management, Cloud ALM, Data Intelligence, Datasphere, S/4HANA Cloud public
edition, synthetic HTTP checks, or "what cloud data do we have?".
**Not for:** CPI / Integration Suite messages and iFlows →
[integration-messages.md](integration-messages.md); certificate expiry →
[certificates-and-licenses.md](certificates-and-licenses.md); the Cloud
agent not sending → [feed-health.md](feed-health.md); on-premise ABAP
audit → [security-audit.md](security-audit.md); SAP Cloud Connector (Java
agent) → [java-stack.md](java-stack.md).

The core insight: **a cloud event type exists only if someone created and
licensed an input for that tenant.** Nothing is on by default. Each input
polls one API of one tenant, is licensed per plugin per production tenant,
and stamps its records with the System ID typed into the input. So an
absent type means "no input configured", never "no activity", and the SID
is a label chosen by an administrator, not an SAP system ID. Start every
cloud question with the census in step 1.

Cloud records differ from ABAP records in three ways:

- **Field names are lowercase** in the samples seen (Dynatrace). Confirm
  the casing by sample on Splunk; a wrongly cased name returns zero rows.
- **No `CURRENT_TIMESTAMP` / `UTCDIFF`.** Times come from the cloud API,
  normally UTC; use the platform event time and check one sample.
- **Several state fields are added by the Dynatrace pipeline** for the
  shipped alerts (`http_ping_failed`, `cloud_syslog_http_status`,
  `fg_records_failed`, ...). Elsewhere derive them from raw fields.

## Fields every cloud record carries

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `event_type` | event type (Dynatrace: also `dt.source_entity_name`) | lowercase | sample (Dynatrace) |
| `sid` | System ID set on the input (= `source` / `log.source`) | | sample (Dynatrace) |
| `input_id` | which input produced it | `audit-log-neo`, `cpi-audit-log` seen | sample (Dynatrace) |
| `system_type`, `platform`, `host` | product family; environment; machine running the Cloud agent (not an SAP host; Dynatrace: `host.name`) | `btp`, `cpi`, `sf`, `api-m`, `synthetics`; `Neo`, `CF`. Not on every type | sample (Dynatrace) |

## Data by service

`matcher` = named in a shipped Dynatrace alert matcher (may be derived).
*(name?)* = event type not in the catalog; find its name in the census.

**BTP platform**

| Service | Event type | What it answers | Key fields | Confirmed |
|---|---|---|---|---|
| Audit log (Neo, CF) | `cp_audit_log` | security events, configuration changes, personal-data access and modification | `category` (`audit.security-events`, `audit.configuration`, `audit.data-access`, `audit.data-modification`), `user`, `tenant`, `account`, `application`, `time`, `uuid`; detail is in the message text (`content` is plain text, not JSON). A value with a trailing dot (`audit.data-access.`) was seen: match with a prefix test | sample (Dynatrace); category list: docs |
| Cloud Foundry syslog (beta) | `syslog` | application errors, HTTP status and latency of bound apps | `cloud_syslog_http_status`, `cloud_syslog_response_time` (seconds) | matcher |
| Alert Notification | `btp_alert` | platform alerts: app crash, failed health check | `category` (`ALERT`), severity, subject, resource | `category`: matcher; rest: docs prose |
| Destination certificates | `btp_certificate` | certificate inventory and expiry | `btp_cert_days_to_expiry`, `btp_cert_expired` | matcher |
| Billing | `monthly_subaccounts_cost` | estimated monthly cost per subaccount, service and plan | `subaccount_name`, `service_name`, `plan_name`, `cost`, `currency`, `usage`, `report_year_month`, `estimated` | sample (Dynatrace) |
| Job Scheduling | *(name?)* | job schedules, runs, status, errors | sample first | unconfirmed |
| Platform users (Neo) | `cp_users` | user inventory with roles | `user_name`, `roles` | sample (Dynatrace) |
| Synthetics | `http_ping` | endpoint availability, response, certificate status | `http_ping_failed` (string `1` / `0`), `name`, `url`, `response_time`, `certificates` | sample (Dynatrace) |

**Identity**

| Service | Event type | What it answers | Key fields | Confirmed |
|---|---|---|---|---|
| IAS audit | `ias_audit_log` | logons, failed logons, configuration changes in Identity Authentication (delivered through the BTP audit log service) | same `audit.*` categories as `cp_audit_log` | docs; no record seen |
| IAS users | `ias_user` | user inventory, failed attempts, MFA state | `failed_login_attempts`, `ias_mfa_disabled` (`1`) | matcher |

**Integration and operations**

| Service | Event type | What it answers | Key fields | Confirmed |
|---|---|---|---|---|
| CPI audit (Neo) | `cpi_audit_log` | who read or changed which integration object | `action`, `obj_type`, `obj_name`, `username`, `user_type`, `client_ip`, `node_type`, `change_id` | sample (Dynatrace) |
| CPI messages, artifacts | `cpi_message`, `cpi_artifact`, `cpi_inventory` | → [integration-messages.md](integration-messages.md) | `custom_status`, `iflow_status` | matcher |
| API Management | `api_management_performance`; per-call logs through a syslog input | API response times, volumes, HTTP status; call logs as defined in the proxy logging policy | `api_proxy`, `request_url`, `response_code`, `average_response_time`, `target_response_time`, `call_counter`, `errors_counter` (numbers, per time bucket) | sample (Dynatrace); syslog: unconfirmed |
| Cloud ALM | *(name?)* status events; CPI metrics | service disruptions, degradations, maintenance; CPI datastore and database usage | sample first | unconfirmed |

**SaaS applications**

| Service | Event type | What it answers | Key fields | Confirmed |
|---|---|---|---|---|
| SuccessFactors operations | `sf_em_event`, `sf_employee_replication` | Execution Manager jobs and integrations (status, start, end); employee replication errors | `sf_em_event`: subtypes `START`, `END`, `ERROR`; `name`, `description`, `time`, `process` (a JSON string holding `state`, `type`, `definition_name`) | `sf_em_event`: sample (Dynatrace); replication: unconfirmed |
| SuccessFactors processes | `sf_payroll_run_results`, `sf_payroll_configuration`, `sf_onboarding_process` | payroll runs synced from ECP; onboarding and offboarding state | sample first | unconfirmed |
| SuccessFactors audit | `sf_odata_api_audit_log`, `sf_compound_api_audit_log`, `sf_change_audit_report` | API calls; who changed which record (change reports arrive by SFTP) | OData log: `user_id`, `api_call`, `entity_name`, `processing_time`, `request_url`, payload `status` | OData log: sample (Dynatrace); others: unconfirmed |
| Ariba | `ariba_audit_log` | authentication, data access, configuration changes | `loglevel` (`SEVERE`) | matcher |
| Fieldglass | `fg_audit_trail` | integration runs between Fieldglass and other systems | `fg_records_failed` | matcher |
| CPQ; Analytics Cloud | `cpq_event_log`, `cpq_audit_trail_user_action`; `sac_activities` | CPQ events and user audit trail; SAC story access, configuration changes, logons | sample first | unconfirmed |

**Data platforms and S/4HANA Cloud**

| Service | Event type | What it answers | Key fields | Confirmed |
|---|---|---|---|---|
| Data Intelligence | `di_metric`, `di_graphs` | Kubernetes resource metrics; pipeline (graph) runs | `metric_name`, `metric_value`; `di_graph_status` (`Failed`) | matcher |
| Datasphere | `datasphere_task_log`, `datasphere_space_memory`, `datasphere_oom`, `datasphere_admission_control` | task runs, space memory, out-of-memory and rejection events | sample first; no documentation page | unconfirmed |
| S/4HANA Cloud public edition | `s4hana_cloud_audit_log` | security audit log of the tenant | `event_id` (for example `AU1`), `log_tstmp` (UTC), `slgmand`, `user_Id`, `terminal_name`, `slgrepna`, `slgtc`, `rsau_text`, `param_a`..`param_d` | docs |
| S/4HANA Cloud public edition | `s4hana_cloud_user`, `s4hana_cloud_user_change` | user inventory; user and role changes | sample first | unconfirmed |

The S/4HANA Cloud audit log uses SM20-style message ids, so the patterns
in [security-audit.md](security-audit.md) apply with these field names.

## Investigation sequence

1. **Census: which cloud inputs exist and are they current?** Keep the
   window short (2 h, then 24 h); this is the one query without an event
   type filter.

```spl
index=<IDX> sourcetype=sap:cloud
| stats count max(_time) as newest by source event_type input_id
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:cloud"
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name, input_id}
```

   Polled inventories (certificates, cost, users) are snapshots; audit
   logs and syslog are event streams. Judge freshness per input.
2. **Sample one record** of the type in question; the docs rarely name fields.
3. **Aggregate before reading records.** For audit-type logs start with
   the category and actor distribution:

```spl
index=<IDX> sourcetype=sap:cloud event_type=cp_audit_log
| stats count dc(user) as users max(_time) as last by source category
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:cloud" and dt.source_entity_name == "cp_audit_log"
| summarize {events = count(), users = countDistinct(user), last = max(timestamp)}, by: {log.source, category}
```

   Technical OAuth clients usually dominate `audit.data-access`; separate
   them from named users first.
4. **Check health conditions** with the shipped matchers, using the step
   3 skeleton with the condition as filter. On Dynatrace they work as
   written (look for open problems first); elsewhere rebuild the
   condition from sampled raw fields. Only the `http_ping` matcher has
   been run against data; for a numeric one, sample the field first and
   wrap it in `toDouble()` if it is a string.

| Condition (Dynatrace matcher) | Event type | Meaning |
|---|---|---|
| `http_ping_failed == "1"` (confirmed by sample) | `http_ping` | endpoint not HTTP 200 or connection error |
| `cloud_syslog_http_status >= 500`; `cloud_syslog_response_time > 5` | `syslog` | CF app server error; request slower than 5 s |
| `metric_name == "sap_pod_status_ready"` and `metric_value == "0"` | `di_metric` | Data Intelligence pod not ready |
| `di_graph_status == "Failed"` | `di_graphs` | graph run failed |
| `fg_records_failed > 0` | `fg_audit_trail` | Fieldglass integration run with failed records |
| `loglevel == "SEVERE"` | `ariba_audit_log` | severe Ariba audit record |
| `failed_login_attempts >= 5`; `ias_mfa_disabled == "1"` | `ias_user` | repeated failed logins; no MFA (alert off by default) |
| `category == "ALERT"` | `btp_alert` | BTP Alert Notification of category ALERT |

5. **Drill** into a handful of records for one user, app, job or tenant.
6. **Correlate.** IAS logon failures with the application's own audit
   log; CF `syslog` errors with `btp_alert` and `http_ping`; `cpi_message`
   with on-premise `STAD` for end-to-end flows (see integration-messages).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Event type absent from the census | no input for it, input disabled, or plugin not licensed | coverage gap; point to PowerConnect Cloud → Inputs |
| All cloud types stale at once | Cloud agent down or output failing | [feed-health.md](feed-health.md); agent logs in `/opt/powerconnect/logs` or `cf logs <app> --recent` |
| One input stale, others fine | expired API credential or revoked scope on that tenant | owner renews the OAuth client or service key |
| IAS audit empty, feed just created | the IAS-to-audit-log feed needs about 15 minutes | re-check later |
| Zero rows on Splunk with a field filter | field-name casing differs | sample and correct |

## What to tell the user

- Service, tenant label (SID), input, window and counts. Treat user
  names, e-mail addresses and HR or payroll content as sensitive: report
  counts, not personal records, unless explicitly asked.
- Where a human verifies: BTP cockpit, IAS admin console, SuccessFactors
  Execution Manager, the PowerConnect Cloud UI (Inputs).
- What is not collected, by service, and that enabling it needs an input
  and a licence per production tenant (KB 215).

## Alert ideas

Start from the shipped Dynatrace alerts above (`davis.sap.cloud.*`). Additions:

| Condition | Event type | Notes |
|---|---|---|
| Cloud input silent beyond 2× its poll interval | any, plus `agent_health` | per input, not per stack |
| Spike of failed logons in IAS or S/4HANA Cloud | `ias_audit_log`, `s4hana_cloud_audit_log` | baseline per tenant |
| SuccessFactors job or replication failure | `sf_em_event`, `sf_employee_replication` | status values from a sample |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `powerconnect-cloud-inputs`, `cloud-troubleshooting`,
  `kb-215-powerconnect-cloud-licensing`
- BTP and IAS — `sap-btp-audit-logs`, `cloud-foundry-syslog`,
  `alert-notification-service`, `destination-certificates`,
  `job-scheduling-service`, `ias-audit-log`
- `sap-successfactors`, `successfactors-execution-manager`,
  `successfactors-change-audit-reports`, `sap-ariba`, `sap-fieldglass`,
  `sap-cpq`, `sap-analytics-cloud`, `sac-user-activities`
- `sap-api-management`, `sap-api-management-syslog`, `sap-cloud-alm`,
  `sap-cloud-alm-status-events`, `sap-cloud-alm-metrics-for-cpi`,
  `sap-data-intelligence-cloud-edition`,
  `sap-s-4-hana-cloud-public-edition`,
  `sap-s-4-hana-cloud-public-edition-audit-logs`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
