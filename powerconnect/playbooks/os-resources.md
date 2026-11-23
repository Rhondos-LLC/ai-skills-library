# OS resources — CPU, memory, swap, file systems, disks, network

**Use when:** a host is short of CPU or memory, a file system is filling,
disk I/O is slow, a network interface reports errors, or someone asks
about server hardware or the contents of an SAP directory.
**Not for:** slow transactions and work-process shortage →
[performance-triage.md](performance-triage.md); database volumes →
[database-health.md](database-health.md); Java hosts and the JVM →
[java-stack.md](java-stack.md).

The core insight: **`ST06` is one event type holding several record kinds,
told apart by `EVENT_SUBTYPE`.** The empty subtype is the host summary;
`CPU_SINGLE` and `LAN_SINGLE` are per-CPU and per-adapter detail. Filter
the subtype explicitly or detail rows leak into host averages (`CPU_SINGLE`
records carry a `CPU_TOTAL` too, and newer releases add `_METRICS_`). Second
trap: the sampled `FREE_MEM` is kilobytes, not a percentage; compute the
ratio to `PHYS_MEM` before comparing it with a threshold.

## Data it needs

| Event type | Stack | Shape | What it gives | Default |
|---|---|---|---|---|
| `ST06` | ABAP | snapshot | `""` host summary (CPU, load, memory, swap, busiest disk, LAN totals); `CPU_SINGLE`; `LAN_SINGLE` per adapter | yes |
| `ST06_FSYS` | ABAP | snapshot | capacity and free space per file system | yes |
| `ST06_SN_DISK`, `ST06_TOP_CPU`, `ST06_HW` | ABAP | snapshot | per-disk utilisation and response time; top CPU processes; hardware information | yes |
| `AL11` | ABAP | snapshot | `""` directory summary, `NAMES` file names | yes, but only for directories in the AL11 metric filter |
| `ST02_BFFR`, `ST02_CALL`, `ST02_MEM` | ABAP | snapshot | SAP buffer and memory statistics (in the catalog, no documentation page) | yes |

Instances that share a host report the same host values (the source is
the SAP host agent): reduce to one row per host before averaging.

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `INSTANCE_NAME` (+ `HOST`) | application server instance; entity key. On Dynatrace `host.name` was missing on most ST06* records: key and filter on `instance_name` | | sample (Dynatrace); Splunk per KB 188 |
| `CPU_TOTAL` | CPU utilisation %, user + system | shipped alert: > 90 | sample (Dynatrace) + docs |
| `USR_TOTAL`, `SYS_TOTAL`, `WAIT_TRUE`, `LOAD5_AVG`, `NBR_CPU` | CPU split %; load average; CPU count | high `WAIT_TRUE` = I/O wait; load above `NBR_CPU` = queueing | sample (Dynatrace) |
| `FREE_MEM`, `PHYS_MEM` | free and physical memory, both KB; Dynatrace adds derived `TOTAL_MEM` (free %, = 100 × free / phys), `RAM_UTIL` (used %, = 100 − `TOTAL_MEM`), `SWAP_UTIL` (went negative where `SWAP_FREE` > `SWAP_SIZE`) | shipped alert tests `free_mem < 10`, which KB values never meet | sample (Dynatrace) + docs |
| `SWAP_FREE`, `SWAP_SIZE`, `IN_PG_SEC`, `OUT_PG_SEC` | swap, KB; pages in / out per second | sustained page-out = real memory pressure | sample (Dynatrace) |
| `DISKNAME`, `UTIL`, `RESPONSE_TIME`, `AVG_QUEUELEN`, `AVG_WAIT` | busiest disk in the summary record | | sample (Dynatrace) |
| `IN_ERRORS`, `OUT_ERRORS`, `IN_PACKETS`, `OUT_PACKETS`, `COLLISIONS` | LAN counters; per adapter in `LAN_SINGLE`, where the adapter is `LANNAME` (+ `SERIALNR`) and packets out is `OUT_PACKET` | shipped alerts: `!= 0` on `LAN_SINGLE`; values moved up and down between polls (per interval, not cumulative) | sample (Dynatrace) + docs |
| `SERIALNR`, `USR_CPU`, `SYS_CPU`, `IDLE_CPU` | `CPU_SINGLE`: CPU number and its split %; Dynatrace adds derived `TOTAL_CPU` | | sample (Dynatrace) |
| `FSYSNAME`, `CAPACITY`, `FREE` | file system, size and free space (MB in the sample); Dynatrace adds derived `UTIL_PERC`, `FREE_PERC` | | sample (Dynatrace) |
| `ST06_SN_DISK`, `ST06_TOP_CPU`, `ST06_HW`, `AL11`, `ST02_*` | not listed in the documentation | | unconfirmed — sample first |

## Investigation sequence

1. **Confirm the feed and its subtypes** (adapter idiom "count and
   freshness per type", split by `EVENT_SUBTYPE`), then sample each kind
   you will use. Snapshots: a quiet `ST06` is a broken feed.

2. **Current CPU, load and memory per host** — latest summary record per
   instance, with the memory percentage computed from the raw values.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST06 EVENT_SUBTYPE=""
| stats latest(CPU_TOTAL) as cpu latest(LOAD5_AVG) as load5 latest(NBR_CPU) as cpus latest(FREE_MEM) as free latest(PHYS_MEM) as phys latest(OUT_PG_SEC) as pageout by host INSTANCE_NAME
| eval cpu=tonumber(cpu), free_pct=round(100*tonumber(free)/tonumber(phys),1)
| sort - cpu
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "ST06" and dt.source_entity_type == ""
| sort timestamp asc
| summarize {cpu = takeLast(toDouble(cpu_total)), load5 = takeLast(toDouble(load5_avg)), cpus = takeLast(toLong(nbr_cpu)), free = takeLast(toDouble(free_mem)), phys = takeLast(toDouble(phys_mem)), pageout = takeLast(toDouble(out_pg_sec))}, by: {host.name, instance_name}
| fieldsAdd free_pct = round(100 * free / phys, decimals: 1)
| sort cpu desc
```

3. **When did it start, is it sustained** — one value per time slot. One
   poll above 90 % is a spike; several in a row is a shortage.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST06 EVENT_SUBTYPE="" host=<HOST>
| eval cpu=tonumber(CPU_TOTAL), free_pct=100*tonumber(FREE_MEM)/tonumber(PHYS_MEM)
| timechart span=15m max(cpu) as cpu_max min(free_pct) as free_pct_min
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "ST06" and dt.source_entity_type == "" and instance_name == "<INSTANCE_NAME>"
| summarize {cpu_max = max(toDouble(cpu_total)), free_pct_min = min(100 * toDouble(free_mem) / toDouble(phys_mem))}, by: {slot = bin(timestamp, 15m)}
| sort slot asc
```

4. **File systems** — latest record per instance and file system. 85 % is
   a starting point; on a large file system read the free megabytes too.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST06_FSYS
| stats latest(CAPACITY) as cap latest(FREE) as free by host INSTANCE_NAME FSYSNAME
| eval used_pct=round(100*(1-tonumber(free)/tonumber(cap)),1)
| where used_pct > 85
| sort - used_pct
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "ST06_FSYS"
| sort timestamp asc
| summarize {cap = takeLast(toDouble(capacity)), free = takeLast(toDouble(free))}, by: {host.name, instance_name, fsysname}
| fieldsAdd used_pct = round(100 * (1 - free / cap), decimals: 1)
| filter used_pct > 85
| sort used_pct desc
```

5. **Network errors** per adapter (`LANNAME`). In the sample the counters
   were per-interval values; confirm that on your feed before calling a
   non-zero value a new problem.

```spl
index=<IDX> sourcetype=sap:abap EVENT_TYPE=ST06 EVENT_SUBTYPE=LAN_SINGLE
| eval in_err=tonumber(IN_ERRORS), out_err=tonumber(OUT_ERRORS)
| where in_err > 0 OR out_err > 0
| stats count as polls max(in_err) as in_err max(out_err) as out_err by host
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:abap" and dt.source_entity_name == "ST06" and dt.source_entity_type == "LAN_SINGLE"
| filter toLong(in_errors) > 0 or toLong(out_errors) > 0
| summarize {polls = count(), in_err = max(toLong(in_errors)), out_err = max(toLong(out_errors))}, by: {host.name, instance_name, lanname}
```

6. **Correlate.** For "who uses the CPU", sample `ST06_TOP_CPU` for that
   host; for work processes continue in
   [performance-triage.md](performance-triage.md) (`SM50`, `SM66`, `SM37`).
   For slow I/O, compare `WAIT_TRUE` with `ST06_SN_DISK`. A full file
   system often explains dumps, failed jobs and stopped updates at once;
   `AL11` names the directory if its filter covers it.

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| `CPU_TOTAL` > 90 sustained, load above `NBR_CPU` | CPU shortage | top processes; workload at that time |
| Low `free_pct` but no page-out and little swap used | file cache holding memory (normal on Linux) | not an incident; watch paging |
| Sustained `OUT_PG_SEC` and shrinking `SWAP_FREE` | real memory pressure | SAP memory parameters, sizing; ST02 data |
| High `WAIT_TRUE`, high disk `RESPONSE_TIME` | storage bottleneck | `ST06_SN_DISK`; storage team |
| File system above 95 % and growing | work, log or trace files accumulating; archive log area | name the directory; housekeeping jobs |
| `AL11` empty on S/4HANA with SP 6.07 | extractor bug (KB 139) | update to SP 6.08+ |
| Splunk System Overview gauges show 0 (app 6.2.0); File System instance filter ignored (7.1.0–7.3.0) | dashboard bugs (KB 98, KB 188) | query the data directly |

## What to tell the user

- Host, instance, metric, value, since when and for how many polls.
- Verify in ST06 (AL11 for directories). Hardware, storage and network
  belong to the infrastructure team; SAP-caused load to Basis.
- Not visible: hosts without an ABAP instance; unfiltered AL11 paths.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `cpu_total > 90` | `ST06` | shipped `davis.sap.st06.cpu_util`; require several consecutive polls |
| free memory below 10 % | `ST06` | shipped `davis.sap.st06.memory_util` tests `free_mem < 10`; confirm the unit, or alert on the computed ratio |
| `in_errors != 0` / `out_errors != 0` on `LAN_SINGLE` | `ST06` | shipped `davis.sap.st06.packet_errors_in`, `.packet_errors_out` |
| File system used above 85–90 %, or free below a fixed size | `ST06_FSYS` | starting points; per file system |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `st06`, `st06_fsys`, `st06_hw`, `st06_sn_disk`, `st06_top_cpu`, `al11`
- KB 98, 188, 139 — `kb-98-cpu-memory-and-availability-gauges-displayin`,
  `kb-188-instance-filter-non-functional-in-splunk-fi`,
  `kb-139-al11-does-not-collect-file-information`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
