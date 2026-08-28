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
    return ("{:." + str(decimals) + "f}").format(value).replace(".", ",")


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
    return "{:,}".format(int(value)).replace(",", ".")
