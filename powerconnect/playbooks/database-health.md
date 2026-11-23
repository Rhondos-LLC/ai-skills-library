# Database health — HANA, Oracle, SQL Server, DB2, ASE

**Use when:** the database is suspected of being slow, blocked, full or
unavailable; or for HANA alerts, expensive SQL, database locks, backups,
table growth, replication or secondary DB connections.
**Not for:** ABAP enqueue locks and updates (SM12 / SM13) →
[locks-and-updates.md](locks-and-updates.md); response-time breakdown →
[performance-triage.md](performance-triage.md); application-server file
systems → [os-resources.md](os-resources.md); who changed a HANA
parameter or user → [change-tracking.md](change-tracking.md).

The core insight: **find the database type first.** Each SAP system has
one database and sends only that family's event types, so the other four
families being absent is by design, not a coverage gap. Second: most of
these types are DBA Cockpit **snapshots, many with counters that
accumulate** since the database or the SQL plan was created. Take the
latest record per object, compare two polls for a rate, and never sum a
counter across polls.

## Data it needs

`PC_HEALTH` with `EVENT_SUBTYPE=INFO` carries the database type. The
families are `HDB_*` (HANA), `ORA_*` (Oracle), `MSS_*` (SQL Server),
`DB6_*` (DB2), `ASE_*` (Sybase ASE). All are ABAP-stack types.

| Concern | HANA | Oracle | SQL Server | DB2 | ASE |
|---|---|---|---|---|---|
| Overview, load | `HDB_DB02_OVVW`, `HDB_DBCC_SRVCS`, `HDB_DBCC_LDHIST`, `HDB_DBCC_SYSMON`* | `ORA_DB02_PFOV`, `ORA_DB02_SMTR`, `ORA_DB02_SYEH` | `MSS_DB02_OVVW`, `MSS_DB02_PERF`, `MSS_DB02_MEMORY` | `DB6_DB02_OVVW`, `DB6_DB02_DBPF`, `DB6_DB02_TIMESPT`* | `ASE_DBCC_SYSACT`, `ASE_DBCC_RESOUR` |
| Alerts, error log | `HDB_DBCC_ALERT` (`CURRENT`, `HISTORY`), `HDB_DBCC_EVENTS`, `HDB_DBCC_MDIAGF`* | `ORA_DB02_ALRT` | `MSS_DB02_ELOG` | — | `ASE_DBCC_ERRLOG`, `ASE_DBCC_DBALOG` |
| Expensive SQL | `HDB_DBCC_EXPSTM`, `HDB_DBCC_ACTSTM`, `HDB_DBCC_SQLPL` | `ORA_DB02_CACH`, `ORA_DB02_DBAHIST`, `ORA_DB02_TBLA` | `MSS_DB02_STMT` | `DB6_DB02_STMT` | `ASE_DBCC_CCSTAT` |
| Locks, blocking | `HDB_DBCC_BTRAN`, `HDB_DBCC_OLOCK`, `HDB_DBCC_RLOCK`* | `ORA_DB01_LOCK`, `ORA_DB02_ENQU`, `ORA_DB02_LTCH`, `ORA_DB02_BFFR` | `MSS_DB02_BLOCKS`, `MSS_DB02_DDLK`, `MSS_DB02_DDLKXE` | `DB6_DB02_LOCKS`, `DB6_DB02_TELWT`* | `ASE_DBCC_LKWAIT`, `ASE_DBCC_SPINLC` |
| Sessions, threads | `HDB_DBCC_THREAD`, `HDB_DBCC_CONLST`, `HDB_THRDSMP_STAT`* | `ORA_DB02_SESS` | — | `DB6_DB02_APPL`, `DB6_DB02_TRANS` | `ASE_DBCC_PROCES` |
| Space, growth, I/O | `HDB_DBCC_DISKS` (`DISKS`, `VOLUMES`), `HDB_DBCC_LRGTAB`*, `HDB_DBCC_HEAP` | `ORA_DB02_SPOV`, `ORA_DB02_TSOV`, `ORA_DB02_TBLG`, `ORA_DB02_IOACT` (`AGGRBY_*` subtypes) | `MSS_DB02_OVFL`, `MSS_DB02_LRGTAB`, `MSS_DB02_IOPF` | `DB6_DB02_FSYST`, `DB6_DB02_TRLOG`, `DB6_DB02_SSNAP` | `ASE_DBCC_DBSIZE`, `ASE_DBCC_DEVCIO` |
| Backup | `HDB_DBCC_BCCAT` | `ORA_DB02_BCKP` | `MSS_DB02_BCKP`, `MSS_DB02_RSTR` | `DB6_DB02_BHIST`, `DB6_DB02_BLOGS` | `ASE_DBCC_DMPHIS`* |
| HA, replication | `HDB_REPL_STATE` | — | `MSS_DB02_AOOV` | `DB6_DB02_HADR`* | — |
| Audit, config, users | `HDB_DBCC_AUDIT`, `HDB_DBCC_INI`, `HDB_DBCC_INIHST`, `HDB_DBCC_USERS`, `HDB_DBCC_USRPRV`* | — | — | — | — |

`*` = not active by default; the rest are default for the system's own
database. Database-independent: `DBCO`* (ping of secondary connections),
`TABLE_COUNT` (records and size of the largest tables, top 50 by default),
`TAANA`* (table analysis by field) and the custom-SQL extractors
`OSQLSCRIPTS`*, `HDBSCRIPTS`*, `ORASCRIPTS`*, `MSSSCRIPTS`*, `ASESCRIPTS`*,
whose fields are whatever the script selects.

Notes on specific types:
- `HDB_DBCC_ALERT` has subtypes `CURRENT` (open alerts; expect them to
  repeat on every poll, confirm by sample) and `HISTORY`. `ACTSTM`,
  `THREAD`, `INI`, `USERS` are documented as snapshots; `EXPSTM` holds
  statements above HANA's own configured threshold.
- `HDB_DBCC_BCCAT` sends log backups only with metric configuration
  `GET_LOG = X` (7.03+), marked `log backup` in `EVENT_TYPE_NAME`.
- `HDB_DBCC_SYSMON` covers every HANA system registered in DBA Cockpit,
  so one SAP system can report several databases.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `DB_SYS` in `PC_HEALTH` `INFO` | database family of the system (also `OPSYS`, `RELEASE_NO`) | `HDB` seen | sample (Dynatrace) |
| `ALERT_RATING` | HANA alert severity | shipped alerts: `>= 5` critical, `4` high, `3` medium; `1`–`2` information / low (SAP) | docs (alert) |
| `ALERT_ID`, `ALERT_NAME`, `ALERT_DETAILS`, `ALERT_TIMESTAMP` | HANA statistics-service columns | | SAP — sample first |
| `SQLHANDLE`, `PLAN_HANDLE`, `SQLTEXT`, `OBJECT_NAME` | SQL Server statement key, text (truncated), main table | | sample (Dynatrace) |
| `ABAP_NAME`, `ABAP_LOC` | ABAP program and source position issuing the statement | bridge to the application | sample (Dynatrace) |
| `EXEC_COUNT`, `TTL_ELAPSED_TIME`, `TTL_CPU_TIME`, `TTL_LOGICAL_READS`, `TTL_PHYS_READS`, `TTL_ROWS` | cumulative totals since `CREATION_TIME` of the plan | strings; convert | sample (Dynatrace) |
| `AVG_ELAPSED_TIME`, `MAX_ELAPSED_TIME`, `PCT_ELAPSED_TIME`, `EXECS_PER_HOUR`, `LAST_EXEC_TIME` | per-execution and share figures | | sample (Dynatrace) |
| `PING_RC`, `PING_ERROR`; `EVENT_TYPE_NAME` | `DBCO` connection test; `HDB_DBCC_BCCAT` entry kind | `X` = ping successful; `log backup` | docs |
| everything else | the documentation shows screenshots, not field lists (HANA `M_*` view columns and DBA Cockpit column names are likely) | | unconfirmed — sample first |

## Investigation sequence

1. **Determine the database type.** Read one `PC_HEALTH` `INFO` record
   (`DB_SYS`), confirm with the census of family types per system, then
   sample one record of each type you will use and note its subtypes. On
   Dynatrace the prefix filter does not prune the scan (about 7.6 GB for
   one hour of ABAP data on a busy tenant): keep this census to one hour.

```spl
index=<IDX> sourcetype=sap:abap (EVENT_TYPE=HDB_* OR EVENT_TYPE=ORA_* OR EVENT_TYPE=MSS_* OR EVENT_TYPE=DB6_* OR EVENT_TYPE=ASE_*)
| stats count max(_time) as newest by source EVENT_TYPE
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap"
| filter startsWith(dt.source_entity_name, "HDB_") or startsWith(dt.source_entity_name, "ORA_") or startsWith(dt.source_entity_name, "MSS_") or startsWith(dt.source_entity_name, "DB6_") or startsWith(dt.source_entity_name, "ASE_")
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name}
```

2. **Alerts and errors.** HANA: open alerts by rating. `CURRENT` repeats
   every poll, so divide records by polls instead of counting rows. Other
   families: sample the error-log type and group by its message field.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=HDB_DBCC_ALERT EVENT_SUBTYPE=CURRENT
| eval rating=tonumber(ALERT_RATING)
| where rating >= 3
| stats count as records dc(CURRENT_TIMESTAMP) as polls max(_time) as newest by source rating
| eval open_per_poll=round(records/polls,1)
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "HDB_DBCC_ALERT" and dt.source_entity_type == "CURRENT"
| filter toLong(alert_rating) >= 3
| summarize {records = count(), polls = countDistinct(current_timestamp), newest = max(timestamp)}, by: {log.source, alert_rating}
| fieldsAdd open_per_poll = round(toDouble(records) / polls, decimals: 1)
```

3. **Expensive statements.** Latest record per statement, ranked by total
   elapsed time. Shown for SQL Server (confirmed fields); elsewhere use
   the "Expensive SQL" row with field names from your sample. Totals are
   cumulative: a statement matters now only if it grows between polls.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=MSS_DB02_STMT
| stats latest(TTL_ELAPSED_TIME) as ttl latest(EXEC_COUNT) as execs latest(AVG_ELAPSED_TIME) as avg latest(OBJECT_NAME) as object latest(ABAP_NAME) as program by source SQLHANDLE
| eval ttl=tonumber(ttl), execs=tonumber(execs), avg=tonumber(avg)
| sort - ttl
| head 20
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "MSS_DB02_STMT"
| sort timestamp asc
| summarize {ttl = takeLast(toDouble(ttl_elapsed_time)), execs = takeLast(toLong(exec_count)), avg = takeLast(toDouble(avg_elapsed_time)), object = takeLast(object_name), program = takeLast(abap_name)}, by: {log.source, sqlhandle}
| sort ttl desc
| limit 20
```

4. **Locks and blocking.** These types are snapshots of what is blocked
   at poll time, so the measure is rows per poll: count records of the
   family's lock type by `CURRENT_TIMESTAMP`, sort descending, then
   project the fields of the worst polls (holder, waiter, object) using
   the names from your sample. Blocking in consecutive polls matters;
   a single poll is usually transient.

5. **Space, backup, connections.** Sample the type; reduce to the latest
   record per volume, tablespace, file or table; convert sizes and compute
   the used percentage. For backups report the newest successful full
   backup and any failure. `DBCO`: `PING_RC` other than `X` has failed.

6. **Correlate.** Database trouble shows in ABAP as `DBSQL_*` dumps
   ([abap-dumps.md](abap-dumps.md)), a rising database share of response
   time ([performance-triage.md](performance-triage.md)) and long SM12
   locks. `ABAP_NAME` ties a SQL Server statement to its program.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| No family types at all | DB extractors inactive or DBA Cockpit not reachable | [feed-health.md](feed-health.md); group definitions |
| HANA alert rating 4–5 persisting over many polls | condition still open in HANA | read the alert details; DBA Cockpit / HANA cockpit |
| Same statement tops every poll, total barely moving | historical cost, not current load | compare two polls |
| Blocked rows in consecutive polls | long-running lock holder | identify the holder session; application owner |
| Backup type has data but no recent successful full backup | backups failing or not scheduled | backup team; for HANA check `GET_LOG` before judging log backups |
| `HDB_DBCC_AUDIT` empty | auditing off or privilege missing (KB 126) | enable per the KB |
| `DBSQL_SQL_ERROR` duplicate-key dumps on ASE with PowerConnect ≤ 7.00 | PowerConnect program error (KB 176) | update to SP 7.01+; workaround in the KB |
| Splunk HANA dashboards list non-HANA systems (app 7.2.0) | dropdown not filtered by DB type (KB 172) | dashboard fix |

## What to tell the user

- Database type and SID, event type and subtype, window, counts per poll,
  and the concrete statement, object, alert or lock holder.
- Verify in DBACOCKPIT / DB02 / ST04 or the database's own tools. Owner:
  DBA team or hosting provider for space, backup and availability; the
  application owner for expensive SQL and lock holders.
- Not visible: non-default types, SQL text beyond the truncated field,
  anything the SAP DB user may not read.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `alert_rating >= 5`; `== 4`; `== 3` | `HDB_DBCC_ALERT` | shipped `davis.sap.hdb_dbcc_alert.critical`, `.high`, `.medium`; one event per record, so restrict to one subtype |
| Blocked rows in N consecutive polls | lock type of the family | starting point: 3 polls |
| No successful full backup in 24–48 h | backup type of the family | align with the backup schedule |
| `PING_RC != "X"`; used space above 85–90 % | `DBCO`; space type of the family | starting points; per connection, volume or tablespace |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- HANA: `hdb_dbcc_alert`, `hdb_dbcc_expstm`, `hdb_dbcc_actstm`,
  `hdb_dbcc_btran`, `hdb_dbcc_thread`, `hdb_dbcc_disks`, `hdb_dbcc_lrgtab`,
  `hdb_dbcc_srvcs`, `hdb_dbcc_bccat`, `hdb_dbcc_audit`,
  `hdb_dbcc_sysmon-hana-systems-monitor`, `hdb_dbcc_ini-hana-ini-files`,
  `hdb_dbcc_olock-hana-database-object-locks`,
  `hdb_thrdsmp_stat-kpis-for-individual-hana-database`
- Others: `ora_db02_alrt`, `ora_db02_pfov`, `ora_db02_spov`,
  `ora_db02_sess`, `ora_db02_cach`, `mss_db02_stmt`, `mss_db02_ovvw`,
  `mss_db02_bckp`, `mss_db02_elog`, `mss_db02_aoov`, `db6_db02_trlog`,
  `mss_db02_blocks-ms-sql-database-blocking-locks`, `ase_dbcc_dmphis`
- Cross-database: `pc_health`, `table_count`, `taana-table-data-analysis`,
  `dbco-secondary-db-connections-monitor`,
  `osqlscripts-open-sql-scripts-extractor`
- KB 126, 172, 176 — `kb-126-splunking-hana-audit-log`,
  `kb-172-hana-dashboard-shows-all-systems-in-system-`,
  `kb-176-dbsql_sql_error-abap-dumps-sybase`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
