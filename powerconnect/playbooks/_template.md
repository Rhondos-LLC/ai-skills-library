# <Playbook title>

<!-- Maintainer template. Not routed to. Keep each playbook 80–160 lines. -->

**Use when:** <the questions that lead here, in the user's words>
**Not for:** <the neighbouring question> → [other-playbook.md](other-playbook.md)

One or two sentences: what this playbook establishes and the core insight
that stops the most common wrong conclusion.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `SM37` | ABAP | header + detail | job runs, steps, logs | yes |

Shape is one of: event stream, snapshot, header + detail (see
[../reference/data-model.md](../reference/data-model.md)). "Default" says
whether the extractor is active out of the box. If a type is missing, say
it is a coverage gap and name the extractor to enable; do not treat missing
data as a healthy result.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `JOBNAME` | job name | | sample (Dynatrace) |

Write field names in UPPERCASE; the backend adapter gives the casing.
"Confirmed" is one of: `sample (<backend>)` = seen in a live record;
`docs` = named on a documentation page or in a shipped alert matcher;
`SAP` = standard SAP table field, expected but not yet seen. Anything not
confirmed by sample must be checked with a one-record sample before it is
used in a filter.

## Investigation sequence

1. **Confirm the feed.** Count and newest timestamp for each event type in
   scope. Stop here with a coverage finding if the key type is absent.
2. **Sample one record** of each type you will filter on and reconcile the
   field names above with what is there.
3. **<Scope the problem>** — aggregate first.
4. **<Drill>** — at most a handful of concrete records.
5. **<Correlate>** — name the other event types and the join key.

For each step give the intent, then the query in both documented backends:

```spl
<Splunk SPL, using index=<IDX> and the sourcetype convention from Step 0>
```

```dql
<Dynatrace DQL, with explicit from:/to: and service.name + dt.source_entity_name filters>
```

On any other backend, translate the intent with the idioms recorded in the
profile (see [../backends/other.md](../backends/other.md)).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|

## What to tell the user

- The finding, with event type, window, count and identifiers.
- The SAP transaction where a human verifies it.
- The recommended action and who owns it.
- What you could not see and why.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|

Hand these to [alert-builder.md](alert-builder.md) to turn into a platform
alert.

## Documentation

- <Page title> — `<slug>`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
