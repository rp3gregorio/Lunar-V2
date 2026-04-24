# Phase 4 — Thesis Integration & Further Improvements (TBD)

Bundle the figures and tables produced in Phases 1–3 into the LaTeX
thesis chapters and the companion PSJ / JGR / Icarus submission.
This phase also collects the "future work" follow-ons that would extend
the Lunar-V2 pipeline beyond the thesis scope.

## Planned notebooks

| Notebook | Purpose |
|---|---|
| `12_thesis_figure_bundle.ipynb` | Regenerate every thesis figure from cached solver outputs at a fixed style (no cell execution drift). |
| `13_paper_tables.ipynb` | CSV → LaTeX table conversions (Apollo RMSE, global Diviner residuals, retrieval Jacobian condition numbers). |
| `14_future_work.ipynb` | Scoping notebook for post-thesis extensions. |

## Candidate "future work" extensions (non-thesis)

1. **Small-scale surface roughness** as an additional forward-model
   layer (Bandfield et al. 2015; Warren et al. 2019) — shrinks residual
   brightness-T bias at high-phase angle retrievals.
2. **Time-dependent ice retreat** — couple the Phase-3 ice-stability
   map to a Diviner-constrained surface-age model and forward-model
   ice-loss rates.
3. **Mars adaptation** — port the improved solver to MGS-MOLA +
   Mars-Climate-Database for a cross-target validation.
4. **TSUKIMI in-flight retrieval harness** — operational wrapper that
   turns the Jacobian into a real Levenberg-Marquardt retrieval with
   the observation-error covariance from radiometric cal.

## Success criterion

`make thesis` produces the full manuscript PDF with every figure at
300 DPI and every table consistent with the final numerics (no stale
numbers in the LaTeX). The pipeline proposal PDF under `paper/pipeline/`
accurately describes what is in each phase folder.
