PAPER = paper
TEX = $(wildcard *.tex)
BIB = bib.bib

PLOTS = ../generated/plots/boxplot_unique_cat.pdf ../generated/plots/platform-dependent-and-independent-in-projects.pdf ../generated/plots/implementation.pdf ../generated/plots/fourplots.pdf ../generated/plots/tool-evaluation.pdf ../generated/historical-data/plots/png/4740-intel-tinycbor.csv.png

.PHONY: all clean

$(PAPER).pdf: $(TEX) bib.bib ../generated/latex/generated.tex $(PLOTS)
	pdflatex $(PAPER)
	bibtex $(PAPER)
	pdflatex $(PAPER)
	pdflatex $(PAPER)

########################### csv files ##################################

# Compute data for Figure 1
../generated/unique_builtins_per_category.csv ../generated/builtins_per_category.csv:
	../src/boxplot-builtins-per-project.py

# Compute data for Figure 4.
../generated/historical-data/csv/4740-intel-tinycbor.csv ../generated/historical-data/csv/252-sheepdog-sheepdog.csv ../generated/historical-data/csv/5-libav-libav.csv ../generated/historical-data/csv/761-vstakhov-libucl.csv:
	../src/historical-data.py

########################### latex commands #############################

../generated/latex/generated.tex ../generated/platform-specific-builtins-in-projects.csv ../generated/platform-independent-builtins-in-projects.csv: ../src/stats.py
	../src/stats.py > ../generated/latex/generated.tex

########################### plot tables ################################

# Plots Table 2 and generates csv files for Figure 3
# IMPORTANT: Note that regenerating this table needs about 15 hours on our machine.
../generated/greedy-all.csv ../generated/greedy-machine-independent.csv ../generated/most-frequent-all.csv ../generated/most-frequent-machine-independent.csv: ../src/implementation_effort.py
# commented out to prevent that the time-intensive generation of hte table is accidentally triggered:
#	../src/implementation_effort.py > ../generated/latex/implementtable.tex


########################### plot figures ###############################

plots: $(PLOTS)

# plot Figure 1 (number of architecture-specific and architecture-independent builtins per project)
../generated/plots/boxplot_unique_cat.pdf: ../src/plots/boxplot.r ../generated/unique_builtins_per_category.csv ../generated/builtins_per_category.csv
	Rscript ../src/plots/boxplot.r

# plot Figure 2 (number of projects that rely on architecture-independent and architecture-specific builtins)
../generated/plots/platform-dependent-and-independent-in-projects.pdf: ../generated/platform-independent-builtins-in-projects.csv ../generated/platform-specific-builtins-in-projects.csv ../src/plots/builtin-category-barplots.r
	Rscript ../src/plots/builtin-category-barplots.r

# plot Figure 3 (the implementation effort evaluated using a greedy and frequency-based strategy)
../generated/plots/implementation.pdf: ../src/plots/implementation.r ../generated/greedy-all.csv ../generated/greedy-machine-independent.csv ../generated/most-frequent-all.csv ../generated/most-frequent-machine-independent.csv
	Rscript ../src/plots/implementation.r

# plot Figure 4 (builtin development illustrated on four representative projects)
../generated/plots/fourplots.pdf: ../src/plots/four-plots.r ../generated/historical-data/csv/4740-intel-tinycbor.csv ../generated/historical-data/csv/252-sheepdog-sheepdog.csv ../generated/historical-data/csv/5-libav-libav.csv ../generated/historical-data/csv/761-vstakhov-libucl.csv
	Rscript ../src/plots/four-plots.r

# plot Figure 5 (how well various tools perform on the GCC test cases)
../generated/plots/tool-evaluation.pdf: ../src/plots/tool-evaluation.r ../gcc-builtin-tests/tool-evaluation.csv
	Rscript ../src/plots/tool-evaluation.r

# plot the historical trend figures. Note that this step takes a while (15 minutes on our machine)
../generated/historical-data/plots/png/4740-intel-tinycbor.csv.png:
	Rscript ../src/plots/make-historical-dataplots.r

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PAPER).pdf

