GNUPLOT ?= gnuplot

scripts := $(wildcard scripts/*.gpl)

.PHONY: graphs
graphs:
	for s in $(scripts); do\
	  $(GNUPLOT) $$s; \
	done

.PHONY: clean
clean:
	$(RM) *.pdf

