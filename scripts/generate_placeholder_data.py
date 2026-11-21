#!/usr/bin/env python3
"""
Generate deterministic PLACEHOLDER data for the audio-compression-results repository.

Everything this script produces is synthetic. The "compressed" artifacts are random
bytes, and every metric is drawn from a simple bitrate-dependent model plus noise.
It exists only so the repository layout, schema and tooling can be exercised before
real measurements are available. Delete its output once real results are added.

Usage:
    python scripts/generate_placeholder_data.py [--seed 20261121] [--artifact-bytes 2048]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
RESULTS_DIR = ROOT / "results"
SCHEMA_VERSION = "1.0.0"

# --------------------------------------------------------------------------- corpus
CATEGORIES = [
    ("speech", ["Male Narration", "Female Narration", "Conversational Dialogue", "Podcast Excerpt"]),
    ("music_acoustic", ["Solo Piano", "String Quartet", "Acoustic Guitar", "Choral Ensemble"]),
    ("music_electronic", ["Synth Pad", "Drum and Bass Loop", "Ambient Texture", "Electro Pop Mix"]),
    ("music_band", ["Rock Band", "Jazz Trio", "Orchestral Tutti", "Vocal Pop Mix"]),
    ("critical", ["Castanets", "Harpsichord", "Pitch Pipe", "Applause"]),
]

# --------------------------------------------------------------------------- codecs
# name, encoder, version, container/ext, list of (mode, setting, nominal kbps or None)
CODECS = [
    ("opus", "libopus", "1.5.2", "opus",
     [("vbr", "6k", 6), ("vbr", "12k", 12), ("vbr", "24k", 24), ("vbr", "48k", 48), ("vbr", "96k", 96)]),
    ("aac_lc", "fdk-aac", "2.0.3", "m4a",
     [("cbr", "64k", 64), ("cbr", "128k", 128), ("cbr", "192k", 192)]),
    ("mp3", "lame", "3.100", "mp3",
     [("cbr", "96k", 96), ("cbr", "128k", 128), ("cbr", "192k", 192), ("cbr", "320k", 320)]),
    ("vorbis", "libvorbis", "1.3.7", "ogg",
     [("vbr", "q2", 96), ("vbr", "q5", 160), ("vbr", "q8", 256)]),
    ("flac", "libFLAC", "1.4.3", "flac",
     [("lossless", "level0", None), ("lossless", "level5", None), ("lossless", "level8", None)]),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def build_corpus(rng: random.Random) -> list[dict]:
    entries = []
    idx = 1
    for category, titles in CATEGORIES:
        for title in titles:
            sid = f"ACR-{idx:03d}"
            channels = 1 if category == "speech" else 2
            sample_rate = rng.choice([44100, 48000]) if category != "speech" else 48000
            bit_depth = rng.choice([16, 24])
            duration = round(rng.uniform(10.0, 30.0), 3)
            slug = title.lower().replace(" ", "_")
            filename = f"{sid}_{slug}.wav"
            pcm_bytes = int(duration * sample_rate * channels * bit_depth / 8)
            entries.append({
                "source_id": sid,
                "filename": filename,
                "title": title,
                "category": category,
                "duration_s": duration,
                "sample_rate_hz": sample_rate,
                "bit_depth": bit_depth,
                "channels": channels,
                "pcm_bytes": pcm_bytes,
                # Hash of a non-existent file: placeholder only.
                "sha256": sha256_bytes(f"placeholder::{filename}".encode()),
                "license": "TBD",
                "provenance": "PLACEHOLDER",
            })
            idx += 1
    return entries


# --------------------------------------------------------------------------- metrics model
CATEGORY_DIFFICULTY = {
    "speech": -0.25, "music_acoustic": 0.10, "music_electronic": 0.05,
    "music_band": 0.15, "critical": 0.45,
}
CODEC_EFFICIENCY = {"opus": 1.35, "aac_lc": 1.10, "vorbis": 1.05, "mp3": 0.85}


def lossy_metrics(rng, codec, kbps, src) -> dict:
    eff = CODEC_EFFICIENCY[codec]
    difficulty = CATEGORY_DIFFICULTY[src["category"]]
    # Effective "quality bitrate" per channel drives a saturating quality curve.
    per_ch = kbps * eff / src["channels"]
    q = 1.0 - math.exp(-per_ch / 38.0)              # 0..1
    q = clamp(q - difficulty * 0.12 + rng.gauss(0, 0.03), 0.0, 1.0)
    odg = round(-4.0 + 4.0 * q ** 0.8, 3)            # PEAQ ODG range [-4, 0]
    mos = round(clamp(1.0 + 3.75 * q + rng.gauss(0, 0.05), 1.0, 4.75), 3)  # ViSQOL v3
    snr = round(clamp(4 + 32 * q + rng.gauss(0, 1.5), 0, 60), 2)
    return {
        "peaq_odg": odg,
        "visqol_mos": mos,
        "snr_db": snr,
        "bit_exact": False,
    }


def make_result(rng, src, codec, encoder, version, ext, mode, setting, kbps,
                artifact_bytes, run_ts) -> tuple[dict, bytes]:
    duration = src["duration_s"]
    if kbps is None:  # lossless
        level = int(setting.replace("level", ""))
        ratio = clamp(1.55 + 0.03 * level + rng.gauss(0, 0.08)
                      - 0.2 * (src["category"] == "music_electronic"), 1.15, 2.6)
        est_size = int(src["pcm_bytes"] / ratio)
        actual_kbps = est_size * 8 / duration / 1000
        metrics = {"peaq_odg": 0.0, "visqol_mos": 4.75, "snr_db": None, "bit_exact": True}
    else:
        actual_kbps = kbps * clamp(rng.gauss(1.0, 0.06 if mode == "vbr" else 0.01), 0.75, 1.3)
        est_size = int(actual_kbps * 1000 * duration / 8)
        ratio = src["pcm_bytes"] / est_size
        metrics = lossy_metrics(rng, codec, kbps, src)

    speed_base = {"opus": 140, "aac_lc": 95, "mp3": 60, "vorbis": 45, "flac": 400}[codec]
    if codec == "flac":
        speed_base /= 1 + int(setting[-1]) * 0.35
    encode_rt = round(speed_base * rng.uniform(0.85, 1.15), 1)
    decode_rt = round(encode_rt * rng.uniform(2.5, 6.0), 1)

    payload = rng.randbytes(artifact_bytes)
    rid = f"{src['source_id']}__{codec}__{setting}"
    rel_path = f"results/{codec}/{src['source_id']}/{rid}.{ext}"

    result = {
        "schema_version": SCHEMA_VERSION,
        "result_id": rid,
        "synthetic": True,
        "source": {
            "source_id": src["source_id"],
            "filename": src["filename"],
            "sha256": src["sha256"],
        },
        "codec": {
            "name": codec,
            "encoder": encoder,
            "encoder_version": version,
            "mode": mode,
            "setting": setting,
            "nominal_bitrate_kbps": kbps,
            "command": f"<placeholder> encode --codec {codec} --setting {setting} {src['filename']}",
        },
        "output": {
            "path": rel_path,
            "container": ext,
            "artifact_bytes": artifact_bytes,
            "artifact_sha256": sha256_bytes(payload),
            "estimated_encoded_bytes": est_size,
            "measured_bitrate_kbps": round(actual_kbps, 2),
            "compression_ratio": round(ratio, 3),
        },
        "quality": metrics,
        "performance": {
            "encode_speed_x_realtime": encode_rt,
            "decode_speed_x_realtime": decode_rt,
        },
        "environment": {
            "host": "placeholder-runner-01",
            "cpu": "TBD",
            "os": "TBD",
        },
        "created_utc": run_ts.isoformat().replace("+00:00", "Z"),
    }
    return result, payload


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20261121)
    ap.add_argument("--artifact-bytes", type=int, default=2048,
                    help="Size of each random placeholder artifact (default: 2048)")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    # Clean previous generated output.
    for codec, *_ in CODECS:
        shutil.rmtree(RESULTS_DIR / codec, ignore_errors=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    CORPUS_DIR.mkdir(exist_ok=True)

    corpus = build_corpus(rng)
    with open(CORPUS_DIR / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(corpus[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(corpus)

    t0 = datetime(2026, 11, 21, 9, 0, 0, tzinfo=timezone.utc)
    index_rows = []
    n = 0
    for src in corpus:
        for codec, encoder, version, ext, configs in CODECS:
            for mode, setting, kbps in configs:
                ts = t0 + timedelta(seconds=37 * n)
                result, payload = make_result(rng, src, codec, encoder, version, ext,
                                              mode, setting, kbps, args.artifact_bytes, ts)
                out_dir = RESULTS_DIR / codec / src["source_id"]
                out_dir.mkdir(parents=True, exist_ok=True)
                (ROOT / result["output"]["path"]).write_bytes(payload)
                (out_dir / f"{result['result_id']}.json").write_text(json.dumps(result, indent=2) + "\n")
                index_rows.append({
                    "result_id": result["result_id"],
                    "source_id": src["source_id"],
                    "category": src["category"],
                    "codec": codec,
                    "mode": mode,
                    "setting": setting,
                    "nominal_bitrate_kbps": "" if kbps is None else kbps,
                    "measured_bitrate_kbps": result["output"]["measured_bitrate_kbps"],
                    "compression_ratio": result["output"]["compression_ratio"],
                    "peaq_odg": result["quality"]["peaq_odg"],
                    "visqol_mos": result["quality"]["visqol_mos"],
                    "snr_db": "" if result["quality"]["snr_db"] is None else result["quality"]["snr_db"],
                    "bit_exact": result["quality"]["bit_exact"],
                    "encode_speed_x_realtime": result["performance"]["encode_speed_x_realtime"],
                    "decode_speed_x_realtime": result["performance"]["decode_speed_x_realtime"],
                    "synthetic": True,
                })
                n += 1

    with open(RESULTS_DIR / "index.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(index_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(index_rows)

    print(f"Generated {len(corpus)} corpus entries and {n} placeholder results (seed={args.seed}).")


if __name__ == "__main__":
    main()
