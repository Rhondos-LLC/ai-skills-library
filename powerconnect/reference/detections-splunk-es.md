# Splunk Enterprise Security content pack — correlation searches

Generated from the product documentation ("List of Correlation Searches"). Each row is a shipped detection, the CIM data model it uses and the PowerConnect event type it reads.

| CorrelationSearch | DataModel | EventType | Description |
|---|---|---|---|
| Initial or WellKnown PW | Alerts | RSUSR003 | Detects when an account password is too common or has not yet been reset from its initial state. |
| Dialog User PW Expiration Violation | N/A | RSUSR200 | Detects when an SAP Dialog user is violating the password expiration policy. |
| PW Reset NonDialog | N/A | RSUSR200 | Detects password reset on a non-dialog user in SAP. |
| Static Profile Parameter Change | Change | RZ10_LOG | Detects changes to static profile parameters in SAP systems. |
| Client Open for Change | N/A | SCC4 | Detects when an SAP client has been opened for a change. |
| New Client Created | N/A | SCC4 | Detects a new client in SAP. |
| Namespace Open for Change | N/A | SE06 | Detects when an SAP namespace is open for change. |
| Manual Function Module Execution | Data_Access | SE37_LOG | Indicates function modules that have been executed manually by users in an SAP system. |
| Many Accounts One Terminal | Network_Sessions | SM04 | Detects multiples accounts logging in from a single terminal. |
| One Account Many Geos | N/A | SM04 | Detects one account logging in from multiple geographies. |
| One Account Many Terminals | Network_Sessions | SM04 | Detects one account logging in from multiple terminals. |
| Account High Transaction Failure | Authentication | SM20 | Detects a high number of transaction failures in the set timeframe. |
| Account Multiple Login Failures | Authentication | SM20 | Detects multiple login failures from a user account on an SAP system. |
| Audit Log Deletion | Authentication | SM20 | Detects an audit log deletion. |
| File Downloads | Authentication | SM20 | Detects data downloads from SAP systems, indicating potential data theft. |
| Logical Path Access Failure | Authentication | SM20 | Detects logical path access failure in an SAP system. |
| Privileged Account Login | Authentication | SM20 | Detects login events for privileged SAP accounts SAP\* and DDIC. |
| SM59 Destination Deletion | Alerts | SM21_LOG | Detects deletion of SM59 destinations in SAP systems. |
| Dynamic Profile Parameter Change | Alerts | SM21_LOG | Detects changes in dynamic profile parameters. |
| IDOC Removal | Alerts | SM21_LOG | Detects removal of IDocs in SAP systems. |
| SM59 Destination Change | Alerts | SM21_LOG | Detects deletion of RFC destinations in SAP systems. |
| Debug Mode Execution | Alerts | SM21_LOG | Detects execution of debug mode on SAP systems. |
| OS Command Change | Change | SM69 | Detects execution of an OS command. |
| Sensitive Transaction Execution | N/A | STAD | Detects execution of a set of predefined sensitive transactions. Uses the PowerConnect app's "sensitive_tcodes" lookup to define sensitive transactions. |
| Transport Added to Import Queue | Change | STMS_TPLOG | Detects when a user adds a transport to the import queue on an SAP system. |
| Transport Removed from Import Queue | Change | STMS_TPLOG | Detects when a user removes a transport to the import queue on an SAP system. |
| Certificate Expired | Certificates | STRUST | Detects expired SSL certificates. |
| Certificate Changes | Change | STRUST_HISTORY | Detects changes in SSL certificates. |
| Profile Change | Change | SUIM | Detects profile change in SAP systems. |
| User Change | Change | SUIM | Detects user changes in SAP. Does not conflict with correlation searches for admin profile assignments. |
| Admin Profile Assigned | Change | SUIM | Detects assignment of admin profile in SAP. |
| New User Created | Change | SUIM | Detects creation of a new user in SAP. |
| Sensitive Role Assigned | N/A | SUIM | Detects assignment of a sensitive user role in SAP. Uses the PowerConnect app's "sensitive_user_roles" lookup to define sensitive roles. |
| User Type Changed | Change | SUIM | Detects change in user type in SAP. |
| User Unlocked | Change | SUIM | Detects user unlocks in SAP. |
| Connectivity Object Change | Change | UCON_LOG | Detects connectivity object changes in SAP. |
| User with multiple composite roles | Authentication | SU01 | Scans user security config to determine when a user has been assigned multiple composite roles. |
| Potential Duplicate Users | Authentication | SU01 | Scans user security configuration data to detect accounts with identical first and last names. |
