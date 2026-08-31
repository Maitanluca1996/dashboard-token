"""Testi inglesi: interfaccia (UI), formattazione (FMT), terminale (CLI).

Gemello di lang_it.py, con le stesse identiche chiavi. Le convenzioni (solo
dati, niente entita' HTML, dove va ogni dizionario) sono spiegate nel
docstring di lang_it.py; il disegno complessivo in quello di i18n.py.

Quando si aggiunge una chiave, la si aggiunge in ENTRAMBI i file. Se manca
qui, la pagina inglese mostrera' il nome della chiave: e' voluto, perche' si
veda subito.

[EN] English texts: interface (UI), formatting (FMT), terminal (CLI).

Twin of lang_it.py, with exactly the same keys. The conventions (data
only, no HTML entities, where each dictionary goes) are explained in
lang_it.py's docstring; the overall design in i18n.py's.

When adding a key, add it to BOTH files. If it is missing here, the
English page will show the key name: that is deliberate, so it is
noticed immediately.
"""

# ------------------------------------------------------------------
# UI -- tutto cio' che si vede nelle tre pagine.
# [EN] UI -- everything visible on the three pages.
# ------------------------------------------------------------------
UI = {
    "page": {
        "dashboard": "Claude Code — Token usage",
        "pricing": "Price list — Claude Code",
        "guide": "Cost optimisation guide — Claude Code",
    },

    "header": {
        "brandTag": "Token & Cost Monitoring",
        "updatedTitle": "Date and time of the last update",
        "updated": "Updated",
        "refreshTitle": "Reload the data keeping the chosen filters",
        "refresh": "Refresh",
        "nav": "Main navigation",
        "langSwitch": "Page language",
    },

    "nav": {
        "dashboard": "Dashboard",
        "pricing": "Pricing",
        "guide": "Cost guide",
    },
}


# ------------------------------------------------------------------
# FMT -- come si scrivono numeri, valute e date in questa lingua.
# Vedi lang_it.py per il significato di ogni chiave.
# [EN] FMT -- how numbers, currencies and dates are written in this
# language. See lang_it.py for the meaning of each key.
# ------------------------------------------------------------------
FMT = {
    # Punto per i decimali, virgola per le migliaia: 1,234.56.
    # [EN] Dot for decimals, comma for thousands: 1,234.56.
    "dec": ".",
    "thou": ",",

    # Il simbolo di valuta va DAVANTI e attaccato: "$12.50". Per questo
    # il pezzo anteriore e' pieno e quello posteriore vuoto -- lo
    # specchio esatto dell'italiano.
    # [EN] The currency symbol goes IN FRONT and attached: "$12.50".
    # Hence the front piece is filled and the back one empty -- the exact
    # mirror of Italian.
    "moneyPre": "$",
    "moneyPostUsd": "",
    "moneyPostEur": "",

    # "B" per billion. Vedi la nota sul falso amico in lang_it.py.
    # [EN] "B" for billion. See the false-friend note in lang_it.py.
    "billion": "B",

    # Mesi in inglese: maiuscoli, come vuole la lingua.
    # [EN] Months in English: capitalised, as the language requires.
    "monthsShort": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
    "monthsLong": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
}


# ------------------------------------------------------------------
# CLI -- i messaggi stampati a terminale. Non arrivano mai al browser.
# [EN] CLI -- the messages printed to the terminal. They never reach the
# browser.
# ------------------------------------------------------------------
CLI = {}
