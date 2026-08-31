"""Genera guida-costi.html: guida all'ottimizzazione dei costi.

Prezzi, rapporti e soglie di convenienza NON sono scritti a mano nel testo:
vengono ricalcolati da pricing.MODEL_PRICING ad ogni rigenerazione. Cosi'
quando il listino cambia (es. la fine della promo Sonnet 5 il 2026-08-31) la
pagina resta coerente da sola invece di diventare silenziosamente sbagliata
-- che e' esattamente il tipo di errore piu' difficile da notare in un
documento di riferimento.

NOTA PER CHI NON CONOSCE PYTHON:
Come render_pricing.py, anche qui l'HTML viene costruito come testo diretto
in Python (niente JSON/JavaScript): la pagina e' statica, calcolata una
volta sola alla generazione.

[EN] Generates guida-costi.html: the cost-optimization guide.

Prices, ratios and break-even thresholds are NOT hand-written in the
text: they are recomputed from pricing.MODEL_PRICING on every
regeneration. This way when the price list changes (e.g. the end of the
Sonnet 5 promo on 2026-08-31) the page stays consistent on its own
instead of silently becoming wrong -- which is exactly the kind of
error hardest to notice in a reference document.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
Like render_pricing.py, here too the HTML is built as direct text in
Python (no JSON/JavaScript): the page is static, computed once at
generation time.
"""
from . import config
from . import guide_css
from . import i18n
from . import numfmt
from . import pricing
from . import templating

# Modelli mostrati nella tabella di convenienza: la "scala" di riferimento
# attuale, non tutti e 9 quelli del tariffario (le versioni precedenti
# renderebbero la tabella illeggibile senza aggiungere nulla al
# ragionamento). Le chiavi mancanti vengono semplicemente saltate, cosi' il
# giorno che una sparisce da MODEL_PRICING la pagina continua a generarsi.
# [EN] Models shown in the break-even table: the current reference
# "ladder", not all 9 from the price list (previous versions would make
# the table unreadable without adding anything to the reasoning).
# Missing keys are simply skipped, so the day one disappears from
# MODEL_PRICING the page keeps generating.
GUIDE_MODELS = ["claude-haiku-4-5", "claude-sonnet-5", "claude-opus-5", "claude-fable-5"]

# Parametri dell'esempio numerico sulla cache nella sezione 1 della guida.
# [EN] Parameters of the numeric cache example in section 1 of the
# guide.
GUIDE_EX_CONTEXT_TOKENS = 60000
GUIDE_EX_TURNS = 40


def _price_rows(base_in, base_label, lang, T):
    """Tabella modelli con soglia di convenienza.

    Il rapporto e' identico calcolato su input o su output (in questo
    listino output = 5x input per ogni modello), quindi un solo rapporto
    descrive correttamente la convenienza complessiva.

    [EN] Model table with break-even threshold.

    The ratio is identical whether computed on input or on output (in
    this price list output = 5x input for every model), so a single
    ratio correctly describes the overall convenience.
    """
    rows = []
    for key in GUIDE_MODELS:
        # dict.get(chiave) restituisce None se la chiave non c'e' (invece di
        # dare errore come farebbe dict[chiave]): "if not m: continue"
        # salta silenziosamente i modelli non (piu') presenti nel listino.
        # [EN] dict.get(key) returns None if the key is not there
        # (instead of raising an error as dict[key] would): "if not m:
        # continue" silently skips models not (or no longer) present in
        # the price list.
        m = pricing.MODEL_PRICING.get(key)
        if not m:
            continue

        # Rapporto tra il prezzo di questo modello e quello del modello di
        # riferimento (base_in, es. Sonnet 5). ratio < 1 vuol dire "questo
        # modello costa meno del riferimento"; ratio > 1 vuol dire "costa di
        # piu'".
        # [EN] Ratio between this model's price and the reference
        # model's (base_in, e.g. Sonnet 5). ratio < 1 means "this model
        # costs less than the reference"; ratio > 1 means "it costs
        # more".
        ratio = m["input"] / base_in
        is_base = key == pricing.DEFAULT_MODEL_KEY

        if is_base:
            verdict = T("guide.verdictBase")
        elif ratio < 1:
            # Modello piu' economico: conviene finche' non si consumano
            # troppi PIU' token del riferimento per compensare il prezzo
            # unitario piu' basso. "1 / ratio" e' proprio quel moltiplicatore
            # massimo di token in piu' che si puo' permettere restando
            # comunque piu' economici.
            # [EN] Cheaper model: it is worthwhile as long as it does
            # not consume too many MORE tokens than the reference,
            # offsetting the lower unit price. "1 / ratio" is precisely
            # that maximum multiplier of extra tokens one can afford
            # while still coming out cheaper.
            verdict = T("guide.verdictCheaper",
                        mult=numfmt.num(1 / ratio, 1, lang), base=base_label)
        else:
            # Modello piu' costoso: conviene solo se il compito richiede
            # DECISAMENTE meno token del riferimento. "100 / ratio" esprime
            # quella soglia come percentuale.
            # [EN] More expensive model: it is worthwhile only if the
            # task requires DEFINITELY fewer tokens than the reference.
            # "100 / ratio" expresses that threshold as a percentage.
            verdict = T("guide.verdictPricier",
                        pct=numfmt.num(100 / ratio, 0, lang), base=base_label)

        note = m.get("note", "")
        if note:
            # "+=" su una stringa vuol dire "incolla questo testo alla fine
            # di quello che c'era gia' in verdict" (equivalente a
            # "verdict = verdict + ...").
            # [EN] "+=" on a string means "glue this text to the end of
            # what was already in verdict" (equivalent to
            # "verdict = verdict + ...").
            verdict += '<span class="cell-note">{}</span>'.format(note)

        # I due prezzi portano il valore in dollari in data-i18n-money e
        # il testo gia' scritto come ripiego: e' la stessa coppia usata
        # dal tariffario, e per lo stesso motivo. La guida esiste in un
        # file per lingua ma non in un file per valuta, quindi il numero
        # definitivo lo scrive il browser (I18N_APPLY, vedi header.py)
        # nella valuta scelta nell'intestazione.
        # Il rapporto fra i modelli NON passa di li': e' un numero puro,
        # e un rapporto non cambia cambiando valuta -- convertirlo
        # vorrebbe dire moltiplicarlo per il cambio, cioe' sbagliarlo.
        # [EN] The two prices carry the dollar value in data-i18n-money
        # and the already-written text as a fallback: it is the same pair
        # the price list uses, and for the same reason. The guide exists
        # as one file per language but not as one file per currency, so
        # the final number is written by the browser (I18N_APPLY, see
        # header.py) in the currency chosen in the header.
        # The ratio between models does NOT go through there: it is a
        # pure number, and a ratio does not change when the currency
        # changes -- converting it would mean multiplying it by the rate,
        # that is, getting it wrong.
        rows.append(
            '<tr{hi}>'
            '<td class="model-name">{label}</td>'
            '<td class="num" data-i18n-money="{inRaw:.6f}">${inp}</td>'
            '<td class="num" data-i18n-money="{outRaw:.6f}">${out}</td>'
            '<td class="num">{ratio}&times;</td>'
            '<td>{verdict}</td>'
            "</tr>".format(
                inRaw=m["input"],
                outRaw=m["output"],
                # Se questo e' il modello di riferimento, aggiunge
                # class="row-hi" alla riga per evidenziarla graficamente;
                # altrimenti nessun attributo extra (stringa vuota).
                # [EN] If this is the reference model, adds
                # class="row-hi" to the row to highlight it visually;
                # otherwise no extra attribute (empty string).
                hi=' class="row-hi"' if is_base else "",
                label=m["label"],
                inp=numfmt.num(m["input"], 2, lang),
                out=numfmt.num(m["output"], 2, lang),
                ratio=numfmt.num(ratio, 2, lang),
                verdict=verdict,
            )
        )
    return rows


def _promo_block(base, base_label, T):
    """Avviso sul cambio di listino imminente.

    Compare solo se il modello di riferimento ha una nota nel tariffario
    (oggi: la promo introduttiva). Quando la nota sparisce perche' il
    prezzo e' stato aggiornato, l'avviso sparisce da solo.

    [EN] Notice about the imminent price-list change.

    It appears only if the reference model has a note in the price list
    (today: the introductory promo). When the note disappears because
    the price has been updated, the notice disappears on its own.
    """
    promo_note = base.get("note", "")
    if not promo_note:
        # Nessuna nota attiva sul modello di riferimento: nessun avviso da
        # mostrare, si restituisce una stringa vuota che __PROMO_BLOCK__
        # sostituira' con "niente" nel template.
        # [EN] No active note on the reference model: no notice to
        # show, an empty string is returned which will replace
        # __PROMO_BLOCK__ with "nothing" in the template.
        return ""
    return (
        '<div class="callout">'
        '<span class="callout-title">' + T("guide.promoTitle") + "</span>"
        "<p>" + T("guide.promoBody", label=base_label, note=promo_note) + "</p>"
        "</div>"
    )


def render(lang="it"):
    """Punto d'ingresso del modulo, chiamato da main.py una volta per
    lingua. Scrive guida-costi.html oppure cost-guide.html.

    La guida e' l'unica pagina che esiste in due file invece di essere
    tradotta a runtime come le altre due. Il motivo e' che qui non ci sono
    etichette ma prosa lunga: centosettanta blocchi di testo scritto, che
    dentro un dizionario Python sarebbero illeggibili da scrivere e
    irrecensibili in un diff. Due template la lasciano quello che e', HTML
    che si legge.
    Cio' che passa comunque dal dizionario sono le poche frasi COSTRUITE
    dai numeri del tariffario (la colonna delle soglie, il riquadro della
    nota di listino): quelle non possono stare nel template, perche' vanno
    calcolate.
    Struttura e stile non possono divergere fra i due file: il CSS e' in
    guide_css.py, e il selftest confronta gli id delle sezioni.

    [EN] Entry point of the module, called by main.py once per language.
    Writes guida-costi.html or cost-guide.html.

    The guide is the only page existing as two files instead of being
    translated at runtime like the other two. The reason is that there are
    no labels here but long prose: a hundred and seventy blocks of written
    text, which inside a Python dictionary would be unreadable to write and
    unreviewable in a diff. Two templates leave it what it is, HTML one can
    read.
    What does go through the dictionary anyway are the few sentences BUILT
    from the price list's numbers (the thresholds column, the price-note
    callout): those cannot live in the template, because they must be
    computed.
    Structure and style cannot diverge between the two files: the CSS lives
    in guide_css.py, and the selftest compares the sections' ids."""
    template_name = "guide.html" if lang == "it" else "guide.en.html"
    out_path = config.OUT_GUIDE_HTML if lang == "it" else config.OUT_GUIDE_HTML_EN
    T = i18n.translator(lang, "UI")
    base = pricing.MODEL_PRICING[pricing.DEFAULT_MODEL_KEY]
    base_in = base["input"]
    base_label = base["label"]

    rows = _price_rows(base_in, base_label, lang, T)
    promo_block = _promo_block(base, base_label, T)

    # --- Esempio numerico sulla cache (sezione 1 della guida) --------------
    # Confronta il costo di 40 turni consecutivi che ripartono ogni volta da
    # zero (nessuna cache) contro lo stesso lavoro CON la cache di contesto
    # attiva: primo turno paga il prezzo pieno di scrittura cache (1,25x),
    # i successivi pagano solo il prezzo ridotto di lettura cache (0,1x).
    #
    # "1e6" e' notazione scientifica Python per 1 milione (1_000_000.0): i
    # prezzi in MODEL_PRICING sono "dollari per milione di token", quindi
    # dividiamo il numero di token dell'esempio per un milione prima di
    # moltiplicarlo per il prezzo unitario.
    # [EN] --- Numeric cache example (section 1 of the guide) ---------
    # Compares the cost of 40 consecutive turns each starting from
    # scratch (no cache) against the same work WITH the context cache
    # active: the first turn pays the full cache-write price (1.25x),
    # the following ones pay only the reduced cache-read price (0.1x).
    #
    # "1e6" is Python scientific notation for 1 million (1_000_000.0):
    # prices in MODEL_PRICING are "dollars per million tokens", so we
    # divide the example's token count by one million before
    # multiplying it by the unit price.
    ctx_m = GUIDE_EX_CONTEXT_TOKENS / 1e6
    no_cache = GUIDE_EX_TURNS * ctx_m * base_in
    with_cache = (ctx_m * base_in * pricing.CACHE_WRITE_MULTIPLIER
                  + (GUIDE_EX_TURNS - 1) * ctx_m * base_in * pricing.CACHE_READ_MULTIPLIER)
    # "if with_cache else 0": protezione contro una divisione per zero nel
    # caso limite (teorico, non realistico con questi numeri) in cui
    # with_cache risultasse 0.
    # [EN] "if with_cache else 0": protection against a division by
    # zero in the edge case (theoretical, not realistic with these
    # numbers) where with_cache turned out to be 0.
    ratio_cache = no_cache / with_cache if with_cache else 0

    html = templating.load_template(template_name)
    # Il CSS proprio di questa pagina, tenuto fuori dal template perche'
    # i template della guida sono due, uno per lingua, e lo stile e' lo
    # stesso: vedi il docstring di guide_css.py.
    # [EN] This page's own CSS, kept out of the template because the
    # guide has two templates, one per language, and the style is the
    # same: see guide_css.py's docstring.
    html = html.replace("__GUIDE_CSS__", guide_css.GUIDE_CSS)
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
    html = html.replace("__SITE_HEADER__",
                        templating.render_header("guide", currency_control=True))
    html = html.replace("__PRICE_ROWS__", "\n            ".join(rows))
    html = html.replace("__PROMO_BLOCK__", promo_block)
    html = html.replace("__BASE_LABEL__", base_label)
    html = html.replace("__CW__", numfmt.num(pricing.CACHE_WRITE_MULTIPLIER, 2, lang))
    html = html.replace("__CR__", numfmt.num(pricing.CACHE_READ_MULTIPLIER, 2, lang))
    html = html.replace("__EX_TURNS__", str(GUIDE_EX_TURNS))
    html = html.replace("__EX_CTX__", numfmt.thousands(GUIDE_EX_CONTEXT_TOKENS, lang))
    # I due importi dell'esempio, nella stessa forma dei prezzi in
    # tabella: valore in dollari nell'attributo, testo di ripiego dentro.
    # Uno <span> e non la cella perche' qui stanno in mezzo a una frase.
    # [EN] The example's two amounts, in the same shape as the prices in
    # the table: dollar value in the attribute, fallback text inside. A
    # <span> and not a cell because here they sit inside a sentence.
    def _money_span(value):
        return '<span data-i18n-money="{:.6f}">${}</span>'.format(
            value, numfmt.num(value, 2, lang))

    html = html.replace("__EX_NOCACHE__", _money_span(no_cache))
    html = html.replace("__EX_CACHE__", _money_span(with_cache))
    html = html.replace("__EX_RATIO__", numfmt.num(ratio_cache, 1, lang))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
