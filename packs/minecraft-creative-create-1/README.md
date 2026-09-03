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
Mechanicals Lib, Sable, Player Animator, GlitchCore, Kotlin for Forge), Iron's Spells 'n
Spellbooks, Farmer's Delight, Sophisticated Backpacks, and Xaero's World Map. `packwiz list`
for the full set.

Kotlin for Forge looks out of place in a Create pack and is easy to remove by mistake: Create
Slice & Dice was **rewritten in Kotlin at 4.3.0**, so from that version on it loads through the
`kotlinforforge` language provider rather than `javafml`. Without it Slice & Dice does not load
at all, which crashes the server. `scripts/check-deps.py` catches this class of gap.

That same rewrite is why **Create Slice & Dice: Crop Accelerator is not in the pack**. It links
against `SprinkleBehaviour`, a class that existed in 4.2.4 and was removed when 4.3.0 rewrote
the sprinkler package, so it dies with `NoClassDefFoundError` on any 4.3.x. It has had exactly
one release (2026-05-30) and no update since. Modrinth metadata cannot catch this — the addon
declares `sliceanddice 4.0 or above`, which 4.3.3 satisfies on paper. Re-adding it means pinning
Slice & Dice back to 4.2.4 (and then Kotlin for Forge is unnecessary).

### Wanted but not (yet) included

Not available on Modrinth for 1.21.1/NeoForge — candidates for a CurseForge source later:
CBC Advanced Technology, Create Confectionery, Create Fluid Logistics, Create Bells and Whistles,
Steam 'n' Rails.

### Sides

| `side` | Count | |
|---|---|---|
| `both` | 56 | |
| `client` | 1 | Xaero's World Map |
| `server` | 1 | Create: Liquid Fuel |

Set `side = "client"` on anything purely cosmetic, map-related, or UI-related as it gets added —
otherwise the default `both` puts it on the server, where it is dead weight at best and a crash
at worst.
