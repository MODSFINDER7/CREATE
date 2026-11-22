# Create for Starling

This repository stages the existing **Create-Horizon Rust port** as a Starling flat native package. It does not rewrite Create or replace its selective asset extraction pipeline.

## Package format

- Output: `.hmod` containing `horizon-mod.toml`, `[native]`, `Cargo.toml`, `src/`, `assets/` and `data/`.
- This is a **flat native package**, not a content-only pack. Starling detects the `[native]` manifest and imports it into its native-mod inventory.
- The older `.hnmod` format uses `horizon-native.json` and `horizon-mixin.toml`; it is not the format used by this Create-Horizon source tree.

## Build the package

Requirements: Python 3.11+, the original Create 6.0.10 JAR for Minecraft 1.21.1, and the source archive `Create-Horizon-main.zip` in this repository.

```sh
python tools/build_starling_hmod.py --create-jar /path/to/create-1.21.1-6.0.10.jar
```

The script:
1. Extracts the checked-in Create-Horizon source archive into a temporary directory.
2. Runs the upstream module generators.
3. Runs the upstream selective asset extractor against the supplied Create JAR.
4. Packages the flat native source and staged assets as `dist/create-0.1.0.hmod`.
5. Checks the required manifest, Cargo crate and source layout, and prints the package SHA-256.

The upstream extractor verifies the Create JAR SHA-256 before importing assets. It will reject a different JAR rather than silently mixing assets from another version.

## Compatibility status

The package structure is supported by Starling's flat native-package importer, but **the current Create-Horizon source is not yet compilable through Starling 0.9.0's per-mod Compile v2 route**. That route refuses `[native.*]` tables and any Cargo dependency other than `horizon-mod-api`; this project currently has `[[native.mixin]]`, the local `create-kinetics` crate, and `flate2`. The legacy `.hnmod` route is not a workaround: Starling 0.9.0 no longer compiles the old bundle format for its game-as-libraries build.

See [STARLING_0_9_0_BLOCKERS.md](STARLING_0_9_0_BLOCKERS.md) for the source-level audit and the two engineering routes. No successful compile or runtime test is claimed.

Do not rename the package to `.hnmod`: this project uses the flat native `.hmod` structure, which Starling identifies by its manifest.
