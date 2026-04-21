# Lunar-V2 / TSUKIMI Pipeline Roadmap — LaTeX Book

A developer's manual and scientific roadmap for the `Lunar-V2` pipeline,
compiled as a LaTeX book (`\documentclass{book}`) covering Phase 1
through Phase 4.

## Files

```
docs/roadmap/
├── main.tex                         # book entry point
├── preamble.tex                     # packages, colours, styles, TikZ
├── references.bib                   # natbib bibliography
├── chapters/
│   ├── 00_introduction.tex
│   ├── 01_novelty.tex               # four-pillar novelty statement
│   ├── 02_phase1_validation.tex     # Apollo / CE-4 / ChaSTE
│   ├── 03_phase2_illumination.tex   # DEM + horizon + slope
│   ├── 04_phase3_polar_maps.tex     # Diviner + ice-coupled k
│   └── 05_phase4_manuscript.tex     # PSJ manuscript plan
└── figures/                         # optional: copy figures here for Overleaf
```

## Build locally

From `docs/roadmap/`:

```bash
latexmk -pdf main.tex
```

Or manually:

```bash
pdflatex -interaction=nonstopmode main
bibtex main
pdflatex -interaction=nonstopmode main
pdflatex -interaction=nonstopmode main
```

Requires a TeXLive installation (no shell-escape, no `minted`, so
`latexmk -pdf` works out of the box).

## Build on Overleaf

1. From the repo root, copy the Phase 1 figures into the roadmap
   folder so Overleaf can find them:

   ```bash
   cp output/figures/a15_*.pdf  docs/roadmap/figures/
   cp output/figures/a17_*.pdf  docs/roadmap/figures/
   cp output/figures/change4_validation.pdf  docs/roadmap/figures/
   cp output/figures/chaste_validation.pdf   docs/roadmap/figures/
   ```

2. Zip `docs/roadmap/` (including the figures folder):

   ```bash
   cd docs && zip -r roadmap.zip roadmap/
   ```

3. In Overleaf: **New Project → Upload Project → roadmap.zip**.

4. In Overleaf project settings set:
   - **Main document:** `main.tex`
   - **Compiler:** `pdfLaTeX`
   - **TeX Live version:** 2023 or newer.

5. Click **Recompile**. The `\graphicspath` in `preamble.tex` tries
   `../../output/figures/` first (for local builds inside the repo),
   then `./figures/` (for Overleaf after step 1).

## Chapter map

| # | Chapter | Status | Focus |
|---|---------|--------|-------|
| 1 | Introduction                   | done  | pipeline overview, nomenclature |
| 2 | Research Novelty               | done  | four-pillar originality statement |
| 3 | Phase 1 — Point-source validation | shipped | equations, code, figures, RMSE table |
| 4 | Phase 2 — Illumination coupling   | in progress | DEM + horizon + slope + shadow |
| 5 | Phase 3 — Polar maps + ice        | planned | Diviner + ice-coupled `k` |
| 6 | Phase 4 — Manuscript + thesis     | planned | PSJ submission + dissertation |

## Citation convention

The bibliography uses `natbib` with the `plainnat` style.  Cite as
`\citep{hayne2017}` for parenthetical or `\citet{hayne2017}` for
in-text.  Cross-references to equations, figures, and tables use
`cleveref`: `\cref{eq:heat1d}`, `\cref{fig:a15-meanT}`,
`\cref{tab:phase1-rmse}`.
