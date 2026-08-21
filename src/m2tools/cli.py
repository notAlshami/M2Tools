import argparse
import os
import shutil
import sys
from pathlib import Path

import argcomplete


def find_artifact_dirs(repo: Path, app: str):
    return [p for p in repo.rglob(app) if p.is_dir()]


def matching_version_dirs(app_dir: Path, version: str):
    return sorted(p for p in app_dir.glob(f"{version}*") if p.is_dir())


def _app_completer(prefix, parsed_args, **kwargs):
    repo = Path(parsed_args.repo).expanduser()
    if not repo.is_dir():
        return []
    names = set()
    for d in repo.rglob(f"{prefix}*"):
        if d.is_dir() and any(c.is_dir() for c in d.iterdir()):
            names.add(d.name)
    return sorted(names)


def _version_completer(prefix, parsed_args, **kwargs):
    repo = Path(parsed_args.repo).expanduser()
    app = getattr(parsed_args, "app", None)
    if not app or not repo.is_dir():
        return []
    names = set()
    for app_dir in find_artifact_dirs(repo, app):
        for v in app_dir.glob(f"{prefix}*"):
            if v.is_dir():
                names.add(v.name)
    return sorted(names)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="m2delete",
        description="Delete a specific version (snapshot) of a Java application from the local Maven repository.",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("M2_REPO", str(Path.home() / ".m2" / "repository")),
        help="Path to the local Maven repository (default: $M2_REPO or ~/.m2/repository)",
    )
    app_arg = parser.add_argument(
        "app", help="Artifact/application name (the Maven artifactId)"
    )
    app_arg.completer = _app_completer
    version_arg = parser.add_argument(
        "version",
        nargs="?",
        default="1.0-SNAPSHOT",
        help="Version prefix to delete (default: 1.0-SNAPSHOT)",
    )
    version_arg.completer = _version_completer
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything",
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser()
    if not repo.is_dir():
        print(f"Repository path not found: {repo}", file=sys.stderr)
        return 1

    app_dirs = find_artifact_dirs(repo, args.app)
    if not app_dirs:
        print(f"No artifact directory named '{args.app}' found under {repo}", file=sys.stderr)
        return 1

    deleted_any = False
    for app_dir in app_dirs:
        for version_dir in matching_version_dirs(app_dir, args.version):
            deleted_any = True
            if args.dry_run:
                print(f"Would delete: {version_dir}")
            else:
                print(f"Deleting: {version_dir}")
                shutil.rmtree(version_dir)

    if not deleted_any:
        print(
            f"No matching version found for '{args.app}' ({args.version}*) under {repo}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
