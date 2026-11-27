#!/usr/bin/env python3
"""Serve powerconnect bundle files, preferring a newer published release.

    python3 <skill folder>/scripts/fetch.py --check   # once per conversation
    python3 <skill folder>/scripts/fetch.py <path>    # e.g. playbooks/idocs.md

The published release is the powerconnect/ folder on the `release` branch
of the ai-skills-library repository (RELEASE_URL). --check downloads its
manifest.json. If the published version is newer than this installed copy,
it downloads every file that differs, verifies each one against the SHA-256
in the manifest and keeps it in a cache. <path> then prints the published
file. In every other case (same or older version, no network, any error) it
prints the installed file. The first output line says which copy it is.

Standard library only; writes nothing outside its cache directory.

Environment, for maintainers only (the assistant must not set these):
  POWERCONNECT_BUNDLE_URL  publish location to use instead of RELEASE_URL
                           (https, or http on localhost for tests)
  POWERCONNECT_OFFLINE=1   never use the network
  POWERCONNECT_CACHE_DIR   cache directory (default ~/.cache/powerconnect-skill)
"""
import hashlib
import json
import os
import posixpath
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

RELEASE_URL = "https://raw.githubusercontent.com/Rhondos-LLC/ai-skills-library/release/powerconnect/"
STATE_TTL = 6 * 3600   # seconds before a file read re-checks the published release
TIMEOUT = 10           # seconds per request
MAX_BYTES = 1000000    # largest file accepted
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.abspath(__file__)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class FetchError(Exception):
    pass


def digest(data):
    """SHA-256 of the file with CRLF normalised, so Windows checkouts match.
    Must stay identical to digest() in tools/build_powerconnect_manifest.py."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def parse_version(text):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def installed_version():
    try:
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            frontmatter = f.read().split("\n---", 1)[0]
    except OSError:
        return None
    m = re.search(r'^\s*version:\s*"?(\d+\.\d+\.\d+)"?\s*$', frontmatter, re.M)
    return m.group(1) if m else None


def is_newer(manifest):
    published = parse_version(manifest["version"])
    installed = parse_version(installed_version())
    return published is not None and (installed is None or published > installed)


def release_url():
    url = os.environ.get("POWERCONNECT_BUNDLE_URL") or RELEASE_URL
    parts = urllib.parse.urlsplit(url)
    on_localhost = parts.scheme == "http" and parts.hostname in ("localhost", "127.0.0.1")
    if not (parts.scheme == "https" or on_localhost) or parts.query or parts.fragment:
        raise FetchError("POWERCONNECT_BUNDLE_URL must be an https URL")
    return url if url.endswith("/") else url + "/"


# --- network ---------------------------------------------------------------

def http_get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "powerconnect-skill"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code} for {url}")
    except (urllib.error.URLError, OSError) as e:
        # Some Python installs have no CA certificates; curl uses the system's.
        reason = getattr(e, "reason", e)
        if not isinstance(reason, ssl.SSLError) or shutil.which("curl") is None:
            raise FetchError(f"{url}: {reason}")
        result = subprocess.run(
            ["curl", "-fsSL", "--proto", "=https,http", "--proto-redir", "=https",
             "--max-time", str(TIMEOUT), "--max-filesize", str(MAX_BYTES),
             "-A", "powerconnect-skill", url],
            capture_output=True)
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", "replace").strip() or reason
            raise FetchError(f"{url}: {detail} (via curl)")
        data = result.stdout
    if len(data) > MAX_BYTES:
        raise FetchError(f"{url}: larger than {MAX_BYTES} bytes")
    return data


def is_bundle_path(rel):
    return (isinstance(rel, str) and rel.endswith(".md") and "\\" not in rel
            and not rel.startswith(("/", "../")) and posixpath.normpath(rel) == rel)


def validate_manifest(obj):
    if not isinstance(obj, dict):
        raise FetchError("manifest.json is not an object")
    version, files = obj.get("version"), obj.get("files")
    if not isinstance(version, str) or parse_version(version) is None:
        raise FetchError("manifest.json has no valid version")
    if not isinstance(files, dict) or not files:
        raise FetchError("manifest.json has no files")
    for rel, sha in files.items():
        if not is_bundle_path(rel) or not isinstance(sha, str) or not SHA256.match(sha):
            raise FetchError(f"manifest.json has an invalid entry: {rel!r}")
    return {"version": version, "files": files}


# --- cache -----------------------------------------------------------------

def cache_dir():
    default = os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"),
        "powerconnect-skill")
    for candidate in (os.environ.get("POWERCONNECT_CACHE_DIR") or default,
                      os.path.join(tempfile.gettempdir(), "powerconnect-skill")):
        try:
            os.makedirs(os.path.join(candidate, "files"), exist_ok=True)
            return candidate
        except OSError:
            continue
    return None


def write_atomic(path, data):
    """Best effort: the cache only saves downloads, so failures are ignored."""
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except OSError:
        pass


def load_state(cache, base):
    if not cache:
        return None
    try:
        with open(os.path.join(cache, "state.json"), encoding="utf-8") as f:
            state = json.load(f)
        age = time.time() - float(state["checked_at"])
        if state.get("base_url") != base or not 0 <= age < STATE_TTL:
            return None
        if state.get("manifest") is not None:
            state["manifest"] = validate_manifest(state["manifest"])
        return state
    except (OSError, ValueError, KeyError, TypeError, FetchError):
        return None


# --- bundle files ----------------------------------------------------------

def read_installed(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as f:
        return f.read()


def installed_digest(rel):
    try:
        return digest(read_installed(rel))
    except OSError:
        return None


def changed_files(manifest):
    return [rel for rel, sha in sorted(manifest["files"].items())
            if installed_digest(rel) != sha]


def get_published(base, rel, sha, cache):
    cached = os.path.join(cache, "files", sha) if cache else None
    if cached:
        try:
            with open(cached, "rb") as f:
                data = f.read()
            if digest(data) == sha:
                return data
        except OSError:
            pass
    data = http_get(base + urllib.parse.quote(rel))
    if digest(data) != sha:
        raise FetchError(f"{rel}: download does not match the manifest checksum")
    if cached:
        write_atomic(cached, data)
    return data


def check(base, cache):
    """Fetch the published manifest; if it is newer, download every changed
    file up front so the conversation never mixes two versions."""
    state = {"base_url": base, "checked_at": time.time(), "manifest": None, "error": None}
    if os.environ.get("POWERCONNECT_OFFLINE") == "1":
        state["error"] = "offline mode is on"
        return state
    try:
        manifest = validate_manifest(json.loads(http_get(base + "manifest.json").decode("utf-8")))
        if is_newer(manifest):
            if not cache:
                raise FetchError("no writable cache directory for the published files")
            for rel in changed_files(manifest):
                get_published(base, rel, manifest["files"][rel], cache)
        state["manifest"] = manifest
    except (FetchError, ValueError, UnicodeDecodeError) as e:
        state["error"] = str(e) if isinstance(e, FetchError) else "manifest.json is not valid JSON"
    if cache:
        write_atomic(os.path.join(cache, "state.json"), json.dumps(state).encode("utf-8"))
    return state


def strip_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            return text[end + 4:].lstrip("\n")
    return text


# --- commands --------------------------------------------------------------

def cmd_check():
    installed = installed_version() or "unknown"
    direct = "Read the bundle files directly."
    try:
        base = release_url()
    except FetchError as e:
        print(f"powerconnect bundle: using installed {installed}; {e}. {direct}")
        return 0
    cache = cache_dir()
    state = check(base, cache)
    manifest = state["manifest"]
    if manifest is None:
        print(f"powerconnect bundle: using installed {installed}; the published release "
              f"could not be used ({state['error']}). {direct}")
        return 0
    if not is_newer(manifest):
        same = parse_version(manifest["version"]) == parse_version(installed)
        relation = "is current" if same else "is newer than the published release"
        print(f"powerconnect bundle: installed {installed} {relation} "
              f"(published {manifest['version']}). {direct}")
        return 0
    changed = changed_files(manifest)
    router = None
    if "SKILL.md" in changed:
        try:
            sha = manifest["files"]["SKILL.md"]
            router = strip_frontmatter(get_published(base, "SKILL.md", sha, cache).decode("utf-8"))
        except (FetchError, UnicodeDecodeError) as e:
            print(f"powerconnect bundle: using installed {installed}; the published router "
                  f"could not be read ({e}). {direct}")
            return 0
    print(f"powerconnect bundle: published {manifest['version']} is newer than installed "
          f"{installed}; using the published release.")
    print("For the rest of this conversation, read every bundle file (playbooks, backends, "
          "reference) through this script instead of opening it:")
    print(f"  python3 {shlex.quote(SCRIPT)} <path relative to the skill folder>")
    print("Changed since the installed version: " + ", ".join(
        rel + ("" if installed_digest(rel) else " (new)") for rel in changed))
    if router is not None:
        print("\nThe router changed. Follow the router below instead of the SKILL.md you "
              "loaded (its frontmatter is omitted).\n")
        sys.stdout.flush()
        sys.stdout.buffer.write(router.encode("utf-8"))
    return 0


def normalise(path):
    if os.path.isabs(path):
        path = os.path.relpath(path, ROOT)
    rel = posixpath.normpath(path.replace("\\", "/"))
    if not is_bundle_path(rel):
        raise FetchError(f"{path}: give a .md path inside the skill folder, "
                         "relative to it (for example playbooks/idocs.md)")
    return rel


def emit(rel, source, data):
    sys.stdout.flush()
    sys.stdout.buffer.write(f"<!-- powerconnect {rel}: {source} -->\n".encode("utf-8") + data)
    if not data.endswith(b"\n"):
        sys.stdout.buffer.write(b"\n")
    return 0


def cmd_read(path):
    try:
        rel = normalise(path)
    except FetchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    installed = installed_version() or "unknown"
    note = f"installed {installed}"
    try:
        base = release_url()
        cache = cache_dir()
        state = load_state(cache, base) or check(base, cache)
        manifest = state["manifest"]
        if manifest is None:
            note += f"; published release not used ({state['error']})"
        elif is_newer(manifest):
            sha = manifest["files"].get(rel)
            if sha is None:
                note += f"; not part of published {manifest['version']}"
            elif installed_digest(rel) == sha:
                note += f", identical to published {manifest['version']}"
            else:
                data = get_published(base, rel, sha, cache)
                return emit(rel, f"published {manifest['version']}", data)
    except Exception as e:  # any failure here falls back to the installed copy
        note += f"; published file could not be used ({e})"
    try:
        return emit(rel, note, read_installed(rel))
    except OSError:
        print(f"error: {rel} is not in the installed bundle ({note})", file=sys.stderr)
        return 1


def main(argv):
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    if argv[0] != "--check":
        return cmd_read(argv[0])
    try:
        return cmd_check()
    except Exception as e:  # never block the investigation on an update check
        print(f"powerconnect bundle: using installed {installed_version() or 'unknown'}; "
              f"the update check failed ({e}). Read the bundle files directly.")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
