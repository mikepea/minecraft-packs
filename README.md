# minecraft-creative-create-1 modpack

[packwiz](https://packwiz.infra.link/) source for the **NeoForge** Create-focused modpack that
runs on the `minecraft-creative-create-1` server in the
[talos-homelab](https://github.com/mikepea/talos-homelab) cluster
(`apps/base/minecraft-creative-create-1/`). The exported `.mrpack` is published to Modrinth; the
`itzg/minecraft-server` container installs it on boot via `TYPE=MODRINTH` + `MODRINTH_MODPACK`.

## Versions

| | |
|---|---|
| Minecraft | **1.21.1** |
| Loader | **NeoForge 21.1.248** |
| Java | **21** (server image `itzg/minecraft-server:java21`) |

**Why 1.21.1 and not the latest?** The Create mod's newest NeoForge build tops out at MC 1.21.1
(`create 6.0.10+mc1.21.1`) — it has no 26.2 build. The whole pack is pinned to what Create + its
add-ons actually support.

## Contents

~58 mods: the full Create Aeronautics suite, Create Big Cannons, and a large set of Create
add-ons, plus their libraries (Architectury, Curios, GeckoLib, DragonLib, Moonlight, Iron's Lib,
Mechanicals Lib, Sable, Player Animator, GlitchCore), Iron's Spells 'n Spellbooks, Farmer's
Delight, Sophisticated Backpacks, and Xaero's World Map. `packwiz list` for the full set.

### Wanted but not (yet) included

Not available on Modrinth for 1.21.1/NeoForge — candidates for a CurseForge source later:
CBC Advanced Technology, Create Confectionery, Create Fluid Logistics, Create Bells and Whistles,
Steam 'n' Rails.

## Working with the pack

```bash
packwiz list                        # list mods
packwiz modrinth add <slug|url>     # add a Modrinth mod (resolves deps)
packwiz curseforge add <slug|url>   # add a CurseForge mod
packwiz remove <name>               # remove a mod
packwiz update --all                # bump all mods to newest compatible
packwiz refresh                     # recompute index.toml after manual edits
packwiz modrinth export             # -> minecraft-creative-create-1-<version>.mrpack (gitignored)
```

## Publish / deploy loop

1. Edit mods (add/remove/update) → `packwiz refresh`.
2. Bump `version` in `pack.toml`, commit.
3. `packwiz modrinth export` → new `.mrpack`.
4. Upload the `.mrpack` as a new version to the Modrinth modpack project (visibility: unlisted).
5. Set `MODRINTH_MODPACK` in the server's `deployment.yaml` to that version's URL, then
   `kubectl -n minecraft rollout restart deploy/minecraft-creative-create-1` (itzg reinstalls
   the pack on boot).

The `.mrpack` is a build artifact (gitignored) — the TOML files here are the source of truth.
