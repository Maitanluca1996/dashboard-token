"""Formattazione numeri in stile italiano (virgola decimale, punto delle migliaia).

NOTA PER CHI NON CONOSCE PYTHON:
Python, come quasi tutti i linguaggi di programmazione, formatta i numeri
in stile "americano" di default: punto per i decimali (3.14) e nessun
separatore delle migliaia, oppure virgola per le migliaia (1,234.56). In
italiano usiamo l'esatto contrario (virgola per i decimali, punto per le
migliaia: 1.234,56). Queste due funzioni prendono il formato di Python e
lo "girano" scambiando i due simboli.

[EN] Italian-style number formatting (decimal comma, thousands dot).

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
Python, like almost every programming language, formats numbers in the
"American" style by default: a dot for decimals (3.14) and no thousands
separator, or a comma for thousands (1,234.56). In Italian we use the
exact opposite (comma for decimals, dot for thousands: 1.234,56). These
two functions take Python's format and "flip" it by swapping the two
symbols.
"""


# I separatori li tiene il profilo di formattazione della lingua (FMT in
# lang_it.py / lang_en.py), lo stesso da cui li legge il JavaScript delle
# pagine. Non sono duplicati qui: una convenzione tipografica scritta in due
# posti e' una convenzione che prima o poi si contraddice.
# [EN] The separators are held by the language's formatting profile (FMT in
# lang_it.py / lang_en.py), the same one the pages' JavaScript reads them
# from. They are not duplicated here: a typographic convention written in
# two places is a convention that sooner or later contradicts itself.
def _sep(lang, which):
    from . import i18n
    return i18n.lookup(lang, which, "FMT")


def num(value, decimals=2, lang="it"):
    """Numero con i separatori della lingua indicata.

    [EN] Number with the given language's separators."""
    # NIENTE separatore delle migliaia, di proposito: questa funzione
    # formatta prezzi unitari, rapporti e moltiplicatori -- numeri piccoli
    # -- e raggrupparli sarebbe rumore. Chi vuole le migliaia raggruppate
    # chiama thousands() qui sotto. E' esattamente il comportamento che
    # aveva it_num prima di imparare le lingue: cambiarlo qui avrebbe
    # riscritto di soppiatto tutti i numeri della guida.
    # [EN] NO thousands separator, deliberately: this function formats unit
    # prices, ratios and multipliers -- small numbers -- and grouping them
    # would be noise. Whoever wants grouped thousands calls thousands()
    # below. It is exactly the behaviour it_num had before it learned
    # languages: changing it here would have quietly rewritten every number
    # in the guide.
    return (("{:." + str(decimals) + "f}").format(value)
            .replace(".", _sep(lang, "dec")))


def thousands(value, lang="it"):
    """Intero con il separatore delle migliaia della lingua indicata.

    [EN] Integer with the given language's thousands separator."""
    return "{:,}".format(int(value)).replace(",", _sep(lang, "thou"))


def it_num(value, decimals=2):
    """Numero con la virgola decimale, come nel resto dell'interfaccia.

    "decimals=2" e' un PARAMETRO CON VALORE DI DEFAULT: se chi chiama la
    funzione non specifica quante cifre decimali vuole (es. it_num(3.14159)),
    Python usa automaticamente 2; altrimenti si puo' forzare un altro valore
    (es. it_num(3.14159, decimals=1) -> "3,1").

    [EN] Number with the decimal comma, as in the rest of the interface.

    "decimals=2" is a PARAMETER WITH A DEFAULT VALUE: if the caller does
    not specify how many decimal digits they want (e.g. it_num(3.14159)),
    Python automatically uses 2; otherwise another value can be forced
    (e.g. it_num(3.14159, decimals=1) -> "3,1").
    """
    # "{:." + str(decimals) + "f}" costruisce al volo una stringa di formato
    # tipo "{:.2f}" (2 decimali) incollando il numero "decimals" dentro un
    # testo -- serve perche' il numero di decimali qui non e' fisso, ma
    # decrescente in base a chi chiama. ".format(value)" applica quel
    # formato al numero, producendo qualcosa come "3.14" (ancora con il
    # punto, stile americano). ".replace(".", ",")" alla fine sostituisce
    # quel punto con la virgola italiana.
    # [EN] "{:." + str(decimals) + "f}" builds on the fly a format string
    # like "{:.2f}" (2 decimals) by gluing the number "decimals" inside
    # some text -- needed because the number of decimals here is not
    # fixed, but varies depending on the caller. ".format(value)" applies
    # that format to the number, producing something like "3.14" (still
    # with the dot, American style). ".replace(".", ",")" at the end
    # replaces that dot with the Italian comma.
    # Da quando esistono due lingue, il lavoro vero lo fa num(): questa
    # resta come scorciatoia per i punti di chiamata che l'italiano lo
    # vogliono per definizione. Una sola implementazione, cosi' le due non
    # possono divergere.
    # [EN] Since there are two languages, the real work is done by num():
    # this stays as a shorthand for the call sites that want Italian by
    # definition. One implementation only, so the two cannot diverge.
    return num(value, decimals, "it")


def it_thousands(value):
    """Intero con il punto come separatore delle migliaia (formato italiano).

    [EN] Integer with the dot as thousands separator (Italian format).
    """
    # "{:,}" e' un formato Python che aggiunge la virgola ogni 3 cifre (es.
    # 1234567 -> "1,234,567", stile americano). int(value) forza il numero a
    # essere un intero prima di formattarlo (niente decimali). Come sopra,
    # ".replace(",", ".")" gira la virgola americana nel punto italiano,
    # ottenendo "1.234.567".
    # [EN] "{:,}" is a Python format that adds a comma every 3 digits
    # (e.g. 1234567 -> "1,234,567", American style). int(value) forces
    # the number to be an integer before formatting it (no decimals). As
    # above, ".replace(",", ".")" turns the American comma into the
    # Italian dot, producing "1.234.567".
    # Come sopra: il lavoro lo fa thousands(), questa e' la scorciatoia.
    # [EN] As above: the work is done by thousands(), this is the shorthand.
    return thousands(value, "it")
