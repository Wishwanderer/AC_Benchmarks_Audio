#!/usr/bin/env python3
"""
Aggregate per-result records into codec/setting summaries.

Reads results/index.csv and writes:
  - results/summary.csv : one row per (codec, setting), averaged over the corpus
  - results/summary.md  : the same table in Markdown, suitable for pasting into the README

Usage:
    python scripts/summarize.py
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

CODEC_ORDER = ["opus", "aac_lc", "mp3", "vorbis", "flac"]


def fnum(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def avg(values):
    values = [v for v in values if v is not None]
    return round(mean(values), 3) if values else None


def main() -> None:
    with open(RESULTS / "index.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["codec"], r["setting"])].append(r)

    def sort_key(k):
        codec, setting = k
        nominal = fnum(groups[k][0]["nominal_bitrate_kbps"])
        return (CODEC_ORDER.index(codec) if codec in CODEC_ORDER else 99,
                nominal if nominal is not None else 0, setting)

    summary = []
    for key in sorted(groups, key=sort_key):
        g = groups[key]
        summary.append({
            "codec": key[0],
            "setting": key[1],
            "n": len(g),
            "mean_bitrate_kbps": avg(fnum(r["measured_bitrate_kbps"]) for r in g),
            "mean_compression_ratio": avg(fnum(r["compression_ratio"]) for r in g),
            "mean_peaq_odg": avg(fnum(r["peaq_odg"]) for r in g),
            "mean_visqol_mos": avg(fnum(r["visqol_mos"]) for r in g),
            "mean_encode_x_rt": avg(fnum(r["encode_speed_x_realtime"]) for r in g),
        })

    with open(RESULTS / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(summary)

    headers = ["Codec", "Setting", "N", "Bitrate (kbps)", "Ratio", "PEAQ ODG", "ViSQOL MOS", "Encode (×RT)"]
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join([":---", ":---"] + ["---:"] * (len(headers) - 2)) + "|"]
    for s in summary:
        cells = [s["codec"], s["setting"], s["n"], f"{s['mean_bitrate_kbps']:.1f}",
                 f"{s['mean_compression_ratio']:.2f}", f"{s['mean_peaq_odg']:.2f}",
                 f"{s['mean_visqol_mos']:.2f}", f"{s['mean_encode_x_rt']:.0f}"]
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n")

    print(f"Summarized {len(rows)} results into {len(summary)} configurations.")


if __name__ == "__main__":
    main()
