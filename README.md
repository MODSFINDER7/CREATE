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

Package layout is adapted for Starling's flat native package reader. **This does not yet prove that the mod compiles or runs in Starling 0.9.0.** The existing `[native]` Horizon and horizon-mixins commit pins still need to be checked against the exact game build served to Starling 0.9.0, then the package must pass Starling's native build service. No runtime test is claimed here.

Do not rename the package to `.hnmod`: the native flat package is identified by its manifest and is imported as native code by Starling.
