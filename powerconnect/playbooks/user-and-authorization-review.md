# User and authorization review — users, roles, passwords, critical access

**Use when:** "which users are dormant?", "who still has an initial or
default password?", "who is locked and why?", "who has SAP_ALL?", "which
roles carry S_TCODE for SU01?", "what changed on this user or role?", "show
SoD violations", "who can log on to HANA?".
**Not for:** what a user actually did (logons, downloads, debugging) →
[security-audit.md](security-audit.md); who is logged on now →
[user-activity-and-fiori.md](user-activity-and-fiori.md); transports and
configuration changes → [change-tracking.md](change-tracking.md); active
user counts for licensing → [certificates-and-licenses.md](certificates-and-licenses.md).

The core insight: **these are inventories, not event counts.** Most types
here re-send the whole user or authorization list on a schedule, so a raw
row count is "users × polls". Always reduce to the latest record per
system + client + user (or role) before counting. Two further traps:
`USER_AUTH` and `ROLE_AUTH` contain only what an administrator listed as
sensitive in the metric filter, so "nobody has X" is true only if X is in
that filter; and some feeds also emit KPI records with subtype `_METRICS_`
that have no user fields and must be excluded.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `RSUSR200` | ABAP | snapshot | per user: last logon, password state, lock reason, validity | yes |
| `RSUSR003` | ABAP | snapshot | standard users (SAP*, DDIC, ...) with default or well-known passwords, all clients | yes |
| `SU01` | ABAP | snapshot (first run of the day) + deltas; subtypes empty, `ROLE`, `PROF`, `ADDR` | user master, assigned roles and profiles | yes |
| `USER_AUTH` | ABAP | snapshot; subtypes `ROLE`, `PROFILE`, `AUTH`, `TCODE` | users holding sensitive roles, profiles, authorizations, transactions (single client) | yes, filter-driven |
| `ROLE_AUTH` | ABAP | snapshot | authorization values inside roles (AGR_1251) | yes, empty until its filter is set |
| `SUIM` | ABAP | event stream; subtypes `USER`, `ADMR`, `ROLE`, `PROF`, `AUTH` | change documents for users, role assignments, roles, profiles | yes |
| `USH02` | ABAP | event stream | change history of logon data (locks, password resets, type) | yes |
| `SECPOL_LOG` | ABAP | event stream | security policy changes (NetWeaver 7.40+) | yes |
| `GRC_REQUESTS`, `GRC_SODREP` | ABAP (GRC) | header + detail / report | access requests; SoD violation report | no |
| `HDB_DBCC_USERS`, `HDB_DBCC_USRPRV` | ABAP (HANA) | snapshot; USRPRV subtypes `ROLES`, `SQL_PRIVILEGES`, `SYS_PRIVILEGES` | HANA database users and privileges | USERS yes, USRPRV no |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `BNAME`, `MANDT` (RSUSR200) | user, client: the entity key with SID | | sample (Dynatrace) |
| `TRDAT`, `LTIME` | last logon date and time | `00000000` = never logged on | sample (Dynatrace) |
| `USTYP` | user type | `A` dialog, `B` system, `C` communication, `S` service, `L` reference (codes: SAP) | sample (Dynatrace) |
| `LOCK_REASON`, `LOCK_STATE`, `LOCNT` | lock reason as text, state, failed-logon counter | reason is free text, e.g. failed logon, local lock by admin | sample (Dynatrace) |
| `PWD_STATE`, `BCDA1` | password status, last password change date | read the values present before filtering | sample (Dynatrace) |
| `GLTGV`, `GLTGB`, `ERDAT`, `ANAME`, `CLASS` | valid from / to, created on, created by, user group | `00000000` = no limit | sample (Dynatrace) |
| `USER_NAME`, `MANDT`, `PROF_NAME`, `AUTH_OBJCT`, `AUTH_FIELD`, `AUTH_LOW`, `AUTH_HIGH` (USER_AUTH) | user and the sensitive item matched | seen on subtypes `AUTH` and `TCODE`; other subtypes: sample | sample (Dynatrace) |
| `UFLAG`, `USTYP`, `TRDAT`, `CHANGE_USER`, `CHANGE_DATE` (USER_AUTH) | lock flag, type, last logon, last changer | `UFLAG` `0` unlocked, `64` admin lock, `128` failed-logon lock (SAP) | sample (Dynatrace) |
| `AGR_NAME`, `OBJECT`, `AUTH`, `FIELD`, `LOW`, `HIGH`, `DELETED` (ROLE_AUTH) | role, authorization object, field and value range | `DELETED` = `X` means the value is inactive in the role | sample (Dynatrace) |
| `NAME`, `VALUE`, `UNIT`, `DIMENSIONS`, `DESCRIPTION` (subtype `_METRICS_`) | pre-computed KPI record | seen on `RSUSR003` | sample (Dynatrace) |
| `USERNAME`, `MANDT`, `PWSTATUS`, `LOCKED`, `LOCKREASON`, `UNSUCESSLOGINS`, `VALIDFRM`, `VALIDTO` (RSUSR003) | standard user, client, password status as text, lock flag and reason, failed logons, validity | `PWSTATUS` is free text; read the values present. `UNSUCESSLOGINS` is spelled this way | sample (Dynatrace) |
| `USERNAME`, `UDATE`, `UTIME`, `TCODE`, `OBJECTID`, `TABNAME`, `TABDESCR`, `CHANGENR`, `MANDT` (SUIM `ADMR`) | who changed which role, when (system-local), with which transaction | `OBJECTID` = role | sample (Dynatrace) |
| `PROFILE`, `ACTION`, `MODIFIER`, `MODDATE`, `MODTIME`, `OBJECT`, `AUTH`, `PTEXT` (SUIM `PROF`) | profile, what happened as text, who and when | | sample (Dynatrace) |
| SUIM `USER` / `ROLE` / `AUTH`, SU01, USH02, SECPOL_LOG, GRC_*, HDB_* fields | | no record seen; sample first | unconfirmed |

## Investigation sequence

1. **Confirm the feeds and their subtypes.** This also shows whether
   `_METRICS_` records exist and whether SU01 or RSUSR003 detail is there.
   Use a lookback of at least 24 h: SU01 sends its full list once a day.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE IN (RSUSR200,RSUSR003,SU01,USER_AUTH,ROLE_AUTH,SUIM,USH02)
| stats count max(_time) as newest by source EVENT_TYPE EVENT_SUBTYPE
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and in(dt.source_entity_name, {"RSUSR200", "RSUSR003", "SU01", "USER_AUTH", "ROLE_AUTH", "SUIM", "USH02"})
| summarize {events = count(), newest = max(timestamp)}, by: {log.source, dt.source_entity_name, dt.source_entity_type}
```

2. **Sample one record** of each type you will filter on.
3. **Dormant, never-used and locked users** from `RSUSR200`, latest record
   per user. `<CUTOFF>` is a date as `yyyymmdd` (90 days before `T_END` is
   a starting point). Swap the last line to group by `PWD_STATE` for
   initial or expired passwords, or by `LOCK_REASON` for locks.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=RSUSR200 BNAME=*
| stats latest(TRDAT) as TRDAT latest(USTYP) as USTYP latest(LOCK_REASON) as LOCK_REASON latest(PWD_STATE) as PWD_STATE by source MANDT BNAME
| where USTYP="A" AND tonumber(TRDAT) < <CUTOFF>
| stats count as users by source MANDT LOCK_REASON
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "RSUSR200" and isNotNull(bname)
| sort timestamp asc
| summarize {trdat = takeLast(trdat), ustyp = takeLast(ustyp), lock_reason = takeLast(lock_reason), pwd_state = takeLast(pwd_state)}, by: {log.source, mandt, bname}
| filter ustyp == "A" and toLong(trdat) < <CUTOFF>
| summarize users = count(), by: {log.source, mandt, lock_reason}
```

   A dormant user that is already locked is housekeeping; a dormant,
   unlocked dialog user with a valid date range is the finding. For
   default passwords sample `RSUSR003`, exclude `_METRICS_`, and report
   standard users per client that are unlocked with an unchanged password.

4. **Critical access** from `USER_AUTH`, latest per user and item. Check
   first that the profile or role you ask about is in the metric filter
   (it appears in the data for at least one user, or the administrator
   confirms it).

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=USER_AUTH PROF_NAME IN ("SAP_ALL","SAP_NEW")
| stats latest(UFLAG) as UFLAG latest(USTYP) as USTYP latest(TRDAT) as TRDAT by source MANDT USER_NAME PROF_NAME
| sort source MANDT USER_NAME
```
```dql
fetch logs, from: <START>, to: <END>
| filter service.name == "sap:abap" and dt.source_entity_name == "USER_AUTH"
| filter in(prof_name, {"SAP_ALL", "SAP_NEW"})
| sort timestamp asc
| summarize {uflag = takeLast(uflag), ustyp = takeLast(ustyp), trdat = takeLast(trdat)}, by: {log.source, mandt, user_name, prof_name}
```

   For "which roles grant transaction X", query `ROLE_AUTH` with
   `OBJECT=S_TCODE`, `DELETED` not `X`, and `LOW`/`HIGH` covering X or `*`.
5. **Changes.** For "what changed on user or role Y", count `SUIM` by
   `EVENT_SUBTYPE` in the window, sample one record of the subtype, then
   list the changes for Y. `USH02` adds lock, unlock and password resets.
6. **Correlate** on user + client (system-local times): a `SUIM` grant,
   then `SM20` / `STAD` activity, then removal is the pattern auditors want.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Counts far above the real user base | raw rows counted | reduce to latest per SID + client + user |
| No user holds a critical profile | profile not in the `USER_AUTH` filter, or really none | verify the filter (`/BNWVS/MAIN` → Metric Filters → User Authorizations) |
| `ROLE_AUTH` empty | filter not configured (it is required) | coverage gap; name the filter "Role authorizations" |
| Only one client in `USER_AUTH` | extractor is single-client | say which client is covered |
| SU01 has deltas but no full list in the window | snapshot is sent at the first run of the day | widen to 24–48 h |
| Standard user with default password, unlocked | real exposure | report first, with client |
| SUIM stopped and ST22 shows ITAB_ILLEGAL_SORT_ORDER | KB 203 (CUA systems, 7.03–8.01) | point to the KB workaround |

## What to tell the user

- Counts per system and client, the lookback used, and that figures are
  latest-per-user. List individual users only when asked or when the list
  is the finding (critical profiles, default passwords); otherwise give
  counts and offer the list.
- Where a human verifies: RSUSR200, RSUSR003, SU01, SUIM (change
  documents), SE16 on AGR_1251, DBACOCKPIT for HANA users.
- The action and owner (security administration): lock or delimit
  dormant users, reset default passwords, remove broad profiles.
- What you could not see: clients not extracted, items missing from the
  sensitive lists, GRC and HANA privilege feeds (off by default).

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| Standard user with initial or well-known password | `RSUSR003` | shipped in Splunk ES as "Initial or WellKnown PW" |
| Admin profile or sensitive role assigned | `SUIM` | shipped: "Admin Profile Assigned", "Sensitive Role Assigned" |
| User unlocked, type changed, new user created | `SUIM` | shipped ES searches of the same names |
| Dialog user past password expiry; password reset on non-dialog user | `RSUSR200` | shipped ES searches |
| New SoD violation | `GRC_SODREP` | needs the GRC extractor enabled |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `su01`, `rsusr003`, `rsusr200`, `ush02`, `suim`, `role_auth`,
  `user_auth-user-authorizations`,
  `secpol_log-change-logs-for-security-policies`
- `grc_requests-access-requests-in-sap-grc`,
  `grc_sodrep-grc-sod-violations-report-data`
- `hdb_dbcc_users-hana-db-user-list`, `hdb_dbcc_usrprv`
- KB 162 (collector role gaps) — `kb-162-authorization-objects-related-issues`;
  KB 203 — `kb-203-itab_illegal_sort_order-abap-dumps-suim`;
  `list-of-correlation-searches`

Slugs resolve as `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
