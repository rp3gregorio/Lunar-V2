# Build the Lunar-V2 pipeline proposal PDF.
#
#   make         ... build the PDF
#   make clean   ... remove LaTeX aux files
#   make view    ... build + open the PDF (if xdg-open is available)
#
TEX = pdflatex -interaction=nonstopmode -halt-on-error
SRC = lunarv2_pipeline.tex
OUT = lunarv2_pipeline.pdf

.PHONY: all clean view

all: $(OUT)

$(OUT): $(SRC)
	$(TEX) $(SRC)
	$(TEX) $(SRC)

view: $(OUT)
	@command -v xdg-open >/dev/null && xdg-open $(OUT) || echo "open $(OUT) manually"

clean:
	rm -f *.aux *.log *.toc *.out *.fdb_latexmk *.fls
