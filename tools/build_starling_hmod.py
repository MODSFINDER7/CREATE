#!/usr/bin/env python3
"""Build Create-Horizon as a Starling flat native .hmod package.

The input repository stores the upstream source archive as Create-Horizon-main.zip.
The original Create 6.0.10 / Minecraft 1.21.1 JAR is required only as the asset source.
The upstream selective extractor stages only referenced Create models, textures,
blockstates, sounds and data; the Minecraft game JAR is never packaged.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import tomllib
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARCHIVE = ROOT / "Create-Horizon-main.zip"


def run(args: list[str], cwd: Path) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def extract_source(archive_path: Path, destination: Path) -> None:
    """Extract the checked-in source archive without accepting traversal paths or links."""
    with ZipFile(archive_path) as archive:
        for info in archive.infolist():
            rel = PurePosixPath(info.filename)
            if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
                raise SystemExit(f"Unsafe path in source archive: {info.filename}")
            mode = info.external_attr >> 16
            if mode and mode & 0o170000 not in (0, 0o100000, 0o040000):
                raise SystemExit(f"Unsupported link or special file in source archive: {info.filename}")
            target = destination.joinpath(*rel.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))


def find_project(folder: Path) -> Path:
    matches = [
        p.parent.parent
        for p in folder.rglob("tools/stage_package.py")
        if (p.parent.parent / "mod/horizon-mod.toml").is_file()
    ]
    if len(matches) != 1:
        raise SystemExit(f"Expected one Create-Horizon source tree, found {len(matches)}")
    return matches[0]


def package_file_allowed(rel: str) -> bool:
    p = PurePosixPath(rel)
    if rel in {"horizon-mod.toml", "Cargo.toml", "Cargo.lock", "icon.png"}:
        return True
    if p.parts and p.parts[0] in {"assets", "data"}:
        return True
    if p.parts and p.parts[0] == "src":
        return p.suffix in {".rs", ".toml"}
    if len(p.parts) == 1 and p.name.startswith(
        ("README", "LICENSE", "LICENCE", "COPYING", "NOTICE")
    ):
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-jar",
        required=True,
        type=Path,
        help="Original Create 6.0.10 / Minecraft 1.21.1 JAR used by the selective asset extractor",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    if not SOURCE_ARCHIVE.is_file():
        raise SystemExit(f"Missing source archive: {SOURCE_ARCHIVE}")
    jar = args.create_jar.expanduser().resolve()
    if not jar.is_file():
        raise SystemExit(f"Create JAR not found: {jar}")

    with tempfile.TemporaryDirectory(prefix="create-starling-") as tmp:
        unpacked = Path(tmp) / "source"
        unpacked.mkdir()
        extract_source(SOURCE_ARCHIVE, unpacked)
        project = find_project(unpacked)

        # Preserve the upstream source generators and selective asset pipeline.
        for script in ("gen_modules.py", "gen_forward.py", "gen_parts.py"):
            run([sys.executable, f"tools/{script}"], project)
        run([sys.executable, "tools/stage_package.py", str(jar)], project)

        staged = project / "target/package"
        manifest_path = staged / "horizon-mod.toml"
        cargo_path = staged / "Cargo.toml"
        lib_path = staged / "src/lib.rs"
        for required in (manifest_path, cargo_path, lib_path):
            if not required.is_file():
                raise SystemExit(f"Staged native package is missing {required.relative_to(staged)}")

        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        native = manifest.get("native")
        if not isinstance(native, dict):
            raise SystemExit("horizon-mod.toml has no [native] section")
        if not isinstance(native.get("game"), str) or not native["game"]:
            raise SystemExit("Invalid [native].game in horizon-mod.toml")
        for key in ("horizon", "mixins"):
            value = native.get(key)
            if (
                not isinstance(value, str)
                or len(value) != 40
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise SystemExit(f"[native].{key} must be an exact lowercase 40-character commit")

        files: list[tuple[str, Path]] = []
        for path in sorted(staged.rglob("*")):
            if path.is_symlink():
                raise SystemExit(f"Package cannot contain symlinks: {path}")
            if not path.is_file():
                continue
            rel = path.relative_to(staged).as_posix()
            if not package_file_allowed(rel):
                raise SystemExit(f"Starling native package format does not allow this file: {rel}")
            files.append((rel, path))

        output_dir = args.output.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"{manifest['id']}-{manifest['version']}.hmod"
        part = output.with_suffix(output.suffix + ".part")
        with ZipFile(part, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for rel, path in files:
                info = ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())

        # Structural validation of the exact archive Starling will import.
        with ZipFile(part) as archive:
            names = set(archive.namelist())
            if not {"horizon-mod.toml", "Cargo.toml", "src/lib.rs"} <= names:
                raise SystemExit("Final .hmod failed its flat native-package structure check")
            if any(name.startswith((".horizon/", "target/")) for name in names):
                raise SystemExit("SDK cache or build output leaked into the .hmod")
        os.replace(part, output)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"Created: {output}")
    print(f"Files:   {len(files)}")
    print(f"SHA256:  {digest}")
    print("Format:  flat native .hmod; Starling imports it as native code.")


if __name__ == "__main__":
    main()
