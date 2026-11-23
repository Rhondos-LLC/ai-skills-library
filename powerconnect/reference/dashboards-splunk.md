# Shipped Splunk dashboards and the event types they read

Generated from the product documentation ("List of Event Types"). Search this file by topic, dashboard name or event type. **Menu path** is where the dashboard sits in the PowerConnect Splunk app; blank means it is reached by drill-down or from System Analysis. Panel-level detail is in the documentation page `list-of-dashboards.md`.

| Dashboard | View ID | Menu path | Event types |
|---|---|---|---|
| Background Jobs | `pc_abap_bp_jobs` | Business Process > Background Jobs | LOGS, SM37, ST22 |
| Intermediate Documents (iDocs) | `pc_abap_bp_idoc` | Business Process > Intermediate Documents (iDocs) | BD87, BD87_DYN, BPM_BOR_REL, WE02 |
| Transports | `pc_abap_bp_transports` | Business Process > Transports | E070, STMS |
| Basis Health Checks | `basis_health_checks` | Dashboard Studio > Basis Health Checks | CCMS, ni_ping, SCC4, SM12, SM13, SM37, SM51, SM58, SMQ1, SP01, ST01_STATE, ST03_TIME, ST03_TIME_AGG, ST06, ST06_SN_DISK, ST22 |
| Weekly Usage Statistics | `weekly_usage_statistics` | Dashboard Studio > Weekly Usage Statistics | BD87, BD87_DYN, SM20, SM37, STAD |
| ASE: Computation Usage Details | `ase_dbcc_cusage` | Database > ASE > ASE: Computation Usage Details | ASE_DBCC_CUSAGE |
| ASE: Database Details | `ase_dbcc_dbsize` | Database > ASE > ASE: Database Details | ASE_DBCC_DBSIZE, ASE_DBCC_PROCES |
| ASE: DeviceIO Details | `ase_dbcc_devcio` | Database > ASE > ASE: DeviceIO Details | ASE_DBCC_DEVCIO |
| ASE: Expensive Statements (raw) | `ase_dbcc_expensive_statements` | Database > ASE > ASE: Expensive Statements (raw) | ASE_DBCC_CCSTAT |
| ASE: Log Details | `ase_dbcc_dbalog` | Database > ASE > ASE: Log Details | ASE_DBCC_DBALOG |
| ASE: Resource Details | `ase_dbcc_resource` | Database > ASE > ASE: Resource Details | ASE_DBCC_RESOUR |
| ASE: SpinLock/System State Details | `ase_dbcc_sywait` | Database > ASE > ASE: SpinLock/System State Details | ASE_DBCC_SPINLC, ASE_DBCC_SYWAIT |
| ASE: System Action Details | `ase_dbcc_sysact` | Database > ASE > ASE: System Action Details | ASE_DBCC_SYSACT |
| DB/2: Activities | `sap_db2_activities` | Database > DB/2 > DB/2: Activities | DB6_DB02_ACTVT |
| DB/2: Expensive Statements (raw) | `sap_db2_expensive_statements` | Database > DB/2 > DB/2: Expensive Statements (raw) | DB6_DB02_STMT |
| DB/2: Overview | `sap_db2_ovvw` | Database > DB/2 > DB/2: Overview | DB6_DB02_DBPF, DB6_DB02_OVVW |
| HANA: Active Statements | `hana_active_statements` | Database > HANA > HANA: Active Statements | HDB_DBCC_ACTSTM |
| HANA: Alert Details (Current) | `hana_alert_details_current` | Database > HANA > HANA: Alert Details (Current) | HDB_DBCC_ALERT |
| HANA: Alert Details (Historical) | `hdb_dbcc_alert` | Database > HANA > HANA: Alert Details (Historical) | HDB_DBCC_ALERT |
| HANA: Audits | `hdb_dbcc_audits` | Database > HANA > HANA: Audits | HDB_DBCC_AUDIT |
| HANA: Backup Overview Dashboard | `hana_backup_overview_dashboard` | Database > HANA > HANA: Backup Overview Dashboard | HDB_DBCC_BCCAT |
| HANA: Blocked Transactions | `hana_blocked_transacts` | Database > HANA > HANA: Blocked Transactions | HDB_DBCC_BTRAN |
| HANA: Certificate Status | `hdb_cert_list` | Database > HANA > HANA: Certificate Status | HDB_CERT_LIST |
| HANA: Config (INI) Change | `hana_config_ini_change` | Database > HANA > HANA: Config (INI) Change | HDB_DBCC_INIHST |
| HANA: Configuration Mini-checks | `hdb_dbcc_custom_scripts` | Database > HANA > HANA: Configuration Mini-checks | HDBSCRIPTS |
| HANA: DB Load History | `hana_db_load_history` | Database > HANA > HANA: DB Load History | HDB_DBCC_LDHIST |
| HANA: Diagnostic Files | `hdb_dbcc_diagnostic_files` | Database > HANA > HANA: Diagnostic Files | HDB_DBCC_FDIAG |
| HANA: Disk Overview | `hana_disk_dashboard` | Database > HANA > HANA: Disk Overview | HDB_DBCC_DISKS |
| HANA: Expensive Statements (raw) | `hdb_expensive_statements` | Database > HANA > HANA: Expensive Statements (raw) | HDB_DBCC_EXPSTM |
| HANA: Heap Memory Usage | `hdb_dbcc_memory_usage` | Database > HANA > HANA: Heap Memory Usage | HDB_DBCC_HEAP |
| HANA: Large Table Details | `hana_large_table_details` | Database > HANA > HANA: Large Table Details | HDB_DBCC_LRGTAB |
| HANA: Large Table Overview | `hana_large_table_overview` | Database > HANA > HANA: Large Table Overview | HDB_DBCC_LRGTAB |
| HANA: Locks | `hana_locks` | Database > HANA > HANA: Locks | HDB_DBCC_OLOCK, HDB_DBCC_RLOCK |
| HANA: Overview | `hdb_db02_ovvw` | Database > HANA > HANA: Overview | HDB_DB02_OVVW, HDB_DBCC_ALERT, HDB_DBCC_AUDIT, HDB_DBCC_HEAP, HDB_DBCC_MDIAGF, HDB_DBCC_SQLPL, HDB_DBCC_SRVCS, HDB_DBCC_THREAD, H_DB02_OVVW |
| HANA: Replication | `hdb_replication` | Database > HANA > HANA: Replication | HDB_REPL_STATE |
| HANA: SQL Plan Statistics | `hana_sql_plan_statistics` | Database > HANA > HANA: SQL Plan Statistics | HDB_DBCC_SQLPL |
| HANA: SQLPL Details | `hdb_dbcc_sqlpl` | Database > HANA > HANA: SQLPL Details | HDB_DBCC_SQLPL |
| HANA: Services | `hdb_dbcc_services` | Database > HANA > HANA: Services | HDB_DBCC_SRVCS |
| HANA: Space | `HANA` | Database > HANA > HANA: Space | HDB_DB02_OVVW, H_DB02_OVVW |
| HANA: Threads | `hdb_dbcc_threads` | Database > HANA > HANA: Threads | HDB_DBCC_THREAD |
| HANA: Trace | `hdb_dbcc_trace` | Database > HANA > HANA: Trace | HDB_DBCC_MDIAGF |
| Oracle: Expensive Statements (raw) | `oracle_expensive_statements` | Database > Oracle > Oracle: Expensive Statements (raw) | ORA_DB02_CACH |
| Oracle: Overview | `oracle_ovvw` | Database > Oracle > Oracle: Overview | ORA_DB02_FILE, ORA_DB02_SPOV |
| Oracle: SQL Plan Statistics | `ora_sql_plan_stats` | Database > Oracle > Oracle: SQL Plan Statistics | ORA_DB02_DBAHIST |
| Oracle: Segments | `oracle_segments` | Database > Oracle > Oracle: Segments | ORA_DB02_TBLG |
| Oracle: Tablespace Growth | `oracle_table_space_growth` | Database > Oracle > Oracle: Tablespace Growth | ORA_DB02_TSOV |
| SQL Server: AlwaysOn Availability Monitoring | `sql_server_aoov` | Database > SQL Server > SQL Server: AlwaysOn Availability Monitoring | MSS_DB02_AOOV |
| SQL Server: Expensive Statements (raw) | `sql_server_expensive_statements` | Database > SQL Server > SQL Server: Expensive Statements (raw) | MSS_DB02_STMT |
| SQL Server: Large Tables | `sql_server_lrgtab` | Database > SQL Server > SQL Server: Large Tables | MSS_DB02_LRGTAB |
| SQL Server: Memory | `sql_server_mem` | Database > SQL Server > SQL Server: Memory | MSS_DB02_MEMORY |
| SQL Server: Overview | `sql_server_ovvw` | Database > SQL Server > SQL Server: Overview | MSS_DB02_IOPF, MSS_DB02_OVVW |
| Processed XML Messages | `pc_abap_int_sxmb` | Interfaces > Processed XML Messages | SMQ2, SXMB_MONI |
| Remote Function Calls (RFCs) | `pc_abap_int_rfc` | Interfaces > Remote Function Calls (RFCs) | SM58, SM59, SMQ1, SMQ2 |
| SAP Business Objects - Overview | `sap_bo_overview` | Java > Business Objects > SAP Business Objects - Overview | server |
| Page Hit Rate | `page_hit_rate` | Java > EP > Page Hit Rate | portal_activity_log |
| Page Response Time | `page_response_time` | Java > EP > Page Response Time | portal_activity_log |
| JVM Overview | `JVM` | Java > JVM > JVM Overview | jmx |
| Thread Hotspots | `jvm_thread_hotspots` | Java > JVM > Thread Hotspots | thread |
| Java Agent Health | `java_agent_health` | Java > Java Agent Health | agent_health |
| Java System Overview | `java_system_overview` | Java > Java System Overview | db_connection, db_sql, dsr, jmx |
| Application Trace logs | `app_trace_logs` | Java > NW > Application Trace logs | application_trace_log |
| Default Trace logs | `default_trace_logs` | Java > NW > Default Trace logs | default_trace_log |
| NetWeaver Java: Certificate Monitoring | `netweaver_java_certificate_monitoring` | Java > NW > NetWeaver Java: Certificate Monitoring | certificate |
| NetWeaver Java: Component Information | `netweaver_java_component_information` | Java > NW > NetWeaver Java: Component Information | component |
| NetWeaver Java: Config Changes Monitoring | `netweaver_java_config_changes_monitoring` | Java > NW > NetWeaver Java: Config Changes Monitoring | config_changes_log |
| NetWeaver Java: DB Connection Statistics | `netweaver_java_db_connection_statistics` | Java > NW > NetWeaver Java: DB Connection Statistics | db_connection |
| NetWeaver Java: Disk Monitoring | `netweaver_java_disk_monitoring` | Java > NW > NetWeaver Java: Disk Monitoring | disk |
| NetWeaver Java: Distributed Trace | `netweaver_java_distributed_trace` | Java > NW > NetWeaver Java: Distributed Trace | dsr |
| NetWeaver Java: Locks | `netweaver_java_locks` | Java > NW > NetWeaver Java: Locks | locks |
| NetWeaver Java: MPI Buffer Stats | `netweaver_java_mpi_buffer_stats` | Java > NW > NetWeaver Java: MPI Buffer Stats | mpi_buffer |
| NetWeaver Java: Message Server | `netweaver_java_message_server` | Java > NW > NetWeaver Java: Message Server | msg_server_parameters |
| NetWeaver Java: Network Monitoring | `netweaver_java_network_monitoring` | Java > NW > NetWeaver Java: Network Monitoring | network |
| NetWeaver Java: Process Information | `netweaver_java_process_information` | Java > NW > NetWeaver Java: Process Information | process |
| NetWeaver Java: Security Audit Logs | `netweaver_java_security_audit_logs` | Java > NW > NetWeaver Java: Security Audit Logs | security_audit_log |
| NetWeaver Java: Security Logs | `netweaver_java_security_logs` | Java > NW > NetWeaver Java: Security Logs | security_log |
| NetWeaver Java: Task Monitoring | `netweaver_java_task_monitoring` | Java > NW > NetWeaver Java: Task Monitoring | task |
| NetWeaver Java: UME | `netweaver_java_ume` | Java > NW > NetWeaver Java: UME | users |
| NetWeaver Java: User Sessions | `netweaver_java_user_sessions` | Java > NW > NetWeaver Java: User Sessions | session |
| NetWeaver Java: Web Sessions | `netweaver_java_web_sessions` | Java > NW > NetWeaver Java: Web Sessions | web_session |
| Java PI - ABAP Correlation | `java_pi_abap_correlation` | Java > PI/PO > Java PI - ABAP Correlation | dsr, pi_message, STATS |
| PI/PO Adapter Engine Queues | `pipo_adapter_engine_queues` | Java > PI/PO > PI/PO Adapter Engine Queues | pi_queues |
| PI/PO Channel Monitoring | `channel_monitoring` | Java > PI/PO > PI/PO Channel Monitoring | channel_status |
| PI/PO Messages | `pi_message` | Java > PI/PO > PI/PO Messages | pi_message |
| PI/PO Performance Monitoring | `pi_performance` | Java > PI/PO > PI/PO Performance Monitoring | pi_performance |
| Availability Management Information System | `availability_management_information_system_clone` | Landscape > Legacy > Availability Management Information System | CCMS, ni_ping, SM51, ST03_TIME, ST06 |
| Landscape Component Information | `sap_landscape_component_information` | Landscape > Legacy > Landscape Component Information | SYSTEM_STATUS |
| Landscape Overview | `sap_landscape_ovw` | Landscape > Legacy > Landscape Overview | CCMS, jmx, SCC4, SM12, SM13, SM37, SM51, SM58, SMQ1, ST01_STATE, ST03_TIME, ST06, ST22, SYSTEM_STATUS |
| SAP Landscape Analysis | `sap_landscape_analysis` | Landscape > Legacy > SAP Landscape Analysis | CCMS, ni_ping, SM13, SM37, SM51, SM51_STATE, ST03_TIME, ST06, ST06_FSYS, ST06_SN_DISK, ST22, STAD3, STMS |
| System Availability Details | `system_availability_details` | Landscape > Legacy > System Availability Details | CCMS, ni_ping, SM51, SM51_STATE, ST03_TIME, ST06 |
| System Overview | `sap_system_ovw_7x` | Landscape > Legacy > System Overview | CCMS, ni_ping, SCC4, SM04, SM12, SM13, SM20, SM21_LOG, SM37, SM51, SM58, SMQ1, ST01_STATE, ST03_TIME, ST06, ST22, STAD3 |
| Weekly Usage Statistics | `sap_weekly_usage_statistics` | Landscape > Legacy > Weekly Usage Statistics | BD87, BD87_DYN, SM20, SM37, STAD |
| Appservers | `pc_abap_perf_app_summary` | Performance > Appservers | CCMS, SM51, SM51_CBLCK, SM51_QUEUE, SM51_STATE, ST02_BFFR, ST02_MEM, ST03_TIME, ST06 |
| HANA Database | `pc_abap_perf_db_hana_summary` | Performance > HANA Database | HDBSCRIPTS, HDB_CERT_LIST, HDB_DB02_OVVW, HDB_DBCC_ACTSTM, HDB_DBCC_ALERT, HDB_DBCC_AUDIT, HDB_DBCC_BCCAT, HDB_DBCC_BTRAN, HDB_DBCC_DISKS, HDB_DBCC_FDIAG, HDB_DBCC_HEAP, HDB_DBCC_INIHST, HDB_DBCC_LDHIST, HDB_DBCC_LRGTAB, HDB_DBCC_MDIAGF, HDB_DBCC_OLOCK, HDB_DBCC_RLOCK, HDB_DBCC_SQLPL, HDB_DBCC_SRVCS, HDB_DBCC_THREAD, H_DB02_OVVW |
| Microsoft SQL Server | `pc_abap_perf_db_sql_summary` | Performance > Microsoft SQL Server | MSS_DB02_AOOV, MSS_DB02_DDLK, MSS_DB02_IOPF, MSS_DB02_LRGTAB, MSS_DB02_MEMORY, MSS_DB02_OVVW, MSS_DB02_PERF, MSS_DB02_STMT |
| Operating System | `pc_abap_perf_os` | Performance > Operating System | ST06, ST06_FSYS, ST06_SN_DISK, SYSTEM_TIME |
| SAP Environment | `pc_abap_perf_env_summary` | Performance > SAP Environment | CCMS, LOGS, ni_ping, SM12, SM13, SM13_STATE, SM21_LOG, SM51, SMGW, SMICM, ST03_TIME, ST06, ST22 |
| System Activity | `pc_abap_perf_activity` | Performance > System Activity | STAD3, STATS |
| Alert Definition (Legacy) | `ootb_alerts` | PowerConnect > Events and Alerts > Alert Definition (Legacy) | GROUP_LIST |
| ABAP Extractor Data Preview | `extractor_data_preview` | PowerConnect > Extractor > ABAP Extractor Data Preview | MTR_DDIC |
| ABAP Extractor Status | `sap_extractor_status` | PowerConnect > Extractor > ABAP Extractor Status | GROUP_LIST, PC_TRACE |
| Data Dictionary | `sap_data_dictionary` | PowerConnect > Extractor > Data Dictionary | MTR_DDIC |
| PowerConnect Extractor Schedule | `powerconnect_extractor_schedule` | PowerConnect > Extractor > PowerConnect Extractor Schedule | PC_SCHEDULE |
| Extractors | `pc_abap_pc_extract` | PowerConnect > Extractors | GROUP_LIST, MTR_DDIC, PC_SCHEDULE |
| Health | `pc_abap_pc_health` | PowerConnect > Health | GROUP_LIST, PC_AUDIT, PC_METRIC_QUEUE, PC_SENT_STATS, SLG1, SM51 |
| PowerConnect Audit | `powerconnect_audit` | PowerConnect > Health > PowerConnect Audit | PC_AUDIT |
| PowerConnect Change Logs | `powerconnect_change_logs` | PowerConnect > Health > PowerConnect Change Logs | PC_AUDIT |
| PowerConnect Data Meter | `powerconnect_data_meter` | PowerConnect > Health > PowerConnect Data Meter | agent_health, PC_SENT_STATS |
| PowerConnect Health | `powerconnect_health` | PowerConnect > Health > PowerConnect Health | SLG1 |
| PowerConnect Resource Utilization | `powerconnect_resource_utilization` | PowerConnect > Health > PowerConnect Resource Utilization | GROUP_LIST, jmx, PC_METRIC_QUEUE, SM51 |
| Event Types (SAP Group Definition) with Dashboards | `map_event_type_dashboard` | PowerConnect > Mapping > Event Types (SAP Group Definition) with Dashboards | GROUP_LIST |
| Background Job Analysis by Instance | `sap_instance_background_job_analysis` | SAP Business Process > Background Jobs > Background Job Analysis by Instance | SM37 |
| Background Jobs Overview | `sap_batch_jobs` | SAP Business Process > Background Jobs > Background Jobs Overview | LOGS, SM37, ST22 |
| Business Process Monitoring KPIs | `business_process_monitoring_kpis` | SAP Business Process > Business KPIs > Business Process Monitoring KPIs | BPM_ST13_TBI |
| Smart Business KPI | `smart_business_kpi` | SAP Business Process > Business KPIs > Smart Business KPI | SSB_KPI |
| Cross System Locks | `smcl_cross_sys_locks` | SAP Business Process > Cross System Locks | SMCL |
| DB Table Synchronization | `hdbs_slt_db_table_sync` | SAP Business Process > DB Table Synchronization | HDBS_SLT |
| FRE_UI Analysis | `fre_ui_analysis` | SAP Business Process > FRE_UI Analysis | FRE_UI |
| IDOC Segments Overview | `idoc_segmentation` | SAP Business Process > IDOCs > IDOC Segments Overview | BD87_DYN |
| IDOC Status (BD87) | `sap_global_idoc_status` | SAP Business Process > IDOCs > IDOC Status (BD87) | BD87, BD87_DYN |
| IDOC Status for WE02 Details | `we02_details` | SAP Business Process > IDOCs > IDOC Status for WE02 Details | WE02 |
| IDOC Status for WE02 Overview | `we02_dashboard` | SAP Business Process > IDOCs > IDOC Status for WE02 Overview | WE02 |
| IDOC To Business Object Relationship | `bpm_idoc_to_business_object_relationship` | SAP Business Process > IDOCs > IDOC To Business Object Relationship | BPM_BOR_REL |
| Point of Sale IDOC Errors | `wper_idoc_mon` | SAP Business Process > IDOCs > Point of Sale IDOC Errors | WPER |
| Number Range Monitoring | `sap_global_number_range_monitoring` | SAP Business Process > Number Range Monitoring | NRIV |
| OData Service Viewer | `odata_service_viewer` | SAP Business Process > OData Service Viewer | ODATA_SERVICE |
| Outbound Delivery Monitor | `outbound_delivery_monitor` | SAP Business Process > Outbound Delivery Monitor | BPM_ECC_VL06O |
| SAP ALV Reports Output | `alv_reports_dashboard` | SAP Business Process > SAP ALV Reports Output | ALV_REPORTS |
| SAP Change Documents | `sap_change_documents` | SAP Business Process > SAP Change Documents | CDPOS |
| SAP Connect: Send Requests | `sap_connect_send_requests` | SAP Business Process > SAP Connect: Send Requests | SOST |
| SAP Table Reader | `sap_table_reader` | SAP Business Process > SAP Table Reader | TREAD_DYN |
| SLG1 Dashboard | `slg1_dashboard` | SAP Business Process > SLG1 Dashboard | SLG1 |
| Transport Details | `transport_per_system_detail` | SAP Business Process > Transport Details | E070, STMS |
| Transport Overview | `sap_transport_dashboard` | SAP Business Process > Transport Overview | E070, STMS |
| Transport Routes Overview | `transport_routes_overview` | SAP Business Process > Transport Routes Overview | STMS_ROUTE |
| SAP Cloud - API Management Monitoring | `sap_cloud_api_management_monitoring` | SAP Cloud > API Management > SAP Cloud - API Management Monitoring | api_management_performance |
| SAP Analytics Cloud - User Activity | `sap_sac_user_activity` | SAP Cloud > Analytics Cloud > SAP Analytics Cloud - User Activity | sac_activities |
| SAP Ariba - Security Monitoring | `sap_ariba_security_monitoring` | SAP Cloud > Ariba > SAP Ariba - Security Monitoring | ariba_audit_log |
| SAP Cloud - Audit Logs | `sap_cloud_audit_logs` | SAP Cloud > BTP > SAP Cloud - Audit Logs | cp_audit_log |
| SAP Cloud - Estimated Billing | `sap_cloud_estimated_billing` | SAP Cloud > BTP > SAP Cloud - Estimated Billing | monthly_subaccounts_cost |
| SAP Cloud Foundry Syslog | `sap_cloud_btp_syslog` | SAP Cloud > BTP > SAP Cloud Foundry Syslog | syslog |
| CPI - S/4 HANA Correlation (STAD3) | `sap_cloud_cpi_s4h_stad3` | SAP Cloud > CPI > CPI - S/4 HANA Correlation (STAD3) | cpi_message, STAD3 |
| CPI - S/4 HANA Correlation (STATS) | `sap_cloud_cpi_s4h_stats` | SAP Cloud > CPI > CPI - S/4 HANA Correlation (STATS) | cpi_message, STATS |
| SAP Cloud - CPI Message Monitoring | `sap_cloud_cpi_message_monitoring` | SAP Cloud > CPI > SAP Cloud - CPI Message Monitoring | cpi_artifact, cpi_message |
| SAP Cloud - CPI Message Status Overview | `sap_cloud_cpi_msg_status` | SAP Cloud > CPI > SAP Cloud - CPI Message Status Overview | cpi_inventory, cpi_message |
| Overview | `sap_cpq_overview` | SAP Cloud > CPQ > Overview | cpq_audit_trail_user_action, cpq_event_log |
| SAP Data Intelligence Overview | `sap_dataintelligence_overview` | SAP Cloud > Data Intelligence > SAP Data Intelligence Overview | di_graphs, di_metric |
| SAP Datasphere - Overview | `pc_cloud_datasphere_overview` | SAP Cloud > Datasphere > SAP Datasphere - Overview | datasphere_admission_control, datasphere_oom, datasphere_space_memory, datasphere_task_log, ENQUEUE, REJECT |
| SAP Datasphere - Task Logs | `pc_cloud_datasphere_tasks` | SAP Cloud > Datasphere > SAP Datasphere - Task Logs | datasphere_task_log |
| SAP FieldGlass Overview | `sap_fieldglass_overview` | SAP Cloud > FieldGlass > SAP FieldGlass Overview | fg_audit_trail |
| SAP Cloud - IAS Security Monitoring | `sap_cloud_ias_audit` | SAP Cloud > IAS > SAP Cloud - IAS Security Monitoring | ias_audit_log |
| PowerConnect Cloud Agent Health | `powerconnect_cloud_agent_health` | SAP Cloud > PowerConnect Cloud Agent Health | agent_health |
| SAP S/4HANA Cloud Public Edition - Audit Logs | `sap_s4hcpe_audit_log` | SAP Cloud > S/4 HANA Cloud Public Edition > SAP S/4HANA Cloud Public Edition - Audit Logs | s4hana_cloud_audit_log, s4hana_cloud_user |
| SAP S/4HANA Cloud Public Edition - Security Overview | `sap_s4hcpe_security_ovvw` | SAP Cloud > S/4 HANA Cloud Public Edition > SAP S/4HANA Cloud Public Edition - Security Overview | s4hana_cloud_audit_log, s4hana_cloud_user, s4hana_cloud_user_change |
| SAP Cloud Connector | `pc_java_cloud_connector_overview` | SAP Cloud > SAP Cloud Connector | alert, certificate_status, cpu_status, disk_status, http_access_log, ljs_trace_log, master_role, memory_status, scc_backend_connection, subaccount, usage_backend |
| Change Audit | `sap_successfactors_change_audit_monitoring` | SAP Cloud > SuccessFactors > Change Audit | sf_change_audit_report |
| Onboarding Process Monitoring | `sap_successfactors_onboarding_process_monitoring` | SAP Cloud > SuccessFactors > Onboarding Process Monitoring | sf_onboarding_process |
| Payroll Monitoring | `sap_successfactors_payroll_monitoring` | SAP Cloud > SuccessFactors > Payroll Monitoring | sf_payroll_configuration, sf_payroll_run_results |
| Process Monitoring | `sap_successfactors_process_monitoring` | SAP Cloud > SuccessFactors > Process Monitoring | sf_employee_replication, sf_em_event |
| Security Monitoring | `sap_successfactors_security_monitoring` | SAP Cloud > SuccessFactors > Security Monitoring | ias_audit_log, sf_compound_api_audit_log, sf_odata_api_audit_log |
| Synthetics Monitoring | `sap_cloud_synthetics` | SAP Cloud > Synthetics Monitoring | http_ping |
| Fiori Statistics Details | `fiori_statistics_details` | SAP Fiori > Fiori Statistics Details | STATS |
| Fiori Statistics Overview | `fiori_stats` | SAP Fiori > Fiori Statistics Overview | STATS |
| SAP Fiori: Details | `sap_fiori_details` | SAP Fiori > SAP Fiori: Details | FLP_MONITOR |
| SAP Fiori: Gateway Error Log | `sap_fiori_gateway_error_log` | SAP Fiori > SAP Fiori: Gateway Error Log | GW_ERROR_BEP, GW_ERROR_FND |
| SAP Fiori: ODATA Metering Trace | `sap_fiori_odata_metering_trace` | SAP Fiori > SAP Fiori: ODATA Metering Trace | ODATA_TRACE |
| SAP Fiori: SAP Gateway and OData Statistics | `sap_fiori_sap_gateway_statistics` | SAP Fiori > SAP Fiori: SAP Gateway and OData Statistics | GW_TRACE_STATS, STAD |
| SAP Fiori: Summary | `sap_fiori_summary` | SAP Fiori > SAP Fiori: Summary | FLP_MONITOR |
| ABAP Messaging Channel Receiver Monitoring | `sap_smamc` | SAP Interfaces > ABAP Messaging Channel Receiver Monitoring | SMAMC |
| ADS Connection Check | `ads_dashboard` | SAP Interfaces > ADS Connection Check | ADS_CHECK |
| AIF Error Monitoring | `aif_error_monitoring` | SAP Interfaces > AIF Error Monitoring | AIF_ERROR |
| Background RFC(BgRFC) Monitor ‚Äì SBGRFCMON | `bgrfc_mon_dashboard` | SAP Interfaces > Background RFC(BgRFC) Monitor ‚Äì SBGRFCMON | BGRFC_MON |
| Background RFC(BgRFC) Performance Monitor ‚Äì SBGRFCPERFMON | `bgrfc_perfmon_dashboard` | SAP Interfaces > Background RFC(BgRFC) Performance Monitor ‚Äì SBGRFCPERFMON | BGRFC_PERFMON |
| Monitor for Processed XML Messages (SXMB_MONI) | `monitor_for_processed_xml_messages` | SAP Interfaces > Monitor for Processed XML Messages (SXMB_MONI) | SMQ2, SXMB_MONI |
| RFC Connection Status | `sap_global_rfc_connection_status` | SAP Interfaces > RFC Connection Status | PC_SCHEDULE, SM59 |
| SAP Connect | `sap_connect` | SAP Interfaces > SAP Connect | SCOT |
| SAP Directories | `sap_directories` | SAP Interfaces > SAP Directories | AL11 |
| Unified Connectivity Audit Log | `ucon_log` | SAP Interfaces > Unified Connectivity Audit Log | UCON_LOG |
| Web Service Message Monitor (SRT_MONI) | `srt_moni_dashboard` | SAP Interfaces > Web Service Message Monitor (SRT_MONI) | SMQ2, SRT_MONI |
| Web Services Error Log (SRT_LOG) | `srt_log_dashboard` | SAP Interfaces > Web Services Error Log (SRT_LOG) | SRT_LOG |
| Web Services Monitor | `sap_web_services` | SAP Interfaces > Web Services Monitor | SOA_PING |
| qRFC Monitor | `qrfc_monitor` | SAP Interfaces > qRFC Monitor | PC_SCHEDULE |
| tRFC Monitor (SM58) | `trfc_errors` | SAP Interfaces > tRFC Monitor (SM58) | SM58 |
| Application Servers Overview | `application_servers_overview` | SAP Performance > App Server Monitoring > Application Servers Overview | SM51_CBLCK, SM51_QUEUE, SM51_STATE |
| CPU vs. Work Processes | `sap_global_cpu_vs_wp` | SAP Performance > App Server Monitoring > CPU vs. Work Processes | CCMS, LOGS, SM37, SM51, ST03_TIME, ST06, SU01 |
| SAP Buffers | `sap_instance_buffers` | SAP Performance > App Server Monitoring > SAP Buffers | ST02_BFFR |
| SAP Instance Memory (ST02) | `sap_memory` | SAP Performance > App Server Monitoring > SAP Instance Memory (ST02) | ST02_MEM |
| SAP Logs Search | `sap_logs_search` | SAP Performance > App Server Monitoring > SAP Logs Search | LOGS |
| SM51 - RFC Communication Block | `sm51_rfc_communication_block` | SAP Performance > App Server Monitoring > SM51 - RFC Communication Block | SM51_CBLCK |
| SM51 - Request Queue Information | `sm51_request_queue_information` | SAP Performance > App Server Monitoring > SM51 - Request Queue Information | SM51_QUEUE |
| System Time Monitor | `system_time_monitor` | SAP Performance > App Server Monitoring > System Time Monitor | SYSTEM_TIME |
| Work Process Detailed Analysis | `work_process_detailed_analysis` | SAP Performance > App Server Monitoring > Work Process Detailed Analysis | LOGS, SM37, SM51, SU01 |
| Work Processes Overview | `sap_global_work_processes` | SAP Performance > App Server Monitoring > Work Processes Overview | SM51 |
| STATS End User Monitoring | `stats_end_user_monitoring` | SAP Performance > End User Monitoring > STATS End User Monitoring | STATS |
| User Experience (Geo) | `sap_global_user_experience` | SAP Performance > End User Monitoring > User Experience (Geo) | CCMS, SM04, SM51, ST02_MEM, ST03_TIME, ST06, STAD3 |
| CPU All Instances | `sap_global_cpu_all_instances` | SAP Performance > Operating System monitoring > CPU All Instances | ST06 |
| Capacity Management Information System | `capacity_management_information_system` | SAP Performance > Operating System monitoring > Capacity Management Information System | ST06, ST06_FSYS |
| Disk | `sap_hardware_disk` | SAP Performance > Operating System monitoring > Disk | ST06_SN_DISK |
| File System | `file_system` | SAP Performance > Operating System monitoring > File System | ST06_FSYS |
| SAP Network | `sap_networking` | SAP Performance > Operating System monitoring > SAP Network | ST06, STAD3 |
| SAP OS Memory (ST06) | `sap_instance_memory` | SAP Performance > Operating System monitoring > SAP OS Memory (ST06) | ST06 |
| Output Device Status | `output_device_status` | SAP Performance > Spool > Output Device Status | SPAD_STATUS |
| Spool Content | `spool_content` | SAP Performance > Spool > Spool Content | SP01_CONTENT |
| Spool Information | `spool_information` | SAP Performance > Spool > Spool Information | SP01, SPAD_STATUS |
| Spool Monitoring | `spool_monitoring` | SAP Performance > Spool > Spool Monitoring | SP01 |
| Parameter Changes (TU02) | `tu02_dashboard` | SAP Performance > System Configuration > Parameter Changes (TU02) | TU02 |
| SAP RZ10 Comparison | `sap_rz10` | SAP Performance > System Configuration > SAP RZ10 Comparison | RZ10 |
| SAP RZ10 Profile Parameters | `sap_rz10_profile_parameters` | SAP Performance > System Configuration > SAP RZ10 Profile Parameters | RZ10, RZ10_LOG |
| ICM Monitoring Dashboard | `icm_monitoring_dashboard` | SAP Performance > System Monitoring > ICM Monitoring Dashboard | LOGS, SMICM |
| Performance measurement of synthetic code (ABAPmeter) | `abap_meter_matric_dashboard` | SAP Performance > System Monitoring > Performance measurement of synthetic code (ABAPmeter) | ABAP_METER |
| SAP CCMS | `sap_global_sap_ccms` | SAP Performance > System Monitoring > SAP CCMS | CCMS |
| SAP Gateway Monitoring | `sap_gateway_monitoring` | SAP Performance > System Monitoring > SAP Gateway Monitoring | LOGS, SMGW |
| SAP ITS Memory Statistics | `sap_its_memory_statistics` | SAP Performance > System Monitoring > SAP ITS Memory Statistics | ITS_MEMORY |
| SM12 Locks | `sap_global_locks` | SAP Performance > System Monitoring > SM12 Locks | SM12, SM12_STATS |
| SM13 Updates | `sap_global_updates` | SAP Performance > System Monitoring > SM13 Updates | SM13, SM13_STATE |
| SM21 System Logs | `system_logs` | SAP Performance > System Monitoring > SM21 System Logs | SM21_LOG |
| SMLG Details | `smlg_dashboard` | SAP Performance > System Monitoring > SMLG Details | SMLG |
| ST22 Dump Details | `sap_st22_dump_details` | SAP Performance > System Monitoring > ST22 Dump Details | E070, LOGS, ST22 |
| ST22 Dump Overview | `sap_global_abap_dumps` | SAP Performance > System Monitoring > ST22 Dump Overview | ST22 |
| Time Machine Dashboard | `sap_global_time_machine_dashboard` | SAP Performance > Time Machine Dashboard | AL08, CCMS, SM04, SM21_LOG, SM37, SM51, ST03_TIME, ST06, ST22, STAD3 |
| SQL Code Analysis Details | `sql_code_analysis` | SAP Performance > Traces > SQL Code > SQL Code Analysis Details | SQLM |
| SQL Code Analysis Overview | `sql_code_analysis_overview` | SAP Performance > Traces > SQL Code > SQL Code Analysis Overview | SQLM |
| ST05 Performance Metrics | `st05_performance_metrics` | SAP Performance > Traces > ST05 Performance Metrics | ST05 |
| SWPR - Workflow After Restart | `swpr_workflow_after_restart` | SAP Performance > Workflow > SWPR - Workflow After Restart | SWPR |
| Workflow Event Queue | `workflow_event_queue` | SAP Performance > Workflow > Workflow Event Queue | SWEQUEUE |
| DIA steps (Total) | `dia_global_steps_clone` | SAP Performance > Workload Monitoring > DIA steps (Total) | ST03_TIME |
| SAP Global STAD | `sap_global_stad` | SAP Performance > Workload Monitoring > SAP Global STAD | STAD3 |
| SAP Global Transactions | `sap_global_transactions` | SAP Performance > Workload Monitoring > SAP Global Transactions | STAD3 |
| SAP Global Transactions (raw) | `sap_global_transactions_raw` | SAP Performance > Workload Monitoring > SAP Global Transactions (raw) | STAD |
| SAP Web Page Response time | `sap_web_page_response_time` | SAP Performance > Workload Monitoring > SAP Web Page Response time | STAD3 |
| HTTP Client Profile | `st03_http_client_profile` | SAP Performance > Workload Monitoring > ST03 - RFC and Web Services > HTTP Client Profile | ST03_WEBC |
| HTTP Server Profile | `st03_http_server_profile` | SAP Performance > Workload Monitoring > ST03 - RFC and Web Services > HTTP Server Profile | ST03_WEBS |
| RFC Client Profile | `st03_rfc_client_profile` | SAP Performance > Workload Monitoring > ST03 - RFC and Web Services > RFC Client Profile | ST03_RFCC |
| RFC Server Profile | `st03_rfc_server_profile` | SAP Performance > Workload Monitoring > ST03 - RFC and Web Services > RFC Server Profile | ST03_RFCS |
| ST03 - User Profile | `st03_user_profile` | SAP Performance > Workload Monitoring > ST03 - User Profile | ST03_USRT |
| STATS Details | `stats` | SAP Performance > Workload Monitoring > STATS Details | STATS |
| STATS Overview | `stats_overview` | SAP Performance > Workload Monitoring > STATS Overview | STATS |
| Audit Integrity Check | `audit_integrity_check` | SAP Security > Audits > Audit Integrity Check | RSAU_CHECK |
| SAP Read Access Login (SRAL) | `sral_dashboard` | SAP Security > Audits > SAP Read Access Login (SRAL) | SRAL |
| SM20 Audit Logs | `audit_logs` | SAP Security > Audits > SM20 Audit Logs | SM20, SU01 |
| Authorization Data Details (SU53) | `sap_authorization_data_su53` | SAP Security > Authorization > Authorization Data Details (SU53) | SU53 |
| Authorization Data Overview (SU53) | `authorization_failure_overview` | SAP Security > Authorization > Authorization Data Overview (SU53) | SU53 |
| Sensitive Authorization | `sensitive_authorization` | SAP Security > Authorization > Sensitive Authorization | ROLE_AUTH, SU01 |
| USR009 - Users With Critical Authorizations | `usr009_users_crit_auth` | SAP Security > Authorization > USR009 - Users With Critical Authorizations | RSUSR009 |
| SAP Security Essentials | `sap_security_essentials` | SAP Security > SAP Security Essentials | DEVACCESS, GROUP_LIST, LOGS, RSUSR003, RSUSR200, RZ10, SCC4, SE06, SM04, SM19, SM20, SM21_LOG, SNOTE, STAD, STMS, STRUST, SUIM, USER_AUTH |
| SAP Security Landscape (Concept) | `sap_security_landscape` | SAP Security > SAP Security Landscape (Concept) | DEVACCESS, RSUSR200, SCC4, SM04, SM19, SM20, SM21_LOG, SNOTE, STAD, STMS, SUIM, USER_AUTH |
| SAP Security Scorecard | `sap_global_security_usecases` | SAP Security > SAP Security Scorecard | GROUP_LIST, SM04, SM20 |
| SE37 Function Module Execution Log | `se37_log_dashboard` | SAP Security > SE37 Function Module Execution Log | SE37_LOG |
| ABAP Test Cockpit (ATC) : Results | `atc_dashboard` | SAP Security > System Security > ABAP Test Cockpit (ATC) : Results | ATC |
| Certificate Change History | `strust_certificate_changes` | SAP Security > System Security > Certificate Change History | STRUST_HISTORY |
| Certificate Status | `strust_certificates_validity` | SAP Security > System Security > Certificate Status | HDB_CERT_LIST, STRUST |
| Rule Processing Framework | `rpf_check` | SAP Security > System Security > Rule Processing Framework | RPF_CHECK |
| SAP License | `sap_license` | SAP Security > System Security > SAP License | SLICENSE |
| SAP Notes Implementation (SNOTE) | `snote_dashboard` | SAP Security > System Security > SAP Notes Implementation (SNOTE) | SNOTE |
| SAP Security Notes | `sap_security_note` | SAP Security > System Security > SAP Security Notes | RPF_CHECK |
| SAP Security Notes (Solution Manager) | `sap_security_notes_solman` | SAP Security > System Security > SAP Security Notes (Solution Manager) | SM_SAP_NOTES |
| SE16 Table Browser - Change Documents | `tablebrowser_changedocs` | SAP Security > System Security > SE16 Table Browser - Change Documents | S416N_CD, SE16N_CD |
| SICF Public Services & Services with Logon Data | `sicfchk_dashboard` | SAP Security > System Security > SICF Public Services & Services with Logon Data | SICFCHK |
| SM69 - External OS Commands Logs | `sm69_change_logs` | SAP Security > System Security > SM69 - External OS Commands Logs | SM69 |
| Secure-by-Default Logs | `sbdlog_mon` | SAP Security > System Security > Secure-by-Default Logs | SBDLOG |
| Security Policy Changes Dashboard | `security_policy_changes_dashboard` | SAP Security > System Security > Security Policy Changes Dashboard | SECPOL_LOG |
| System Changes Overview | `sap_system_changes` | SAP Security > System Security > System Changes Overview | E070, RSAU_CHECK, RZ10_LOG, SCC4, SM20, SM21_LOG, SM51_STATE, SM59_RFCDES, SPAD_STATUS, ST01_STATE, STMS, STRUST_HISTORY, SUIM, UCON_LOG |
| System Component Versions | `system_settings` | SAP Security > System Security > System Component Versions | SE06 |
| Audited Logins | `sap_global_audit_logins` | SAP Security > Users and Logins > Audited Logins | SM20 |
| Login Failure | `login_failure_drilldown` | SAP Security > Users and Logins > Login Failure | SM20, SU01 |
| Sensitive User Authorizations | `user_auth_dashboard` | SAP Security > Users and Logins > Sensitive User Authorizations | USER_AUTH |
| UME for ABAP | `ume_for_abap` | SAP Security > Users and Logins > UME for ABAP | SU01 |
| User Change Log | `user_change_log` | SAP Security > Users and Logins > User Change Log | SU01, SUIM |
| User Password Status | `sap_global_user_password_status` | SAP Security > Users and Logins > User Password Status | RSUSR200, SUIM |
| User Sessions by SAPGUI Version | `sap_global_client_version` | SAP Security > Users and Logins > User Sessions by SAPGUI Version | SM04 |
| Users by Instance | `users_by_instance` | SAP Security > Users and Logins > Users by Instance | GROUP_LIST, SM20 |
| Users logged in | `sap_global_users` | SAP Security > Users and Logins > Users logged in | AL08, RSUSR200 |
| Audits | `pc_abap_sec_audits` | Security > Audits | RSAU_CHECK, SE37_LOG, SM20, SRAL |
| Certificates & Licensing | `pc_abap_sec_certs_licensing` | Security > Certificates & Licensing | HDB_CERT_LIST, SLICENSE, STRUST, STRUST_HISTORY |
| Security Essentials | `pc_abap_sec_overview` | Security > Security Essentials | DEVACCESS, LOGS, RSUSR003, RSUSR200, RZ10, SCC4, SE06, SM04, SM19, SM20, SM21_LOG, SNOTE, STAD, STATS, STMS, STRUST, SUIM, USER_AUTH |
| Security Notes & Compliance | `pc_abap_sec_notes_compliance` | Security > Security Notes & Compliance | ATC, RPF_CHECK, SNOTE |
| System Configuration & Change Tracking | `pc_abap_sec_config_changes` | Security > System Configuration & Change Tracking | E070, RSAU_CHECK, RZ10_LOG, S416N_CD, SBDLOG, SCC4, SE06, SE16N_CD, SECPOL_LOG, SICFCHK, SM20, SM21_LOG, SM51_STATE, SM59_RFCDES, SM69, SPAD_STATUS, ST01_STATE, STMS, STRUST_HISTORY, SUIM, UCON_LOG |
| Users & Authorizations | `pc_abap_sec_users_auths` | Security > Users & Authorizations | AL08, ROLE_AUTH, RSUSR003, RSUSR009, RSUSR200, SM04, SM20, SU01, SU53, SUIM, USER_AUTH |
| System Overview | `pc_abap_overview` | System Overview | CCMS, ni_ping, SCC4, SM04, SM12, SM13, SM20, SM21_LOG, SM37, SM51, SM58, SMQ1, ST01_STATE, ST03_TIME, ST06, ST22, STAD3 |
| DB2 | `DB2` |  | DB6_DB02_DBPF, DB6_DB02_OVVW |
| SAP Global | `SAP_others` |  | AL11, RSUSR200, SCOT, SM04, SM12, SM13, SM59, ST03_TIME_TOT |
| SAP Systems | `sap_systems_without_tstats` |  | CCMS, SM51, ST03_TIME, ST06 |
| STAD | `STAD` |  | STAD3 |
| STAD | `sap_stad_global` |  | STAD3 |
