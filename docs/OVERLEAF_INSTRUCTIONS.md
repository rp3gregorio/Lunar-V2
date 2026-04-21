# Lunar-V2 / TSUKIMI — LaTeX Book on Overleaf

The roadmap book in `docs/roadmap/` is a full LaTeX `\documentclass{book}` project.
It compiles to a 50+ page technical manual covering Phase 1–4 of the TSUKIMI pipeline.

## Quick Start (Overleaf)

### Option 1: Upload from ZIP (recommended)

1. **From the repo root, create a ZIP archive:**
   ```bash
   cd docs
   zip -r roadmap.zip roadmap/
   ```

2. **In Overleaf:**
   - Go to **New Project** → **Upload Project**
   - Select `roadmap.zip`
   - Wait for extraction

3. **Configure:**
   - Click **Menu** → **Settings**
   - Set **Main document** to `roadmap/main.tex`
   - Set **Compiler** to `pdfLaTeX`
   - Set **TeX Live version** to 2023 or later

4. **Compile:**
   - Click **Recompile**
   - Wait ~30–60 seconds (first compile is slower due to bibliography)

### Option 2: Clone directly to Overleaf

If you have Overleaf Premium and a connected GitHub account:

1. Link your GitHub repo to Overleaf
2. Set the root path to `docs/roadmap/`
3. Set main document to `main.tex`

## Build Locally (macOS / Linux / WSL)

### Prerequisites

Requires a TeX distribution (TexLive, MacTeX, or MiKTeX):

**macOS (MacTeX):**
```bash
# Install via Homebrew or MacTeX.pkg from tug.org
brew install macTeX
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install texlive texlive-latex-extra texlive-fonts-recommended
```

**Windows (WSL):**
```bash
# Inside WSL Ubuntu
sudo apt-get install texlive texlive-latex-extra texlive-fonts-recommended
```

### Compile

From `docs/roadmap/`:

```bash
# One-liner (if latexmk is installed):
latexmk -pdf main.tex

# Or manually:
pdflatex -interaction=nonstopmode main
bibtex main
pdflatex -interaction=nonstopmode main
pdflatex -interaction=nonstopmode main
```

The output is `main.pdf` (~3 MB).

## File Structure

```
docs/roadmap/
├── main.tex                    # book entry point + frontmatter
├── preamble.tex                # packages, colors, styles, TikZ
├── references.bib              # 22 natbib entries
├── chapters/
│   ├── 00_introduction.tex     # overview + nomenclature
│   ├── 01_novelty.tex          # four-pillar novelty statement
│   ├── 02_phase1_validation.tex # equations + figures + RMSE table
│   ├── 03_phase2_illumination.tex # DEM + horizon + slope
│   ├── 04_phase3_polar_maps.tex # ice-coupled k + Diviner
│   └── 05_phase4_manuscript.tex # PSJ schedule + deliverables
├── figures/                    # Phase 1 PDF figures (pre-staged for Overleaf)
│   ├── a15_stability_region.pdf
│   ├── a15_mean_T_profile.pdf
│   ├── a17_mean_T_profile.pdf
│   └── ... (9 total)
└── README.md                   # this guide
```

## Troubleshooting

### Build fails: "citations not found"

After modifying `references.bib`, re-run the full sequence:
```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

### Build fails: "figure not found"

The `\graphicspath` in `preamble.tex` tries:
1. `../../output/figures/` (for local builds inside the repo)
2. `./figures/` (for Overleaf after ZIP upload)

If you moved figures, check that they're in one of these paths.

### "tcbox unknown" or tcolorbox errors

Ensure `\usepackage[most]{tcolorbox}` is uncommented in `preamble.tex`.
On Overleaf, this should work out of the box; if not, check that you're
using TeX Live 2020 or later.

## Customisation

### Colours

Defined in `preamble.tex`:
- `\definecolor{noveltyOrange}{HTML}{D97706}` — research novelty boxes
- `\definecolor{conceptBlue}{HTML}{1D4ED8}` — concept boxes
- `\definecolor{warningRed}{HTML}{B91C1C}` — warning boxes
- `\definecolor{milestoneGreen}{HTML}{047857}` — milestone boxes

### Fonts

- Default: Computer Modern (TeX's built-in)
- Body: 11pt (book class default)
- Code: `\ttfamily\footnotesize` (fixed-width)

To use Helvetica instead, add to `preamble.tex`:
```latex
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
```

## Citation Style

Uses `natbib` with `plainnat`:
- `\citep{hayne2017}` → (Hayne 2017)
- `\citet{hayne2017}` → Hayne 2017
- `\cref{eq:heat1d}` → Eq. (2.1) (via `cleveref`)
- `\cref{fig:a15-meanT}` → Fig. 2.3
- `\cref{tab:phase1-rmse}` → Table 2.1

## Extending the Book

### Add a new chapter

1. Create `chapters/06_myheading.tex` with `\chapter{...}` and content
2. In `main.tex`, add:
   ```latex
   \input{chapters/06_myheading}
   ```
3. Re-compile

### Add figures

Place PDFs in `figures/` and reference with:
```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.8\linewidth]{myplot.pdf}
  \caption{My caption.}
  \label{fig:myplot}
\end{figure}
```

### Add equations

Use `align*` or `equation`:
```latex
\begin{equation}
  T = \frac{Q}{\sigma A^2}
  \label{eq:mytherm}
\end{equation}
```

Reference with `\cref{eq:mytherm}`.

## Rendering Issues on Overleaf

If preview hangs or is blank:

1. Click **Logs and output files** → **Clear cached files**
2. Click **Recompile** from scratch
3. Check the raw logs for error messages

Typical causes:
- Missing figures (check `figures/` folder)
- Unmatched braces in `preamble.tex`
- Non-ASCII characters in `references.bib` (use `\'{e}` instead of `é`)

## Support

Questions about the LaTeX book setup? Check:
- `README.md` in `docs/roadmap/` for quick build guide
- `preamble.tex` for package versions and styles
- The `.md` files in `docs/` for broader project documentation

For physics/numerical questions, see `notebooks/phase1_validation/README.md`.
