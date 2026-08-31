"""Testi italiani: interfaccia (UI), formattazione (FMT), terminale (CLI).

Questo file contiene SOLO dati. Come vengono raggiunti, perche' stanno in
un modulo Python e non in un JSON, come funzionano i plurali e cosa
succede quando una chiave manca: e' tutto nel docstring di i18n.py, che e'
il posto unico dove quel disegno e' spiegato.

Le tre lingue del file hanno tre destini diversi:

  UI  -> serializzato in site-i18n.js e letto dal browser
  FMT -> idem: e' il profilo che rende "1.234,56" invece di "1,234.56"
  CLI -> resta in Python, non viaggia mai verso il browser

lang_en.py ha ESATTAMENTE le stesse chiavi. Aggiungerne una qui e non
la' significa che in inglese comparira' il nome della chiave al posto del
testo -- brutto ma visibile, che e' il comportamento voluto.

CONVENZIONE SUGLI ACCENTI E SUI SIMBOLI. Qui si scrive UTF-8 vero
("perche'" con l'apostrofo, "e'" con l'apostrofo, il simbolo €), mai
entita' HTML tipo &egrave; o &mdash;. Quasi tutte le stringhe finiscono
in textContent, dove un'entita' verrebbe mostrata alla lettera. Le poche
che finiscono in innerHTML stanno sotto una chiave che lo dice
esplicitamente (vedi data-i18n-html in header.py): sono l'eccezione, e
sono marcate.

[EN] Italian texts: interface (UI), formatting (FMT), terminal (CLI).

This file contains ONLY data. How they are reached, why they live in a
Python module and not in a JSON, how plurals work and what happens when
a key is missing: it is all in i18n.py's docstring, which is the single
place where that design is explained.

The file's three dictionaries have three different destinies:

  UI  -> serialised into site-i18n.js and read by the browser
  FMT -> likewise: it is the profile that renders "1.234,56" instead of
         "1,234.56"
  CLI -> stays in Python, never travels to the browser

lang_en.py has EXACTLY the same keys. Adding one here and not there
means English will show the key name instead of the text -- ugly but
visible, which is the intended behaviour.

CONVENTION ON ACCENTS AND SYMBOLS. Here we write real UTF-8 ("perche'"
with the apostrophe, the € symbol), never HTML entities like &egrave; or
&mdash;. Almost every string ends up in textContent, where an entity
would be displayed literally. The few that end up in innerHTML sit under
a key that says so explicitly (see data-i18n-html in header.py): they
are the exception, and they are marked.
"""

# ------------------------------------------------------------------
# UI -- tutto cio' che si vede nelle tre pagine.
# [EN] UI -- everything visible on the three pages.
# ------------------------------------------------------------------
UI = {
    # Il titolo della scheda del browser, uno per pagina. Il trattino
    # lungo e' il carattere vero, non &mdash;: finisce in textContent.
    # [EN] The browser tab title, one per page. The em dash is the real
    # character, not &mdash;: it ends up in textContent.
    "page": {
        "dashboard": "Claude Code — Utilizzo token",
        "pricing": "Tariffario prezzi — Claude Code",
        "guide": "Guida all'ottimizzazione dei costi — Claude Code",
    },

    # L'intestazione condivisa dalle tre pagine (header.py).
    # [EN] The header shared by the three pages (header.py).
    "header": {
        "brandTag": "Monitoraggio Token & Costi",
        "updatedTitle": "Data e ora dell'ultimo aggiornamento",
        "updated": "Aggiornato",
        "refreshTitle": "Ricarica i dati conservando i filtri scelti",
        "refresh": "Aggiorna",
        "nav": "Navigazione principale",
        # Etichetta parlata dello switch di lingua. I nomi delle lingue
        # dentro lo switch NON stanno qui: sono endonimi e vivono in
        # i18n.ENDONYMS, perche' non si traducono mai.
        # [EN] Spoken label of the language switch. The language names
        # inside the switch are NOT here: they are endonyms and live in
        # i18n.ENDONYMS, because they are never translated.
        "langSwitch": "Lingua della pagina",
    },

    # Le tre schede della barra di navigazione.
    # [EN] The three tabs of the navigation bar.
    "nav": {
        "dashboard": "Dashboard",
        "pricing": "Tariffario",
        "guide": "Guida ai costi",
    },
}


# ------------------------------------------------------------------
# FMT -- come si scrivono numeri, valute e date in questa lingua.
#
# Non e' testo tradotto ma convenzione tipografica, e per questo sta in
# un dizionario a parte: le funzioni che formattano leggono questo
# profilo una volta sola invece di chiedersi "che lingua e'?" ad ogni
# numero. Aggiungere una lingua significa aggiungere un profilo, non
# toccare le quindici funzioni che formattano.
# [EN] FMT -- how numbers, currencies and dates are written in this
# language.
#
# It is not translated text but typographic convention, which is why it
# sits in a separate dictionary: the formatting functions read this
# profile once instead of asking "which language is it?" at every
# number. Adding a language means adding a profile, not touching the
# fifteen formatting functions.
# ------------------------------------------------------------------
FMT = {
    # In italiano la virgola separa i decimali e il punto le migliaia:
    # 1.234,56. E' l'esatto contrario dell'inglese, ed e' il motivo per
    # cui questi due simboli non possono essere costanti nel codice.
    # [EN] In Italian the comma separates decimals and the dot separates
    # thousands: 1.234,56. It is the exact opposite of English, and it is
    # why these two symbols cannot be constants in the code.
    "dec": ",",
    "thou": ".",

    # Il simbolo di valuta va DOPO il numero, con uno spazio: "12,50 $".
    # In inglese va prima e senza spazio, quindi il posto del simbolo e'
    # parte del profilo e non della funzione: chi formatta incolla il
    # pezzo davanti e quello dietro, e uno dei due e' vuoto.
    # [EN] The currency symbol goes AFTER the number, with a space:
    # "12,50 $". In English it goes before and without a space, so the
    # symbol's position is part of the profile and not of the function:
    # the formatter glues on the front piece and the back piece, and one
    # of the two is empty.
    "moneyPre": "",
    "moneyPostUsd": " $",
    "moneyPostEur": " €",

    # Abbreviazione dei miliardi nei numeri compatti. In italiano si usa
    # "Md" (miliardi); l'inglese usa "B" (billion), che in italiano
    # significherebbe "bilione" cioe' mille volte tanto -- il classico
    # falso amico, e la ragione per cui questa lettera e' un dato.
    # [EN] Abbreviation for billions in compact numbers. Italian uses
    # "Md" (miliardi); English uses "B" (billion), which in Italian would
    # read as "bilione", a thousand times larger -- the classic false
    # friend, and the reason this letter is data.
    "billion": "Md",

    # I mesi, in forma corta e per esteso. Servono sia alle date brevi
    # ("25 ago, 14:30") sia alle etichette per esteso dei grafici
    # mensili. Minuscoli, come si scrivono in italiano.
    # [EN] The months, short and full. They serve both the short dates
    # ("25 ago, 14:30") and the full labels of the monthly charts.
    # Lowercase, as they are written in Italian.
    "monthsShort": [
        "gen", "feb", "mar", "apr", "mag", "giu",
        "lug", "ago", "set", "ott", "nov", "dic",
    ],
    "monthsLong": [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ],
}


# ------------------------------------------------------------------
# CLI -- i messaggi stampati a terminale. Non arrivano mai al browser.
# [EN] CLI -- the messages printed to the terminal. They never reach the
# browser.
# ------------------------------------------------------------------
CLI = {}
