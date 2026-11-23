# Backend adapter — any other platform

Use this when the SAP data is reachable through a query tool that is neither
Splunk nor Dynatrace: Elastic / OpenSearch, Microsoft Sentinel, Datadog,
Splunk Observability Cloud, a SQL warehouse, or a custom MCP server.
PowerConnect can send to any HTTP endpoint through its outbound connection,
so the envelope is whatever the customer's pipeline made of it. The SAP
payload inside is unchanged.

The method is: discover the envelope once, write it into the profile, then
run playbooks exactly as on the documented backends.

## 1. Find the query tool

List your tools and pick the one that runs a query and returns rows
(ES|QL / KQL / SQL / a search endpoint). If the platform offers both a
"run this query" tool and an "ask a question" tool, use only the first.
If no tool can run a query, say so and answer documentation questions only.

## 2. Find where SAP events land

Use the platform's cheapest metadata query (list indexes, data streams,
tables or log groups; then a count by source for the last few hours). You
are looking for records whose body or fields contain PowerConnect's
signature fields: `EVENT_TYPE` and `CURRENT_TIMESTAMP` (any casing), or
values such as `sap:abap`, `sap:java`, `sap:cloud`.

## 3. Map the logical fields

Sample **one** record of one common event type and fill this table. Every
playbook depends on it.

| Logical name | What to look for | On this platform |
|---|---|---|
| `EVENT_TYPE` | field holding `SM37`, `ST22`, `jmx`, ... | |
| `EVENT_SUBTYPE` | field holding `STEP`, `LOGS`, `INFO`, `STAT`, ... | |
| `SID` | three-character SAP system ID | |
| `HOST` | application server name | |
| `STACK` | `sap:abap` / `sap:java` / `sap:cloud` | |
| `EXTRACTED_AT` | `yyyymmddhhmmss` value | |
| Event time | the platform's own timestamp | |
| Payload casing | UPPERCASE, lowercase, or nested under a prefix | |
| Number typing | are numerics strings or numbers | |

Then work out the six idioms the playbooks rely on, in this platform's
query language: select an event type; sample one record; count and newest
timestamp by type; latest state per entity key; distinct count; numeric
conversion.

## 4. Record it

Write the mapping and the six idioms into `customer-profile.md` under a
"Backend" heading so the next session does not rediscover them. If you
cannot write files, give the block to the user to save.

## 5. Step 0 — Orient

Count records and newest timestamp by `STACK` and `SID` over the last two
hours in the confirmed scope. `T_END` is the newest timestamp.

## Rules that hold on every platform

- Filter by event type and time before anything else; never scan the whole
  store.
- Return aggregates, and raw records only as narrow field projections of a
  few rows.
- One query at a time unless the platform's tool documentation says
  concurrency is safe.
- Read-only: no statement or API call that inserts, updates, deletes or
  changes configuration.
- If the platform is a metrics or traces store rather than an event store
  (Splunk Observability Cloud, Dynatrace metrics ingest, OpenTelemetry
  traces), only a subset of PowerConnect data is there. Say which event
  types you found and which playbooks therefore cannot run.
