# SAP Java stack — JVM, threads, processes, Java logs, Cloud Connector

**Use when:** a NetWeaver Java / PO / Portal system is slow or unstable,
heap or GC is suspected, threads are blocked, a Java process stopped, the
default trace shows errors, or SAP Cloud Connector needs a health check.
**Not for:** PI/PO messages and channels →
[integration-messages.md](integration-messages.md); keystore expiry →
[certificates-and-licenses.md](certificates-and-licenses.md); Java security
logs → [security-audit.md](security-audit.md); a silent Java agent →
[feed-health.md](feed-health.md).

The core insight: **`jmx` is one record per MBean per poll, and each MBean
has its own attributes.** There is no single "JVM record": pick the MBean
first (`mbean_name`), then read its attributes. A filter on an attribute
silently drops every other MBean, and attribute names keep the MBean's
mixed case (`CollectionCount`, `LastGcInfo.duration`) on both backends;
DQL reads them without backticks.
Second: the NetWeaver, Cloud Connector, BusinessObjects and Data Services
agents reuse type names (`jmx`, `thread`, `alert`); split by `system_type`.

## Data it needs

On Splunk: sourcetype `sap:java` or `jmx`, type in `event_type`.

| Event type | Shape | What it gives | Default |
|---|---|---|---|
| `jmx` | snapshot | JVM and host metrics per enabled MBean (heap pools, GC, OS, threading, runtime) | yes, every 60 s |
| `thread` | snapshot | thread dump: state, CPU time, stack trace, deadlock flag | no |
| `process`, `component`, `task` | snapshot | SAP Control process list and state; component status; running tasks | check by count |
| `session`, `web_session`, `locks` | snapshot | user sessions; HTTP sessions; enqueue lock table | `web_session` no |
| `db_connection`, `db_sql` | snapshot | Open SQL connection pools; SQL statement statistics | check by count |
| `dsr` | event stream | per-request response, database and CPU time (the Java STAD) | check by count |
| `default_trace_log`, `application_trace_log`, `http_access_log` | event stream | log lines; trace logs carry the DSR transaction id | no; agent restart needed |
| `security_log`, `certificate` | stream / snapshot | see the security and certificate playbooks | no / check |
| `server` | snapshot | BusinessObjects servers: health, enabled and running state | BO agent only |
| `agent_health` | continuous | agent self-metrics (events sent, errors, retries, limits) | only if "Report PowerConnect Agent Health" is on |
| `scc_backend_connection`, `alert`, `usage_backend` (also `health`, `master_role`, `cpu_status`, `memory_status`, `disk_status`) | snapshot | Cloud Connector backends, alerts, usage, health, HA role, resources | per property in the SCC agent's properties file |

## Fields that matter

| Logical field | Meaning | Values worth knowing | Confirmed |
|---|---|---|---|
| `instance_id`, `sap_system_name`, `system_type`, `pid` (+ `HOST`) | Java instance / node identity, on every Java record | `system_type` `netweaver` seen | sample (Dynatrace) |
| `mbean_name`, `ObjectName`, `Name` | which MBean a `jmx` record describes | e.g. `java.lang:type=OperatingSystem`; `mbean_name` sorts the keys (`java.lang:name=<collector>,type=GarbageCollector`), `ObjectName` keeps `type=` first | sample (Dynatrace) + docs |
| `CollectionCount`, `CollectionTime`, `LastGcInfo.duration` | GC runs, cumulative GC ms, last pause ms | docs spell `LastGCInfo`; the sample has `LastGcInfo` | sample (Dynatrace) |
| `ProcessCpuLoad`, `SystemCpuLoad`, `FreePhysicalMemorySize`, `TotalPhysicalMemorySize`, `FreeSwapSpaceSize` | OperatingSystem MBean | CPU load is a 0–1 fraction; sizes in bytes | sample (Dynatrace) |
| `HeapMemoryUsage.used`, `HeapMemoryUsage.max` | `java.lang:type=Memory` MBean, bytes | the heap source in the sample | sample (Dynatrace) |
| `Usage.used`, `Usage.max`, `Type` | MemoryPool MBean per pool (not enabled in the sample) | `Type` `HEAP` / `NON_HEAP` | docs |
| `ThreadCount`, `PeakThreadCount`, `Uptime`, `StartTime` | Threading and Runtime MBeans | falling `Uptime` = restart | sample (Dynatrace); `StartTime` docs |
| `jvm_heap_util`, `jvm_process_cpu_util`, `jvm_host_mem_util`, `jvm_host_swap_util`, `jvm_gc_last_duration_ms`, `jvm_gc_collector` | Dynatrace-derived percentages / ms, each present only on its MBean's record: heap on `Memory`, CPU, host memory and swap on `OperatingSystem`, GC on `GarbageCollector` | shipped alerts: heap > 90, CPU > 90, host memory > 95, swap > 80, GC pause > 5000 ms | sample (Dynatrace) + docs (alerts) |
| `name`, `id`, `state`, `thread_group` | thread identity and state | `BLOCKED`, `RUNNABLE`, `WAITING`, `TIMED_WAITING` seen; alert uses `BLOCKED` | sample (Dynatrace) + docs |
| `cpu_time`, `blocked_count`, `waited_count`, `deadlocked`, `stack_trace` | thread cost, contention, deadlock flag, frames (`class_name`, `method_name`, `line_number`) | `deadlocked` is boolean | sample (Dynatrace) |
| `name`, `type`, `state`, `restart_count`, `exit_code` (process) | Java process identity and state | `Disabled` seen; alert uses `Stopped` | sample (Dynatrace) + docs (alert) |
| `db_conn_used_rate` | Dynatrace-derived pool usage % | alert `>= 90` | docs (alert) |
| `Severity`, `Location`, `Application`, `Text`, `DSRTransaction`, `ThreadName` | default / application trace columns (default header mapping) | on Dynatrace `Severity` is absent at top level; the alert tests `loglevel == "ERROR"` (seen) | sample (Dynatrace); `Severity` docs |
| other types | `dsr`, `session`, `task`, `locks`, `db_sql`, `server`, SCC types | | unconfirmed — sample first |

## Investigation sequence

1. **Confirm the feeds** (adapter idiom "count and freshness per type",
   split by `system_type`), then sample one record per type. For `jmx`,
   list the distinct `mbean_name` values before reading any attribute.

2. **Garbage collection per node** — last and longest pause per
   collector. Long old-generation pauses with a full heap mean pressure.

```spl
index=<IDX> sourcetype IN ("sap:java", "jmx") event_type=jmx mbean_name="java.lang:*type=GarbageCollector*"
| stats latest("LastGcInfo.duration") as last_gc_ms max("LastGcInfo.duration") as max_gc_ms latest(CollectionCount) as collections by host instance_id Name
| sort - max_gc_ms
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:java" and dt.source_entity_name == "jmx" and isNotNull(jvm_gc_last_duration_ms)
| sort timestamp asc
| summarize {last_gc_ms = takeLast(toLong(jvm_gc_last_duration_ms)), max_gc_ms = max(toLong(jvm_gc_last_duration_ms))}, by: {host.name, instance_id, jvm_gc_collector}
| sort max_gc_ms desc
```

3. **Heap, JVM CPU and host memory per node.** On Dynatrace use the
   derived fields; elsewhere read the OperatingSystem MBean and compute
   heap from the Memory MBean (`HeapMemoryUsage.used` / `.max`) or the
   `HEAP` MemoryPool records (`Usage.used` / `Usage.max`).

```spl
index=<IDX> sourcetype IN ("sap:java", "jmx") event_type=jmx mbean_name="java.lang:type=OperatingSystem"
| eval jvm_cpu=100*tonumber(ProcessCpuLoad), host_cpu=100*tonumber(SystemCpuLoad), mem_used_pct=100*(1-tonumber(FreePhysicalMemorySize)/tonumber(TotalPhysicalMemorySize))
| stats max(jvm_cpu) as jvm_cpu_max latest(host_cpu) as host_cpu latest(mem_used_pct) as mem_used_pct by host instance_id
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:java" and dt.source_entity_name == "jmx"
| filter isNotNull(jvm_heap_util) or isNotNull(jvm_process_cpu_util) or isNotNull(jvm_host_mem_util)
| summarize {heap_max = max(toDouble(jvm_heap_util)), jvm_cpu_max = max(toDouble(jvm_process_cpu_util)), host_mem_max = max(toDouble(jvm_host_mem_util))}, by: {host.name, instance_id}
```

4. **Blocked and deadlocked threads.** A dump is taken every poll: one
   `BLOCKED` sample is normal contention; the same thread blocked from
   `first` to `last` over many polls is stuck. Then read its `stack_trace`.

```spl
index=<IDX> sourcetype IN ("sap:java", "jmx") event_type=thread (state=BLOCKED OR deadlocked=true)
| stats count as samples min(_time) as first max(_time) as last latest(thread_group) as thread_group by host instance_id name
| sort - samples
```

```dql
fetch logs, from: "<T_START>", to: "<T_END>"
| filter service.name == "sap:java" and dt.source_entity_name == "thread"
| filter state == "BLOCKED" or deadlocked == true
| summarize {samples = count(), first = min(timestamp), last = max(timestamp), thread_group = takeAny(thread_group)}, by: {host.name, instance_id, name}
| sort samples desc
```

5. **Stopped processes and trace errors.** Latest `process` record per
   process, keeping `state` `Stopped`. For `default_trace_log`, sample
   first, then count error lines per node and location: on Dynatrace
   filter `loglevel == "ERROR"` (the shipped alert's test), on Splunk the
   severity column of the log header (`Severity`, values to confirm).

6. **Correlate.** `dsr` gives slow requests and the transaction id that
   also tags trace-log lines; `db_connection` and `db_sql` show whether
   the database pool is the bottleneck; `locks` shows enqueue contention.
   Cloud Connector: sample `health`, `master_role`, `alert` and
   `scc_backend_connection`. A dual-stack host's shortage also shows in
   [os-resources.md](os-resources.md).

## Reading the results

| You see | It usually means | Next step |
|---|---|---|
| Heap > 90 % with GC pauses of seconds | memory pressure or leak | heap dump analysis by the Java team; compare after restart |
| High JVM CPU, many `RUNNABLE` threads in one class | hot code path | Thread Hotspots dashboard; `stack_trace` |
| Same thread `BLOCKED` across polls, or `deadlocked` true | lock contention or deadlock | owner of the blocking monitor; restart is a human decision |
| `db_conn_used_rate` ≥ 90 | pool exhaustion or slow database | `db_sql`; [database-health.md](database-health.md) |
| `process` `Stopped`, `Uptime` reset | node crash or restart | default trace, `std_server*.out` on the host |
| Only `agent_health` arrives | agent in safe mode (KB 198, 8.1.0+) | reset `powerconnect.safemode` and restart the agent |
| Nothing from a node; UI URL returns 404 | agent not deployed (KB 45) or `spcj_wd` failed with the `library:sdo` class-loader error (KB 163, SAP Note 2186799) | deployment check; SAP patch |
| Extra CPU / log volume with AppDynamics present | unsupported coexistence (KB 213) | choose one instrumentation |

## What to tell the user

- System, host, node (`instance_id`), metric, value and since when; for
  threads the name and top stack frames.
- Verify in NWA (system reports, thread dump, log viewer). Owner: Java
  Basis; the application team for hot code and leaks.
- Not visible: plug-ins that are off (threads, logs and web sessions by
  default) and MBeans not in the enabled list.

## Alert ideas

| Condition | Event type | Notes |
|---|---|---|
| `jvm_heap_util > 90`; `jvm_process_cpu_util > 90`; `jvm_gc_last_duration_ms > 5000`; `jvm_host_mem_util > 95`; `jvm_host_swap_util > 80` | `jmx` | shipped `davis.sap.java.jmx.heap_util`, `.process_cpu_util`, `.gc_pause`, `.host_mem_util`, `.host_swap_util` |
| `state == "BLOCKED"` | `thread` | shipped `davis.sap.java.thread.blocked`, disabled by default (one event per sampled thread); prefer "blocked in N polls" |
| `state == "Stopped"`; `db_conn_used_rate >= 90`; `loglevel == "ERROR"` | `process`; `db_connection`; `default_trace_log` | shipped `davis.sap.java.process.stopped`, `.db_connection.pool_util`, `.default_trace_log.error` |

Hand these to [alert-builder.md](alert-builder.md).

## Documentation

- `jmx`, `threads`, `logs-java`, `dsr`, `powerconnect-java-extractors`,
  `java-data-extraction-user-guide`, `java-troubleshooting`, `java`
- KB 123, 45, 198, 163, 213 — `kb-123-monitoring-sap-cloud-connector`,
  `kb-45-checking-if-the-java-agent-is-deployed-corre`,
  `kb-198-starting-the-powerconnect-java-agent-in-saf`,
  `kb-163-classloader-error-library-sdo-on-agent-star`,
  `kb-213-running-powerconnect-java-alongside-appdyna`

Slugs resolve as
`https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.
