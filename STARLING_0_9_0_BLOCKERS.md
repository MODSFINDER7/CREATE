# Starling 0.9.0 compatibility audit

## Result

The existing Create-Horizon source can be packaged as a **flat native `.hmod`**. It is not a legacy `.hnmod` bundle. Starling's importer recognises a flat package with a valid `horizon-mod.toml` and `[native]`, then installs it in its native-mod directory.

However, **the current Create-Horizon source cannot be compiled by Starling 0.9.0's per-mod Compile v2 route as-is**. Packaging alone does not make it runnable.

## Exact Compile v2 blockers

Starling's `mod_lib.py` accepts only a native package that:
- has no `[native.*]` tables (mixins, bridges, modules, state or loops);
- has no build script, build dependencies or Cargo features;
- depends only on `horizon-mod-api`.

The existing Create-Horizon package violates three of those conditions:

| Existing source | Why Compile v2 rejects it |
|---|---|
| `[[native.mixin]] local_player_solid` in `mod/horizon-mod.toml` | Any `[native.*]` table is refused by the per-mod builder |
| `create-kinetics = { path = "src/kinetics" }` | The local crate is an additional Cargo dependency |
| `flate2 = ...` | Registry dependency other than `horizon-mod-api` |

Starling 0.9.0's game code also says that legacy `.hnmod` bundles are not compiled by the new game-as-libraries route. Converting this project into the old `horizon-native.json` / `horizon-mixin.toml` archive would therefore be the wrong fix.

## Build-pin warning

The existing manifest pins Horizon commit `0b14f8acfd97fa2c750e42795249dcc981178ca4`. Starling's `v0.9.0` tag is `ff303502a4f7982551a0e0d3622d9268efe9e829`; GitHub reports those histories as diverged. The exact game-build ID used by the 0.9.0 mod store must be confirmed before changing the pin. The existing mixins pin also needs to be checked against the target build.

## What is needed to finish

There are two valid engineering routes:

1. **Preserve the existing Create port:** extend Starling's native build path so flat native packages with `[native.mixin]` and additional Cargo dependencies can be compiled for the phone. This is the route that avoids silently removing Create functionality, but it requires changes to Starling's build system/service, not only this repository.
2. **Fit Compile v2's restricted route:** inline the `create-kinetics` crate, remove or replace `flate2` schematic compression, and remove or redesign the `local_player_solid` game mixin. This changes or removes existing behavior and should not be done without an explicit decision.

## Current repository changes

- `tools/build_starling_hmod.py` stages the upstream source archive and uses its existing selective Create-JAR asset extractor to make the flat native `.hmod`.
- It does not claim a successful Starling compile or runtime test.
- The source Create JAR must be supplied locally; the extractor checks its SHA-256 and refuses a different version.
