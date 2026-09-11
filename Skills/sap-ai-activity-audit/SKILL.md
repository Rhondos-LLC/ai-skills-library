---
name: sap-ai-activity-audit
description: >
  Audit what an AI triage account actually did in Splunk — every search it
  ran, what it touched, how much data it pulled — from Splunk's _audit
  index. Use this skill when the security team asks "what has the AI been
  doing?", for a scheduled AI-activity review, after any suspected misuse or
  prompt-injection incident, to close the loop on a hardening check, or to
  produce evidence for auditors that AI access is monitored. MUST be run
  from a privileged security/admin session — never from the AI account
  itself (it cannot and must not read its own audit trail).
metadata:
  version: "1.0.0"
  line: base
---

# SAP AI Activity Audit

The watcher's watcher, pointed at the agent. The core insight: **an AI
account is a service account with an unusually articulate operator — audit
it like one.** Everything it does lands in `_audit` like any user's
searches; the review is a census (what/where/how much/when), a policy diff
(anything outside the allowlisted indexes and read-only command set?), and
a trend (is today's behavior shaped like last week's?). Separation of duty
is absolute: this skill runs from the security team's session, and one of
its checks is that the AI account itself cannot do what this session is
doing.

## Rules

1. **Vantage first.** Confirm this session is not the AI account and can
   read `_audit`; if either fails, stop and say which.
2. **Search strings are sensitive.** `_audit` records the full SPL the
   agent ran, which can embed data values (document numbers, user names).
   Aggregate first; quote individual search strings only when a finding
   needs them, trimmed with `substr()`.
3. **`_audit` field availability varies by Splunk version** (`event_count`
   vs `result_count`, action naming for logons). When a field returns
   nothing, pull ONE event with `| head 1 | fields *` and adapt — never
   conclude "no activity" from a possibly wrong field name.
4. **Splunk MCP hygiene:** one query at a time; always set both
   `earliest_time` and `latest_time` tool parameters; keep results small.
5. **Purpose limitation.** This audits the *AI account's* behavior — do not
   widen it into general user surveillance; that is a different, governed
   activity.

`$AI$` below = the AI account name(s) from customer-profile.md (Tier 1 and
Tier 2 separately). Default window: last 7 days.

## Audit sequence

**Check 0 — Vantage.**

```spl
| rest splunk_server=local /services/authentication/current-context
| fields username, roles
```

Then confirm `_audit` visibility with the Check 1 query — zero rows for a
known-active account means this session lacks `_audit` access: stop.

**Check 1 — Activity census.** Volume, cadence, and result mass:

```spl
search index=_audit action=search info=completed user=$AI$ earliest=-7d
| eval events_ret=coalesce(tonumber(event_count), tonumber(result_count))
| bin _time span=1d
| stats count as searches, sum(events_ret) as events_returned, avg(eval(tonumber(total_run_time))) as avg_runtime_s by _time, user
```

```spl
search index=_audit action=search info=completed user=$AI$ earliest=-7d
| timechart span=1h count as searches
```

Read: a triage account's shape is bursty-but-bounded (investigations) or
metronomic (scheduled health checks). New nightly activity, a 10× volume
day, or `events_returned` jumping orders of magnitude = review the searches
from that window (Check 3).

**Check 2 — What it touched.** Indexes referenced in its searches:

```spl
search index=_audit action=search info=granted user=$AI$ earliest=-7d
| rex max_match=5 field=search "index\s*(=|::)\s*\"?(?<idx>[A-Za-z0-9_\*-]+)"
| stats count by idx
| sort -count
```

Every `idx` outside the profile allowlist (or `*`) is a finding — cross-check
against the hardening report: if the role fence is right, an out-of-scope
reference returned nothing, but the *attempt* still matters (skill drift or
injection steering). `sourcetype` references can be extracted the same way
when a finding needs them.

**Check 3 — Command policy diff.** Read-only means read-only:

```spl
search index=_audit action=search user=$AI$ earliest=-7d (search="*| delete*" OR search="*| collect*" OR search="*outputlookup*" OR search="*sendemail*" OR search="*| script*" OR search="*mcollect*" OR search="*| rest*")
| eval search_trim=substr(search,1,200)
| table _time, info, search_trim
```

Any row is a finding: `| rest` reads may be legitimate for the hardening
skill (profile-listed) — everything else on a triage account is either
misconfiguration, a broken skill, or steering; correlate the timestamp with
what the session was investigating. Note: this matches substrings — clear
false positives (e.g. `_internal` mentions in a comment) by reading the
trimmed string, and say so.

**Check 4 — Authentication trail.** Token/logon behavior for the account:

```spl
search index=_audit user=$AI$ earliest=-7d action IN ("login attempt", "login_attempt")
| stats count, values(info) as outcomes, min(_time) as first, max(_time) as last by action, src
| convert ctime(first) ctime(last)
```

Failed attempts against the AI account, or successes from an unexpected
source, are security events (hand to `sap-lockout-and-audit-triage`
thinking, applied to Splunk itself). Naming varies by version — rule 3
applies. Where the MCP server app logs its own component telemetry, review
it per the Splunk MCP documentation from this same privileged session;
don't assert paths the docs don't.

**Check 5 — Separation proof.** From this session, confirm the AI account's
role still matches the blueprint (the hardening skill's admin handoff):

```spl
| rest /services/authorization/roles splunk_server=local
| search title=<ai role>
| fields title, capabilities, imported_capabilities, srchIndexesAllowed, srchFilter
```

Diff against `role-blueprint.md`; any capability drift since the last
hardening report is the headline finding.

## The report

```markdown
# AI activity audit — <account(s)> — <period>

| # | Check | Verdict | Headline |
|---|---|---|---|
| 1 | Volume/cadence | ✅ | 214 searches, all business hours, shapes match skills |
| 2 | Index scope | ✅ | sap_prod only |
| 3 | Command policy | 🔴 | 1 outputlookup attempt on <date> — trace below |
| 4 | AuthN trail | ✅ | token use only, expected sources |
| 5 | Role drift | ✅ | matches blueprint of <date> |

## Findings
per non-green: the evidence (trimmed search strings, timestamps), the
correlated investigation context, and the routing (Basis/MCP admin/SOC).

## Trend vs previous period
searches/day, events returned, new behaviors
```

File it with the hardening report — the pair answers "what could it do"
and "what did it do".

## Alerts (continuous coverage between reviews)

Cron 15 min, results > 0, owned by the security team's app context (not
the AI account):

**sap_ai_out_of_scope_search**

```spl
index=_audit action=search info=granted user=$AI$ earliest=-30m
| rex max_match=5 field=search "index\s*(=|::)\s*\"?(?<idx>[A-Za-z0-9_\*-]+)"
| where isnotnull(idx) AND NOT idx IN (<allowlisted indexes>)
| eval search_trim=substr(search,1,200)
| table _time, idx, search_trim
```

**sap_ai_writeish_command**

```spl
index=_audit action=search user=$AI$ earliest=-30m (search="*| delete*" OR search="*| collect*" OR search="*outputlookup*" OR search="*sendemail*" OR search="*mcollect*")
| eval search_trim=substr(search,1,200)
| table _time, info, search_trim
```

**sap_ai_volume_anomaly**

```spl
index=_audit action=search info=completed user=$AI$ earliest=-7d
| eval bucket=if(_time>=relative_time(now(),"-1h"),"now","base")
| stats count(eval(bucket="base")) as base_searches, count(eval(bucket="now")) as now_searches
| eval base_hourly=base_searches/167
| where now_searches>10 AND now_searches>5*base_hourly
```

## Guardrails

- Never run from, or with the credentials of, the audited AI account.
- Aggregate before quoting; trim search strings; this report may itself
  contain data values — handle it at the same classification as the
  underlying index.
- Findings about *people* steering the agent are SOC matters — route,
  don't investigate individuals here (purpose limitation).
- An empty `_audit` result for an account known to be active is a logging
  problem, not a clean bill — treat as a finding.

## customer-profile.md (bespoke layer, optional)

```markdown
# Customer profile — <CUSTOMER>
## AI accounts under audit
| Account | Tier | Allowlisted indexes | Expected shape | Owner |
|---|---|---|---|---|
| ai_triage_ro | 1 | sap_prod | interactive, business hours + 07:00 health check | <team> |
## Legitimate `| rest` usage
- sap-mcp-hardening-check runs /services/authentication/current-context — expected
## Cadence
- Review: weekly · Alerts: continuous · Pair with hardening check: quarterly
```
