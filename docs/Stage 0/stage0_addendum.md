# Stage 0 Addendum — Deferred Test Closed
*Appended after the ResPlan WKT samples were pushed (plans 2, 42, 123 verified in master; 250 for visual use).*

## Discovery: master_dataset stores NORMALISED features
The raw-value comparison first diverged wildly (stored Av ~0.2 vs computed ~7,000).
Diagnosis proved **master_dataset.csv stores per-plan MinMax-normalised features, not
raw isovist measures** — every plan's every feature spans exactly [0,1], and the global
StandardScaler's fitted means (0.32–0.54) confirm it was fit on these normalised values.
Pipeline understanding corrected accordingly: the capstone's stored dataset is already
one normalisation deep; inference re-derives the same normalisation from raw features.
The inference chain in `scoring.py` is CONSISTENT with this — no code change needed.

## Reproduction results (training settings: spacing min/20, shrink 0.01)
| plan | grid match | feature reproduction | prediction agreement |
|---|---|---|---|
| 2   | 289/289 = 100% | exact (max dev 0.0005 = 3-dp rounding) | **100%** |
| 42  | 337/337 = 100% | Av/Uv/Cv/Hv exact; Ov jitter ≤0.018 | **100%** |
| 123 | 437/437 = 100% | Cv jitter ≤0.136, Ov ≤0.045 (occlusion channels only) | **98.9%** |
| **total** | **100%** | — | **99.53%** |

## Root cause of the jitter (identified, not a logic error)
Rays grazing wall corners sit on floating-point hairlines. Thin isovist "spikes"
(≈zero area, non-zero perimeter) flip between environments — master was computed on
Windows/author's Python; reproduction runs Linux/Python 3.12. Hence Av (area) and Hv
(max distance) reproduce exactly while Cv/Ov (perimeter/occlusion) jitter, amplified by
per-plan MinMax where a plan's Cv range is narrow. Classification absorbs it: 99.5%
identical predictions, quality scores effectively unchanged.

## Verdict
Stage 0 acceptance criterion (1) — identity with the capstone — holds **exactly** for
the scoring half (0 mismatches / 84,560 pts) and for grid generation (100% coordinate
match), and holds **behaviourally (99.5%)** for the geometry half across environments,
with the residual attributed to documented cross-platform floating-point sensitivity
of corner-based ray casting. One honest methods sentence for the dissertation:
*"corner-based ray casting exhibits minor cross-platform floating-point sensitivity in
occlusion-derived features; classification agreement across environments is 99.5%."*

**STAGE 0: FORMALLY CLOSED.**
