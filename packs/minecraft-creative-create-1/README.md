# minecraft-creative-create-1

[packwiz](https://packwiz.infra.link/) source for the **NeoForge** Create-focused modpack that
runs on the `minecraft-creative-create-1` server in the
[talos-homelab](https://github.com/mikepea/talos-homelab) cluster
(`apps/base/minecraft-creative-create-1/`).

**Pack URL:** <https://mikepea.github.io/minecraft-packs/minecraft-creative-create-1/pack.toml>

See the [repo README](../../README.md) for how to point a server or a Prism instance at that URL,
and for the publish loop.

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

### Sides

56 mods are `side = "both"` and 2 are `side = "server"`; nothing is marked `client`. Xaero's
World Map is a client-side mod currently declared `both`, so the server installs it needlessly —
worth changing to `side = "client"` (then `packwiz refresh`) along with any other client-only
additions.
