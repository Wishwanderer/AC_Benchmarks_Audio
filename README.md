# Audio Compression Results

[![Validate](https://github.com/<ORG>/audio-compression-results/actions/workflows/validate.yml/badge.svg)](https://github.com/<ORG>/audio-compression-results/actions/workflows/validate.yml)
![Schema](https://img.shields.io/badge/schema-v1.0.0-blue)
![Status](https://img.shields.io/badge/data-placeholder-orange)
![License](https://img.shields.io/badge/code-MIT-green)

A versioned repository of encoded audio renditions and their associated objective quality, efficiency and performance measurements, intended to support reproducible comparison of lossy and lossless audio codecs across a fixed reference corpus.

> [!IMPORTANT]
> **All data currently in this repository is synthetic placeholder data.**
> The compressed artifacts are random bytes, and all metrics were produced by
> [`scripts/generate_placeholder_data.py`](scripts/generate_placeholder_data.py) from a simple
> statistical model. Every record carries `"synthetic": true`. Nothing here should be cited,
> compared or used to draw conclusions until real measurements replace it.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [Reference Corpus](#3-reference-corpus)
4. [Codecs and Configurations](#4-codecs-and-configurations)
5. [Metrics](#5-metrics)
6. [Data Format](#6-data-format)
7. [Results Summary](#7-results-summary)
8. [Usage](#8-usage)
9. [Methodology](#9-methodology)
10. [Contributing](#10-contributing)
11. [Citation](#11-citation)
12. [License](#12-license)
13. [Contact](#13-contact)

---

## 1. Overview

This project records how a set of audio codecs perform when applied to a common corpus of source recordings. For every combination of **source item × codec × configuration**, the repository stores:

- the encoded artifact produced by the encoder;
- a machine-readable result record describing how the artifact was produced; and
- objective measurements of quality, compression efficiency and computational cost.

The aims of the project are to:

- provide a **single, auditable location** for compression results;
- make every result **traceable** to its source file, encoder version and command line;
- support **reproducible** re-measurement as encoders and metrics evolve; and
- enable **consistent aggregation** across codecs, bitrates and content categories.

| Item | Current value |
|:---|:---|
| Corpus items | 20 |
| Codecs | 5 (Opus, AAC-LC, MP3, Vorbis, FLAC) |
| Configurations per item | 18 |
| Result records | 360 |
| Schema version | 1.0.0 |
| Data status | **Placeholder** |

## 2. Repository Structure

```
audio-compression-results/
├── corpus/
│   └── manifest.csv              # Reference corpus: one row per source item
├── results/
│   ├── index.csv                 # Flat index of every result record
│   ├── summary.csv               # Per-configuration averages (generated)
│   ├── summary.md                # Markdown rendering of summary.csv (generated)
│   └── <codec>/<source_id>/
│       ├── <result_id>.<ext>     # Encoded artifact
│       └── <result_id>.json      # Result record (see §6)
├── schema/
│   └── result.schema.json        # JSON Schema for result records
├── scripts/
│   ├── generate_placeholder_data.py
│   ├── summarize.py
│   └── validate.py
├── docs/
│   └── methodology.md            # Measurement protocol (draft)
├── .github/workflows/validate.yml
├── CHANGELOG.md
├── CITATION.cff
├── CONTRIBUTING.md
└── LICENSE
```

**Naming convention.** Each result is identified by a `result_id` of the form

```
<source_id>__<codec>__<setting>        e.g.  ACR-007__opus__48k
```

The artifact and its record share this identifier and differ only in extension.

## 3. Reference Corpus

The corpus consists of 20 items, numbered `ACR-001` to `ACR-020`, grouped into five content categories of four items each. Full technical details (duration, sample rate, bit depth, channel count, checksum) are recorded in [`corpus/manifest.csv`](corpus/manifest.csv).

| Category | Items | Description |
|:---|:---|:---|
| `speech` | ACR-001 – ACR-004 | Narration, dialogue and podcast-style speech (mono) |
| `music_acoustic` | ACR-005 – ACR-008 | Piano, strings, guitar and choral material |
| `music_electronic` | ACR-009 – ACR-012 | Synthesised and electronically produced material |
| `music_band` | ACR-013 – ACR-016 | Full-band, jazz, orchestral and vocal-pop mixes |
| `critical` | ACR-017 – ACR-020 | Codec-critical signals (transients, tonal, noise-like) |

Source audio is **not** distributed in this repository. Licensing and provenance for each item are tracked in the manifest (`license`, `provenance`) and are currently marked `TBD` / `PLACEHOLDER`.

## 4. Codecs and Configurations

| Codec | Encoder (version) | Container | Mode | Settings |
|:---|:---|:---|:---|:---|
| Opus | libopus 1.5.2 | `.opus` | VBR | 6, 12, 24, 48, 96 kbps |
| AAC-LC | fdk-aac 2.0.3 | `.m4a` | CBR | 64, 128, 192 kbps |
| MP3 | LAME 3.100 | `.mp3` | CBR | 96, 128, 192, 320 kbps |
| Vorbis | libvorbis 1.3.7 | `.ogg` | VBR | q2, q5, q8 |
| FLAC | libFLAC 1.4.3 | `.flac` | Lossless | levels 0, 5, 8 |

Encoder versions and settings above are provisional and will be confirmed when real measurements are taken. The exact command line used for each artifact is recorded in its result record (`codec.command`).

## 5. Metrics

| Field | Unit / range | Direction | Description |
|:---|:---|:---:|:---|
| `measured_bitrate_kbps` | kbit/s | — | Encoded size × 8 ÷ duration |
| `compression_ratio` | ratio | ↑ | Uncompressed PCM size ÷ encoded size |
| `peaq_odg` | −4.0 … 0.0 | ↑ | PEAQ Objective Difference Grade (ITU-R BS.1387) |
| `visqol_mos` | 1.0 … 5.0 | ↑ | ViSQOL v3 estimated mean opinion score |
| `snr_db` | dB | ↑ | Signal-to-noise ratio of decoded vs. reference |
| `bit_exact` | boolean | — | Decoded output is sample-identical to the source |
| `encode_speed_x_realtime` | × real time | ↑ | Audio duration ÷ wall-clock encode time |
| `decode_speed_x_realtime` | × real time | ↑ | Audio duration ÷ wall-clock decode time |

Objective metrics are an approximation of perceived quality and are not a substitute for formal listening tests (e.g. ITU-R BS.1116 or MUSHRA, ITU-R BS.1534).

## 6. Data Format

Each result record is a JSON document validated against [`schema/result.schema.json`](schema/result.schema.json). An abridged example:

```json
{
  "schema_version": "1.0.0",
  "result_id": "ACR-007__opus__48k",
  "synthetic": true,
  "source":  { "source_id": "ACR-007", "filename": "ACR-007_acoustic_guitar.wav", "sha256": "…" },
  "codec":   { "name": "opus", "encoder": "libopus", "encoder_version": "1.5.2",
               "mode": "vbr", "setting": "48k", "nominal_bitrate_kbps": 48, "command": "…" },
  "output":  { "path": "results/opus/ACR-007/ACR-007__opus__48k.opus", "container": "opus",
               "artifact_bytes": 2048, "artifact_sha256": "…",
               "measured_bitrate_kbps": 47.9, "compression_ratio": 29.4 },
  "quality": { "peaq_odg": -1.21, "visqol_mos": 3.35, "snr_db": 21.7, "bit_exact": false },
  "performance": { "encode_speed_x_realtime": 141.2, "decode_speed_x_realtime": 610.4 },
  "environment": { "host": "…", "cpu": "TBD", "os": "TBD" },
  "created_utc": "2026-11-21T09:00:00Z"
}
```

`results/index.csv` flattens the most commonly used fields of every record into a single table for convenient analysis in spreadsheets, pandas or R.

## 7. Results Summary

Mean values across all 20 corpus items for each configuration. Regenerate with `python scripts/summarize.py`.

> [!WARNING]
> The figures below are **synthetic** and illustrate the table format only.

| Codec | Setting | N | Bitrate (kbps) | Ratio | PEAQ ODG | ViSQOL MOS | Encode (×RT) |
|:---|:---|---:|---:|---:|---:|---:|---:|
| opus | 6k | 20 | 6.1 | 278.15 | -3.37 | 1.38 | 141 |
| opus | 12k | 20 | 11.8 | 144.36 | -2.83 | 1.81 | 136 |
| opus | 24k | 20 | 24.1 | 70.61 | -2.17 | 2.44 | 140 |
| opus | 48k | 20 | 47.7 | 35.70 | -1.32 | 3.28 | 143 |
| opus | 96k | 20 | 96.7 | 17.68 | -0.56 | 4.11 | 136 |
| aac_lc | 64k | 20 | 64.2 | 26.48 | -1.23 | 3.38 | 94 |
| aac_lc | 128k | 20 | 127.7 | 13.28 | -0.45 | 4.22 | 94 |
| aac_lc | 192k | 20 | 191.7 | 8.85 | -0.23 | 4.47 | 96 |
| mp3 | 96k | 20 | 96.1 | 17.67 | -1.01 | 3.61 | 61 |
| mp3 | 128k | 20 | 128.3 | 13.23 | -0.70 | 3.94 | 58 |
| mp3 | 192k | 20 | 191.6 | 8.87 | -0.36 | 4.34 | 59 |
| mp3 | 320k | 20 | 318.9 | 5.32 | -0.13 | 4.61 | 57 |
| vorbis | q2 | 20 | 95.1 | 18.13 | -0.81 | 3.84 | 46 |
| vorbis | q5 | 20 | 156.3 | 10.86 | -0.35 | 4.33 | 44 |
| vorbis | q8 | 20 | 254.3 | 6.74 | -0.13 | 4.60 | 44 |
| flac | level0 | 20 | 1136.3 | 1.49 | 0.00 | 4.75 | 394 |
| flac | level5 | 20 | 1037.2 | 1.65 | 0.00 | 4.75 | 146 |
| flac | level8 | 20 | 972.1 | 1.75 | 0.00 | 4.75 | 107 |

## 8. Usage

**Requirements:** Python 3.10 or later. Schema validation additionally requires `jsonschema`.

```bash
git clone https://github.com/<ORG>/audio-compression-results.git
cd audio-compression-results
python -m pip install -r requirements.txt
```

| Task | Command |
|:---|:---|
| Validate all records, checksums and references | `python scripts/validate.py` |
| Regenerate `summary.csv` and `summary.md` | `python scripts/summarize.py` |
| Regenerate placeholder data (overwrites `results/`) | `python scripts/generate_placeholder_data.py --seed 20261121` |

Loading the index for analysis:

```python
import pandas as pd

df = pd.read_csv("results/index.csv")
df[df.codec == "opus"].groupby("setting")[["visqol_mos", "peaq_odg"]].mean()
```

## 9. Methodology

The measurement protocol — source preparation, encoder invocation, decoding, level and delay alignment, metric computation and hardware environment — is documented in [`docs/methodology.md`](docs/methodology.md). That document is currently a draft and will be completed before the first real data release.

## 10. Contributing

Contributions of new results, codecs or corpus items are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request. In summary, every submission must:

1. follow the directory layout and naming convention in §2;
2. include a result record that passes `python scripts/validate.py`;
3. record the exact encoder version and command line used; and
4. set `"synthetic": false` only for genuine measurements.

For large binary artifacts, use [Git LFS](https://git-lfs.com/) (see `.gitattributes`).

## 11. Citation

If you use this dataset, please cite it using the metadata in [`CITATION.cff`](CITATION.cff):

```bibtex
@misc{audio_compression_results_2026,
  title        = {Audio Compression Results},
  author       = {{<AUTHOR OR ORGANISATION>}},
  year         = {2026},
  howpublished = {\url{https://github.com/<ORG>/audio-compression-results}},
  note         = {Version 0.1.0 (placeholder data)}
}
```

## 12. License

- **Code** (`scripts/`, `schema/`): MIT License — see [`LICENSE`](LICENSE).
- **Result data** (`results/`, `corpus/manifest.csv`): license to be determined.
- **Source audio**: not distributed; each item retains its original license as recorded in the manifest.

## 13. Contact

Maintainer: `<NAME>` — `<EMAIL>`
Issues and questions: [GitHub Issues](https://github.com/<ORG>/audio-compression-results/issues)
