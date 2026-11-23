# Backend adapter — Splunk

Use this when the SAP data is in Splunk and you have a Splunk MCP server
exposing `splunk_run_query`.

## Where the data is

- **Scope:** one or more indexes named in `customer-profile.md`. Never use
  `index=*` outside the explorer playbook.
- **Stack / sourcetype:** `sap:abap` or `sap_abap` (ABAP), `sap:java` and
  `jmx` (Java), `sap:cloud` (Cloud).
- **Three ABAP sourcetype conventions exist.** Some collectors emit
  `sap:abap:<EVENT_TYPE>` (for example `sap:abap:WE02`); others emit
  everything as `sap:abap` or `sap_abap` with the type in the `EVENT_TYPE`
  field. Step 0 tells you which. Where the PowerConnect Splunk app is
  installed, the macro `` `sap-abap(<TYPE>)` `` resolves all conventions at
  once; prefer it if a probe shows it resolves, and `` `sap-index` `` for
  the index list.
- **SID** = `source`. **Host** = `host`. On indexes carrying several
  systems, filter `source=<SID>` once the profile names one.
- **Payload fields** are UPPERCASE and auto-extracted from JSON (no
  `spath`).

## Step 0 — Orient

```spl
| tstats count max(_time) as newest where index=<PROFILE_INDEX> sourcetype IN ("sap:abap*","sap_abap","sap:java","jmx","sap:cloud") by sourcetype source
| eval age_min=round((now()-newest)/60,0), newest=strftime(newest,"%F %T")
| sort - count
```

`T_END` is the largest `newest`. State index, sourcetype convention, SIDs
and data age in one line before continuing.

## Query idioms

| Need | SPL |
|---|---|
| Select an event type | `index=<IDX> sourcetype=sap:abap EVENT_TYPE=<TYPE>` or `index=<IDX> sourcetype=sap:abap:<TYPE>` or `` `sap-abap(<TYPE>)` `` |
| Sample one record | `... \| head 1 \| fields *` |
| List field names | `... \| head 200 \| fieldsummary \| fields field count distinct_count` |
| Count and freshness per type | `\| tstats count max(_time) as newest where index=<IDX> by sourcetype` (per-type convention) or `... \| stats count max(_time) as newest by EVENT_TYPE` |
| Latest state per entity | `... \| stats latest(<STATE>) as state latest(_time) as seen by <KEY>` |
| Distinct runs | `... \| stats dc(<RUN_ID>) as runs by <GROUP>` |
| Numeric comparison | `\| eval n=tonumber(<FIELD>) \| where n > 90` |
| Header records with empty subtype | `NOT EVENT_SUBTYPE IN ("STEP","LOGS",...)` or `\| fillnull value="" EVENT_SUBTYPE`; an empty JSON string may not be extracted, so `EVENT_SUBTYPE=""` can match nothing |
| Unpopulated value | `<FIELD>!="???" <FIELD>!=""` |
| Local date + time to epoch | `\| eval t=strptime(<DATE>.<TIME>,"%Y%m%d%H%M%S")` (system-local; apply `UTCDIFF`/`UTCSIGN` before comparing with `_time`) |

## Tool hygiene (these caused real failures)

- Run **one** `splunk_run_query` at a time and wait for it. Concurrent
  searches make the bridge fail.
- Always set both tool parameters `earliest_time` and `latest_time` to match
  the window. Use absolute epoch values derived from `T_END`.
- Keep results small: `row_limit` ≤ 50 for tables, ≤ 200 for stats. Never
  `table _raw`; never return raw events without `| fields`. ST22 events are
  5–10 KB each, SM37 headers about 2 KB.
- `splunk_get_indexes` event counts are unreliable on distributed stacks.
  Use the `tstats` orientation instead.
- If a query times out or errors, do not re-run it unchanged: halve the
  window, add the sourcetype, or switch to `tstats`.
- Do **not** use `saia_ask_splunk_question`, `saia_generate_spl` or
  `saia_optimize_spl`; they hand the reasoning to another model and break
  the evidence chain. `saia_explain_spl` is fine for explaining a query you
  wrote.
- Never use `| delete`, `| outputlookup`, `| collect`, `| sendemail` or any
  other command that writes or sends.

## Platform features worth knowing

- The **PowerConnect Splunk app** ships dashboards, macros, lookups
  (`pc_sap_systems`), an alert manager with templates, a KPI engine and CIM
  mappings. See the dashboard-finder and alert-builder playbooks.
- The **Enterprise Security content pack** ships correlation searches over
  SM20, SM21_LOG, SM04, RSUSR003, RSUSR200, SCC4 and others. See the
  security-audit playbook.
