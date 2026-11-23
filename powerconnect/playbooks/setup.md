# Guided setup — create or update the customer profile

**Use when:** no `customer-profile.md` can be found on first use; the user
says "set up", "configure", "onboard" or "update the profile"; or the
profile is older than its review date.
**Not for:** a full coverage assessment →
[explorer.md](explorer.md) (setup offers it as an option); a documentation
question, which never needs a profile → [docs-qa.md](docs-qa.md).

The core insight: **detect everything you can, ask only what you cannot,
and ask it as choices.** A setup that interrogates the user gets skipped.
Two short rounds of multiple-choice questions, pre-filled from what the
data shows, are enough to make every later investigation start in the
right scope.

## 1. Offer, do not force

When a data question arrives and no profile exists, answer in one line
that setup has not been done and offer three choices:

- **Set up now** (about two minutes) — continue below, then answer the
  original question.
- **Skip for now** — run Step 0 from the adapter, answer the question, and
  do not offer again in this conversation.
- **Full assessment** — setup plus the explorer census of every feed.

If the user's message is urgent or incident-like ("production is down"),
skip the offer, answer first, and offer setup at the end.

## 2. How to ask

Use a structured question tool if you have one, so the user gets a popup
or menu instead of typing:

- In Claude Code, `AskUserQuestion` (up to four questions per call, two to
  four options each, `multiSelect` for lists, the recommended option first).
- In other clients, any tool that asks the user multiple-choice questions
  or elicits a form.

If you have no such tool, print the questions as a short numbered menu
with lettered options and ask for a reply such as `1b 2a,c 3a`. Either
way: every question has a sensible default, an "I don't know" option where
that is a real answer, and never asks for something a query can tell you.

## 3. Detect before asking

Do this silently, with the cheapest queries the adapter offers:

| Fact | How |
|---|---|
| Platform(s) available | the query tools you have (see the table in `SKILL.md`) |
| Scope, stacks, SIDs, data age | Step 0 — Orient from the adapter |
| PowerConnect ABAP version, database type | one `PC_HEALTH` record with subtype `INFO` (`RELEASE_NO`, `DB_SYS`) |
| System time zone | `UTCDIFF` / `UTCSIGN` from the same record |
| Sourcetype convention (Splunk) | Step 0 result |

If Step 0 finds no SAP data, stop setup, say so, and switch to
[feed-health.md](feed-health.md); a profile of an empty scope is worthless.

## 4. Round one — scope (one popup)

Ask only the questions whose answer is not already unambiguous:

1. **Where is the SAP data?** Only if more than one platform or more than
   one candidate scope (index, bucket) was detected. Options: the detected
   candidates, with event counts in the description.
2. **Which systems should this skill cover?** Multi-select from the SIDs
   found, plus "All of them". Put the busiest systems first.
3. **How is the landscape operated?** Options: "Customer-operated
   (standard)", "SAP Enterprise Cloud Services / RISE", "Mixed or not
   sure". The answer decides whether the ECS overlay applies.
4. **How deep should setup go?** Options: "Quick — save the essentials
   (recommended)", "Full — also assess every feed now". Skip this question
   if the user already chose in step 1.

## 5. Round two — context (one popup, optional)

Offer it as "a few optional questions that make answers better"; the user
may skip the whole round.

1. **What role does each system play?** For up to four systems: Production
   / Quality / Development / Other. With more systems, ask in chat for a
   list instead.
2. **How should personal data appear in answers?** "Show user names when
   relevant", "Mask user names", "Aggregate only, never list individuals".
3. **When is the batch window?** "Overnight (system time)", "No fixed
   window", "I'll type it" — plus business hours if the user offers them.
4. **Who carries out SAP-side changes?** "Our own Basis team", "A managed
   service partner", "SAP ECS via service request".

Anything the user does not answer goes into the profile as
`TODO(owner)`, not as a guess.

## 6. Write the profile

Fill [../customer-profile.template.md](../customer-profile.template.md)
with detected values, the answers, today's date and a review trigger. For
"Quick" setup leave the "Feeds present" table to a later explorer run and
say so in the file. Never write passwords, tokens or licence keys.

Save it in the first place that works, and tell the user where it went:

1. `customer-profile.md` beside `SKILL.md`, if the skill folder is
   writable (typical for a local install).
2. `customer-profile.md` in the current project or working directory.
3. If you cannot write files (typical for a skill uploaded to a chat app,
   where the skill folder is read-only): give the user the finished
   profile as a file or a code block, and ask them to add it to the
   project's knowledge or paste it at the start of future conversations.
   Use it from the conversation for the rest of this one.

## 7. Confirm and continue

Show a five-line summary — platform and scope, systems and roles,
landscape line, PowerConnect version, where the profile was saved — and
ask for corrections in one line. Then return to the user's original
question, or start [explorer.md](explorer.md) if they chose the full
assessment.

## Updating an existing profile

When asked to update, read the current profile and present each setting
with its current value as the first, pre-selected option ("Keep: ...").
Re-run the detection in section 3 and point out anything that has changed
since the profile was written: a new SID, a new PowerConnect version, a
feed that has gone quiet. Change only what the user confirms, and update
the date.

## Guardrails

- At most two rounds of questions, four questions each. If more is
  needed, finish setup and ask the rest when a playbook actually needs it.
- Do not block an answer on setup. Skipping is always allowed.
- Setup runs only read-only queries, and only the handful listed in
  section 3. It writes one file, the profile, and nothing in the platform.
- If the user's answers contradict the data (they name a SID that is not
  in the scope), say so and record both, rather than silently choosing one.
