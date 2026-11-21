#!/usr/bin/env python3
"""
Validate every result record in results/ against the repository's conventions.

Checks performed:
  1. Each JSON record conforms to schema/result.schema.json (if `jsonschema` is installed).
  2. The referenced artifact exists and its SHA-256 matches `output.artifact_sha256`.
  3. The referenced source_id exists in corpus/manifest.csv.
  4. result_id values are unique.
  5. Every compressed artifact has a matching JSON record (no orphans).

Exit status is non-zero if any check fails.

Usage:
    python scripts/validate.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def main() -> int:
    errors: list[str] = []

    try:
        import jsonschema  # type: ignore
        schema = json.loads((ROOT / "schema" / "result.schema.json").read_text())
        validator = jsonschema.Draft202012Validator(schema)
    except ImportError:
        validator = None
        print("note: `jsonschema` not installed; skipping schema validation "
              "(pip install jsonschema)", file=sys.stderr)

    with open(ROOT / "corpus" / "manifest.csv", newline="") as fh:
        source_ids = {row["source_id"] for row in csv.DictReader(fh)}

    seen_ids: set[str] = set()
    referenced: set[Path] = set()
    records = sorted(RESULTS.glob("*/*/*.json"))

    for path in records:
        rel = path.relative_to(ROOT)
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue

        if validator is not None:
            for err in validator.iter_errors(rec):
                loc = "/".join(map(str, err.absolute_path)) or "<root>"
                errors.append(f"{rel}: schema: {loc}: {err.message}")

        rid = rec.get("result_id")
        if rid in seen_ids:
            errors.append(f"{rel}: duplicate result_id {rid}")
        seen_ids.add(rid)

        sid = rec.get("source", {}).get("source_id")
        if sid not in source_ids:
            errors.append(f"{rel}: unknown source_id {sid}")

        out = rec.get("output", {})
        artifact = ROOT / out.get("path", "")
        referenced.add(artifact.resolve())
        if not artifact.is_file():
            errors.append(f"{rel}: missing artifact {out.get('path')}")
        else:
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if digest != out.get("artifact_sha256"):
                errors.append(f"{rel}: checksum mismatch for {out.get('path')}")

    for artifact in RESULTS.glob("*/*/*"):
        if artifact.suffix != ".json" and artifact.resolve() not in referenced:
            errors.append(f"{artifact.relative_to(ROOT)}: orphan artifact (no JSON record)")

    if errors:
        print(f"FAILED: {len(errors)} problem(s) across {len(records)} records")
        for e in errors[:200]:
            print("  -", e)
        return 1

    print(f"OK: {len(records)} records validated against {len(source_ids)} corpus entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
