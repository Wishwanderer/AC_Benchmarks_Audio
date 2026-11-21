# Measurement Methodology

**Status:** Draft — to be completed before the first real data release.

This document will define the protocol used to produce every result in this repository. Sections marked _TBD_ are placeholders.

## 1. Source preparation

- Format: uncompressed PCM WAV, 16- or 24-bit, 44.1 kHz or 48 kHz.
- Loudness normalisation: _TBD_ (e.g. −23 LUFS integrated, EBU R 128).
- Trimming and fades: _TBD_.
- Checksums: SHA-256 of each source file recorded in `corpus/manifest.csv`.

## 2. Encoding

- One encoder invocation per (source × configuration); no multi-pass unless stated in `codec.mode`.
- The exact command line is stored in `codec.command`.
- Encoder binaries and versions: _TBD_ (pinned build hashes).

## 3. Decoding and alignment

- Decoder per codec: _TBD_.
- Sample-rate conversion back to source rate: _TBD_.
- Delay compensation (encoder priming / padding removal): _TBD_.
- Level alignment: _TBD_.

## 4. Metrics

| Metric | Implementation | Version | Notes |
|:---|:---|:---|:---|
| PEAQ ODG | _TBD_ | _TBD_ | Basic version, 48 kHz |
| ViSQOL MOS | google/visqol | v3 | Audio mode |
| SNR | in-house | — | After alignment |

## 5. Performance measurement

- Hardware and OS: _TBD_ (recorded in each record's `environment`).
- Timing: median of _N_ runs, single thread, wall clock.

## 6. Known limitations

- Objective metrics do not fully reflect perceived quality.
- _TBD_.
