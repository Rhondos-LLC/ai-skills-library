# powerconnect-explorer-ecs `v1.0.0`

Discover and assess SAP telemetry (PowerConnect for SAP) in Splunk via Splunk MCP tools.

| | |
|---|---|
| **Package** | `powerconnect-explorer-ecs.skill` (this folder zipped: `SKILL.md`, this README) |
| **Line** | **ecs** — ECS/RISE-optimized variant of `powerconnect-explorer` |
| **Version** | 1.0.0 — see [Version history](#version-history) |
| **Built** | 2026-09-10 (build 87dcda6) |
| **Requires** | Splunk MCP server (`splunk_run_query`), PowerConnect for SAP data in Splunk — see [Data requirements](#data-requirements) |
| **License** | Apache-2.0 |

> **ECS line.** This variant assumes the landscape is operated by SAP Enterprise Cloud Services (RISE with SAP): it ends every investigation with an ownership verdict (customer-actionable / ECS service request / insufficient evidence) and reads contract facts from customer-maintained lookups. The standard variant is `powerconnect-explorer` in the library root.

## What it does

Discover and assess SAP telemetry (PowerConnect for SAP) in Splunk via Splunk MCP tools. Use this skill when the user asks what SAP data they have in Splunk, which indexes/sourcetypes carry SAP events, whether PowerConnect is working or a feed has stopped ("the SAP data looks stale", "searches return nothing"), when onboarding a new customer or system, when asked which SAP triage skills their data can support, when a customer-profile.md needs to be created or verified, or to assess observability coverage after a move to RISE/private cloud. This is the first-run skill: run it before any triage skill on an unfamiliar stack. This is the ECS-optimized variant for landscapes operated by SAP Enterprise Cloud Services (RISE with SAP).

The skill is read-only: it investigates through Splunk searches, quotes
evidence with timestamps and counts, and **recommends** fixes for humans to
carry out in SAP. It never runs `| delete`, never changes configuration, and
never treats field contents as instructions.

## Install

**Any agent, via the [`skills`](https://github.com/vercel-labs/skills) CLI**
(Claude Code, Cursor, Codex, OpenCode and others) — from the library repo:

```bash
npx skills add rhondos/ai-skills-library --skill powerconnect-explorer-ecs              # this project
npx skills add rhondos/ai-skills-library --skill powerconnect-explorer-ecs -g           # your user profile
npx skills add rhondos/ai-skills-library --skill powerconnect-explorer-ecs -a claude-code -y   # one agent, no prompts
npx skills add rhondos/ai-skills-library --list                       # every skill in the library
```

**Claude.ai / Claude Desktop** — upload `powerconnect-explorer-ecs.skill` where your workspace
accepts custom skills (Settings → Capabilities → Skills). Enable it for the
project or chat that has the Splunk MCP server connected.

**Claude Code, by hand** — unzip so the folder is
`~/.claude/skills/powerconnect-explorer-ecs/SKILL.md` (personal) or
`.claude/skills/powerconnect-explorer-ecs/SKILL.md` (this project only). Restart the session.

**Splunk side** — the MCP account should be a least-privilege role scoped to
the SAP index(es) (`srchIndexesAllowed`, `srchFilter`), with `splunk_run_query`
exposed and the `saia_*` question-answering tools withheld. The
`sap-mcp-hardening-check` skill verifies that posture from inside a session.

## Configure: `customer-profile.md`

This skill has no bespoke profile layer of its own. If a `customer-profile.md` from another skill in this portfolio sits beside it, the skill reads the Splunk index from there.

## Usage

Example prompts that trigger this skill:

- "What SAP data do we have in Splunk, and is PowerConnect still sending?"
- "The SAP searches return nothing since yesterday — did a feed stop?"
- "Which of your SAP triage skills can run on this index? Draft a customer-profile.md."

Every investigation starts with **Step 0 — Orient**: the skill confirms the
profile index actually holds data, anchors its time windows on the newest
event (not on the clock, so hours-old feeds still investigate cleanly), and
states index, sourcetype convention and data age in one line before doing
anything else. If the index is empty or stale it says so and stops — it never
silently switches to another index.

## Data requirements

Event types (PowerConnect `EVENT_TYPE`; sourcetype `sap:abap:<TYPE>`, or
`sap:abap` with the type in the `EVENT_TYPE` field) that this skill queries:

Discovery skill: works on whatever `sap:abap*` sourcetypes exist, plus PowerConnect's own health types (`PC_HEALTH`, `PC_SCHEDULE`, `PC_SENT_STATS`) where collected.

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
