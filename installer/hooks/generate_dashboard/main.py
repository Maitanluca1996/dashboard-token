"""Orchestrazione: legge i log e rigenera le tre pagine in OUT_DIR.

Per aggiungere una quarta pagina: un nuovo modulo render_xxx.py con una
render(), un OUT_XXX_HTML in config.py, il template in templates/, e una
riga qui sotto.

NOTA PER CHI NON CONOSCE PYTHON:
Questo e' il file "regista" del package: non calcola nulla direttamente,
chiama in ordine le funzioni degli altri moduli. E' la funzione main() qui
sotto quella che generate_dashboard/__init__.py espone come punto
d'ingresso del package intero (vedi il commento in __init__.py), ed e' lei
che log_tokens.py invoca ad ogni fine turno con
"import generate_dashboard; generate_dashboard.main()".

[EN] Orchestration: reads the logs and regenerates the three pages in
OUT_DIR.

To add a fourth page: a new render_xxx.py module with a render(), an
OUT_XXX_HTML in config.py, the template in templates/, and one line
below.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
This is the "director" file of the package: it computes nothing
directly, it calls the other modules' functions in order. The main()
function below is the one that generate_dashboard/__init__.py exposes
as the entry point of the whole package (see the comment in
__init__.py), and it is the one log_tokens.py invokes at the end of
every turn with "import generate_dashboard; generate_dashboard.main()".
"""
import json
import os

from . import config
from . import data
from . import i18n
from . import render_dashboard
from . import render_guide
from . import render_pricing
from . import timeutils


def main():
    # 1. Leggiamo tutti i dati grezzi dai due file CSV di log.
    # [EN] 1. We read all the raw data from the two CSV log files.
    tokens = data.read_tokens()
    ops = data.read_ops()

    # 2. Ci assicuriamo che la cartella di output esista (se e' il primissimo
    #    avvio su questo PC, potrebbe non esserci ancora). exist_ok=True
    #    vuol dire "se esiste gia', va bene comunque, non dare errore".
    # [EN] 2. We make sure the output folder exists (on the very first
    # run on this PC, it might not be there yet). exist_ok=True means
    # "if it already exists, that is fine, do not raise an error".
    os.makedirs(config.OUT_DIR, exist_ok=True)

    # 3. Un solo orario di generazione per tutte e 3 le pagine (prima ogni
    #    render_*.py lo calcolava per conto suo, con la teorica possibilita'
    #    di 3 orari leggermente diversi), scritto in site-meta.js come
    #    variabile JS: e' l'intestazione condivisa (header.py) a leggerla a
    #    runtime nel browser, cosi' il testo dell'orario non finisce piu'
    #    "congelato" dentro i 3 file .html.
    # [EN] 3. A single generation time for all 3 pages (previously each
    # render_*.py computed it on its own, with the theoretical
    # possibility of 3 slightly different times), written into
    # site-meta.js as a JS variable: the shared header (header.py) reads
    # it at runtime in the browser, so the time text no longer ends up
    # "frozen" inside the 3 .html files.
    generated_at = timeutils.generated_at_now()
    with open(config.OUT_META_JS, "w", encoding="utf-8") as f:
        f.write("var GENERATED_AT = " + json.dumps(generated_at) + ";\n")

    # 3-bis. Le stringhe tradotte, tutte le lingue insieme, in un unico
    #    site-i18n.js che le tre pagine caricano nel loro <head>. Il
    #    perche' di ogni scelta (un modulo Python invece di un JSON, tutte
    #    le lingue invece della sola scelta, il <head> invece del fondo
    #    pagina) sta nel docstring di i18n.py: qui basta sapere che senza
    #    questo file le pagine mostrerebbero i nomi delle chiavi.
    # [EN] 3-bis. The translated strings, all languages together, in a
    # single site-i18n.js that the three pages load in their <head>. The
    # reason for every choice (a Python module instead of a JSON, all
    # languages instead of just the chosen one, the <head> instead of the
    # bottom of the page) is in i18n.py's docstring: here it is enough to
    # know that without this file the pages would show the key names.
    with open(config.OUT_I18N_JS, "w", encoding="utf-8") as f:
        f.write(i18n.js_payload())

    # 4. Ogni funzione render() qui sotto legge i dati che le servono e
    #    scrive la propria pagina HTML finale su disco. Vengono chiamate in
    #    sequenza, una dopo l'altra (non e' importante l'ordine tra loro:
    #    sono indipendenti, ognuna scrive un file diverso). Nessuna delle
    #    tre ha piu' bisogno di generated_at: lo script di site-meta.js
    #    scritto sopra basta da solo a valorizzare l'orario in pagina.
    # [EN] 4. Each render() function below reads the data it needs and
    # writes its own final HTML page to disk. They are called in
    # sequence, one after the other (the order between them does not
    # matter: they are independent, each writes a different file). None
    # of the three needs generated_at anymore: the site-meta.js script
    # written above is enough on its own to fill in the time on the
    # page.
    render_dashboard.render(tokens, ops)
    render_pricing.render()
    render_guide.render()
