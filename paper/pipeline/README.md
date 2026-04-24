# Lunar-V2 Pipeline Proposal

Multi-page, book-style design document for the four-phase Lunar-V2
thermal modelling pipeline.

## Build

```bash
cd paper/pipeline
make         # produces lunarv2_pipeline.pdf
make clean   # remove aux files
```

## Requirements

Any modern LaTeX distribution. The document uses only `book` class,
`amsmath`, `graphicx`, `booktabs`, `longtable`, `hyperref`, `fancyhdr`
and `titlesec` — all shipped by the default Debian/Ubuntu `texlive-
latex-recommended` + `texlive-latex-extra` metapackages.

```bash
sudo apt-get install texlive-latex-recommended texlive-latex-extra
```

macOS: `brew install --cask mactex-no-gui` (or the full MacTeX).

## What's inside

| Chapter | Contents |
|---|---|
| Overview | At-a-glance table of Phases 1–4 and the overall pipeline success definition. |
| Phase 1 | Point validation against Apollo 15/17 HFE stabilised-window deep sensors. Model formulas (K(T,z), ρ(z), A(i)), validation targets, scope boundaries. |
| Phase 2 | Improved Hayne 2017 global model (H-lat + rock abundance + Martinez-Siegler + Burger + DEM shadowing). |
| Phase 3 | RTM coupling, Jacobian, ice-stability index. |
| Phase 4 | Thesis integration + candidate post-thesis extensions. |
| Appendix A | Repository layout tree. |
| Appendix B | Key references. |

Update this file whenever a phase's scope, data source, or success
criterion is adjusted — the pipeline PDF is the canonical statement of
what the thesis has committed to building.
