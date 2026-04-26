# Lunar-V2 / TSUKIMI — Phase-1 Letter Article (Draft)

This bundle contains a draft GRL letter article for the Phase-1
Apollo Heat-Flow Experiment validation of the Lunar-V2 / TSUKIMI
thermal modelling pipeline, plus a comprehensive book-like
Supporting-Information appendix.

## Contents

```
letter/
  letter.tex          # main GRL letter (article class, GRL-compatible)
  references.bib      # shared bibliography
  letter.pdf          # compiled PDF (8 pages)
  figures/            # the four letter-grade figures (PDF)
appendix/
  appendix.tex        # book-like SI (report class, ~25 pages)
  references.bib      # same bib (copied for self-contained build)
  appendix.pdf        # compiled PDF (25 pages)
  figures/            # SI Figs S1-S11 (PDF)
README.md             # this file
```

## Compile from source

Both files are self-contained. With any modern TeX Live (2020+):

```bash
cd letter
pdflatex letter && bibtex letter && pdflatex letter && pdflatex letter

cd ../appendix
pdflatex appendix && bibtex appendix && pdflatex appendix && pdflatex appendix
```

## Overleaf

To use Overleaf, upload the `letter/` folder (or `appendix/`) as a
new project. The main file is `letter.tex` (resp. `appendix.tex`).
Overleaf will autodetect pdflatex+bibtex; no other configuration
needed.

## Submitting to AGU/GRL

The letter is written in `\documentclass{article}` for portability.
To submit to GRL, swap the first line of `letter.tex` for the AGU
class:

```latex
\documentclass[draft,grl]{agutex}
```

All other commands (siunitx, natbib, hyperref, booktabs) are
AGU-compatible. Figures are PDF and 7.0 in-wide compatible with the
AGU double-column figure budget.

## Reproducibility

All figures are produced by the open-source notebooks at
<https://github.com/rp3gregorio/Lunar-V2> on branch
`claude/cleanup-repo-organization-EcS3U`:

- `notebooks/phase1_validation/01_apollo_validation.ipynb` — Letter
  Figs 1-4, Table 1, SI Figs S7-S11.
- `notebooks/phase1_validation/01b_apollo_SI.ipynb` — SI Figs S1-S6.
