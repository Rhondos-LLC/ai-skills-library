# Business process data — orders, documents, number ranges, table readers

**Use when:** the user asks about sales orders, sales document flow,
material documents, bank and payment messages, number ranges running out,
table sizes and growth, the content of a custom table or ALV report that
PowerConnect extracts, Smart Business or BPM KPIs, or SLT replication.
**Not for:** IDocs (`WE02`) → [idocs.md](idocs.md) · enabling an
extractor or changing its filter →
[extractor-config-advisor.md](extractor-config-advisor.md) · a stopped
feed → [feed-health.md](feed-health.md) · `RPF_CHECK` baseline results →
[security-audit.md](security-audit.md) · HANA table sizes →
[database-health.md](database-health.md)

The core insight: **these extractors send what the customer configured,
not a fixed schema.** Most are off by default or need a mandatory metric
filter, and the generic readers (`TREAD_DYN`, `ALV_REPORTS`, `SQVI`,
`ODATA_SERVICE`, `BPM_*`) carry whatever table, report or KPI was chosen.
So step one is always "is it collected, and what was configured", read
from one sample. And this is business data: aggregate it; do not list
document contents, partners, prices or people.

## Data it needs

| Event type | Shape | What it gives | Default |
|---|---|---|---|
| `NRIV` | snapshot | number range intervals and current level | yes |
| `TABLE_COUNT` | snapshot | record count and size, top 50 tables or a configured list | yes |
| `TREAD_DYN` | configured (delta stream or repeated full read) | rows of any table; `EVENT_SUBTYPE` = table name | needs Table reader filter |
| `ALV_REPORTS` | snapshot per interval | ALV output of a report + variant; `EVENT_SUBTYPE` = transaction | needs ALV Reports filter |
| `SQVI` | snapshot | QuickView query output | needs SQVI report filter |
| `SALES_ORDERS` | event stream | one record per created (`I`) or changed (`U`) order, items nested in `ITEMS`; subgroup `SO` | no |
| `SALES_DOC_FLOW` | event stream | VBFA predecessor–successor links | no; filter mandatory |
| `MB51` | event stream | material documents | no; MB51 filter mandatory |
| `BNK_MONI` | event stream | bank and payment batch/message status | no |
| `TAANA` | snapshot | table entry counts by analysis variant | no |
| `SSB_KPI` | header + detail | Smart Business KPI definition (`""`, `KPI_PARAMETER`, `KPI_FILTER`, `KPI_TILEINFO`) and values (`KPI_TILE_OUTPUT`) | needs SSB KPI filter |
| `BPM_ST13_TBI` and other `BPM_*` | configured | business process monitoring KPIs; subtype = `PROJID/MONOBJ/KEYFIG` | mostly no |
| `FRE_UI` | event stream | Forecasting & Replenishment interface messages | no |
| `LTRC`, `LTRC_DMC`, `LTRC_LATENCY`, `LTRC_CHECK`, `HDBS_SLT` | snapshot | SLT replication status, table load status, latency | LTRC Table filter mandatory |

All are ABAP. `WE02` sits on business dashboards but belongs to
[idocs.md](idocs.md); `ODATA_SERVICE` (reads business data through an
OData endpoint) is in
[user-activity-and-fiori.md](user-activity-and-fiori.md). Subtypes
`_METRICS_` / `_EVENTS_` come from the agent's KPI / Event Definitions
(8.03+ / 8.04+), derived from data already extracted. A missing type is a
configuration gap, never a quiet business day.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `NRIV`: `CLIENT`, `OBJECT`, `SUBOBJECT`, `NRRANGENR`, `TOYEAR` | entity key of an interval; client is `CLIENT`, not `MANDT` | `TOYEAR` in the past = interval no longer used | sample (Dynatrace) |
| `NRIV`: `FROMNUMBER`, `TONUMBER`, `NRLEVEL` | bounds and last number drawn | strings; `NRLEVEL` 0 = never used | sample (Dynatrace) |
| `NRIV`: `EXTERNIND` | external numbering flag | `X` = numbers assigned by users, level is meaningless | sample (Dynatrace); value `X` SAP |
| `NRIV`: `PERCENTAGE` | a percentage shipped with the record | meaning not documented; verify against your own calculation | sample (Dynatrace) |
| `NRIV`: `UTIL_PERC`, `UTIL_OVER_80` | utilisation and flag (`0`/`1`) | Dynatrace-only derived fields | sample (Dynatrace) |
| `TABLE_COUNT`: `TABNAME`, `RECORDS`, `DBSPACE` | table, row count, size (unit not documented) | strings | sample (Dynatrace) |
| `TREAD_DYN`: `TABNAME`, `FLTNAME` | source table and filter name; all other fields are the table's own columns | `EVENT_SUBTYPE` = `TABNAME` | sample (Dynatrace) |
| `ALV_REPORTS`: `PC_REPORT`, `PC_TCODE`, `PC_VARIANT`, `PC_VTEXT` | which report, transaction and variant produced the row; other fields are ALV columns | | sample (Dynatrace) |
| `BPM_ST13_TBI`: `PROJID`, `MONOBJ`, `KEYFIG`, `PGROUP`, `RGUID` | KPI identity; remaining fields are the KPI's dimensions and value | | sample (Dynatrace) |
| `SALES_ORDERS`: `VBELN`, `CHANGE_IND`, `AUART`, `VKORG`, `NETWR`, `WAERK`, `GBSTK`, `LFSTK`, `ABSTK`, `LIFSK`, `FAKSK`, `ERDAT`, `UDATE` | order header and status | `CHANGE_IND` `I`/`U`; blocks non-empty = blocked | docs |

Not sampled (fields unknown until you see a record): `SALES_DOC_FLOW`,
`MB51`, `BNK_MONI`, `TAANA`, `SQVI`, `SSB_KPI`, `FRE_UI`, `LTRC*`, `HDBS_SLT`.

## Investigation sequence

1. **Confirm what is collected and how it was configured.** The subtype
   list is the configuration: it names the tables, reports and KPIs.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (NRIV, TABLE_COUNT, TREAD_DYN, ALV_REPORTS, SQVI, SALES_ORDERS, SALES_DOC_FLOW, MB51, BNK_MONI, TAANA, SSB_KPI, FRE_UI, LTRC*, HDBS_SLT, BPM_*)
| stats count max(_time) as newest by source EVENT_TYPE EVENT_SUBTYPE
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap"
| filter in(dt.source_entity_name, {"NRIV", "TABLE_COUNT", "TREAD_DYN", "ALV_REPORTS", "SQVI", "SALES_ORDERS", "SALES_DOC_FLOW", "MB51", "BNK_MONI", "TAANA", "SSB_KPI", "FRE_UI", "HDBS_SLT"})
    or startsWith(dt.source_entity_name, "LTRC") or startsWith(dt.source_entity_name, "BPM_")
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name, dt.source_entity_type}
```

2. **Sample one record per type and subtype you will use.** Decide the
   entity key and time field from it. Report field names, not values: an
   ALV user report carries names and addresses.
3. **Number range exhaustion (worked case).** Latest record per
   interval, drop external ranges, compute utilisation yourself, rank.
   Bounds that do not convert are alphanumeric: not computable.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=NRIV EXTERNIND!="X"
| fillnull value="-" SUBOBJECT TOYEAR
| stats latest(NRLEVEL) as lvl latest(FROMNUMBER) as lo latest(TONUMBER) as hi by source CLIENT OBJECT SUBOBJECT NRRANGENR TOYEAR
| eval lvl=tonumber(lvl), lo=tonumber(lo), hi=tonumber(hi)
| where hi>lo AND lvl>0
| eval used_pct=round(100*(lvl-lo)/(hi-lo),2)
| where used_pct>=80 | sort - used_pct
```
```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "NRIV" and externind != "X"
| sort timestamp asc
| summarize {lvl = takeLast(nrlevel), lo = takeLast(fromnumber), hi = takeLast(tonumber)}, by: {log.source, client, object, subobject, nrrangenr, toyear}
| fieldsAdd lvl = toDouble(lvl), lo = toDouble(lo), hi = toDouble(hi)
| filter hi > lo and lvl > 0
| fieldsAdd used_pct = 100 * (lvl - lo) / (hi - lo)
| filter used_pct >= 80 | sort used_pct desc
```

   `fillnull` is needed because Splunk drops rows whose `by` field is
   empty. For the intervals returned, estimate time to exhaustion: over
   7–30 days take the lowest and highest `NRLEVEL`, divide the difference
   by the days covered, and divide `hi - lvl` by that daily rate. A level
   that went down means a year change or reset; do not extrapolate.
4. **Table growth or unexpected deletion** (`TABLE_COUNT`): same
   pattern without a query of its own. Per `TABNAME`, take the first and
   last `RECORDS` in the window (convert to a number first) and sort by
   the difference; a negative delta on a business table is the "records
   deleted" finding. `TAANA` splits the count by the analysis fields.
5. **Generic readers and documents.** Aggregate by the status or
   organisational field found in step 2 and count *distinct document
   keys* (for example distinct `VBELN`), never rows: a full-read filter
   resends every row each run and an order emits one record per change.
6. **Correlate.** Failing documents → the processing job
   ([background-jobs.md](background-jobs.md)) and the feeding interface
   ([idocs.md](idocs.md)). SLT latency → database and job load.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Type absent | extractor off or mandatory filter empty | name the filter under `/BNWVS/MAIN` → Administrator → Metric Filters; hand off to extractor-config-advisor |
| `TREAD_DYN` row counts multiply every poll | no delta field, or KB 196 (7.4–8.0: date/timestamp field ignored without a select condition) | count distinct keys; recommend the select-condition workaround |
| `TREAD_DYN` event times a second off or on the wrong day | KB 220 (8.0–8.3, long timestamps) | use `UPD_TMSTMP` and a wider window |
| Interval ≥ 80–90 % used, steady daily rate | exhaustion is predictable | give the date estimate; SNRO to extend |
| `LTRC*` absent on S/4HANA 2022+ or after an upgrade to 7.04–8.01 | KB 193 | check agent version; ST22 for the extractor dump |
| `NRIV` Dynatrace `UTIL_PERC` disagrees with your calculation | derived field built on an unexpected value | trust the calculation from raw bounds |

## What to tell the user

- What is configured (types, subtypes, newest data) and the finding as
  counts and percentages per interval or table; document numbers only if
  the user asked about a specific document.
- Where to verify: SNRO or SE16 on `NRIV`, SE16 "number of entries", VA03
  document flow, MB51, `BNK_MONI`, LTRC.
- Who acts: the functional team for ranges and documents, the
  PowerConnect administrator for filters. What you could not see.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Internal interval ≥ 90 % used (current year) | `NRIV` | snapshot: latest per interval, throttle per interval per day; 80 % is the shipped Dynatrace flag |
| SLT latency above the agreed limit | `LTRC_LATENCY` | field names unconfirmed |

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform
alert.

## Documentation

- Event pages: `nriv`, `table_count`, `tread_dyn`, `sqvi`,
  `alv_reports-alv-reports-data`, `sales_doc_flow`,
  `sales_orders-created-and-updated-sales-orders`,
  `mb51-material-documents`, `bnk_moni-bank-and-payment-monitor`,
  `taana-table-data-analysis`, `ssb_kpi-sap-smart-business-ssb-kpi`,
  `fre_ui-user-interface-for-f-r-messages-monitor`,
  `rpf_check-rule-processing-framework`
- SLT: `draft-ltrc`, `ltrc_dmc-slt-replication-table-load-status`,
  `ltrc_latency`, `hdbs_slt-erp-accelerators-fi`,
  `kb-193-ltrc-events-are-not-collected`
- TREAD_DYN issues: `kb-196-tread_dyn-date-timestamp-field-ignored-when`,
  `kb-220-tread_dyn-timestamp-issue-in-records-with-l`
- Derived KPIs and events: `kpi-engine`,
  `kb-214-how-to-generate-and-send-kpis-metrics`,
  `kb-225-how-to-generate-and-send-events`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
