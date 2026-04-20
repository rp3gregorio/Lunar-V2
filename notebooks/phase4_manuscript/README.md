# Phase 4 — Manuscript / Thesis Integration (planned)

Bundle the figures and tables produced in Phases 1–3 into the LaTeX
thesis chapters and the companion PSJ / JGR / Icarus submission.

## Planned notebooks

| Notebook | Purpose |
|---|---|
| `09_thesis_figure_bundle.ipynb` | Regenerate every thesis figure from cached solver outputs at a fixed style (no cell execution drift). |
| `10_paper_tables.ipynb` | CSV → LaTeX table conversions (RMSE, per-sensor biases, K-model comparison). |

## Success criterion

`make thesis` produces the full manuscript PDF with every figure at
300 DPI and every table consistent with the final numerics (no stale
numbers in the LaTeX).
