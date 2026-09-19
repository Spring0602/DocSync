"""Copy the self-authored fixture to a new disposable Git repository."""

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; choose a new directory")
    source = Path(__file__).resolve().parents[1] / "examples" / "minimal_repo"
    shutil.copytree(source, args.out)
    subprocess.run(["git", "init", "--quiet", str(args.out)], check=True)
    subprocess.run(["git", "-C", str(args.out), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(args.out), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(args.out),
            "-c",
            "user.name=DocSync Demo",
            "-c",
            "user.email=demo@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "Self-authored default-value fixture",
        ],
        check=True,
    )
    print(args.out)


if __name__ == "__main__":
    main()
