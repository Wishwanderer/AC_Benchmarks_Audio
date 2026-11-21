# Contributing

Thank you for your interest in contributing to **Audio Compression Results**.

## Adding results

1. Place each encoded artifact at `results/<codec>/<source_id>/<result_id>.<ext>`.
2. Add a matching `<result_id>.json` record that conforms to `schema/result.schema.json`.
3. Add a row for the result to `results/index.csv`.
4. Run the checks locally:
   ```bash
   python scripts/validate.py
   python scripts/summarize.py
   ```
5. Open a pull request describing the encoder build, hardware and any deviations from `docs/methodology.md`.

## Adding a codec or configuration

- Add the codec name to the `codec.name` enum in the schema.
- Document it in the README (§4) and in `docs/methodology.md`.
- Bump `schema_version` if the record structure changes, and note it in `CHANGELOG.md`.

## Adding a corpus item

- Assign the next free `ACR-NNN` identifier; never reuse a retired identifier.
- Record license and provenance in `corpus/manifest.csv`. Items without a clear license will not be accepted.

## Conventions

- Mark genuine measurements with `"synthetic": false`.
- Never edit an existing artifact in place; re-measurements receive a new record and the change is noted in `CHANGELOG.md`.
- Large binaries should be tracked with Git LFS.
