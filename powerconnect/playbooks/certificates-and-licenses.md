# Certificates and licenses — expiry, changes, licence counts

**Use when:** "which certificates expire in the next 30 days?", "who
changed a certificate in STRUST?", "when does the SAP licence run out?",
"is the PowerConnect licence valid?", "how many active users count for
PowerConnect licensing?".
**Not for:** a connection that already fails → [rfc-and-queues.md](rfc-and-queues.md)
or [integration-messages.md](integration-messages.md); data stopped
arriving → [feed-health.md](feed-health.md); other configuration changes →
[change-tracking.md](change-tracking.md); BTP services in general →
[cloud-services.md](cloud-services.md).

The core insight: **certificate lists are snapshots, and "days to expiry"
is not a raw field.** Every poll re-sends every certificate, so count the
latest record per certificate, never rows. The ready-made expiry fields
(`cert_days_to_expiry`, `btp_cert_days_to_expiry`, `time_to_expire`,
`expired`) are computed by the Dynatrace pipeline; elsewhere you calculate
expiry from the valid-to field. An expired entry is not automatically an
incident: trust lists keep old root certificates for years. What matters
is which PSE or keystore holds it and whether that store is in use.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `STRUST` | ABAP | snapshot | certificates in every PSE, per instance | yes |
| `STRUST_HISTORY` | ABAP | event stream | certificate added / removed, by whom, when | yes (KB 192 if empty on 7.4–8.0) |
| `HDB_CERT_LIST` | ABAP (HANA) | snapshot | certificates installed in HANA and their status | yes |
| `certificate` | Java | snapshot | NetWeaver Java keystore entries (TrustedCAs by default; other keystores need `keystore-view.<name>` permission) | when ticked in the Java agent console |
| `btp_certificate` | Cloud | snapshot, polled hourly by default | BTP Destination service certificates (input `certificates-cf`) | when the input exists |
| `http_ping` | Cloud | snapshot | endpoint availability and certificate status of monitored URLs | when the input exists |
| `SLICENSE` | ABAP | snapshot; subtype `LICENSES` seen | SAP licence keys per product with validity | yes |
| `RSUSR200` | ABAP | snapshot | users by type and validity, for the active user count | yes |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `FINGERPR`, `SNUMBER` (STRUST) | fingerprint, serial: certificate identity | | sample (Dynatrace) |
| `SUBJECT`, `ISSUER`, `SUMMARY` | subject, issuer, combined text | | sample (Dynatrace) |
| `APPLIC`, `CONTEXT`, `DESCRIPT`, `CLIENT`, `INSTANCE_NAME` | which PSE holds it (for example SSL client, SSL server, SSO2), where | | sample (Dynatrace) |
| `VALID_FROM`, `VALID_TO` | validity, `yyyymmddhhmmss`, system-local | payload `STATUS` is shadowed by the log record's `status` in Dynatrace; do not filter on it | sample (Dynatrace) |
| `expired`, `time_to_expire`, `cert_exp_ts`, `current_ts` (STRUST) | expiry flag (string `1`); remaining time; `VALID_TO` and `CURRENT_TIMESTAMP` as timestamps | Dynatrace-derived. `time_to_expire` is a duration in nanoseconds = `cert_exp_ts` − `current_ts`, negative once expired; days = `time_to_expire / 24h`. Both timestamps are the local strings read as UTC, so the difference is right but neither is true UTC | sample (Dynatrace) |
| `cert_days_to_expiry` (`certificate`) | days left | Dynatrace-derived; shipped alerts: `< 0` expired, `0–30` expiring | docs |
| `btp_cert_days_to_expiry`, `btp_cert_expired` (`btp_certificate`) | days left; flag `1` | shipped alerts: `0–30` expiring, flag `1` expired | docs |
| `SW_PRODUCT`, `END_DATE`, `BEGIN_DATE`, `ACTIVE`, `VALIDITY`, `INSTALL_NO`, `SYSTEM_NO`, `HWKEY` (SLICENSE) | product, validity `yyyymmdd`, active flag, installation, system number, hardware key | `END_DATE` `99991231` = permanent; `ACTIVE` `X` or empty; sent only every few hours, so look back at least 6 h; do not repeat the numbers and key unless asked | sample (Dynatrace) |
| `BNAME`, `MANDT`, `USTYP`, `GLTGV`, `GLTGB` (RSUSR200) | user, client, type, valid from / to | `USTYP` `A` = dialog; `00000000` = no limit | sample (Dynatrace) |
| `http_ping_failed`, `name`, `url`, `response_time`, `certificates` (`http_ping`) | failure flag (string `1` / `0`), check name, URL, milliseconds, certificate object (`dn`, `issuer`, `not_after` as an HTTP date string) | `http_ping_failed` is Dynatrace-derived; payload `status` is the HTTP code | sample (Dynatrace) |
| STRUST_HISTORY, HDB_CERT_LIST, raw `certificate` / `btp_certificate` fields | | no record seen; sample one record first | unconfirmed |

## Investigation sequence

1. **Confirm the feeds**: count and newest record per type in the table
   above. A missing store is a coverage gap, not "nothing expiring".
2. **Sample one record** of each type and note the valid-to format.
3. **ABAP certificates expiring**, latest per certificate and PSE.
   `<CUTOFF>` = `T_END` + 30 days as `yyyymmdd` (the shipped alerts use 30).

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=STRUST FINGERPR=*
| stats latest(VALID_TO) as VALID_TO latest(SUBJECT) as SUBJECT latest(DESCRIPT) as PSE by source INSTANCE_NAME APPLIC CONTEXT FINGERPR
| where tonumber(substr(VALID_TO,1,8)) <= <CUTOFF>
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "STRUST" and isNotNull(fingerpr)
| sort timestamp asc
| summarize {valid_to = takeLast(valid_to), subject = takeLast(subject), pse = takeLast(descript)}, by: {log.source, instance_name, applic, context, fingerpr}
| filter toLong(substring(valid_to, from: 0, to: 8)) <= <CUTOFF>
```

   Rows dated before `T_END` are already expired. For a day count parse
   `VALID_TO` and `CURRENT_TIMESTAMP` (both system-local) and subtract;
   on Dynatrace take `takeLast(time_to_expire) / 24h` instead.
4. **Other stores**, same latest-per-certificate pattern:

| Store | Event type | Dynatrace | Other backends |
|---|---|---|---|
| Java keystores | `certificate` (`service.name` `sap:java`) | `cert_days_to_expiry <= 30` | valid-to field from a sample minus extraction time |
| BTP destinations | `btp_certificate` (`sap:cloud`) | `btp_cert_days_to_expiry <= 30` or `btp_cert_expired == "1"` | expiry date from a sample |
| HANA; external endpoints | `HDB_CERT_LIST`; `http_ping` | sample, then cutoff comparison | same |

5. **SAP licence expiry**, latest per product:

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=SLICENSE EVENT_SUBTYPE=LICENSES
| stats latest(END_DATE) as END_DATE latest(ACTIVE) as ACTIVE by source SW_PRODUCT
| where ACTIVE="X" AND tonumber(END_DATE) <= <CUTOFF>
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "SLICENSE" and dt.source_entity_type == "LICENSES"
| sort timestamp asc
| summarize {end_date = takeLast(end_date), active = takeLast(active)}, by: {log.source, sw_product}
| filter active == "X" and toLong(end_date) <= <CUTOFF>
```

   No rows with a live feed means no active licence ends before the cutoff.

6. **Who changed a certificate.** Count `STRUST_HISTORY` in the window,
   sample it, then list user, PSE and time; pair removals with `SM59`.
7. **Active users for PowerConnect licensing** (KB 152: dialog users
   valid today; `<TODAY>` as `yyyymmdd`):

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=RSUSR200 BNAME=*
| stats latest(USTYP) as USTYP latest(GLTGV) as VFROM latest(GLTGB) as VTO by source MANDT BNAME
| where USTYP="A" AND tonumber(VFROM) <= <TODAY> AND (tonumber(VTO)=0 OR tonumber(VTO) >= <TODAY>)
| stats count as active_dialog_users by source MANDT
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "RSUSR200" and isNotNull(bname)
| sort timestamp asc
| summarize {ustyp = takeLast(ustyp), vfrom = takeLast(gltgv), vto = takeLast(gltgb)}, by: {log.source, mandt, bname}
| filter ustyp == "A" and toLong(vfrom) <= <TODAY> and (toLong(vto) == 0 or toLong(vto) >= <TODAY>)
| summarize active_dialog_users = count(), by: {log.source, mandt}
```

   Present it as an estimate. The figure that counts is KB 152's: RSUSR200
   in the productive client, "Users Valid Today" and "Dialog Users".

8. **PowerConnect's own licence.** No event type is confirmed to carry
   its validity; sample `PC_HEALTH`. Otherwise a human checks `/BNWVS/MAIN`
   → Administrator → License management (ABAP) or the License page (Java).
   Cloud is licensed per plugin per production tenant (KB 215).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Many expired entries in one PSE | old root or intermediate CAs left in a trust list | report separately from server and client certificates |
| SSL client / server certificate inside the cutoff | renewal needed; connections will fail at expiry | name PSE, instance, date; Basis renews in STRUST |
| The certificate of the PowerConnect target expires | the collector's own HTTPS connection will stop | KB 151 procedure; warn that data flow depends on it |
| `STRUST_HISTORY` empty, SAP 7.40+, agent 7.4–8.0 | KB 192 task-group setting | set SAP Version to `*` |
| Splunk CIM certificate fields missing | KB 239 (see KB 164 for mapping issues) | query the raw event type instead |
| Licence red in License management after SP 8.05, reason "Crypto module" | KB 232 program error | support ticket |

## What to tell the user

- A list ordered by expiry: store or PSE, subject, system, valid-to date,
  trust anchor or own certificate; the cutoff and how days were derived.
- Where a human verifies: STRUST (PSE → History for changes), SLICENSE,
  NWA Key Storage, BTP cockpit destinations, HANA certificate store.
- Owner: Basis or security renews. What you could not see: keystores
  without view permission, stores not collected, the PowerConnect licence.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Certificate expires within 30 days / has expired | `certificate`, `btp_certificate` | shipped Dynatrace alerts (`davis.sap.java.certificate.*`, `davis.sap.cloud.btp_certificate.*`) |
| ABAP certificate expired | `STRUST` | shipped Splunk ES search "Certificate Expired"; on Dynatrace use `expired == "1"` (confirmed by sample) |
| Certificate added or removed | `STRUST_HISTORY` | shipped Splunk ES search "Certificate Changes" |
| Active SAP licence ends within 30 days | `SLICENSE` | exclude `99991231` |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `certificates`, `destination-certificates`, `slicense`, `rsusr200`,
  `strust_history-certificate-change-history`,
  `hdb_cert_list-hana-db-certificate-list`
- `kb-151-update-ssl-certificates`,
  `kb-192-strust_history-events-are-not-collected`,
  `kb-238-splunk-fields-missing-in-certificates-cim-m` (titled KB 239)
- `kb-152-determine-active-user-count-for-powerconnec`,
  `kb-112-license-key-generation`, `kb-124-update-powerconnect-license-key`,
  `kb-215-powerconnect-cloud-licensing`,
  `kb-232-license-validation-error-in-sp-8-05`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
