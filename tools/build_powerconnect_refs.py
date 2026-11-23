import re, sys, os, collections
docs, out = sys.argv[1], sys.argv[2]
P = "powerconnect-for-sap-solutions__"
def rd(n): return open(os.path.join(docs, P + n + ".md"), encoding="utf-8").read()
def cells(line): return [c.strip().replace("\\_", "_").replace("\\&", "&").replace("\\>", ">").replace("\\<", "<") for c in line.strip().strip("|").split("|")]
BASE = "https://docs.rhondos.com/powerconnect-for-sap-solutions/"

# ---- event-types.md
rows = []
for l in rd("summary-of-extractors-and-event_type-s").splitlines():
    if not l.startswith("|"): continue
    c = cells(l)
    if len(c) < 6 or c[0].lower().startswith("extractor") or set(c[0]) <= set("-: "): continue
    m = re.search(r"\((https://[^)]+)\)", c[5])
    slug = m.group(1).replace(BASE, "") if m else ""
    rows.append((c[0], c[1], c[2], "yes" if "Yes" in c[4] else "", slug))
et = collections.OrderedDict()
for l in rd("list-of-event-types").splitlines():
    if not l.startswith("|"): continue
    c = cells(l)
    if len(c) < 3 or c[0] in ("Event Type", "") or set(c[0]) <= set("-: "): continue
    et.setdefault(c[0], [])
    if c[2] and c[2] not in et[c[0]]: et[c[0]].append(c[2])
abap = {r[0] for r in rows}
with open(os.path.join(out, "event-types.md"), "w", encoding="utf-8") as f:
    f.write("# PowerConnect event type catalog\n\n")
    f.write("Generated from the product documentation (\"Summary of Extractors and EVENT_TYPE(s)\" and \"List of Event Types\"). "
            "Use it to find which event type carries the data for a question. Search this file; do not read it end to end.\n\n"
            "- **Default = yes** means the extractor is active out of the box. Anything else must be enabled by an administrator, so its absence is normal.\n"
            "- **Docs** is the page slug: open `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md`.\n"
            "- Whether a type is actually collected on a given system is decided by Step 0 and the explorer playbook, never by this list.\n\n")
    f.write("## ABAP extractors\n\n| Event type | Category | What it carries | Default | Docs |\n|---|---|---|---|---|\n")
    for r in rows: f.write("| `%s` | %s | %s | %s | %s |\n" % r)
    f.write("\n## Java, Cloud and other event types\n\nLowercase event types come from the Java and Cloud agents. The second column lists the shipped Splunk dashboards that read each type, which indicates its purpose.\n\n| Event type | Read by dashboards |\n|---|---|\n")
    for k, v in et.items():
        if k in abap or re.fullmatch(r"[A-Z0-9_/]+", k): continue
        f.write("| `%s` | %s |\n" % (k, "; ".join(v[:6])))
    extra = [k for k in et if re.fullmatch(r"[A-Z0-9_/]+", k) and k not in abap]
    f.write("\n## ABAP event types referenced by dashboards but not in the extractor summary\n\nSub-types and newer extractors.\n\n| Event type | Read by dashboards |\n|---|---|\n")
    for k in extra: f.write("| `%s` | %s |\n" % (k, "; ".join(et[k][:6])))

# ---- dashboards-splunk.md  (event type -> dashboards with menu path)
dm = collections.OrderedDict()
for l in rd("list-of-event-types").splitlines():
    if not l.startswith("|"): continue
    c = cells(l)
    if len(c) < 4 or c[0] in ("Event Type", "") or set(c[0]) <= set("-: "): continue
    menu = c[3]
    m = re.search(r"default: ([^;]+)", menu)
    menu = m.group(1).strip() if m else (menu.split(";")[0].split(":", 1)[-1].strip() if menu else "")
    key = (c[2], c[1])
    d = dm.setdefault(key, {"menu": menu, "types": []})
    if menu and not d["menu"]: d["menu"] = menu
    if c[0] not in d["types"]: d["types"].append(c[0])
with open(os.path.join(out, "dashboards-splunk.md"), "w", encoding="utf-8") as f:
    f.write("# Shipped Splunk dashboards and the event types they read\n\nGenerated from the product documentation (\"List of Event Types\"). Search this file by topic, dashboard name or event type. "
            "**Menu path** is where the dashboard sits in the PowerConnect Splunk app; blank means it is reached by drill-down or from System Analysis. "
            "Panel-level detail is in the documentation page `list-of-dashboards.md`.\n\n| Dashboard | View ID | Menu path | Event types |\n|---|---|---|---|\n")
    for (name, vid), d in sorted(dm.items(), key=lambda x: (x[1]["menu"] == "", x[1]["menu"], x[0][0])):
        f.write("| %s | `%s` | %s | %s |\n" % (name, vid, d["menu"], ", ".join(d["types"])))

# ---- dashboards-dynatrace.md
with open(os.path.join(out, "dashboards-dynatrace.md"), "w", encoding="utf-8") as f:
    f.write("# Shipped Dynatrace dashboards\n\nGenerated from the product documentation (\"List of Dashboards - Dynatrace\"). These are imported from the PowerConnect for SAP Dynatrace app under **Import Dashboards**.\n\n")
    for l in rd("list-of-dashboards-dynatrace").splitlines():
        if l.startswith("|") or l.startswith("## "):
            if l.startswith("|"):
                c = cells(l)
                if set(c[0]) <= set("-: "): f.write("|" + "---|" * len(c) + "\n")
                else: f.write("| " + " | ".join(c) + " |\n")
            else: f.write("\n" + l + "\n\n")

# ---- alerts-dynatrace.md
with open(os.path.join(out, "alerts-dynatrace.md"), "w", encoding="utf-8") as f:
    f.write("# Shipped Dynatrace alerts and their matchers\n\nGenerated from the product documentation (\"List of Alerts - Dynatrace\"). Each alert is a Davis event processor in the OpenPipeline log pipeline; a record that matches raises a `CUSTOM_ALERT` Davis event on the SAP instance entity. "
            "The matchers are the most reliable published source of Dynatrace field names, state values and default thresholds. Backslashes inside string literals are doubled here so the matchers run as DQL.\n")
    for l in rd("list-of-alerts-dynatrace").splitlines():
        if l.startswith("## "): f.write("\n" + l + "\n\n")
        elif l.startswith("|"):
            c = cells(l)
            if set(c[0]) <= set("-: "): f.write("|" + "---|" * len(c) + "\n")
            else: f.write("| " + " | ".join(re.sub(r'(?<!\\)\\(?=[A-Za-z])', r'\\\\', x.replace("**", "")) for x in c) + " |\n")

# ---- detections-splunk-es.md
with open(os.path.join(out, "detections-splunk-es.md"), "w", encoding="utf-8") as f:
    f.write("# Splunk Enterprise Security content pack — correlation searches\n\nGenerated from the product documentation (\"List of Correlation Searches\"). Each row is a shipped detection, the CIM data model it uses and the PowerConnect event type it reads.\n\n")
    for l in rd("list-of-correlation-searches").splitlines():
        if l.startswith("|"):
            c = cells(l)
            if set(c[0]) <= set("-: "): f.write("|" + "---|" * len(c) + "\n")
            else: f.write("| " + " | ".join(x.replace("++", "").replace("**", "") for x in c) + " |\n")

# ---- docs-index.md
idx = []
for l in open(os.path.join(docs, "..", "llms.txt"), encoding="utf-8"):
    m = re.match(r"\* \[(.*)\]\(https://docs\.rhondos\.com/(.*)\.md\)", l.strip())
    if m: idx.append((m.group(1).replace("\\", ""), m.group(2).replace("powerconnect-for-sap-solutions/", "")))
slugs_ev = {r[4].rstrip("-") for r in rows if r[4]}
def group(t, s):
    if re.match(r"kb-?\d", s) or t.startswith("KB"): return "Knowledge base articles"
    if "release-notes" in s or "release notes" in t.lower(): return "Release notes"
    if re.search(r"install|uninstall|upgrad|import-the-agent|prerequisite|post-installation|activate-business|assign-powerconnect|upload-powerconnect|configure-powerconnect-license|apply-powerconnect-license|load-", s): return "Installation, upgrade and uninstallation"
    if re.search(r"configuring|connection|ssl|create-|proxy|systemd|certificat.*ui|authentication|clustering|checkpoint|object-storage|single-sign", s): return "Connection and agent configuration"
    if re.search(r"dashboard|alert|kpi|correlation|content-pack|enterprise-security|splunk-app|dynatrace-app|app-setup|ai-agent|role-based|system-overview|davis|extension", s): return "Apps, dashboards, alerts and security content"
    if re.search(r"troubleshoot|faq|support|matrix|end-of-support|roadmap|open-source|compatib|customer|onboarding|add-an-idea|software|sign-in", s): return "Support, compatibility and general"
    return "Event types, extractors, inputs and other reference"
g = collections.OrderedDict((k, []) for k in ["Support, compatibility and general", "Installation, upgrade and uninstallation", "Connection and agent configuration", "Apps, dashboards, alerts and security content", "Knowledge base articles", "Event types, extractors, inputs and other reference", "Release notes"])
for t, s in idx: g[group(t, s)].append((t, s))
with open(os.path.join(out, "docs-index.md"), "w", encoding="utf-8") as f:
    f.write("# docs.rhondos.com page index (snapshot)\n\nGenerated from `https://docs.rhondos.com/llms.txt`, which is the live, authoritative index; fetch that when you can and use this snapshot when you cannot. "
            "Search this file by keyword; do not read it end to end.\n\nEvery page is available as Markdown at `https://docs.rhondos.com/powerconnect-for-sap-solutions/<slug>.md` (drop `.md` for the human page). The grouping below is a rough aid, not the site's own navigation.\n")
    for k, v in g.items():
        f.write("\n## %s (%d)\n\n" % (k, len(v)))
        for t, s in sorted(v, key=lambda x: x[0].lower()): f.write("- %s — `%s`\n" % (t, s))
print({k: len(v) for k, v in g.items()}, len(rows), len(et))
