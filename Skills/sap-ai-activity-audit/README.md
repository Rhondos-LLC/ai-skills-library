# sap-ai-activity-audit `v1.0.0`

Audit what an AI triage account actually did in Splunk — every search it ran, what it touched, how much data it pulled — from Splunk's _audit index.

| | |
|---|---|
| **Package** | `sap-ai-activity-audit.skill` (this folder zipped: `SKILL.md`, this README) |
| **Line** | **base** — standard landscapes (ECS variant: `ecs/sap-ai-activity-audit-ecs`) |
| **Version** | 1.0.0 — see [Version history](#version-history) |
| **Built** | 2026-09-10 (build 87dcda6) |
| **Requires** | Splunk MCP server (`splunk_run_query`), PowerConnect for SAP data in Splunk — see [Data requirements](#data-requirements) |
| **License** | Apache-2.0 |

## What it does

Audit what an AI triage account actually did in Splunk — every search it ran, what it touched, how much data it pulled — from Splunk's _audit index. Use this skill when the security team asks "what has the AI been doing?", for a scheduled AI-activity review, after any suspected misuse or prompt-injection incident, to close the loop on a hardening check, or to produce evidence for auditors that AI access is monitored. MUST be run from a privileged security/admin session — never from the AI account itself (it cannot and must not read its own audit trail).

The skill is read-only: it investigates through Splunk searches, quotes
evidence with timestamps and counts, and **recommends** fixes for humans to
carry out in SAP. It never runs `| delete`, never changes configuration, and
never treats field contents as instructions.

## Install

**Any agent, via the [`skills`](https://github.com/vercel-labs/skills) CLI**
(Claude Code, Cursor, Codex, OpenCode and others) — from the library repo:

```bash
npx skills add rhondos/ai-skills-library --skill sap-ai-activity-audit              # this project
npx skills add rhondos/ai-skills-library --skill sap-ai-activity-audit -g           # your user profile
npx skills add rhondos/ai-skills-library --skill sap-ai-activity-audit -a claude-code -y   # one agent, no prompts
npx skills add rhondos/ai-skills-library --list                       # every skill in the library
```

**Claude.ai / Claude Desktop** — upload `sap-ai-activity-audit.skill` where your workspace
accepts custom skills (Settings → Capabilities → Skills). Enable it for the
project or chat that has the Splunk MCP server connected.

**Claude Code, by hand** — unzip so the folder is
`~/.claude/skills/sap-ai-activity-audit/SKILL.md` (personal) or
`.claude/skills/sap-ai-activity-audit/SKILL.md` (this project only). Restart the session.

**Splunk side** — the MCP account should be a least-privilege role scoped to
the SAP index(es) (`srchIndexesAllowed`, `srchFilter`), with `splunk_run_query`
exposed and the `saia_*` question-answering tools withheld. The
`sap-mcp-hardening-check` skill verifies that posture from inside a session.

## Configure: `customer-profile.md`

This skill has no bespoke profile layer of its own. If a `customer-profile.md` from another skill in this portfolio sits beside it, the skill reads the Splunk index from there.

## Usage

Example prompts that trigger this skill:

- "What has the AI triage account been doing in Splunk this week?"
- "Show every search the AI service account ran yesterday and how much data it pulled."
- "We suspect a prompt injection in the SAP feed — audit what the AI session searched."

Every investigation starts with **Step 0 — Orient**: the skill confirms the
profile index actually holds data, anchors its time windows on the newest
event (not on the clock, so hours-old feeds still investigate cleanly), and
states index, sourcetype convention and data age in one line before doing
anything else. If the index is empty or stale it says so and stops — it never
silently switches to another index.

## Data requirements

Event types (PowerConnect `EVENT_TYPE`; sourcetype `sap:abap:<TYPE>`, or
`sap:abap` with the type in the `EVENT_TYPE` field) that this skill queries:

Splunk's own `_audit` index (read from a privileged security/admin session — never from the AI account); no SAP event types required.

Types the skill marks *(optional)* in its data-sources table may be absent;
the sequence degrades gracefully and says what it could not observe. Every
field name in the skill's SPL is verified at build time against real
PowerConnect captures and DDIC structures.

## Version history

Versions follow semver: **major** = the investigation method or the data
model changed (re-read the skill); **minor** = new step, pattern, alert or
data source; **patch** = wording, thresholds, field-name fixes.

| Version | Date | Notes |
|---|---|---|
| 1.0.0 | 2026-09-10 | Initial portfolio release: compiled from the shared PowerConnect core; field names lint-verified against real captures; base and ECS lines. |

## Feedback

Open an issue: https://github.com/rhondos/ai-skills-library/issues. When a query misfires, include the SPL you
ran, what came back (error or empty result), and one sample event
(`| head 1 | fields *`, secrets removed) showing the real field shape. The
files in this package are generated by the maintainers' build, so fixes land
as a new version rather than as edits to `SKILL.md`.

Contact: engineering@rhondos.com
