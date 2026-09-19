"""Export installed metadata for review; metadata is not a legal clearance decision."""

import csv
from importlib.metadata import distribution
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "compliance/installed_dependencies.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "name",
                "version",
                "source",
                "license_metadata",
                "license_files",
                "usage",
                "review_status",
            ],
        )
        writer.writeheader()
        for line in (root / "requirements-dev.txt").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            name, _ = line.split("==")
            dist = distribution(name)
            license_text = (
                dist.metadata.get("License-Expression")
                or dist.metadata.get("License")
                or "not declared"
            )
            if len(license_text) > 200:
                license_text = (
                    "Full license text supplied in distribution metadata; review license_files"
                )
            source = dist.metadata.get("Home-page") or next(
                iter(dist.metadata.get_all("Project-URL") or []), ""
            )
            writer.writerow(
                {
                    "name": dist.metadata["Name"],
                    "version": dist.version,
                    "source": source or f"https://pypi.org/project/{name}/{dist.version}/",
                    "license_metadata": license_text,
                    "license_files": ";".join(
                        str(p) for p in (dist.files or []) if "license" in str(p).lower()
                    ),
                    "usage": "locked runtime/build/development dependency",
                    "review_status": "pending human review",
                }
            )


if __name__ == "__main__":
    main()
