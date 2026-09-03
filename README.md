# minecraft-packs

Self-hosted [packwiz](https://packwiz.infra.link/) modpack definitions, published as a static
site on GitHub Pages:

**<https://mikepea.github.io/minecraft-packs/>**

One repo, many packs. Each directory under `packs/` is served at
`https://mikepea.github.io/minecraft-packs/<pack-name>/pack.toml`, which is the only URL a
client or server ever needs.

## Why this exists

packwiz's `.toml` files *are* a distribution format. `packwiz-installer` (Prism Launcher) and
`itzg/docker-minecraft-server` (`PACKWIZ_URL`) both read them straight off any plain HTTP host,
so publishing a pack needs no Modrinth or CurseForge project — and no waiting on a review queue.
The mod **jars** are still fetched from their upstream CDNs; what we host is the ~25 KB of
metadata that pins exact versions and hashes.

The other win is auto-update. A `.mrpack` is a snapshot you re-upload and re-point at on every
change; a packwiz URL is a live pointer. Push to `main` and the next client launch (and the next
server restart) picks the change up on its own.

## Packs

| Pack | Minecraft | Loader | Mods |
|---|---|---|---|
| [`minecraft-creative-create-1`](packs/minecraft-creative-create-1/) | 1.21.1 | NeoForge 21.1.248 | 57 |

## Consuming a pack

### Server — itzg/docker-minecraft-server

packwiz installs mods but **not** the loader, so `TYPE` / `VERSION` are still needed alongside it:

```yaml
TYPE: "NEOFORGE"
VERSION: "1.21.1"
NEOFORGE_VERSION: "21.1.248"
PACKWIZ_URL: "https://mikepea.github.io/minecraft-packs/minecraft-creative-create-1/pack.toml"
```

The image re-syncs on every container start, so deploying a pack update is a
`kubectl rollout restart` — no manifest edit. Only mods marked `side = "server"` or `"both"` are
installed.

### Client — Prism Launcher

1. Create an instance with the matching Minecraft version and loader.
2. Download [`packwiz-installer-bootstrap.jar`](https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest)
   into the instance's `.minecraft` folder (**Edit Instance → Folder** opens it).
3. **Edit Instance → Settings → Custom commands**, tick *Custom commands*, and set the
   **Pre-launch command** to:

   ```
   "$INST_JAVA" -jar "$INST_MC_DIR/packwiz-installer-bootstrap.jar" -g -s client --pack-folder "$INST_MC_DIR" --bootstrap-main-jar "$INST_MC_DIR/packwiz-installer.jar" https://mikepea.github.io/minecraft-packs/minecraft-creative-create-1/pack.toml
   ```

   The absolute `$INST_MC_DIR` paths matter: Prism runs custom commands in the *launcher's*
   working directory, not the instance's, so the bare `-jar packwiz-installer-bootstrap.jar`
   form found in most tutorials will not find the jar. `--pack-folder` then keeps the mods
   landing in `.minecraft` rather than wherever Prism happened to be started from.

Every launch now syncs the instance to the pack before Minecraft starts. To hand the instance to
someone else, use **Export Instance** — the pre-launch command travels in the zip, so they import
it once and never touch packwiz.

## Working on a pack

All `packwiz` commands run **inside the pack directory**:

```bash
cd packs/minecraft-creative-create-1

packwiz list                        # list mods
packwiz modrinth add <slug|url>     # add a Modrinth mod (resolves deps)
packwiz curseforge add <slug|url>   # add a CurseForge mod
packwiz remove <name>               # remove a mod
packwiz update --all                # bump all mods to newest compatible
packwiz refresh                     # recompute index.toml after manual edits
packwiz serve                       # serve this pack on localhost:8080 to test before pushing
```

### After adding or updating mods

```bash
python3 scripts/check-deps.py     # or: scripts/check-deps.py packs/<one-pack>
```

`packwiz modrinth add` offers to pull a mod's dependencies in, but the offer is easy to decline
or miss, and nothing afterwards re-checks. This asks Modrinth what each *pinned version*
actually requires and diffs it against the pack.

The failure it prevents is deferred and disproportionate: the pack publishes, hashes verify,
clients sync — and then the server dies at mod-loading time, taking down every mod that depended
on the one that could not load. It is network-dependent, so it deliberately isn't part of the
publish path; an upstream API blip should never block a deploy.

### Publishing

1. Change mods, then `packwiz refresh`.
2. Bump `version` in the pack's `pack.toml`.
3. Commit and push to `main`.

That's it — the [Publish packs](.github/workflows/pages.yml) workflow rebuilds and deploys the
site. Clients pick the change up on their next launch; servers on their next restart.

`scripts/build-site.py` re-checks every hash in `pack.toml` and `index.toml` before publishing
and fails the build on a mismatch, so a pack where someone forgot to run `packwiz refresh` never
reaches a client. Run it locally to check your work:

```bash
python3 scripts/build-site.py --base-url https://mikepea.github.io/minecraft-packs
```

Pull requests run that same build without deploying.

### Adding a new pack

```bash
mkdir -p packs/<new-pack> && cd packs/<new-pack>
packwiz init          # answer the prompts; the pack name should match the directory
```

Push it. The workflow discovers any `packs/*/pack.toml` automatically — no config to update —
and the new pack appears on the site with its own URL and ready-made itzg and Prism snippets.

### Sides

`side` in each `mods/*.pw.toml` decides who gets the mod: `both` (default), `client`, or
`server`. Client-only mods left as `both` get installed on the server too, where at best they
are dead weight and at worst they crash it. Worth setting explicitly for anything cosmetic,
map-related, or UI-related.
