#!/usr/bin/env python3
"""Build the static packwiz index site published to GitHub Pages.

Every directory under packs/ that contains a pack.toml is copied verbatim to
_site/<dir>/ -- packwiz-installer and itzg/docker-minecraft-server only ever
need the raw .toml files served over HTTP, so "building" is mostly a copy. On
top of that we generate _site/index.html: a human landing page listing each
pack with the exact URL, itzg env block and Prism pre-launch command needed to
consume it, so handing someone a pack is handing them one link.

Usage: build-site.py --base-url https://user.github.io/repo [--out _site]
"""

import argparse
import hashlib
import html
import json
import shutil
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKS_DIR = REPO / "packs"

# packwiz records the loader as a sibling key of `minecraft` under [versions].
# Map those keys to display names and to the itzg TYPE / *_VERSION env vars.
LOADERS = {
    "neoforge": ("NeoForge", "NEOFORGE", "NEOFORGE_VERSION"),
    "forge": ("Forge", "FORGE", "FORGE_VERSION"),
    "fabric": ("Fabric", "FABRIC", "FABRIC_LOADER_VERSION"),
    "quilt": ("Quilt", "QUILT", "QUILT_LOADER_VERSION"),
}


def digest(path, hash_format):
    try:
        h = hashlib.new(hash_format.replace("-", "_"))
    except ValueError:
        sys.exit(f"{path}: unsupported hash-format {hash_format!r}")
    h.update(path.read_bytes())
    return h.hexdigest()


def verify(directory, data):
    """Re-check the hashes packwiz records, so a stale index can't ship.

    `packwiz refresh` is what normally keeps these in sync; forgetting to run
    it after hand-editing a .pw.toml produces an index the installer will
    reject at the client, which is a miserable place to discover the problem.
    Fail the build here instead.
    """
    index_meta = data.get("index", {})
    index_path = directory / index_meta.get("file", "index.toml")
    if not index_path.is_file():
        sys.exit(f"{directory}: missing {index_path.name}")

    actual = digest(index_path, index_meta.get("hash-format", "sha256"))
    if actual != index_meta.get("hash"):
        sys.exit(
            f"{index_path}: hash {actual} does not match pack.toml "
            f"({index_meta.get('hash')}) -- run `packwiz refresh` in {directory}"
        )

    with index_path.open("rb") as fh:
        index = tomllib.load(fh)
    default_format = index.get("hash-format", "sha256")
    for entry in index.get("files", []):
        target = directory / entry["file"]
        if not target.is_file():
            sys.exit(f"{index_path}: references missing file {entry['file']}")
        actual = digest(target, entry.get("hash-format", default_format))
        if actual != entry["hash"]:
            sys.exit(
                f"{target}: hash {actual} does not match {index_path.name} "
                f"({entry['hash']}) -- run `packwiz refresh` in {directory}"
            )


def discover(base_url):
    """Return metadata for each pack under packs/, sorted by directory name."""
    packs = []
    for pack_toml in sorted(PACKS_DIR.glob("*/pack.toml")):
        directory = pack_toml.parent
        with pack_toml.open("rb") as fh:
            data = tomllib.load(fh)
        verify(directory, data)

        versions = data.get("versions", {})
        minecraft = versions.get("minecraft", "?")
        loader_key = next((k for k in LOADERS if k in versions), None)
        if loader_key is None:
            sys.exit(f"{pack_toml}: no known mod loader in [versions]: {list(versions)}")
        loader_name, itzg_type, itzg_version_var = LOADERS[loader_key]

        packs.append(
            {
                "slug": directory.name,
                "dir": directory,
                "name": data.get("name", directory.name),
                "author": data.get("author", ""),
                "version": data.get("version", "0.0.0"),
                "minecraft": minecraft,
                "loader_name": loader_name,
                "loader_version": versions[loader_key],
                "itzg_type": itzg_type,
                "itzg_version_var": itzg_version_var,
                "mod_count": len(list((directory / "mods").glob("*.pw.toml"))),
                "url": f"{base_url}/{directory.name}/pack.toml",
            }
        )
    return packs


def prism_command(pack):
    return (
        '"$INST_JAVA" -jar "$INST_MC_DIR/packwiz-installer-bootstrap.jar" '
        '-g -s client --pack-folder "$INST_MC_DIR" '
        '--bootstrap-main-jar "$INST_MC_DIR/packwiz-installer.jar" '
        f'{pack["url"]}'
    )


def itzg_env(pack):
    return "\n".join(
        [
            f'TYPE: "{pack["itzg_type"]}"',
            f'VERSION: "{pack["minecraft"]}"',
            f'{pack["itzg_version_var"]}: "{pack["loader_version"]}"',
            f'PACKWIZ_URL: "{pack["url"]}"',
        ]
    )


def render(packs, base_url):
    e = html.escape
    cards = []
    for pack in packs:
        cards.append(
            f"""
    <article class="pack">
      <h2>{e(pack["name"])}</h2>
      <p class="meta">
        <span class="tag">Minecraft {e(pack["minecraft"])}</span>
        <span class="tag">{e(pack["loader_name"])} {e(pack["loader_version"])}</span>
        <span class="tag">{pack["mod_count"]} mods</span>
        <span class="tag">v{e(pack["version"])}</span>
      </p>

      <h3>Pack URL</h3>
      <pre><code>{e(pack["url"])}</code></pre>

      <h3>Server &mdash; itzg/docker-minecraft-server</h3>
      <pre><code>{e(itzg_env(pack))}</code></pre>

      <h3>Client &mdash; Prism Launcher pre-launch command</h3>
      <p>Create an instance on Minecraft {e(pack["minecraft"])} with
      {e(pack["loader_name"])} {e(pack["loader_version"])}, drop
      <a href="https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest">packwiz-installer-bootstrap.jar</a>
      into its <code>.minecraft</code> folder, then set this under
      Edit Instance &rarr; Settings &rarr; Custom commands:</p>
      <pre><code>{e(prism_command(pack))}</code></pre>
    </article>"""
        )

    return f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Minecraft modpacks</title>
<style>
  :root {{ color-scheme: light dark; --fg: #16161a; --bg: #fbfbfd; --muted: #5c5c6b;
           --line: #dcdce4; --card: #fff; --code-bg: #f2f2f6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg: #e6e6ec; --bg: #131317; --muted: #9a9aa8;
             --line: #2c2c34; --card: #1a1a20; --code-bg: #24242c; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0 auto; padding: 2.5rem 1.25rem 4rem; max-width: 52rem;
          background: var(--bg); color: var(--fg);
          font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, sans-serif; }}
  h1 {{ font-size: 1.75rem; margin: 0 0 .35rem; }}
  h2 {{ font-size: 1.25rem; margin: 0 0 .6rem; }}
  h3 {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .07em;
        color: var(--muted); margin: 1.4rem 0 .4rem; }}
  .lede {{ color: var(--muted); margin: 0 0 2.5rem; }}
  .pack {{ background: var(--card); border: 1px solid var(--line);
           border-radius: 10px; padding: 1.4rem 1.5rem; margin-bottom: 1.5rem; }}
  .meta {{ margin: 0; display: flex; flex-wrap: wrap; gap: .4rem; }}
  .tag {{ font-size: .8rem; color: var(--muted); border: 1px solid var(--line);
          border-radius: 999px; padding: .1rem .6rem; }}
  pre {{ background: var(--code-bg); border-radius: 7px; padding: .8rem 1rem;
         overflow-x: auto; margin: 0; }}
  code {{ font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; }}
  p {{ margin: .5rem 0; }}
  a {{ color: inherit; }}
  footer {{ color: var(--muted); font-size: .85rem; margin-top: 2.5rem;
            border-top: 1px solid var(--line); padding-top: 1rem; }}
</style>

<h1>Minecraft modpacks</h1>
<p class="lede">Self-hosted <a href="https://packwiz.infra.link/">packwiz</a> modpack
definitions. Point a client or server at a pack URL below and it stays in sync on
every launch &mdash; no Modrinth or CurseForge project needed. Mod jars are still
fetched from their upstream CDNs.</p>
{"".join(cards)}
<footer>Served from GitHub Pages at <code>{e(base_url)}</code>. Regenerated on every
push to <code>main</code>.</footer>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="public site root, no trailing slash")
    parser.add_argument("--out", default="_site")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    packs = discover(base_url)
    if not packs:
        sys.exit("no packs found under packs/*/pack.toml")

    for pack in packs:
        shutil.copytree(pack["dir"], out / pack["slug"])
        print(f"  {pack['slug']}: {pack['mod_count']} mods -> {pack['url']}")

    (out / "index.html").write_text(render(packs, base_url))
    # Jekyll would otherwise swallow any future dotfile/underscore paths.
    (out / ".nojekyll").write_text("")
    # Machine-readable sibling of index.html, for scripting against the site.
    (out / "packs.json").write_text(
        json.dumps(
            [{k: v for k, v in p.items() if k != "dir"} for p in packs],
            indent=2,
        )
        + "\n"
    )
    print(f"built {len(packs)} pack(s) into {out}/")


if __name__ == "__main__":
    main()
