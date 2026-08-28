"""Rigenera dashboard.html, pricing.html e guida-costi.html a partire da
tokens.csv e operations.csv.

Package richiamato dall'hook Stop (~/.claude/hooks/log_tokens.py, via
`import generate_dashboard; generate_dashboard.main()`) alla fine di ogni
turno. Struttura:

    config.py            percorsi di input/output, dashboard_config.json
    pricing.py            listino prezzi (unica fonte per le 3 pagine)
    timeutils.py           ora italiana, formattazione date
    numfmt.py                formattazione numeri in stile italiano
    data.py                   lettura tokens.csv / operations.csv
    sessions.py                titolo/progetto per sessione, con cache
    templating.py               caricamento dei template HTML
    templates/                   i tre template, HTML/CSS/JS inline
    render_dashboard.py           genera dashboard.html
    render_pricing.py              genera pricing.html
    render_guide.py                 genera guida-costi.html
    main.py                          orchestrazione (vedi main.main)

Vedi NOTES.md nel repo dashboard-token per le decisioni di progetto.

NOTA PER CHI NON CONOSCE PYTHON:
Una CARTELLA che contiene un file chiamato esattamente "__init__.py" (come
questa: generate_dashboard/) e' quello che Python chiama un "package": un
gruppo di file .py che si possono importare insieme come se fossero un
unico modulo. Quando da fuori si scrive "import generate_dashboard", Python
esegue PRIMA il codice di questo file __init__.py -- e' come dire "questa e'
la porta d'ingresso della cartella, decide tu cosa mostrare a chi entra".

La riga "from .main import main" qui sotto prende la funzione main()
definita in main.py (il "." vuol dire "guarda dentro questo stesso
package") e la rende disponibile direttamente come generate_dashboard.main,
senza dover scrivere generate_dashboard.main.main. E' un abbellimento
puramente estetico per chi usa il package da fuori.

"__all__" e' una lista opzionale che dichiara esplicitamente "queste sono le
uniche cose pensate per essere usate da fuori questo package" (qui: solo
"main"); serve soprattutto da documentazione per chi legge il codice.

Il blocco finale "if __name__ == '__main__':" e' un'idioma molto comune in
Python: "__name__" e' una variabile speciale che Python riempie con
"__main__" SOLO se questo file viene eseguito direttamente (es. "python3
-m generate_dashboard"), mentre vale il nome del modulo se il file viene
importato da un altro script (come fa log_tokens.py). Quindi questa riga
vuol dire: "se qualcuno lancia questo package direttamente da terminale,
esegui subito main(); se invece viene solo importato, non fare nulla finche'
non viene chiamato esplicitamente main()".

[EN] Regenerates dashboard.html, pricing.html and guida-costi.html from
tokens.csv and operations.csv.

Package invoked by the Stop hook (~/.claude/hooks/log_tokens.py, via
`import generate_dashboard; generate_dashboard.main()`) at the end of
every turn. Structure:

    config.py            input/output paths, dashboard_config.json
    pricing.py            price list (single source for the 3 pages)
    timeutils.py           Italian local time, date formatting
    numfmt.py                Italian-style number formatting
    data.py                   reading tokens.csv / operations.csv
    sessions.py                per-session title/project, with cache
    templating.py               loading of the HTML templates
    templates/                   the three templates, inline HTML/CSS/JS
    render_dashboard.py           generates dashboard.html
    render_pricing.py              generates pricing.html
    render_guide.py                 generates guida-costi.html
    main.py                          orchestration (see main.main)

See NOTES.md in the dashboard-token repo for the design decisions.

NOTE FOR READERS NEW TO PYTHON:
A FOLDER containing a file named exactly "__init__.py" (like this one:
generate_dashboard/) is what Python calls a "package": a group of .py
files that can be imported together as if they were a single module.
When outside code writes "import generate_dashboard", Python FIRST runs
the code in this __init__.py file -- it is like saying "this is the
front door of the folder, and it decides what to show to whoever walks
in".

The line "from .main import main" below takes the main() function
defined in main.py (the "." means "look inside this same package") and
makes it available directly as generate_dashboard.main, without having
to write generate_dashboard.main.main. It is a purely cosmetic nicety
for whoever uses the package from outside.

"__all__" is an optional list that explicitly declares "these are the
only things meant to be used from outside this package" (here: only
"main"); it mostly serves as documentation for whoever reads the code.

The final "if __name__ == '__main__':" block is a very common Python
idiom: "__name__" is a special variable that Python fills with
"__main__" ONLY if this file is executed directly (e.g. "python3 -m
generate_dashboard"), while it holds the module name if the file is
imported by another script (as log_tokens.py does). So this line means:
"if someone launches this package directly from a terminal, run main()
right away; if it is merely imported, do nothing until main() is
called explicitly".
"""
from .main import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
