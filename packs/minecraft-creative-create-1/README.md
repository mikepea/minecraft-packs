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

~67 mods: the full Create Aeronautics suite, Create Big Cannons, the Create: Numismatics
economy suite, Create Nuclear, and a large set of Create add-ons, plus their libraries
(Architectury, Curios, GeckoLib, DragonLib, Moonlight, Iron's Lib, Mechanicals Lib, Sable,
Player Animator, GlitchCore, Kotlin for Forge), Iron's Spells 'n Spellbooks, Farmer's Delight,
Sophisticated Backpacks, and Xaero's World Map. `packwiz list` for the full set.

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

### Dependencies that come from inside another jar

`scripts/check-deps.py` reads Modrinth metadata, which only lists *project* dependencies. Some
mods depend on modIds that no pack entry provides directly because they ship nested (JiJ) inside
a jar the pack already has. Do not "fix" these by adding a standalone copy, and do not assume the
parent is removable:

| modId | Comes from | Needed by |
|---|---|---|
| `ponder` | `create` (nested `ponder-neoforge-1.0.82+mc1.21.1.jar`) | Create Deep Seas |
| `simulated`, `offroad`, `aeronautics` | `create-aeronautics` 1.3.1 (three nested jars) | Create: Tracks+, Create Deep Seas |

Create: Tracks+ is the sharp edge here: its Modrinth metadata declares only Create and Create
Aeronautics, but its `neoforge.mods.toml` also requires `simulated` and `offroad`. Both are
satisfied only because Create Aeronautics bundles them. **Dropping Create Aeronautics would
silently break Tracks+ and Deep Seas.**

### Version pins worth knowing

**Create Nuclear** has no stable channel for 1.21.1 — every 1.21.1/NeoForge build on Modrinth is
marked `beta`, so `1.3.2-beta.3` is the newest available, not a risky opt-in. It is also exactly
the build Create Nuclear Radiation pins, so the two match.

**Create: Wizardry** is pinned to `0.5.0` (release) rather than the newer `0.5.1-pre1` (beta);
their dependency ranges are identical, so there is nothing to gain from the pre-release on a
server. It declares `create` as `[6.0.6, 6.0.10,]` — a malformed range that appears in both
builds, so it is the author's style rather than a regression. Create 6.0.10 satisfies it.

**Create Nuclear Radiation** pins Create `6.0.8` in its Modrinth metadata while the pack runs
`6.0.10`. That pin is cosmetic: the jar's own `neoforge.mods.toml` asks for `[6.0.8,)`.

### Wanted but not (yet) included

Not available on Modrinth for 1.21.1/NeoForge — candidates for a CurseForge source later:
CBC Advanced Technology, Create Confectionery, Create Fluid Logistics, Create Bells and Whistles,
Steam 'n' Rails.

### Removed: broken on a dedicated server

**Create: Linear Bearing** — do not re-add without testing on the server. Its `@Mod` class
constructor calls `LinearBearingClient.registerClient(...)` unconditionally, with no
`FMLEnvironment`/`DistExecutor` dist guard, so a dedicated server crashes resolving client
render classes (`NoClassDefFoundError` on `BakedModel`) before the mod initialises. Checked
every 1.21.1/NeoForge build from 1.2.5 to 1.3.5 — all have the same unguarded call, so there is
no version to downgrade to. Modrinth lists it as `server: required`, which is simply wrong.

### Sides

| `side` | Count | |
|---|---|---|
| `both` | 64 | |
| `client` | 1 | Xaero's World Map |
| `server` | 2 | Create: Liquid Fuel, Create: Numismatics Advancement Seeker |

Set `side = "client"` on anything purely cosmetic, map-related, or UI-related as it gets added —
otherwise the default `both` puts it on the server, where it is dead weight at best and a crash
at worst.
