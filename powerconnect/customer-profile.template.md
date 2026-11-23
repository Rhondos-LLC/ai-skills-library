# Customer profile — PowerConnect for SAP

<!-- Copy to customer-profile.md beside SKILL.md. Drafted by
     playbooks/setup.md (guided) or playbooks/explorer.md (census); every playbook reads it before
     its first query. Replace <...> with observed values. Mark anything
     that needs a human decision TODO(owner). Never store passwords,
     tokens or licence keys here. -->

- Date confirmed: <yyyy-mm-dd>, by <explorer run | name>
- Next review: <date or trigger, e.g. after each PowerConnect upgrade>

## Backend

- Platform: <splunk | dynatrace | other: name>
- Query tool: <e.g. splunk_run_query | execute-dql | tool name>
- Scope (never query outside it):
  - Splunk index(es): <index, index>
  - Dynatrace tenant / bucket: <environment, bucket, or "default logs">
  - Other: <index / data stream / table / log group>
- Role or token limits known: <e.g. cannot read index X | none known>
- Pseudonymization layer: <none | macro or field naming, e.g. sap-safe>
- PowerConnect platform content installed: <Splunk app version | Dynatrace
  app + pipeline version | none>

### Only when Platform = other (from backends/other.md, sections 3–4)

| Logical name | Field on this platform |
|---|---|
| `EVENT_TYPE` | <field> |
| `EVENT_SUBTYPE` | <field> |
| `SID` | <field> |
| `HOST` | <field> |
| `STACK` | <field and its values> |
| `EXTRACTED_AT` | <field> |
| Event time | <field> |
| Payload casing | <UPPERCASE / lowercase / nested under prefix> |
| Number typing | <strings / numbers> |

Query idioms in this platform's language:

- Select an event type: `<query>`
- Sample one record: `<query>`
- Count and newest timestamp by type: `<query>`
- Latest state per entity key: `<query>`
- Distinct count: `<query>`
- Numeric conversion: `<function>`

## Answer preferences

- Personal data in answers: <show user names when relevant | mask user
  names | aggregate only>
- Setup depth done: <quick | full assessment on yyyy-mm-dd>

## Landscape

- Landscape line: <standard | ECS/RISE> (ECS/RISE → also read
  playbooks/ecs-overlay.md and fill the ECS section below)
- System time zone(s): <from UTCDIFF / UTCSIGN>

| SID | Role (PRD/QAS/DEV) | Stack(s) | Clients | App servers | Sourcetype convention or service name |
|---|---|---|---|---|---|
| <SID> | <role> | <abap / java / cloud> | <MANDT list> | <count or names> | <sap:abap + EVENT_TYPE / sap:abap:<TYPE> / sap_abap / service.name value> |

## PowerConnect agents

| Agent | Version | Where it runs | Read from |
|---|---|---|---|
| ABAP | <e.g. 9.xx> | <SID, productive client> | <PC_HEALTH subtype INFO / told by admin> |
| Java | <version> | <SID / host> | <agent_health / told by admin> |
| Cloud | <version> | <standalone host / Cloud Foundry> | <agent_health / told by admin> |

## Feeds present

One row per event type that matters to the playbooks in use. Cadence is the
observed one, not the configured one, unless `PC_SCHEDULE` confirms it.

| Event type | Subtypes seen | Present | Observed cadence | Verdict (LIVE / LAGGING / DEAD / quiet stream) | Notes |
|---|---|---|---|---|---|
| `PC_HEALTH` | <INFO, STAT, ...> | <yes/no> | <min> | <verdict> | |
| `PC_SCHEDULE` | | <yes/no> | <min> | <verdict> | |
| `SM37` | <"", STEP, LOGS, SPOOL> | <yes/no> | <min> | <verdict> | |
| `<TYPE>` | | | | | |

## Known gaps and quirks

- Extractors not collected that a playbook needs: <TYPE → playbook>
- Field-shape drift seen here: <e.g. SMQ2 depth is QDEEP, not ENTRIES>
- Metric filters known to hide data: <e.g. SM37 job-log filter, SM20>
- Agents without self-telemetry: <e.g. Cloud agent_health absent>
- Anything the account could not see: <index / bucket / type>

## Operations context — TODO(owner)

- Business hours and batch window (system-local): <...>
- Critical jobs, queues, interfaces, partners: <...>
- Thresholds agreed with the customer: <...>
- Escalation route and who owns SAP-side changes: <...>

## ECS / RISE only

- Service requests are raised by: <team / portal>
- LogServ subscription: <yes / no / unknown>
- Manual-facts registry (see playbooks/ecs-overlay.md):

| Fact set | Where it is kept | Owner | Update cadence | Last updated |
|---|---|---|---|---|
| Maintenance windows | <lookup / file / table> | <owner> | <cadence> | <date> |
| Monthly availability reports | <...> | <owner> | <cadence> | <date> |
| FUE contract ratios | <...> | <owner> | <cadence> | <date> |
| Service-request log (optional) | <...> | <owner> | <cadence> | <date> |
