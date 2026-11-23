# Install and upgrade advisor

**Use when:** the user asks about prerequisites, the installation order of
an agent (ABAP, Java, Cloud), whether versions are compatible or still
supported, how to get from one major version to another, what to do with
PowerConnect during a system copy, client copy or SAP upgrade, licence
keys, or what is different on RISE.
**Not for:** configuring extractors after installation →
[extractor-config-advisor.md](extractor-config-advisor.md). Data not
arriving after an install or upgrade → [feed-health.md](feed-health.md).
Any other documentation question → [docs-qa.md](docs-qa.md).

A documentation-driven playbook: establish what is installed, read the
version-specific page, and lay out the path for a human to follow. The
core insight: **ABAP major versions cannot be skipped.** Each jump goes
through the last support pack of the current major (applied with SPAM)
before the next major is installed with SAINT, with the metric queue
emptied in between. Skipping this creates object inconsistencies, loses the
configuration and blocks the OCS queue. So the first question is always
"which exact version is installed now", and the data can answer it.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `PC_HEALTH` subtype `INFO` | ABAP | snapshot | installed PowerConnect version and release date, licence expiry, database type, operating system, logged-on users | yes |
| any `sap:abap` / `sap:java` / `sap:cloud` | all | n/a | which agents exist and for which SIDs (Step 0) | n/a |
| `agent_health` | Java, Cloud | stream | agent present; a version field is not confirmed | yes |

If none of this is reachable, ask the user for the version shown in
`/n/BNWVS/MAIN` (ABAP) or the agent UI, and the SAP release from System →
Status.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `EVENT_SUBTYPE` (PC_HEALTH) | record kind | `INFO`, `STAT` (docs); `ERROR` also seen | docs; sample (Dynatrace) |
| `RELEASE_NO`, `RELEASE_DATE` (PC_HEALTH INFO) | installed PowerConnect version and the date of that release (`yyyymmdd`) | `major.minor` string; compare as text, not as a number | sample (Dynatrace) |
| `DB_SYS`, `OPSYS` (PC_HEALTH INFO) | database type and operating system of the SAP system | SAP database code, for example `MSSQL` | sample (Dynatrace) |
| `LICENCE_EXP`, `LICENCE_EOM`, `LICENCE_KIND` (PC_HEALTH INFO) | licence expiry (`yyyymmdd`); the other two are not documented | `99991231` = no expiry date | sample (Dynatrace), meaning partly unconfirmed |
| `USERS_GUI`, `USERS_RFC`, `USERS_PLG` (PC_HEALTH INFO) | logged-on users by GUI, RFC and plug-in type | numbers as strings | sample (Dynatrace) |
| `SID`, `HOST`, `STACK` | which system and agent family | | sample (Dynatrace) |
| `system_type`, `sap_system_name` (Java `agent_health`) | agent flavour and system | `netweaver` | sample (Dynatrace) |

## Investigation sequence

**1. Read the installed ABAP version from the data.** Take the newest
`INFO` record per system. The record repeats every few minutes, so a
one-hour window is enough.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=PC_HEALTH EVENT_SUBTYPE=INFO source=<SID>
| head 1
| table _time source RELEASE_NO RELEASE_DATE DB_SYS OPSYS LICENCE_EXP
```

```dql
fetch logs, from: now() - 1h
| filter service.name == "sap:abap" and dt.source_entity_name == "PC_HEALTH"
| filter dt.source_entity_type == "INFO" and log.source == "<SID>"
| sort timestamp desc
| limit 1
| fields timestamp, log.source, release_no, release_date, db_sys, opsys, licence_exp
```

For the landscape view drop the `SID` filter and take the latest record
per `SID` instead of `limit 1`. If a projected field comes back empty,
pull the whole record once (in Dynatrace ignore the `data.*`, `dt.*` and
`content` copies) and adapt. If no `INFO` record exists the release may
predate it or the type is filtered; fall back to asking. On any other backend, sample one `PC_HEALTH` record with subtype
`INFO` using the idioms in the profile
(see [../backends/other.md](../backends/other.md)).

**2. Establish the target.** SAP product and release (ECC / NetWeaver
level, S/4HANA year, Java 7.5, which cloud services), target platform
(Splunk and app version, Dynatrace), and landscape line (standard or
ECS/RISE).

**3. Check compatibility and support** against the matrices (table below).

**4. Read the version-specific guide** with [docs-qa.md](docs-qa.md) and
lay out the steps in the guide's order. Guides exist per major version;
never mix steps from a 7.X, 8.X and 9.X page.

**5. After the change**, verify with [feed-health.md](feed-health.md): the
`INFO` record shows the new version, the three jobs run, the queue drains.

## What the documentation says, by question

| Question | Key facts (confirm on the page for the user's version) | Page |
|---|---|---|
| Which SAP products are covered | ABAP (NetWeaver, ECC, S/4HANA, BW), Java 7.5 systems (PO, Portal ...), Tomcat-based agents (BusinessObjects, Data Services, Cloud Connector), cloud services via the Cloud agent | `product-compatibility-matrix` |
| ABAP release support | by BASIS / ABAP level; S/4HANA 2022 needs 7.01+, 2023 needs 8.00+, 2025 needs 9.00+; some releases need an ACP file | `abap-support-matrix` |
| Java release support | NetWeaver Java 7.50 only; 7.30 and 7.40 are not supported by current agents (the install guide's "7.4 and above" is older text; the matrix decides) | `java-support-matrix` |
| Splunk app versus Splunk version | per app release; the app goes on search heads, indexers only need the index | `splunk-support-and-deployment-matrix` |
| End of support | 6.x ended 2022; 7.x on 1 Apr 2024; all 8.x on 1 Nov 2026; 9.00 released 1 Dec 2025 with no end date listed. Compare with today's date | `end-of-support` |
| Project prerequisites | SID and installation number for the licence; platform side ready (index, HEC token, role, SSL for Splunk; extension and app for Dynatrace) | `prerequisites-for-a-powerconnect-project` |
| ABAP 9.X prerequisites | SAP Note 1487337; authorization object class `ZBNW` unused; endpoint certificate in STRUST; ports open; Dynatrace SaaS needs the client SNI profile parameter (SAP Note 2124480) | `prerequisites-and-preparation-powerconnect-abap-9-` |
| ABAP install order (9.X) | 1 SAINT import in client 000 (plus any hot-fix transport) → 2 activate BC sets → 3 upload roles → 4 assign roles → 5 licence → 6 SSL → 7 outbound connection → 8–10 optional post steps, HANA scripts, security baseline | `powerconnect-abap-installation-guide-powerconnec-2`, `import-the-agent-via-saint-powerconnect-abap-9-x` |
| Upgrade within a major | stop Check and Collector, wait until unsent is 0, stop Uploader; SPAM in client 000; then BC sets and roles. From ≤ 9.00 to 9.01+ the old authorization-object transport must be removed first | `upgrading-powerconnect-abap-9-x-to-latest-release`, `upgrading-powerconnect-abap-8-x-to-latest-release` |
| 7.X → 8.X | SPAM to 7.04, truncate the metric cluster (mandatory), SAINT to 8.X, BC sets, new authorization transport and roles, start jobs | `powerconnect-abap-support-pack-7-x-to-8-0-upgrade` |
| 8.X → 9.X | same pattern through 8.06 | `powerconnect-abap-support-pack-8-x-to-9-x-upgrade` |
| Older jumps | 5.09 → 5.10 → 6.0; 6.X → 6.10 → 7.0 | KB 87, KB 156 |
| Java agent install | deploy with SUM (telnet for experts); needs admin credentials, 100 MB database space, route to the platform port | `powerconnect-java-installation-guide` |
| Cloud agent install | standalone (64-bit Linux, Java 11, 6 GB RAM; UI on port 3000; outbound 443 to SAP cloud; supports clustering) or Cloud Foundry (single instance, no HA) | `powerconnect-cloud-installation` |
| Cloud agent upgrade | back up the `powerconnect` folder first; separate steps for non-clustered, clustered and Cloud Foundry | `powerconnect-cloud-upgrade` |
| SAP upgrade or migration with PowerConnect installed | first bring PowerConnect to the latest SP of its major; check whether an ACP is needed; then upgrade SAP. NetWeaver → S/4HANA: export configuration, uninstall, install the S/4 package, restore; or the in-place path per major described on the page | `upgrading-migrating-sap-with-powerconnect-installe` |
| SUM | avoid the downtime-minimized mode (inactive imports seen on 7.54) | KB 92 |
| System copy | before: Goto → Backup → Export; after: stop jobs, import the backup, restart jobs | KB 90 |
| Client copy | exclude `/BNWVS/*` tables (report RSCCEXPT) so the cockpit runs in one client only | KB 204 |
| ABAP licence | request needs SAP product, release, installation number and SID; apply under Administrator → License management. SP 8.05: valid key rejected with "Crypto module" needs a fix transport | KB 112, KB 124, KB 232 |
| Cloud licence | per plug-in and per production tenant, per deployment; test tenants included | KB 215 |
| RISE | supported; SAP runs SAINT in client 000 and uploads the authorization transport on a customer incident; customer does the rest in the productive client; proxy allow-listing of the platform URL (port 443) is a service request | KB 191, KB 205 |

## Reading the results

| You see | It usually means | Advice |
|---|---|---|
| Installed major is past its end-of-support date | unsupported release | plan the upgrade path; say the date and the page |
| Installed SP is not the last of its major and the user wants the next major | two-step path | SPAM to the last SP first, then SAINT |
| Different PowerConnect versions across SIDs | staggered rollout | list per SID; upgrade non-production first |
| Target S/4HANA release newer than the agent supports | agent must be upgraded before or with the SAP upgrade | `abap-support-matrix` note for that release |
| Java system on NetWeaver 7.30 / 7.40 | not supported by current Java agents | say so; no workaround in the docs |
| Data stops right after an upgrade | roles or authorization objects not updated, or BC set not activated | [feed-health.md](feed-health.md); KB 197 step 3 |
| ECS/RISE landscape | parts of every path are service requests | [ecs-overlay.md](ecs-overlay.md) |

## What to tell the user

- What is installed, per SID, with the evidence (event type, timestamp) or
  that you had to ask.
- Whether source and target are supported, with the matrix page and date.
- The path as ordered steps, naming SPAM versus SAINT, the client (000 for
  imports, productive client for configuration), and the mandatory queue
  clean-up where it applies.
- Risks called out by the docs: configuration loss when a major is
  skipped, unsent metrics discarded by the truncate, hot-fix transports
  named in release notes.
- That software packages, ACP files and licence keys come from PowerConnect
  support (`open-a-support-ticket`), and that you only describe the steps.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Installed version changed | `PC_HEALTH` INFO | `RELEASE_NO` differs from the previous day; useful as a change record |
| Version differs between production SIDs | `PC_HEALTH` INFO | report, not an alert |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `product-compatibility-matrix`, `abap-support-matrix`, `java-support-matrix`, `splunk-support-and-deployment-matrix`, `end-of-support`
- `prerequisites-for-a-powerconnect-project`, `prerequisites-and-preparation-powerconnect-abap-9-`
- `powerconnect-abap-installation-guide-powerconnec-2`, `import-the-agent-via-saint-powerconnect-abap-9-x`
- `upgrading-powerconnect-abap-9-x-to-latest-release`, `upgrading-powerconnect-abap-8-x-to-latest-release`
- `powerconnect-abap-support-pack-8-x-to-9-x-upgrade`, `powerconnect-abap-support-pack-7-x-to-8-0-upgrade`
- `powerconnect-java-installation-guide`, `powerconnect-cloud-installation`, `powerconnect-cloud-upgrade`
- `upgrading-migrating-sap-with-powerconnect-installe`, `pc_health`
- `kb-90-powerconnect-system-copy-guide`, `kb-204-powerconnect-client-copy-guide`, `kb-92-sap-sum-software-update-manager-downtime-min`
- `kb-156-support-pack-6-x-to-7-0-upgrade`, `kb-87-support-pack-5-09-to-6-0-upgrade`
- `kb-191-support-for-sap-rise-private-cloud-edition`, `kb-205-powerconnect-considerations-for-rise-deploy`
- `kb-112-license-key-generation`, `kb-124-update-powerconnect-license-key`, `kb-215-powerconnect-cloud-licensing`, `kb-232-license-validation-error-in-sp-8-05`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
