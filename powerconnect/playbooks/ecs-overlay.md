# ECS overlay — landscapes operated by SAP (RISE, private cloud)

**Use when:** `customer-profile.md` says the landscape line is ECS/RISE.
Read this *after* the playbook you were routed to. It does not replace that
playbook; it changes how the investigation is bounded and how it ends.
**Not for:** landscapes the customer operates itself; skip this file.
Installing PowerConnect on RISE →
[install-upgrade-advisor.md](install-upgrade-advisor.md).

The core insight: **on ECS the customer keeps the application layer and
loses everything beneath it.** OS, database, kernel, profile parameters
(RZ10) and infrastructure are SAP's to change and the customer's to
evidence: there is no OS shell, no privileged HANA access, and parameter
changes go through service requests. A recommendation such as "restart the
instance" or "raise the parameter" is therefore not an action; it is a
service request that needs evidence attached. Investigate to the evidence
boundary, never past it, and say on which side of the line the cause sits.

## What changes in every playbook

1. **Application-layer telemetry is still fully the customer's** (jobs,
   IDocs, queues, dumps, locks, users, audit log, PowerConnect itself).
   Nothing changes in how you query it.
2. **One lens crosses the line.** `ST06*` (host CPU, memory, disk via
   saposcol) still shows the host without OS access: visibility across the
   boundary, not OS coverage. It evidences a request; it fixes nothing.
3. **Healthy application-layer coverage is never full-stack coverage.**
   Say what the feed cannot see in the same breath as what it can. LogServ
   is an optional subscription, not a given; check the profile.
4. **Portal and contract facts come from the registry below, never from
   assumption** (maintenance windows, availability reports, ratios).

## Ownership verdict — how every investigation ends

Close each finding with exactly one verdict and the evidence behind it:

| Verdict | Use it when | What you hand over |
|---|---|---|
| **Customer-actionable** | the cause and the fix are in the application layer: job scheduling, variants, IDoc and queue reprocessing, user and role administration, custom code, PowerConnect configuration in the productive client | the SAP transaction, the action, the owning team |
| **ECS service request** | the fix needs OS, database, kernel, profile parameter, instance restart, network / proxy or client 000 access | a ready-to-paste evidence block: symptom, time window in system-local time and UTC, SID, instance, counts, the queries run, and what was ruled out at application level |
| **Insufficient evidence** | the application layer shows the symptom but the cause could sit on either side, or the layer where it would show is not collected | what is missing (extractor, LogServ, a registry fact), who can supply it, and the cheapest next observation |

Rules for choosing:

- Decide by **where the fix is applied**, not where the symptom shows: a
  job cancelled by a memory dump is customer-actionable if the program can
  be changed, a service request only if evidence points at a host limit.
- Never upgrade "insufficient evidence" to a service request; a request
  without evidence is returned and the delay is the customer's.
- A finding inside a registered maintenance window is expected behaviour.
- [explorer.md](explorer.md) produces coverage reports, not root-cause
  calls: it closes with the boundary statement and the registry check
  below; the verdict comes from the playbook that investigates.

## Manual-facts registry (customer-maintained lookups)

Facts that live in the SAP for Me portal or the contract are consumed from
lookups the customer maintains. They are never scraped and never assumed.

| Lookup | Columns | Feeds |
|---|---|---|
| `ecs_maintenance_windows.csv` | window_start, window_end (epoch), window_type (scheduled/agreed/emergency), announced_on, reference | window correlation, impact ledger, excluded-hours accounting |
| `ecs_monthly_availability.csv` | month, system, sap_reported_pct, report_received_date | ledger reconciliation, claim-deadline tracking (1 month from report receipt) |
| `fue_contract.csv` | user_class, fue_ratio, licensed_fue_total, memory_tier_gb | FUE / licence exposure math |
| `ecs_sr_log.csv` *(optional)* | sr_id, opened, severity, area, state, closed | service-request follow-through where no API path exists |

**Registry check** — run it in the explorer, and before any playbook that
correlates with windows or availability. Row counts only, never contents:

```spl
| inputlookup ecs_maintenance_windows.csv | stats count
```

Same shape per lookup. On Dynatrace or any other backend the registry is
whatever the profile names; count its rows with that platform's read-only
idiom, or report it missing if the profile names nothing. Per lookup: present /
empty / missing, plus staleness against the update cadence and owner in the
profile. **A missing or empty lookup is a coverage gap exactly like a dead
feed**: rank it in the gap list with what filling it would unlock. A
playbook that needs a fact and finds none says so and lists what to fill
in; it never substitutes a guess for a contract fact.

## ECS-specific findings

| You see | It usually means | Verdict |
|---|---|---|
| All feeds for a SID stop and resume together inside a registered window | planned maintenance | expected; no action |
| Same pattern, no window in the registry | unannounced outage, or a stale registry | insufficient evidence until the registry is refreshed; then service request with the gap timestamps |
| `ST06*` shows host saturation while the application layer looks normal | host-level resource pressure | service request with the ST06 series attached |
| PowerConnect stops sending after a network or certificate change | proxy allow-list or trust store | proxy / firewall → service request; STRUST import → normally customer; see [feed-health.md](feed-health.md) |

## PowerConnect itself on RISE (KB 191, KB 205)

- Supported on RISE private cloud (products per the compatibility matrix).
- **SAP performs** the SAINT import in client 000 and uploads the
  authorization-object transport files, on a customer incident. **The
  customer performs** the rest in the productive client (BC sets, roles,
  licence, connection).
- Outbound traffic usually leaves through SAP's proxy: allow-listing the
  platform URL on port 443 is a service request; the SAP system reaches
  the proxy on port 3128. A direct route needs no request.
- So upgrades, client-000 transports and firewall changes are service
  requests; activating an extractor or fixing a filter is the customer's.

## Guardrails added by this overlay

- Never recommend an action that needs OS, database-admin or client 000
  access as if the customer could perform it.
- Never state an availability percentage, window or contract ratio that is
  not in the registry; quote the lookup row and its date.
- Evidence blocks for service requests carry counts, timestamps and
  technical identifiers only: no payloads, no unnecessary personal data.
- Probing the registry is read-only (`inputlookup`, never `outputlookup`);
  updating a lookup is the named owner's job.

## Documentation

- KB 191 - Support for SAP RISE Private Cloud Edition — `kb-191-support-for-sap-rise-private-cloud-edition`
- KB 205 - PowerConnect Considerations for RISE Deployments — `kb-205-powerconnect-considerations-for-rise-deploy`
