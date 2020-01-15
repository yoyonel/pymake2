from pymake2 import *

debug = True  # <-- set it to True to enable more debugging messages
highlight_errors = True  # To enable the highliter
highlight_warnings = True  # To enable the highliter
HighlightNotes = True  # To enable the highliter

latexfile = 'main.tex'
pdffile = 'main.pdf'


@target
def all(pdf):
    print_color('Build Succeded', colors.Green)
    return True


@target
def pdf(latexfile):
    if run(eval('pdflatex -shell-escape -halt-on-error $(latexfile)'), True, True):
        print_color('Build Succeded', fg='32', b=True)
        run(eval('evince $(pdffile)&'))
        return True


@target
def clean():
    retV = run(eval('rm -f *.aux *.log *.blg *.bbl *.synctex.gz *.out *.cut $(pdffile) *.vtc'), True)
    return retV
