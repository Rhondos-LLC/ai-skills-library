#!/usr/bin/env python3
"""Consistency checks for the powerconnect bundle. Run from the repository root:

    python3 tools/check_powerconnect_bundle.py

Exits non-zero if any check fails. It does not run queries; it only checks
that the files agree with each other.
"""
import glob
import os
import re
import sys

ROOT = "powerconnect"
PLACEHOLDER_LINKS = {"other-playbook.md", "url.md"}
errors, warnings = [], []


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


skill = read(os.path.join(ROOT, "SKILL.md"))

# 1. Frontmatter description within the Agent Skills limit.
m = re.search(r"description: >\n(.*?)\nmetadata", skill, re.S)
if not m:
    errors.append("SKILL.md: no folded 'description: >' block found")
else:
    n = len(" ".join(m.group(1).split()))
    if n > 1024:
        errors.append(f"SKILL.md: description is {n} characters (limit 1024)")

# 2. Every routed playbook exists; every playbook is routed.
routed = set(re.findall(r"\(playbooks/([a-z0-9-]+\.md)\)", skill))
have = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "playbooks", "*.md"))}
for f in sorted(routed - have):
    errors.append(f"SKILL.md routes to playbooks/{f}, which does not exist")
for f in sorted(have - routed - {"_template.md"}):
    errors.append(f"playbooks/{f} is not linked from SKILL.md")

# 3. Relative Markdown links resolve.
for path in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
    for link in re.findall(r"\]\(([^)#\s]+?\.md)(?:#[^)]*)?\)", read(path)):
        if link.startswith("http") or link in PLACEHOLDER_LINKS:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), link))
        if not os.path.exists(target):
            errors.append(f"{path}: broken link {link}")

# 4. Slugs cited under '## Documentation' exist in the docs index.
slugs = set(re.findall(r"— `([^`]+)`", read(os.path.join(ROOT, "reference", "docs-index.md"))))
for path in sorted(glob.glob(os.path.join(ROOT, "playbooks", "*.md"))):
    text = read(path)
    name = os.path.basename(path)
    if name == "_template.md":
        continue
    i = text.find("## Documentation")
    if i >= 0:
        for slug in re.findall(r"`([a-z0-9][a-z0-9_.-]{3,})`", text[i:]):
            if slug not in slugs and not slug.endswith(".md"):
                errors.append(f"{path}: documentation slug not in docs-index.md: {slug}")
    # 5. DQL conventions learned from live validation.
    for block in re.findall(r"```dql\n(.*?)```", text, re.S):
        if re.search(r'\bin\(\s*[\w.`]+\s*,\s*"', block):
            errors.append(f"{path}: in() without braces; write in(field, {{\"a\", \"b\"}})")
        if "fetch logs" in block and "from:" not in block:
            errors.append(f"{path}: DQL block without an explicit from:")
        if re.search(r"startsWith\(dt\.source_entity_name", block):
            warnings.append(f"{path}: prefix filter on dt.source_entity_name does not prune the scan")
    # 6. SPL must stay read-only.
    for block in re.findall(r"```spl\n(.*?)```", text, re.S):
        if re.search(r"\|\s*(delete|outputlookup|collect|sendemail)\b", block):
            errors.append(f"{path}: SPL block uses a writing command")
    lines = len(text.splitlines())
    if lines > 270:
        warnings.append(f"{path}: {lines} lines; consider splitting")

# 7. The published manifest matches the files, and the fetch script is pinned
#    to the release branch with the same checksum function.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_powerconnect_manifest as manifest_builder  # noqa: E402

try:
    have_manifest = read(os.path.join(ROOT, "manifest.json"))
except OSError:
    have_manifest = None
if have_manifest != manifest_builder.build_manifest(ROOT):
    errors.append("manifest.json is missing or stale; run python3 tools/build_powerconnect_manifest.py")
fetch_py = read(os.path.join(ROOT, "scripts", "fetch.py"))
pinned = re.search(r'^RELEASE_URL = "([^"]+)"$', fetch_py, re.M)
if not pinned or not pinned.group(1).startswith("https://") \
        or not pinned.group(1).endswith("/ai-skills-library/release/powerconnect/"):
    errors.append("scripts/fetch.py: RELEASE_URL must point at the release branch over https")
def digest_src(text):
    return re.search(r"def digest\(data\):.*?return [^\n]+", text, re.S)


builder_digest = digest_src(read(os.path.join("tools", "build_powerconnect_manifest.py")))
fetch_digest = digest_src(fetch_py)
if not builder_digest or not fetch_digest or \
        builder_digest.group(0).splitlines()[-1] != fetch_digest.group(0).splitlines()[-1]:
    errors.append("digest() differs between scripts/fetch.py and the manifest builder")

for w in warnings:
    print("warning:", w)
for e in errors:
    print("ERROR:", e)
print(f"{len(have) - 1} playbooks, {len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
