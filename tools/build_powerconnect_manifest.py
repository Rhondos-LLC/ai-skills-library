#!/usr/bin/env python3
"""Build powerconnect/manifest.json: the bundle version and a SHA-256 per
file the assistant reads. The installed skill's scripts/fetch.py downloads
the manifest published on the `release` branch, compares it with the
installed copy and uses the published files when they are newer.

Run from the repository root after any change under powerconnect/:

    python3 tools/build_powerconnect_manifest.py            # write it
    python3 tools/build_powerconnect_manifest.py --check    # exit 1 if stale

The checksum function must stay identical to digest() in
powerconnect/scripts/fetch.py.
"""
import hashlib
import json
import os
import re
import sys

ROOT = "powerconnect"
# Files the assistant never reads through fetch.py: human docs, the
# customer's own profile, and the manifest itself.
EXCLUDE = {"README.md", "customer-profile.md", "manifest.json"}


def digest(data):
    """SHA-256 of the file with CRLF normalised, so Windows checkouts match."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def bundle_version(root):
    with open(os.path.join(root, "SKILL.md"), encoding="utf-8") as f:
        frontmatter = f.read().split("\n---", 1)[0]
    m = re.search(r'^\s*version:\s*"?(\d+\.\d+\.\d+)"?\s*$', frontmatter, re.M)
    if not m:
        raise SystemExit(f"{root}/SKILL.md: no metadata.version like \"1.2.3\"")
    return m.group(1)


def build_manifest(root=ROOT):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            if not name.endswith(".md") or rel in EXCLUDE:
                continue
            with open(os.path.join(dirpath, name), "rb") as f:
                files[rel] = digest(f.read())
    manifest = {
        "bundle": "powerconnect",
        "version": bundle_version(root),
        "files": dict(sorted(files.items())),
    }
    return json.dumps(manifest, indent=2) + "\n"


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    root = args[0] if args else ROOT
    path = os.path.join(root, "manifest.json")
    want = build_manifest(root)
    try:
        with open(path, encoding="utf-8") as f:
            have = f.read()
    except OSError:
        have = None
    if check:
        if have != want:
            print(f"{path} is stale; run python3 tools/build_powerconnect_manifest.py")
            return 1
        return 0
    if have != want:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(want)
        print(f"wrote {path} ({json.loads(want)['version']}, {len(json.loads(want)['files'])} files)")
    else:
        print(f"{path} is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
