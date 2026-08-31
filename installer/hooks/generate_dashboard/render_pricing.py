"""Genera pricing.html: tabella statica del listino, una riga per modello.

NOTA PER CHI NON CONOSCE PYTHON:
A differenza di render_dashboard.py (che passa i dati come JSON al
JavaScript), qui il testo HTML della tabella viene costruito DIRETTAMENTE in
Python, riga per riga, come stringhe. E' una scelta ragionevole perche'
questa pagina e' statica (non ha filtri interattivi da far girare nel
browser): basta produrre l'HTML gia' pronto una volta sola alla
generazione.

[EN] Generates pricing.html: static table of the price list, one row
per model.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
Unlike render_dashboard.py (which passes the data as JSON to the
JavaScript), here the HTML text of the table is built DIRECTLY in
Python, row by row, as strings. It is a reasonable choice because this
page is static (it has no interactive filters to run in the browser):
producing the ready-made HTML once at generation time is enough.
"""
from . import config
from . import i18n
from . import pricing
from . import templating


# La griglia dei cambi: una riga per valuta di partenza, una colonna per
# valuta di arrivo, e in ogni cella quanto vale una unita' della prima
# espressa nella seconda.
#
# Tutti i cambi che conosciamo partono dal dollaro (pricing.USD_RATES), ma
# la tabella deve dire anche quanto vale un euro in sterline. Si ricava dai
# due che abbiamo: passando dal dollaro, un'unita' di "da" vale 1/rate[da]
# dollari, e quei dollari valgono rate[a] unita' di "a". Quindi il rapporto
# e' rate[a] / rate[da] -- il dollaro sparisce nel mezzo, ed e' il motivo
# per cui basta una colonna di cambi e non una matrice da mantenere.
#
# La diagonale viene 1.0 da sola, senza doverla scrivere come caso a parte:
# rate[x] / rate[x]. Le celle diagonali ricevono comunque una classe
# propria, ma per il colore, non per il calcolo.
#
# I numeri restano in forma "1.1628", col punto decimale, come i prezzi in
# dollari nella tabella qui sopra: la pagina e' un file solo per tutte le
# lingue, quindi qualunque numero cotto qui dentro dalla generazione non
# puo' seguire la lingua scelta a runtime. Quattro decimali perche' un
# cambio a due ("0,86") perde abbastanza da spostare gli importi.
# [EN] The rate grid: one row per source currency, one column per target
# currency, and in each cell what one unit of the first is worth expressed
# in the second.
#
# Every rate we know starts from the dollar (pricing.USD_RATES), but the
# table must also say what a euro is worth in pounds. It follows from the
# two we have: going through the dollar, one unit of "from" is worth
# 1/rate[from] dollars, and those dollars are worth rate[to] units of "to".
# So the ratio is rate[to] / rate[from] -- the dollar cancels in the
# middle, and that is why one column of rates is enough and no matrix has
# to be maintained.
#
# The diagonal comes out as 1.0 by itself, with no special case to write:
# rate[x] / rate[x]. Diagonal cells still get their own class, but for the
# colour, not for the arithmetic.
#
# The numbers stay in "1.1628" form, with a dot decimal, like the dollar
# prices in the table above: the page is a single file for every language,
# so any number baked in here at generation time cannot follow the
# language chosen at runtime. Four decimals because a rate at two ("0.86")
# loses enough to move the amounts.
def _rate_grid():
    codes = [c for c in i18n.CURRENCIES if c in pricing.USD_RATES]
    head = "".join(
        '        <th class="num">%s</th>' % i18n.CURRENCY_CODES[c]
        for c in codes
    )
    rows = []
    for src in codes:
        cells = []
        for dst in codes:
            ratio = pricing.USD_RATES[dst] / pricing.USD_RATES[src]
            klass = "num rate-self" if src == dst else "num"
            cells.append('<td class="%s">%.4f</td>' % (klass, ratio))
        rows.append(
            '        <tr style="--row-i:%d">'
            '<td class="rate-from">1 %s</td>%s</tr>'
            % (len(rows), i18n.CURRENCY_CODES[src], "".join(cells))
        )
    return head, "\n".join(rows)


def render():
    # qui accumuliamo un pezzo di HTML (una stringa) per riga di tabella
    # [EN] here we accumulate one chunk of HTML (a string) per table row
    rows = []

    # pricing.MODEL_PRICING.items() scorre il dizionario restituendo, per
    # ogni voce, una coppia (chiave, valore): qui "key" e' es.
    # "claude-sonnet-5" e "m" e' il dizionario {"label": ..., "input": ...}.
    # [EN] pricing.MODEL_PRICING.items() iterates over the dictionary
    # returning, for each entry, a (key, value) pair: here "key" is
    # e.g. "claude-sonnet-5" and "m" is the dictionary
    # {"label": ..., "input": ...}.
    for key, m in pricing.MODEL_PRICING.items():
        cache_write = m["input"] * pricing.CACHE_WRITE_MULTIPLIER
        cache_read = m["input"] * pricing.CACHE_READ_MULTIPLIER

        # Le righe che iniziano con f'...' o f"..." sono F-STRING: un modo
        # di scrivere stringhe con dei valori Python incollati dentro,
        # scrivendoli tra parentesi graffe {come_questa}. Qui costruiamo
        # una riga di tabella HTML (<tr>...</tr>) con dentro nome del
        # modello, i due prezzi, i due prezzi di cache calcolati sopra, e
        # la chiave tecnica. "{m['input']:.2f}" vuol dire "il valore
        # m['input'], formattato come numero con 2 cifre decimali".
        # Diverse stringhe scritte una sotto l'altra tra parentesi tonde
        # (come qui sotto) vengono automaticamente incollate insieme da
        # Python in un'unica stringa, senza bisogno di un "+" esplicito --
        # e' solo un modo per andare a capo nel codice sorgente senza
        # spezzare il testo HTML prodotto.
        # style="--row-i:N" e' solo il numero d'ordine della riga,
        # passato al CSS come "variabile personalizzata": il foglio di
        # stile di pricing.html lo usa per scaglionare l'entrata delle
        # righe (vedi la regola su tbody tr li' dentro).
        # [EN] Lines starting with f'...' or f"..." are F-STRINGS: a
        # way of writing strings with Python values pasted inside,
        # written between curly braces {like_this}. Here we build an
        # HTML table row (<tr>...</tr>) containing the model name, the
        # two prices, the two cache prices computed above, and the
        # technical key. "{m['input']:.2f}" means "the value
        # m['input'], formatted as a number with 2 decimal digits".
        # Several strings written one below the other between round
        # brackets (as below) are automatically glued together by
        # Python into a single string, with no explicit "+" needed --
        # it is just a way of wrapping lines in the source code without
        # breaking the produced HTML text.
        # style="--row-i:N" is just the row's ordinal number, passed to
        # the CSS as a "custom property": the pricing.html stylesheet
        # uses it to stagger the rows' entrance (see the rule on tbody
        # tr in there).
        rows.append(
            f'<tr style="--row-i:{len(rows)}">'
            f'<td class="model-name">{m["label"]}</td>'
            f'<td class="num">${m["input"]:.2f}</td>'
            f'<td class="num">${m["output"]:.2f}</td>'
            f'<td class="num">${cache_write:.2f}</td>'
            f'<td class="num">${cache_read:.2f}</td>'
            f'<td><code>{key}</code></td>'
            "</tr>"
        )

        # Se questo modello ha una nota (es. la promo di Sonnet 5),
        # aggiungiamo una seconda riga apposta sotto, che occupa tutte le
        # colonne (colspan="6") per mostrare il testo della nota per intero.
        # [EN] If this model has a note (e.g. the Sonnet 5 promo), we
        # add a dedicated second row below, spanning all columns
        # (colspan="6") to show the note text in full.
        note = m.get("note", "")
        if note:
            rows.append(f'<tr class="note-row" style="--row-i:{len(rows)}"><td colspan="6" class="model-note">{note}</td></tr>')

    html = templating.load_template("pricing.html")
    html = html.replace("__HEADER_CSS__", templating.HEADER_CSS)
    # I due pezzi dell'animazione di rivelazione allo scroll, condivisi
    # con le altre pagine (vedi header.py): lo "starter" nell'<head> e
    # l'osservatore in fondo al <body>.
    # [EN] The two pieces of the reveal-on-scroll animation, shared
    # with the other pages (see header.py): the "starter" in the <head>
    # and the observer at the bottom of the <body>.
    html = html.replace("__I18N_BOOT__", templating.I18N_BOOT)
    html = html.replace("__I18N_APPLY__", templating.I18N_APPLY)
    html = html.replace("__REVEAL_BOOT__", templating.REVEAL_BOOT)
    html = html.replace("__REVEAL_JS__", templating.REVEAL_JS)
    html = html.replace("__SITE_HEADER__", templating.render_header("pricing"))
    # "\n        ".join(rows) incolla tutte le righe di "rows" in un'unica
    # stringa, mettendo tra una e l'altra un a-capo seguito da 8 spazi (solo
    # per far apparire l'HTML finale ben indentato se qualcuno lo apre e
    # guarda il sorgente). E' l'operazione "inversa" di uno split: da lista
    # di pezzi a stringa unica.
    # [EN] "\n        ".join(rows) glues all the rows of "rows" into a
    # single string, putting between each a newline followed by 8
    # spaces (only to make the final HTML look nicely indented if
    # someone opens it and looks at the source). It is the "inverse"
    # operation of a split: from a list of pieces to a single string.
    html = html.replace("__ROWS__", "\n        ".join(rows))

    rate_head, rate_rows = _rate_grid()
    html = html.replace("__RATE_HEAD__", rate_head)
    html = html.replace("__RATE_ROWS__", rate_rows)
    html = html.replace("__RATES_DATE__", pricing.USD_RATES_DATE)

    with open(config.OUT_PRICING_HTML, "w", encoding="utf-8") as f:
        f.write(html)
