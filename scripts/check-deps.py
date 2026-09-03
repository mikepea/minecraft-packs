#!/usr/bin/env python3
"""Check every pack for Modrinth-declared required dependencies it is missing.

`packwiz modrinth add` offers to pull a mod's dependencies in, but the offer is
easy to decline or miss, and nothing afterwards re-checks. The failure mode is
nasty and deferred: the pack publishes fine, hashes verify fine, clients sync
fine, and then the *server* dies at mod-loading time -- often taking unrelated
mods down with it, since one unloadable mod fails everything that depends on it.

This asks Modrinth what each pinned version actually requires and compares that
against what the pack contains. Network-dependent, so it is deliberately NOT
part of the publish path (scripts/build-site.py) -- an upstream API blip should
never block a deploy. Run it when adding or updating mods.

Usage: check-deps.py [pack-dir ...]     (default: every pack under packs/)
Exit status: 0 if nothing is missing, 1 otherwise.
"""

import json
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
API = "https://api.modrinth.com/v2"
UA = "mikepea/minecraft-packs dep-check (+https://github.com/mikepea/minecraft-packs)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def check(pack_dir):
    """Return the number of missing required dependencies for one pack."""
    installed = {}
    for meta in sorted((pack_dir / "mods").glob("*.pw.toml")):
        data = tomllib.loads(meta.read_text())
        source = data.get("update", {}).get("modrinth")
        if source:
            installed[source["mod-id"]] = (data["name"], source["version"])

    print(f"{pack_dir.name}: {len(installed)} Modrinth-sourced mods")
    if not installed:
        return 0

    # One bulk call for the exact pinned versions -- their dependency lists are
    # version-specific, so querying the *project* would give the wrong answer.
    ids = urllib.parse.quote(json.dumps([v[1] for v in installed.values()]))
    versions = get(f"{API}/versions?ids={ids}")

    missing = {}
    for version in versions:
        owner = installed.get(version["project_id"])
        if not owner:
            continue
        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") != "required":
                continue
            dep_id = dep.get("project_id")
            if dep_id and dep_id not in installed:
                missing.setdefault(dep_id, set()).add(owner[0])

    if not missing:
        print("  no missing required dependencies\n")
        return 0

    print(f"  MISSING {len(missing)} required dependency project(s):")
    for dep_id, wanted_by in missing.items():
        slug = get(f"{API}/project/{dep_id}")
        print(f"    {slug['title']}  (packwiz modrinth add {slug['slug']})")
        print(f"        required by: {', '.join(sorted(wanted_by))}")
    print()
    return len(missing)


def main():
    if len(sys.argv) > 1:
        packs = [Path(a) for a in sys.argv[1:]]
    else:
        packs = sorted(p.parent for p in (REPO / "packs").glob("*/pack.toml"))

    try:
        total = sum(check(p) for p in packs)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        sys.exit(f"Modrinth API request failed: {exc}")

    if total:
        sys.exit(f"{total} missing required dependency project(s) -- see above")
    print("All packs have their required dependencies.")


if __name__ == "__main__":
    main()
