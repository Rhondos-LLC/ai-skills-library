# Dashboard finder — which shipped dashboard answers it, and what feeds it

**Use when:** the user asks which PowerConnect dashboard shows something,
where a dashboard is in the menu, what a dashboard or panel is built
from, why a shipped dashboard is empty or a dropdown has no systems, or
how dashboards are installed, imported or updated.
**Not for:** answering the underlying SAP question from data → the topic
playbook in [../SKILL.md](../SKILL.md) · a feed that is missing or stale
→ [feed-health.md](feed-health.md) · building an alert from a panel →
[alert-builder.md](alert-builder.md) · any other product how-to →
[docs-qa.md](docs-qa.md)

The core insight: **a dashboard is a view over event types, so "the
dashboard is empty" is a data question first.** Find the event types the
dashboard reads, check that they arrive in the scope the dashboard
searches, and only then look at macros, lookups, dropdowns and known
dashboard bugs. Most empty dashboards are an extractor that is off, an
index the app's macro does not point at, or a product that was not
selected on the setup page. This playbook needs no SPL or DQL except
that one arrival check.

## Sources, and how to use each

| Source | What it holds | How to use it |
|---|---|---|
| [../reference/dashboards-splunk.md](../reference/dashboards-splunk.md) | Splunk: dashboard → view id → menu path → event types | search by topic, dashboard name or event type; this is the main lookup |
| [../reference/dashboards-dynatrace.md](../reference/dashboards-dynatrace.md) | Dynatrace: menu → dashboard name → dashboard id (no event types) | search by topic or name |
| [../reference/event-types.md](../reference/event-types.md) | event type → meaning, default on/off, documentation slug | to explain what a dashboard's event types are and whether they are on by default |
| docs `list-of-event-types` | event type → view id → view name → menu mapping per database flavour | source of the Splunk reference; fetch only to check a newer release |
| docs `list-of-dashboards` | Splunk, one row per **panel**: menu name, dashboard label, dashboard id, panel name | about 1 MB. Never read it whole. Fetch it to a file and search it for the dashboard id or a panel title, or ask the fetch tool a narrow question |
| docs `list-of-dashboards-dynatrace` | source of the Dynatrace reference | only to check a newer release |
| docs `7-1-0-changes-to-existing-dashboards` | panels added, renamed or re-queried in Splunk app 7.1.0 | when a panel moved or changed name |

The panel list does not cover every dashboard. If a search for the view
id returns nothing, say the panel level is not documented and answer at
dashboard level.

## Finding sequence

1. **Pin the platform and app.** Splunk app or Dynatrace app, and the
   version if the user knows it (from the profile, otherwise ask only if
   the answer depends on it). Menus differ by version: the Splunk
   reference lists both the newer consolidated views (ids starting
   `pc_abap_`, for example Security > Users & Authorizations) and the
   classic ones (for example SAP Security > Users and Logins).
2. **Search the reference** with the user's words and their SAP
   synonyms: the transaction (`SM37`), the event type, the topic ("spool",
   "number range", "IDoc"). Search by event type when you already know
   which data answers the question; several dashboards usually read it.
3. **Pick one to three candidates** and say why: the most specific
   dashboard for the question first, then the overview that contains it.
4. **Report** for each: name, id, menu path, and the event types behind
   it (Splunk). In Splunk a view opens at
   `/app/<app folder>/<view id>`; the app folder appears in the
   documentation as `BNW-app-powerconnect`, confirm it on the stack. On
   Dynatrace the `(PC) ...` dashboards exist only after import; say so.
5. **For Dynatrace event types**, the catalog does not list them. The
   Splunk dashboard of the same name is a reasonable guide; label that as
   an inference and offer to confirm by sampling the event type.
6. **For "what is this panel built from"**, search `list-of-dashboards`
   for the dashboard id to get the panel names, then relate the panel to
   the dashboard's event types. The documentation does not publish panel
   queries; the user can open the panel's search in the platform.

## When a dashboard is empty

Work down this list and stop at the first cause that fits.

1. **Are its event types arriving?** Take the event types from the
   reference and check count and newest record in the profile scope over
   the dashboard's own time range.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (<TYPE_1>, <TYPE_2>)
| stats count max(_time) as newest by source EVENT_TYPE
| eval newest=strftime(newest,"%F %T")
```

```dql
fetch logs, from: "<START>", to: "<END>"
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"<TYPE_1>", "<TYPE_2>"})
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name}
```

   Use the Java or Cloud stack value for lowercase types. A type that is
   absent or stale ends this playbook: hand off to
   [feed-health.md](feed-health.md), or to
   [extractor-config-advisor.md](extractor-config-advisor.md) if the
   extractor is off by default. Some dashboards need several types; the
   panels of a missing type stay empty while the rest render.
2. **Does the dashboard search where the data is?** (Splunk) The app's
   searches use the macros `` `sap-index` `` and `` `sap-abap(<TYPE>)` ``.
   Data that you can find by index name but the dashboard cannot is the
   classic sign: the setup page's index selection does not include that
   index, or the macro still assumes an index called `sap` (KB 165).
   (Dynatrace) Dashboards are imported with a "use buckets" option that
   points queries at the buckets created during onboarding; data in
   another bucket will not show.
3. **Is the system selectable?** An empty system dropdown hides
   everything below it. See the KB table (KB 195, KB 202, KB 172) and
   check that the system is in the `pc_sap_systems` lookup.
4. **Is the dashboard visible at all?** (Splunk) The setup page's product
   selection (database types, SAP Cloud products, other products such as
   Fiori) controls which menus appear. (Dynatrace) A dashboard without a
   green check mark in the app's Overview navigation is not imported yet;
   import it under Import Dashboards. Imported dashboards are shared
   read-only with the groups chosen at import, and sharing can silently
   fail (KB 234).
5. **Is it a known issue?** Match the symptom to the table below, then
   read the KB before quoting its fix.
6. **Was the dashboard edited?** App updates overwrite changes to shipped
   dashboards (Dynatrace documentation says so explicitly and recommends
   working on a duplicate). A fix from a KB applied to the original can
   disappear at the next update.

## Known dashboard issues

| Symptom | Applies to | KB slug |
|---|---|---|
| All dashboards empty although a manual search finds data | Splunk; index not named `sap`, macros `sap-abap(1)` / `sap-abap(2)` | `kb-165-out-of-the-box-dashboards-not-populating-da` |
| System dropdown empty on database, cloud or Java dashboards | Splunk app 8.0+; `sap-systems(2)` macro uses `XOR` | `kb-195-system-dropdowns-for-database-cloud-or-java`, `kb-202-system-dropdown-not-populating-in-database-` |
| HANA dashboards list non-HANA systems | Splunk app 7.2.0 | `kb-172-hana-dashboard-shows-all-systems-in-system-` |
| "No result found" in ST03 - User Profile panels | Splunk Cloud 8.2.2111 search optimisation | `kb-150-no-result-found-in-st03-user-profile-dashbo` |
| "A custom JavaScript caused an issue" on Landscape Overview | Splunk 8.2.5, app 6.x; data still shows | `kb-147-a-custom-javascript-caused-an-issue-loading` |
| Landscape Overview slow or stale | summary lookup `landscape_overview_summary_lookup` and its two saved searches | `kb-136-new-summary-lookup-for-landscape-overview`, `kb-206-performance-issues-when-calling-landscape_o` |
| Network Topology panel missing on Java System Overview | Splunk app 7.2.0+; hidden unless a Splunkbase visualisation is installed | `kb-170-enabling-network-topology-panel-in-powercon` |
| Certificate fields missing in CIM-based views | Splunk app 8.3.0–9.0.1 (the page is titled KB 239) | `kb-238-splunk-fields-missing-in-certificates-cim-m` |
| STATS Details "Overall Statistics" empty; Fiori Statistics user filter ignored | field absent on older S/4HANA; app 7.0.0 query bug | `kb-158-splunk-overall-statistics-table-not-renderi`, `kb-157-splunk-user-filter-not-working-in-fiori-sta` |
| Imported Dynatrace dashboards not shared with groups | Dynatrace dashboard API | `kb-234-dashboard-sharing-on-dynatrace` |

Every fix in these articles edits a macro, a saved search or a dashboard.
You describe it; a platform administrator applies it.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Event types absent in scope | extractor off, filtered or feed broken | feed-health or extractor-config-advisor |
| Event types present, dashboard empty | macro / index / bucket mismatch, or empty system dropdown | steps 2–3 above |
| Some panels empty, others fine | one of several event types missing, or a panel-level KB | check each type; search the KB index for the dashboard name |
| Dashboard not in the menu | product not selected at setup (Splunk) or not imported (Dynatrace) | `app-setup-page`, `importing-dashboards` |
| Panel named in an old screenshot is gone | renamed or replaced in a later app release | `7-1-0-changes-to-existing-dashboards`, release notes via docs-qa |

## What to tell the user

- The dashboard(s): name, id, menu path, platform, and why it fits.
- The event types behind it and whether each is arriving, with the
  newest timestamp.
- For an empty dashboard: the first failing check and the KB, if any.
- What is inferred (Dynatrace event types) or not documented (panel
  queries, dashboards missing from the panel list).

## Documentation

- List of Dashboards (Splunk, panel level) — `list-of-dashboards`
- List of Event Types (event type → dashboard) — `list-of-event-types`
- List of Dashboards - Dynatrace — `list-of-dashboards-dynatrace`
- App Setup Page (Splunk) — `app-setup-page`
- 7.1.0 - Changes to Existing Dashboards —
  `7-1-0-changes-to-existing-dashboards`
- Dynatrace app: `system-overview`, `importing-dashboards`,
  `updating-dashboards-and-configuration`, `dashboards` (download and
  upload one dashboard at a time)
- `role-based-access-controls` describes user roles of the PowerConnect
  Cloud agent UI. It does not govern who can see dashboards; that is
  platform permissions and, on Dynatrace, the sharing chosen at import.

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
