# PowerConnect event type catalog

Generated from the product documentation ("Summary of Extractors and EVENT_TYPE(s)" and "List of Event Types"). Use it to find which event type carries the data for a question. Search this file; do not read it end to end.

- **Default = yes** means the extractor is active out of the box. Anything else must be enabled by an administrator, so its absence is normal.
- **Docs** is the page slug: open `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
- Whether a type is actually collected on a given system is decided by Step 0 and the explorer playbook, never by this list.

## ABAP extractors

| Event type | Category | What it carries | Default | Docs |
|---|---|---|---|---|
| `ABAP_METER` | Performance | ABAP performance measurements (SAP Note 2879613) |  |  |
| `ADS_CHECK` | Performance | ADS Destination check | yes | ads_check-adobe-document-service-ads-availability- |
| `AIF_ERROR` | Performance | AIF error monitoring (/AIF/ERR) |  |  |
| `AL08` | Performance, Security | List of logged on users | yes | al08 |
| `AL11` | BPM | SAP directories and files | yes | al11 |
| `ALV_REPORTS` | BPM | Read ALV Reports output data |  | alv_reports-alv-reports-data |
| `ASESCRIPTS` | Performance | SyBase: SQL scripts extractor |  |  |
| `ASE_DBCC_CCSTAT` | ITSI, Performance | SyBase: Cached statements | yes |  |
| `ASE_DBCC_CUSAGE` | Performance | SyBase: Cache usage | yes |  |
| `ASE_DBCC_DBALOG` | Performance | SyBase: DBA log | yes |  |
| `ASE_DBCC_DBSIZE` | ITSI, Performance | SyBase: Database size | yes |  |
| `ASE_DBCC_DEVCIO` | ITSI, Performance | SyBase: Device IO | yes |  |
| `ASE_DBCC_ERRLOG` | Performance | SyBase: Error log | yes |  |
| `ASE_DBCC_LKWAIT` | ITSI, Performance | SyBase: Lock Wait Events | yes |  |
| `ASE_DBCC_PROCES` | ITSI, Performance | SyBase: Processes | yes |  |
| `ASE_DBCC_RESOUR` | ITSI, Performance | SyBase: Resources | yes |  |
| `ASE_DBCC_SPINLC` | Performance | SyBase: Spin Locks | yes |  |
| `ASE_DBCC_SYSACT` | ITSI, Performance | SyBase: System Activities | yes |  |
| `ASE_DBCC_SYWAIT` | Performance | SyBase: System Waits | yes |  |
| `ATC` | Performance, Security | ABAP Test Cockpit Result | yes | atc-abap-test-cockpit-results |
| `ATRA_STATE` | Performance, Security | Performance trace state | yes |  |
| `BD87_DYN` | BPM | IDOC header, status and payload data | yes | bd87_dyn |
| `BGRFC_MON` | Performance | Background RFC monitor - SBGRFCMON |  | bgrfc_mon-background-rfc-monitor |
| `BGRFC_PERFMON` | Performance | Background RFC Performance monitor | yes | bgrfc_perfmon-background-rfc-performance-monitor |
| `BPM_BOR_REL` | BPM | BOR objects relations | yes |  |
| `BPM_CPP_APO` | BPM | APO CIF Postprocessing monitor (APO side) |  |  |
| `BPM_CPP_ECC` | BPM | APO CIF Postprocessing monitor (ERP side) |  |  |
| `BPM_ECC_ESOD` | BPM | ERP Sales Orders |  |  |
| `BPM_ECC_LISIS` | BPM | LIS Information System |  |  |
| `BPM_ECC_VBSK` | BPM | Collective Processing for a Sales Document |  |  |
| `BPM_ECC_VL06O` | BPM | Outbound Delivery Monitor |  |  |
| `BPM_EWM_SMQ` | BPM | EWM queues information |  |  |
| `BPM_ST13_TBI` | BPM | Business process monitoring KPIs |  |  |
| `BPM_TBL_STXL` | BPM | SAPscript texts |  |  |
| `BSP_LOG` | CRM | SAP BSP log |  |  |
| `CCMS` | BPM, ITSI, Performance | CCMS monitor | yes | ccms |
| `CDPOS` | BPM, Performance, Security | SAP Change Documents | yes | cdpos |
| `CTE_MONI` | BPM | Concur Communication Monitor | yes |  |
| `DB6_DB02_ACTVT` | Performance | DB6: DB Activities | yes |  |
| `DB6_DB02_AGENT` | Performance | DB6: Agent list | yes |  |
| `DB6_DB02_APPL` | Performance | DB6: Application List | yes |  |
| `DB6_DB02_ASTOR` | Performance | DB6: Automatic Storage | yes |  |
| `DB6_DB02_AUTILS` | Performance | DB6: Running utilities | yes |  |
| `DB6_DB02_BHIST` | Performance | DB6: Backup History | yes |  |
| `DB6_DB02_BLOGS` | Performance | DB6: Backup Log files | yes |  |
| `DB6_DB02_DBPF` | ITSI, Performance | DB6: Database Performance | yes |  |
| `DB6_DB02_FSYST` | Performance | DB6: File system | yes | db6_db02_fsyst |
| `DB6_DB02_HADR` | Performance | DB6: High availability disaster recovery |  |  |
| `DB6_DB02_LOCKS` | ITSI, Performance | DB6: Database locks overview | yes |  |
| `DB6_DB02_OVVW` | ITSI, Performance | DB6: Database overview | yes |  |
| `DB6_DB02_SSNAP` | Performance | DB6: Tablespace Snapshot Data | yes |  |
| `DB6_DB02_STMT` | ITSI, Performance | DB6: Expensive statements | yes |  |
| `DB6_DB02_TRANS` | Performance | DB6: Transaction list | yes |  |
| `DB6_DB02_TRLOG` | ITSI, Performance | DB6: Transaction log | yes | db6_db02_trlog |
| `DB6_DB02_TSNAP` | Performance | DB6: Table Snapshot Data | yes |  |
| `DEVACCESS` | ITSI, Security | List of users with developer keys | yes | devaccess |
| `E070` | BPM, Security | Change & Transport System: Requests/Tasks | yes | e070 |
| `ECATT` | Performance | ECATT |  |  |
| `FLP_MONITOR` | Performance | Fiori user monitoring (via plugin) | yes |  |
| `GRC_LOGS` | Security | GRC Details related to Firefighter ID Log On |  |  |
| `GROUP_LIST` | Internal | List of PowerConnect extractors | yes |  |
| `GW_ERROR_BEP` | Performance | Gateway Error Log (backend) | yes | gw_error_bep-sap-gateway-backend-error-log |
| `GW_ERROR_FND` | Performance | Gateway Error Log (frontend) | yes | gw_error_fnd-sap-gateway-frontend-error-log |
| `GW_TRACE_PERF` | Performance | Gateway performance trace | yes |  |
| `GW_TRACE_PLOAD` | Performance | Gateway payload trace | yes |  |
| `GW_TRACE_STATS` | Performance | Gateway statistics | yes |  |
| `HDBSCRIPTS` | Performance | HANA: SQL scripts extractor |  |  |
| `HDB_DB02_OVVW` | ITSI, Performance | HANA: DB overview | yes |  |
| `HDB_DBCC_ACTSTM` | ITSI, Performance | HANA: Active statements | yes | hdb_dbcc_actstm |
| `HDB_DBCC_ALERT` | ITSI, Performance | HANA: Alerts | yes | hdb_dbcc_alert |
| `HDB_DBCC_AUDIT` | Performance, Security | HANA: Audit log | yes | hdb_dbcc_audit |
| `HDB_DBCC_AULOG` | ITSI, Performance | HANA: DBACOCKPIT audit log | yes |  |
| `HDB_DBCC_BCCAT` | Performance | HANA: Backup catalogue | yes | hdb_dbcc_bccat |
| `HDB_DBCC_BTRAN` | ITSI, Performance | HANA: Blocked transactions | yes | hdb_dbcc_btran |
| `HDB_DBCC_CONLST` | ITSI, Performance | HANA: Connection list | yes | hdb_dbcc_conlst |
| `HDB_DBCC_DISKS` | Performance | HANA: Disk space overview | yes | hdb_dbcc_disks |
| `HDB_DBCC_EVENTS` | Performance | HANA: Events | yes |  |
| `HDB_DBCC_EXPSTM` | ITSI, Performance | HANA: Expensive statements | yes | hdb_dbcc_expstm |
| `HDB_DBCC_FDIAG` | Performance | HANA: Diagnostic files | yes |  |
| `HDB_DBCC_HEAP` | Performance | HANA: Heap memory overview | yes |  |
| `HDB_DBCC_INIHST` | Security | HANA: INI files change history | yes | hdb_dbcc_inihst-hana-database-ini-files-change-his |
| `HDB_DBCC_JOBP` | Performance | HANA: Jobs progress extractor | yes |  |
| `HDB_DBCC_JOBS` | Performance | HANA: Job history | yes |  |
| `HDB_DBCC_LDHIST` | Performance | HANA: Load History | yes | hdb_dbcc_ldhist-hana-database-load-history |
| `HDB_DBCC_LRGTAB` | Performance | HANA: Large Tables |  | hdb_dbcc_lrgtab |
| `HDB_DBCC_MDIAGF` | Performance | HANA: Merged Diagnosis files |  | hdb_dbcc_mdiagf |
| `HDB_DBCC_MTABID` | Performance | HANA: Missing Tables and Indexes |  | hdb_dbcc_mtabid |
| `HDB_DBCC_OLOCK` | Performance | HANA: Object locks | yes | hdb_dbcc_olock-hana-database-object-locks |
| `HDB_DBCC_RLOCK` | Performance | HANA: Record locks |  | hdb_dbcc_rlock-hana-database-record-locks |
| `HDB_DBCC_SLFMON` | Performance | HANA: Self-Monitoring |  | hdb_dbcc_slfmon |
| `HDB_DBCC_SQLPL` | Performance | HANA: SQL plan cache | yes | hdb_dbcc_sqlpl |
| `HDB_DBCC_SRVCS` | ITSI, Performance | HANA: Services | yes | hdb_dbcc_srvcs |
| `HDB_DBCC_THREAD` | ITSI, Performance | HANA: Threads | yes | hdb_dbcc_thread |
| `HDB_DBCC_USRPRV` | Performance, Security | HANA: User privileges |  | hdb_dbcc_usrprv |
| `HDB_REPL_STATE` | Performance | HANA: Replication status | yes |  |
| `ITS_MEMORY` | Performance | ITS Memory monitor | yes |  |
| `IWXBE_ERRLOG` | BPM, Performance | Enterprise Event Management: Error Log | yes |  |
| `LOGS` | BPM, ITSI, Performance, Security | SAP Log files | yes | logs |
| `LOGSYS_CHECK` | Performance | Logical system check |  |  |
| `LTRC` | BPM | SLT Replication status | yes | draft-ltrc |
| `LTRC_CHECK` | Performance | SLT Replication checks | yes |  |
| `MB51` | BPM | Material Document List (movements) |  | mb51-material-documents |
| `MSSSCRIPTS` | Performance | MS SQL: SQL scripts extractor |  |  |
| `MSS_DB02_BCKP` | Performance | MS SQL: Backup list | yes | mss_db02_bckp |
| `MSS_DB02_DDLK` | ITSI, Performance | MS SQL: Deadlock events | yes | mss_db02_ddlk |
| `MSS_DB02_DDLKXE` | ITSI, Performance | MS SQL: Deadlock events (XE) | yes |  |
| `MSS_DB02_ELOG` | Performance | MS SQL: Error log | yes | mss_db02_elog |
| `MSS_DB02_IOPF` | ITSI, Performance | MS SQL: I/O Performance | yes | mss_db02_iopf |
| `MSS_DB02_OVFL` | Performance | MS SQL: File overview | yes | mss_db02_ovfl |
| `MSS_DB02_OVVW` | ITSI, Performance | MS SQL: DB Overview | yes | mss_db02_ovvw |
| `MSS_DB02_PERF` | ITSI, Performance | MS SQL: Performance Overview | yes | mss_db02_perf |
| `MSS_DB02_RSTR` | Performance | MS SQL: Restore History | yes |  |
| `MSS_DB02_STMT` | ITSI, Performance | MS SQL: Query statistics | yes | mss_db02_stmt |
| `MTR_DDIC` | Internal | PowerConnect metric fields overview | yes |  |
| `NRIV` | BPM, ITSI | Number range monitor | yes | nriv |
| `ODATA_TRACE` | Performance | ODATA Metering Data/statistics |  |  |
| `ORASCRIPTS` | Performance | Oracle: SQL scripts extractor |  |  |
| `ORA_DB01_LOCK` | Performance | Oracle: DB locks overview | yes |  |
| `ORA_DB02_ALRT` | Performance | Oracle: DB alerts | yes | ora_db02_alrt |
| `ORA_DB02_BCKP` | Performance | Oracle: Backup History | yes |  |
| `ORA_DB02_BFFR` | ITSI, Performance | Oracle: Buffer Busy Waits | yes | ora_db02_bffr |
| `ORA_DB02_CACH` | ITSI, Performance | Oracle: Shared Cursor Cache | yes | ora_db02_cach |
| `ORA_DB02_ENQU` | Performance | Oracle: Enqueue Statistics | yes | ora_db02_enqu |
| `ORA_DB02_FILE` | ITSI, Performance | Oracle: Filesystem requests | yes | ora_db02_file |
| `ORA_DB02_IOACT` | Performance | Oracle DB Input Output activities | yes | ora_db02_ioact-oracle-db-io-activities |
| `ORA_DB02_LTCH` | Performance | Oracle: Latch monitor | yes | ora_db02_ltch |
| `ORA_DB02_PFOV` | Performance | Oracle: Performance Overview | yes | ora_db02_pfov |
| `ORA_DB02_PGAS` | Performance | Oracle: PGA Snapshot (all data) | yes |  |
| `ORA_DB02_PGCO` | Performance | Oracle: PGA Current Operations |  |  |
| `ORA_DB02_PGHS` | Performance | Oracle: PGA Workarea Histogram |  |  |
| `ORA_DB02_PGMU` | Performance | Oracle: PGA Memory Usage |  |  |
| `ORA_DB02_PGOM` | Performance | Oracle: PGA One-Multipass Workarea Monitor |  |  |
| `ORA_DB02_PGPO` | Performance | Oracle: PGA Workarea Histogram Percent Optimal |  |  |
| `ORA_DB02_PGST` | Performance | Oracle: PGA Status Monitor |  |  |
| `ORA_DB02_PGSW` | Performance | Oracle: PGA SQL Workarea |  |  |
| `ORA_DB02_PGTA` | Performance | Oracle: PGA Target Advice |  |  |
| `ORA_DB02_PGTH` | Performance | Oracle: PGA Advice Histogram |  |  |
| `ORA_DB02_PGTT` | Performance | Oracle: PGA Top Ten Memory cache consumers |  |  |
| `ORA_DB02_PGWE` | Performance | Oracle: PGA Workarea Execution Monitor |  |  |
| `ORA_DB02_SESS` | ITSI, Performance | Oracle: Session Monitor | yes | ora_db02_sess |
| `ORA_DB02_SGAD` | Performance | Oracle: SGA Monitor Details |  |  |
| `ORA_DB02_SGAM` | Performance | Oracle: SGA Monitor |  |  |
| `ORA_DB02_SGAS` | Performance | Oracle: SGA Snapshot (all data) | yes |  |
| `ORA_DB02_SGBP` | Performance | Oracle: SGA Buffer Pool Statistic Monitor |  |  |
| `ORA_DB02_SGCA` | Performance | Oracle: SGA Cache Advice Monitor |  |  |
| `ORA_DB02_SGCR` | Performance | Oracle: SGA Current Resize Operation |  |  |
| `ORA_DB02_SGDC` | Performance | Oracle: SGA Dynamic Components Monitor |  |  |
| `ORA_DB02_SGOR` | Performance | Oracle: SGA Completed Resize Operation Monitor |  |  |
| `ORA_DB02_SGPA` | Performance | Oracle: SGA Shared Pool Advice Monitor |  |  |
| `ORA_DB02_SMTR` | ITSI, Performance | Oracle: System metrics | yes |  |
| `ORA_DB02_SPOV` | Performance | Oracle: Space Overview | yes | ora_db02_spov |
| `ORA_DB02_SYEH` | Performance | Oracle: System Event History | yes | ora_db02_syeh |
| `ORA_DB02_TBLA` | Performance | Oracle: Table Access statistics | yes | ora_db02_tbla |
| `ORA_DB02_TBLG` | Performance | Oracle: Table Growth statistics | yes |  |
| `ORA_DB02_TSOV` | ITSI, Performance | Oracle: Tablespaces Overview | yes |  |
| `OSQLSCRIPTS` | BPM | Open SQL scripts extractor |  | osqlscripts-open-sql-scripts-extractor |
| `PC_AUDIT` | Internal | PowerConnect audit log | yes | pc_audit |
| `PC_HEALTH` | Internal | PowerConnect health | yes | pc_health |
| `PC_METRIC_QUEUE` | Internal | PowerConnect metric queue | yes |  |
| `PC_SCHEDULE` | Internal | PowerConnect extractor schedule | yes | pc_schedule |
| `PC_SENT_STATS` | Internal | PowerConnect metric sent statistics | yes |  |
| `PC_TRACE` | Internal | PowerConnect trace extractor | yes |  |
| `PRC_CHAIN_LOG` | BPM, Performance | Process Chain log extractor | yes | prc_chain_log |
| `ROLE_AUTH` | ITSI, Security | Sensitive authorizations | yes | role_auth |
| `RPF_CHECK` | Security | Rule framework checks |  | rpf_check-rule-processing-framework |
| `RSAU_CHECK` | Performance, Security | SAP Audit Integrity check monitor | yes |  |
| `RSUSR003` | ITSI, Security | Password status of Standard Users in All Clients | yes | rsusr003 |
| `RSUSR009` | Security | List of Users with Critical Authorizations |  |  |
| `RSUSR200` | ITSI, Security | List of Users According to Logon Date and Password Change | yes | rsusr200 |
| `RZ10` | ITSI, Performance, Security | SAP Profile parameters overview | yes | rz10 |
| `RZ10_LOG` | Performance, Security | SAP Profile parameters change log | yes |  |
| `S416N_CD` | BPM, Security | S416N Change Documents | yes | s416n_cd-s416n-change-documents |
| `SCC4` | ITSI, Security | SAP Client settings | yes | scc4-sap-clients-overview |
| `SCOT` | Performance | SAP Connect settings | yes |  |
| `SCU3` | Security | Table History (change log) | yes | scu3-analysis-of-logged-customizing-objects-and-ta |
| `SE06` | ITSI, Security | System Change settings | yes |  |
| `SE16N_CD` | BPM, Security | SE16N Change Documents | yes | se16n_cd-se16n-change-documents |
| `SE37_LOG` | Security | Manual FM Execution log | yes | se37_log-se37-fm-execution-log |
| `SECPOL_LOG` | Security | Security Policies change log | yes | secpol_log-change-logs-for-security-policies |
| `SICFCHK` | Security | SICF Public Services and Services with Logon Data | yes | sicfchk-sicf-sap-internet-communication-framework- |
| `SLG1` | BPM, Security | Application log monitor | yes | slg1 |
| `SLICENSE` | Performance, Security | SAP licence information | yes | slicense |
| `SLIN_SEC` | Performance, Security | Extended Program Check (CVA) |  |  |
| `SM04` | ITSI, Performance, Security | User sessions list per application server | yes | sm04 |
| `SM12` | ITSI, Performance | SAP Lock details | yes | sm12 |
| `SM12_STATS` | ITSI, Performance | SAP Lock statistics | yes |  |
| `SM13` | ITSI | RFC Update Records | yes | sm13 |
| `SM13_STATE` | ITSI | Update state per application server | yes | sm13_state |
| `SM19` | Security | SAP Audit log configuration | yes | sm19 |
| `SM20` | ITSI, Security | SAP Audit log | yes | sm20 |
| `SM21_LOG` | ITSI, Performance, Security | SAP System log | yes | sm21_log |
| `SM37` | BPM, ITSI, Performance | SAP Jobs (including Steps, Spool and Log) | yes | sm37 |
| `SM51` | ITSI, Performance | Work Process List per application server | yes | sm51 |
| `SM51_CBLCK` | ITSI | Server Communication Blocks overview | yes |  |
| `SM51_QUEUE` | ITSI | Server Request queue | yes |  |
| `SM51_STATE` | ITSI | Application server state |  | sm51_state |
| `SM58` | ITSI, Performance | Asynchronous RFC Error Log (tRFC) | yes | sm58 |
| `SM59` | ITSI, Performance | RFC Destination availability check | yes | sm59 |
| `SM59_RFCDES` | ITSI, Security | RFC Destination details | yes | sm59_rfcdes |
| `SM69` | Security | External OS commands change log | yes | sm69-external-os-commands-logs |
| `SMGW` | ITSI | Gateway Monitor | yes | smgw |
| `SMGW_SEC` | Performance, Security | Gateway Security information | yes | smgw_sec |
| `SMICM` | ITSI, Performance | SAP ICM Monitor | yes |  |
| `SMLG` | Performance | SAP Logon Groups overview | yes |  |
| `SMMS` | Performance | SAP Message Server Monitor | yes | smms |
| `SMQ1` | ITSI, Performance | qRFC Monitor (Outbound Queue) | yes | smq1 |
| `SMQ2` | ITSI, Performance | qRFC Monitor (Inbound Queue) | yes | smq2 |
| `SMQ2_TRFCQIN` | Performance | qRFC Monitor (Inbound Queue) TRFCQIN table overview |  |  |
| `SMQR` | Performance | Registration of Inbound Queues | yes |  |
| `SMW01` | Performance | SAP BDOC records |  |  |
| `SMWS` | Performance | SAP Web Socket Table | yes |  |
| `SNOTE` | ITSI, Security | SAP Notes overview | yes |  |
| `SOIN` | BPM, Performance | SAP Connect Received Requests | yes | soin-inbound-messages-smtp |
| `SOST` | BPM, Performance | SAP Connect Send Requests | yes | sost-send-requests-overview |
| `SP01` | Performance | Spool requests overview | yes |  |
| `SP01_CONTENT` | Performance | Spool requests content |  | sp01_content-spool-request-contents |
| `SPAD_STATUS` | Performance | SAP Printer status |  | spad_status |
| `SQLM` | Performance | SAP SQL Monitor |  |  |
| `SQVI` | Performance | SAP QuickViewer extractor | yes | sqvi |
| `SRAL` | Security | SAP Read access logging | yes |  |
| `SRT_CFG` | Performance | SAP Web-Service configuration |  |  |
| `SRT_LOG` | Performance | SAP Web-Service error log | yes | srt_log-web-services-error-log |
| `SRT_MONI` | Performance | SAP Web-Service message monitor |  |  |
| `SSB_KPI` | BPM | Smart Business KPIs | yes | ssb_kpi-sap-smart-business-ssb-kpi |
| `ST01_AUTH` | Performance | ST01: Authorization trace extractor |  |  |
| `ST01_STATE` | ITSI, Performance, Security | ST01: ABAP trace state | yes |  |
| `ST02_BFFR` | Performance | ST02: Table buffer overview | yes |  |
| `ST02_CALL` | Performance | ST02: Table buffer call statistics | yes |  |
| `ST02_MEM` | ITSI, Performance | ST02: Table buffer memory statistics | yes |  |
| `ST03_RFCC` | Performance | ST03: RFC client statistics per application server | yes | st03_rfcc |
| `ST03_RFCC_TOTAL` | Performance | ST03: RFC client statistics totals | yes |  |
| `ST03_RFCS` | Performance | ST03: RFC server statistics per application server | yes | st03_rfcs |
| `ST03_RFCS_TOTAL` | Performance | ST03: RFC server statistics totals | yes |  |
| `ST03_TIME` | Performance | ST03: Times statistics | yes |  |
| `ST03_TIME_AGG` | ITSI, Performance | ST03: Aggregated times statistics (calculated on fly) | yes |  |
| `ST03_TIME_TOT` | Performance | ST03: Times statistics totals | yes |  |
| `ST03_TIMT` | Performance | ST03: Times statistics (new) |  |  |
| `ST03_TIMT_TOTAL` | Performance | ST03: Times statistics totals (new) |  |  |
| `ST03_USRT` | Performance | ST03: User-tcode statistics | yes |  |
| `ST03_USRT_TOTAL` | Performance | ST03: User-tcode statistics totals | yes |  |
| `ST03_USRW` | Performance | ST03: User-workload statistics | yes |  |
| `ST03_USRW_TOTAL` | Performance | ST03: User-workload statistics totals | yes |  |
| `ST03_WEBC` | Performance | ST03: Web client statistics per application server | yes |  |
| `ST03_WEBC_TOTAL` | Performance | ST03: Web client statistics totals | yes |  |
| `ST03_WEBS` | Performance | ST03: Web server statistics per application server | yes |  |
| `ST03_WEBS_TOTAL` | Performance | ST03: Web server statistics totals | yes |  |
| `ST05` | Performance | ST05: Performance trace |  |  |
| `ST06` | ITSI, Performance | Operating System Monitor | yes | st06 |
| `ST06_FSYS` | ITSI, Performance | Operating System Monitor: File system overview | yes | st06_fsys |
| `ST06_HW` | Performance | Operating System Monitor: Hardware info | yes | st06_hw |
| `ST06_SN_DISK` | ITSI, Performance | Operating System Monitor: Disks overview | yes | st06_sn_disk |
| `ST06_TOP_CPU` | Performance | Operating System Monitor: Process overview | yes | st06_top_cpu |
| `ST10` | Performance | Table Call Statistics | yes |  |
| `ST22` | BPM, ITSI, Performance | ABAP dump details | yes | st22 |
| `STAD` | Performance, Security | SAP statistics records | yes | stad-sap-performance-monitor-statistics-records |
| `STAD3` | Performance | SAP statistics records aggregated | yes |  |
| `STATS` | Performance, Security | SAP statistics records (new) |  | stats-sap-performance-monitor-statistics-records-n |
| `STMS` | BPM, ITSI, Security | Transport Management System log | yes | stms |
| `STMS_QUEUE` | BPM, Performance, Security | Transport Management Queue | yes |  |
| `STMS_ROUTE` | BPM, Performance | Transport Management System routes | yes |  |
| `STRUST` | ITSI, Security | SSL certificates overview | yes |  |
| `STUSERTRACE` | Security | User Trace for Authorization objects | yes |  |
| `SU01` | ITSI, Security | SAP User information | yes | su01 |
| `SU53` | BPM, Security | Failed Authorization Checks | yes |  |
| `SUIM` | ITSI, Security | User change log (profile, role assignments, etc) | yes | suim |
| `SWEQUEUE` | Performance | SAP Workflow: Event Queue of Triggered Events |  |  |
| `SWI1` | Performance | SAP Workflow: work item overview |  | swi1 |
| `SWI1_LOG` | Performance | SAP Workflow: work item log | yes |  |
| `SWPC` | Performance | SAP Workflow: failed workflows overview | yes |  |
| `SWPR` | Performance | SAP Workflow: restart workflows overview | yes |  |
| `SXMB_MONI` | BPM, Performance | Integration Engine Monitoring |  | sxmb_moni |
| `SYSTEM_STATUS` | Performance | System related information | yes | system_status |
| `TABLE_COUNT` | BPM | Table records count | yes | table_count |
| `TREAD_DYN` | BPM | Table reader (retrieve table content based on user defined conditions) | yes | tread_dyn |
| `TU02` | Security | Profile parameters change log | yes | tu02-parameter-changes-in-sap-system |
| `UCON_LOG` | Security | Unified connectivity log | yes |  |
| `USER_AUTH` | Security | Sensitive user authorizations | yes | user_auth-user-authorizations |
| `USH02` | Security | User change history | yes | ush02 |
| `WE02` | BPM, ITSI | IDOC headers (including status) | yes | we02 |
| `DBCO` | Performance | Secondary DB connections test |  | dbco-secondary-db-connections-monitor |
| `FRE_UI` | Performance | User Interface for F&R Messages |  | fre_ui-user-interface-for-f-r-messages-monitor |
| `HDB_DBCC_INI` | Security | HANA: INI files snapshot | yes | hdb_dbcc_ini-hana-ini-files |
| `HDB_DBCC_SYSMON` | Performance | HANA Systems Monitor |  | hdb_dbcc_sysmon-hana-systems-monitor |
| `HDB_DBCC_USERS` | Performance, Security | HANA: List of Users | yes | hdb_dbcc_users-hana-db-user-list |
| `STMS_TPLOG` | Security | Transport Management TP Tool log | yes | stms_tplog-tp-call-log-ulog |
| `VARIANT` | BPM | Reports Variant Data |  | variant-reports-input-screen-variant-details |
| `BPM_ECC_INVOICE` | BPM | Invoice documents extractor (ECC) |  |  |
| `GRC_REQUESTS` | Security | GRC Requests Details |  | grc_requests-access-requests-in-sap-grc |
| `LTRC_DMC` | BPM, Performance | SLT Replication Table & Load Status | yes | ltrc_dmc-slt-replication-table-load-status |
| `SDF_MON` | Performance | Snapshot Monitoring - /SDF/MON |  | sdf_mon-sap-performance-snapshot-monitoring |
| `SMQS` | Performance | SMQS: List of Registered tRFC/qRFC Destinations | yes | smqs-outbound-qrfc-monitor |
| `SM_SAP_NOTES` | Performance, Security | SAP Notes extractor (SolMan) | yes |  |
| `STRUST_HISTORY` | Security | SSL certificates history | yes | strust_history-certificate-change-history |
| `HDBS_SLT` | Performance | HDB Accelerators SLT information |  | hdbs_slt-erp-accelerators-fi |
| `MSS_DB02_BLOCKS` | Performance | MS SQL: Blocking Locks | yes | mss_db02_blocks-ms-sql-database-blocking-locks |
| `ORA_DB02_DBAHIST` | Performance | Oracle: DBA SQL Plan History | yes | ora_db02_dbahist-oracle-database-sql-plan-history |
| `SBDLOG` | Security | Secure-by-Default Log | yes | sbdlog-sap-secure-by-default-logs |
| `SMENQ_REPLICATOR` | ITSI, Performance | SMENQ: Enqueue Replicator Admin data |  | smenq_replicator-enqueue-replicator-admin-data |
| `SMENQ_SERVER` | ITSI, Performance | SMENQ: Enqueue Server Admin data | yes | smenq_server-enqueue-server-admin-data |
| `SOA_PING` | Performance | SOAMANAGER Consumer Proxy Ping |  | soa_ping-soamanager-consumer-proxy-ping |
| `ST03_TIME_DIST` | Performance | ST03: Task Time statistics distribution |  | st03_time_dist-st03-response-time-distribution |
| `SYSTEM_TIME` | Performance, Security | System time information | yes | system_time-time-diagnosis-information |
| `TAANA` | BPM, Performance | TAANA: Table data Analysis |  | taana-table-data-analysis |
| `HDB_CERT_LIST` | Performance, Security | HANA: List of certificates | yes | hdb_cert_list-hana-db-certificate-list |
| `STATS_TRACE` | Performance | SAP statistics records trace |  |  |
| `WPER` | BPM | POS Interface unprocessed inbound IDOCs |  | wper |
| `BNK_MONI` | BPM | Batch and payment monitor |  | bnk_moni-bank-and-payment-monitor |
| `DMFLOG_RFC` | BPM, Performance | DMF Log RFC content |  | dmflog_rfc-dmf-log-rfc-content |
| `MSS_DB02_AOOV` | ITSI, Performance | MS SQL: DB AlwaysOn Overview | yes | mss_db02_aoov |
| `MSS_DB02_LRGTAB` | Performance | MS SQL: Largest Tables | yes | mss_db02_lrgtab-ms-sql-largest-tables |
| `MSS_DB02_MEMORY` | ITSI, Performance | MS SQL: Memory Overview | yes | mss_db02_memory |
| `ODATA_SERVICE` | BPM | ODATA Service Reader |  | odata_service |
| `SMAMC` | Performance | SAP AMC Recipient Table |  | smamc |
| `SMCL` | ITSI, Performance | SAP Cross System Lock details |  | smcl |
| `STAD_TRACE` | Performance | SAP statistics records trace (STAD) |  |  |
| `CRM_ICI_TRACE` | Performance | CRM ICI Trace monitor |  | crm_ici_trace |
| `ASE_DBCC_DMPHIS` | ITSI, Performance | SyBase: Backup history |  | ase_dbcc_dmphis |
| `DB6_DB02_ELWNAME` | Performance | DB6: Extended Latch Wait Names/Types |  | db6_db02_elwname-db6-extended-latch-wait-names-typ |
| `DB6_DB02_TELWT` | Performance | DB6: Total Extended Latch Wait Time drill-down by Service Classes |  | db6_db02_telwt-db6-total-extended-latch-wait-time- |
| `DB6_DB02_TIMESPT` | Performance | DB6: Time Spent Analysis |  | db6_db02_timespt-db6-time-spent-analysis |
| `HDB_THRDSMP_STAT` | Performance | HANA: Thread Sample Statistical Records 2.00.060+ |  | hdb_thrdsmp_stat-kpis-for-individual-hana-database |
| `LTRC_LATENCY` | BPM, Performance | SLT Replication Latency |  | ltrc_latency |
| `PC_SLM_ACTIONLOG` | Internal | PowerConnect SLM Action Logs |  | pc_slm_actionlog-powerconnect-slm-action-logs |
| `PC_SLM_SYNCLOG` | Internal | PowerConnect SLM Sync Logs |  | pc_slm_synclog-powerconnect-slm-sync-logs |
| `SALES_DOC_FLOW` | BPM | Sales Document Flow |  | sales_doc_flow |

## Java, Cloud and other event types

Lowercase event types come from the Java and Cloud agents. The second column lists the shipped Splunk dashboards that read each type, which indicates its purpose.

| Event type | Read by dashboards |
|---|---|
| `agent_health` | Java Agent Health; PowerConnect Cloud Agent Health; PowerConnect Data Meter |
| `alert` | SAP Cloud Connector |
| `api_management_performance` | SAP Cloud - API Management Monitoring |
| `application_trace_log` | Application Trace logs |
| `ariba_audit_log` | SAP Ariba - Security Monitoring |
| `certificate` | NetWeaver Java: Certificate Monitoring |
| `certificate_status` | SAP Cloud Connector |
| `channel_status` | PI/PO Channel Monitoring |
| `component` | NetWeaver Java: Component Information |
| `config_changes_log` | NetWeaver Java: Config Changes Monitoring |
| `cpi_artifact` | SAP Cloud - CPI Message Monitoring |
| `cpi_inventory` | SAP Cloud - CPI Message Status Overview |
| `cpi_message` | SAP Cloud - CPI Message Monitoring; SAP Cloud - CPI Message Status Overview; CPI - S/4 HANA Correlation (STAD3); CPI - S/4 HANA Correlation (STATS) |
| `cpq_audit_trail_user_action` | Overview |
| `cpq_event_log` | Overview |
| `cpu_status` | SAP Cloud Connector |
| `cp_audit_log` | SAP Cloud - Audit Logs |
| `datasphere_admission_control` | SAP Datasphere - Overview |
| `datasphere_oom` | SAP Datasphere - Overview |
| `datasphere_space_memory` | SAP Datasphere - Overview |
| `datasphere_task_log` | SAP Datasphere - Overview; SAP Datasphere - Task Logs |
| `db_connection` | Java System Overview; NetWeaver Java: DB Connection Statistics |
| `db_sql` | Java System Overview |
| `default_trace_log` | Default Trace logs |
| `disk` | NetWeaver Java: Disk Monitoring |
| `disk_status` | SAP Cloud Connector |
| `di_graphs` | SAP Data Intelligence Overview |
| `di_metric` | SAP Data Intelligence Overview |
| `dsr` | Java PI - ABAP Correlation; Java System Overview; NetWeaver Java: Distributed Trace |
| `fg_audit_trail` | SAP FieldGlass Overview |
| `http_access_log` | SAP Cloud Connector |
| `http_ping` | Synthetics Monitoring |
| `ias_audit_log` | SAP Cloud - IAS Security Monitoring; Security Monitoring |
| `jmx` | JVM Overview; Java System Overview; PowerConnect Resource Utilization; Landscape Overview |
| `ljs_trace_log` | SAP Cloud Connector |
| `locks` | NetWeaver Java: Locks |
| `master_role` | SAP Cloud Connector |
| `memory_status` | SAP Cloud Connector |
| `monthly_subaccounts_cost` | SAP Cloud - Estimated Billing |
| `mpi_buffer` | NetWeaver Java: MPI Buffer Stats |
| `msg_server_parameters` | NetWeaver Java: Message Server |
| `network` | NetWeaver Java: Network Monitoring |
| `ni_ping` | Availability Management Information System; Basis Health Checks; System Overview; SAP Environment; SAP Landscape Analysis; System Availability Details |
| `pi_message` | Java PI - ABAP Correlation; PI/PO Messages |
| `pi_performance` | PI/PO Performance Monitoring |
| `pi_queues` | PI/PO Adapter Engine Queues |
| `portal_activity_log` | Page Hit Rate; Page Response Time |
| `process` | NetWeaver Java: Process Information |
| `s4hana_cloud_audit_log` | SAP S/4HANA Cloud Public Edition - Audit Logs; SAP S/4HANA Cloud Public Edition - Security Overview |
| `s4hana_cloud_user` | SAP S/4HANA Cloud Public Edition - Audit Logs; SAP S/4HANA Cloud Public Edition - Security Overview |
| `s4hana_cloud_user_change` | SAP S/4HANA Cloud Public Edition - Security Overview |
| `sac_activities` | SAP Analytics Cloud - User Activity |
| `scc_backend_connection` | SAP Cloud Connector |
| `security_audit_log` | NetWeaver Java: Security Audit Logs |
| `security_log` | NetWeaver Java: Security Logs |
| `server` | SAP Business Objects - Overview |
| `session` | NetWeaver Java: User Sessions |
| `sf_change_audit_report` | Change Audit |
| `sf_compound_api_audit_log` | Security Monitoring |
| `sf_employee_replication` | Process Monitoring |
| `sf_em_event` | Process Monitoring; SuccessFactors Monitoring Dashboard |
| `sf_odata_api_audit_log` | Security Monitoring |
| `sf_onboarding_process` | Onboarding Process Monitoring |
| `sf_payroll_configuration` | Payroll Monitoring |
| `sf_payroll_run_results` | Payroll Monitoring |
| `subaccount` | SAP Cloud Connector |
| `syslog` | SAP Cloud Foundry Syslog |
| `task` | NetWeaver Java: Task Monitoring |
| `thread` | Thread Hotspots |
| `usage_backend` | SAP Cloud Connector |
| `users` | NetWeaver Java: UME |
| `web_session` | NetWeaver Java: Web Sessions |

## ABAP event types referenced by dashboards but not in the extractor summary

Sub-types and newer extractors.

| Event type | Read by dashboards |
|---|---|
| `BD87` | Intermediate Documents (iDocs); IDOC Status (BD87); Weekly Usage Statistics |
| `BSP_WD_DEMO` | SAP CRM BSP Transactions |
| `ENQUEUE` | SAP Datasphere - Overview |
| `H_DB02_OVVW` | HANA: Space; HANA: Overview; HANA Database |
| `REJECT` | SAP Datasphere - Overview |
