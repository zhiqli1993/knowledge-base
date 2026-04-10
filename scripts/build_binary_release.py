from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD_ROOT = ROOT / "build" / "binary-release"
BUNDLE_ROOT = BUILD_ROOT / "bundles"
PYINSTALLER_ROOT = BUILD_ROOT / "pyinstaller"
RELEASE_ROOT = ROOT / "release-assets"
TARGETS = (
    ("kb", ROOT / "src" / "kb" / "cli" / "main.py"),
    ("kb-http", ROOT / "src" / "kb" / "http" / "__main__.py"),
    ("kb-mcp", ROOT / "src" / "kb" / "mcp" / "server.py"),
)
COLLECT_ALL = ("chromadb", "onnxruntime", "tokenizers", "fastmcp", "mcp")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build release-ready kb binaries.")
    parser.add_argument("--platform", required=True, choices=("linux", "darwin", "windows"))
    parser.add_argument("--arch", required=True, choices=("x64", "arm64"))
    return parser.parse_args()


def executable_name(base_name: str, platform_name: str) -> str:
    return f"{base_name}.exe" if platform_name == "windows" else base_name


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build_binary(target_name: str, entrypoint: Path, platform_name: str, dist_dir: Path, work_dir: Path) -> Path:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--paths",
        str(SRC),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir / target_name),
        "--specpath",
        str(work_dir / "spec"),
        "--name",
        target_name,
    ]
    for package_name in COLLECT_ALL:
        command.extend(["--collect-all", package_name])
    command.append(str(entrypoint))
    run(command)
    return dist_dir / executable_name(target_name, platform_name)


def create_archive(bundle_dir: Path, platform_name: str, arch_name: str) -> Path:
    RELEASE_ROOT.mkdir(parents=True, exist_ok=True)
    archive_stem = f"kb-{platform_name}-{arch_name}"
    if platform_name == "windows":
        archive_path = RELEASE_ROOT / f"{archive_stem}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in bundle_dir.iterdir():
                archive.write(file_path, arcname=f"{bundle_dir.name}/{file_path.name}")
        return archive_path

    archive_path = RELEASE_ROOT / f"{archive_stem}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(bundle_dir, arcname=bundle_dir.name)
    return archive_path


def main() -> int:
    args = parse_args()
    bundle_name = f"kb-{args.platform}-{args.arch}"
    bundle_dir = BUNDLE_ROOT / bundle_name
    dist_dir = BUILD_ROOT / "dist"

    shutil.rmtree(bundle_dir, ignore_errors=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_ROOT.mkdir(parents=True, exist_ok=True)

    for target_name, entrypoint in TARGETS:
        built_binary = build_binary(target_name, entrypoint, args.platform, dist_dir, PYINSTALLER_ROOT)
        shutil.copy2(built_binary, bundle_dir / built_binary.name)

    archive_path = create_archive(bundle_dir, args.platform, args.arch)
    print(f"Built binary bundle: {bundle_dir}")
    print(f"Created release archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
