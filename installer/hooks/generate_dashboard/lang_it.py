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
        # Come per la lingua, i nomi delle valute dentro la combo NON
        # stanno qui: sono simboli e codici ISO, e si scrivono uguali in
        # ogni lingua (i18n.CURRENCY_SYMBOLS e CURRENCY_CODES).
        # [EN] As for the language, the currency names inside the combo
        # are NOT here: they are symbols and ISO codes, written the same
        # in every language (i18n.CURRENCY_SYMBOLS and CURRENCY_CODES).
        "currencySwitch": "Valuta degli importi",
    },

    # La pagina della dashboard: titolo e sottotitolo in cima.
    # [EN] The dashboard page: title and subtitle at the top.
    "dash": {
        "h1": "Utilizzo token — Claude Code",
        "desc": "Monitoraggio dettagliato dei consumi, costi stimati e "
                "interazioni per sessione",
    },

    # Il riquadro a scomparsa che spiega quanto costa il monitoraggio.
    # I tre paragrafi contengono markup (<code>, <strong>) e per questo
    # viaggiano su data-i18n-html invece che su data-i18n: sono l'eccezione
    # dichiarata alla regola "solo testo", e le entita' HTML qui dentro ci
    # stanno perche' finiscono in innerHTML.
    # [EN] The collapsible box explaining how much the monitoring costs.
    # The three paragraphs contain markup (<code>, <strong>) and therefore
    # travel on data-i18n-html rather than data-i18n: they are the declared
    # exception to the "text only" rule, and the HTML entities in here
    # belong because they end up in innerHTML.
    "help": {
        "summary": "Quanti token utilizza questo sistema di monitoraggio?",
        "p1": "Il logging (gli hook che scrivono <code>tokens.csv</code> e "
              "<code>operations.csv</code>, piu' la rigenerazione di questa "
              "pagina) non chiama mai l'API di Claude: legge solo file gia' "
              "salvati in locale e scrive file locali. <strong>Token "
              "utilizzati: zero.</strong>",
        "p2": "Gli hook non restituiscono mai messaggi che finiscono nel "
              "contesto della conversazione (nessun <code>systemMessage</code> "
              "o <code>additionalContext</code>), quindi non aggiungono "
              "nemmeno un token nei turni futuri, ne' in questa sessione ne' "
              "in quelle successive.",
        "p3": "L'unico costo e' locale e non monetario: ad ogni tool call e "
              "ad ogni fine turno gli script rileggono il transcript della "
              "sessione per calcolare i delta di utilizzo. Cresce leggermente "
              "con la lunghezza della sessione, ma resta nell'ordine di "
              "millisecondi &mdash; un'attesa impercettibile, non un impatto "
              "sul portafoglio.",
    },

    # I titoli delle due sezioni della colonna di sinistra.
    # [EN] The titles of the two sections in the left-hand column.
    "side": {
        "filters": "Filtri",
        "unit": "Unità",
    },

    # Le etichette dei filtri. I due punti finali fanno parte del testo:
    # non tutte le lingue li usano allo stesso modo, quindi la punteggiatura
    # sta nella traduzione e non incollata nel markup.
    # [EN] The filter labels. The trailing colon is part of the text: not
    # every language uses it the same way, so the punctuation lives in the
    # translation and is not glued on in the markup.
    "filters": {
        "projects": "Progetti:",
        "session": "Sessione:",
        "account": "Account:",
        "period": "Periodo:",
        "model": "Modello:",
        "search": "Cerca nella richiesta:",
        "searchPlaceholder": "Testo della richiesta…",
        "searchClear": "Cancella la ricerca",
        "chooseSessions": "Scegli fra le sessioni",
    },

    # Cosa misurano i grafici. Erano tre voci -- dollari, euro, token --
    # e le prime due sono diventate una sola da quando la valuta si sceglie
    # nell'intestazione e vale per tutta la pagina: qui resta la domanda
    # che riguarda soltanto i grafici, cioe' se l'asse conti soldi o token.
    # "Costo" senza nominare la valuta e' voluto: quale sia lo dice il
    # simbolo sull'asse, e ripeterlo qui sarebbe una seconda cosa da tenere
    # allineata alla combo.
    # [EN] What the charts measure. It used to be three entries -- dollars,
    # euros, tokens -- and the first two became one once the currency is
    # chosen in the header and applies to the whole page: what stays here is
    # the question that concerns the charts alone, namely whether the axis
    # counts money or tokens. "Cost" without naming the currency is
    # deliberate: which one it is, is said by the symbol on the axis, and
    # repeating it here would be a second thing to keep in step with the
    # combo.
    "unit": {
        "money": "Costo",
        "tokens": "Token",
    },

    # I controlli sopra i grafici. Ogni etichetta compare DUE volte nel
    # markup: sul bottone che si vede e sull'<option> del <select> nascosto
    # che fa da deposito del valore. Quel testo non lo legge nessuno, ma
    # viene tradotto lo stesso: lasciare meta' di due liste identiche in
    # italiano e' l'asimmetria che fa sospettare un errore a chi leggera'.
    # [EN] The controls above the charts. Every label appears TWICE in the
    # markup: on the visible button and on the <option> of the hidden
    # <select> that stores the value. Nobody reads that text, but it is
    # translated all the same: leaving half of two identical lists in
    # Italian is the asymmetry that makes a future reader suspect a bug.
    "chart": {
        "groupBy": "Raggruppa:",
        "byDay": "Per giorno",
        "byMonth": "Per mese",
        "bySession": "Per sessione",
        "byProject": "Per progetto",
        "byModel": "Per modello",
        "aggregate": "Aggregato",
        "mode": "Modalità:",
        "scale": "Scala:",
        "linear": "Lineare",
        "log": "Log",
        "period": "Periodo:",
        "rangeAria": "Ampiezza della finestra di tempo",
    },

    # La tabella delle interazioni. Le sei intestazioni di colonna sono
    # scritte in due posti -- il <thead> del markup e la riga che si ripete
    # sotto ogni turno espanso, costruita dal JavaScript -- e leggono le
    # STESSE chiavi: cosi' una traduzione mancante manca in tutti e due i
    # punti insieme, invece di farli divergere in una lingua sola.
    # [EN] The interactions table. The six column headers are written in two
    # places -- the markup's <thead> and the row repeated under every
    # expanded turn, built by the JavaScript -- and they read the SAME keys:
    # this way a missing translation is missing in both places at once,
    # instead of making them diverge in one language only.
    "turns": {
        "recent": "Interazioni recenti",
        "colTs": "Data e ora",
        "colSession": "Sessione",
        "colRequest": "Richiesta",
        "colModel": "Modello",
        "colTotal": "Totale",
        "colCost": "Costo",
        "paginationAria": "Paginazione interazioni",
        "emptyFiltered": "Nessuna interazione corrisponde ai filtri scelti.",
        "emptyNone": "Nessuna interazione registrata ancora.",
        "pageInfo": "{from}–{to} di {total}",
        "pageOf": "  ·  pagina {page} di {total}",
        "prevPage": "Pagina precedente",
        "nextPage": "Pagina successiva",
        "actTimestamp": "Timestamp",
        "actTool": "Tool",
        "actTarget": "Target",
        "actCost": "Costo",
        "noActions": "Nessuna azione registrata per questa interazione.",
        "filterOnSession": "Filtra su questa sessione",
        "rows": "Righe:",
    },

    # Le schede in cima alla pagina. "Input", "Output", "Cache write" e
    # "Cache read" sono i nomi che l'API di Claude da' alle quattro voci di
    # consumo: restano tali e quali in tutte le lingue, come si fa con i
    # nomi propri, perche' tradurli allontanerebbe da cio' che si legge
    # nella documentazione ufficiale.
    # [EN] The cards at the top of the page. "Input", "Output", "Cache
    # write" and "Cache read" are the names Claude's API gives the four
    # usage entries: they stay exactly the same in every language, as with
    # proper nouns, because translating them would move away from what one
    # reads in the official documentation.
    "stats": {
        "input": "Input",
        "output": "Output",
        "cacheWrite": "Cache write",
        "cacheRead": "Cache read",
        "estCost": "Costo stimato",
        "freshTokens": "Token nuovi (input+output)",
        "costToday": "Costo oggi",
        "tokensToday": "Token oggi",
        "turns": "Interazioni registrate",
        "sessions": "Sessioni",
        "avgFresh": "Media nuovi/interazione",
        "totalTokens": "Token totali (con cache)",
    },

    # I titoli che cambiano con l'unita' di misura scelta: il nome della
    # grandezza sulle barre, il titolo del grafico a linee e la descrizione
    # parlata per chi usa un lettore di schermo.
    # [EN] The titles that change with the chosen unit: the quantity's name
    # on the bars, the line chart's title and the spoken description for
    # screen-reader users.
    "unitMode": {
        # Una forma sola per il denaro, non una per valuta: la valuta e'
        # gia' scritta sull'asse e nei numeri, e un titolo che la ripete
        # ("Costo totale in euro") diventa falso il giorno che qualcuno
        # aggiunge una valuta e dimentica di aggiungere il titolo.
        # [EN] One form for money, not one per currency: the currency is
        # already written on the axis and in the numbers, and a title that
        # repeats it ("Total cost in euros") turns false the day someone
        # adds a currency and forgets to add the title.
        "barMoney": "Costo totale",
        "lineMoney": "Andamento costo nel tempo",
        "ariaMoney": "Costo stimato",
        "barTokens": "Token totali",
        "lineTokens": "Andamento token nel tempo",
        "ariaTokens": "Token totali",
    },

    # Le tacche del cursore dei periodi, in forma lunga (la didascalia) e
    # corta (l'etichetta sotto la corsa).
    #
    # Il numero e' un PARAMETRO e non parte del testo: cosi' tredici tacche
    # stanno in nove frasi invece che in ventisei, e aggiungerne una non
    # aggiunge traduzioni. Le quattro forme separate per ore, giorni, mesi e
    # anno non sono un vezzo: in italiano l'aggettivo concorda con il nome
    # che segue -- "Ultime ore" ma "Ultimi giorni" e "Ultimo anno" -- e una
    # frase sola non potrebbe soddisfarli tutti e tre.
    # [EN] The period slider's stops, in long form (the caption) and short
    # form (the label under the track).
    #
    # The number is a PARAMETER and not part of the text: this way thirteen
    # stops fit in nine sentences instead of twenty-six, and adding one adds
    # no translations. The four separate forms for hours, days, months and
    # year are not a whim: in Italian the adjective agrees with the noun
    # that follows -- "Ultime ore" but "Ultimi giorni" and "Ultimo anno" --
    # and a single sentence could not satisfy all three.
    "range": {
        "lastHours": "Ultime {n} ore",
        "lastDays": "Ultimi {n} giorni",
        "lastMonths": "Ultimi {n} mesi",
        "lastYear": "Ultimo anno",
        "all": "Tutto lo storico",
        "shortHours": "{n} ore",
        "shortDays": "{n} gg",
        "shortMonths": "{n} mesi",
        "shortYear": "1 anno",
        "shortAll": "tutto",
    },

    # I riquadrini che riassumono i filtri accesi, sopra i grafici. Le
    # cinque chiavi qui sotto hanno lo stesso nome del tipo di filtro
    # ("project", "session", ...), perche' il codice le compone al volo:
    # rinominarne una qui senza rinominarla la' farebbe comparire il nome
    # della chiave dentro il riquadrino.
    # [EN] The little boxes summarising the active filters, above the
    # charts. The five keys below carry the same name as the filter kind
    # ("project", "session", ...), because the code composes them on the
    # fly: renaming one here without renaming it there would make the key
    # name show up inside the box.
    "chip": {
        "account": "Account",
        "period": "Periodo",
        "model": "Modello",
        "search": "Ricerca",
        "remove": "Togli questo filtro",
        "removeAria": "Togli il filtro {kind}",
        "clearAll": "Azzera tutto",
    },

    # Le prime voci delle tendine, quelle che non filtrano niente. Ognuna
    # ha una forma lunga e una corta: la corta e' quella che resta scritta
    # quando la barra dei filtri si stringe.
    # [EN] The first entries of the dropdowns, the ones that filter nothing.
    # Each has a long and a short form: the short one is what stays written
    # when the filter bar narrows.
    # La finestra da cui si scelgono le sessioni: sono centinaia, e in
    # colonna non ci stavano.
    # [EN] The window the sessions are chosen from: there are hundreds of
    # them, and they did not fit in the column.
    "picker": {
        "sessionsTitle": "Scegli le sessioni",
        "searchSessions": "Cerca una sessione…",
        "searchClear": "Cancella la ricerca",
        "close": "Chiudi",
        "done": "Fatto",
        "noMatch": "Nessuna sessione corrisponde",
        "checkAll": "Spunta tutte le sessioni in elenco",
        "colSession": "Sessione",
        "colProject": "Progetto",
        "colModel": "Modello",
        "colAccount": "Account",
        "colTurns": "Interazioni",
        "colLast": "Ultima attività",
        "none": "Nessuna sessione scelta",
        "selected": {"one": "{n} sessione scelta", "other": "{n} sessioni scelte"},
    },

    "dd": {
        "allSessions": "Tutte le sessioni",
        "noSession": "Nessuna sessione",
        "allPeriods": "Tutti i periodi",
        "shortPeriods": "Periodi",
        "allModels": "Tutti i modelli",
        "shortModels": "Modelli",
        "allAccounts": "Tutti gli account",
        "shortAccounts": "Account",
        "noProject": "Nessun progetto",
        "allProjects": "Tutti i progetti",
        "excludedAlways": "Esclusi sempre",
        "excludeProject": "Escludi sempre questo progetto",
        "restoreProject": "Rimetti questo progetto fra quelli visibili",
        "excludeAria": "Escludi sempre {name}",
        "restoreAria": "Rimetti {name}",
    },

    # Frammenti che compaiono in piu' punti diversi. Il conteggio delle
    # interazioni e delle sessioni ha due forme, singolare e plurale, e il
    # numero e' dentro la frase: in italiano va davanti al nome, ma non e'
    # detto che sia cosi' in ogni lingua, e chi traduce deve poterlo
    # spostare.
    # [EN] Fragments appearing in several different places. The interaction
    # and session counts have two forms, singular and plural, and the number
    # is inside the sentence: in Italian it goes before the noun, but that
    # need not hold in every language, and whoever translates must be able
    # to move it.
    "common": {
        # "Quanto tempo fa", in forma compatta, sotto i titoli delle
        # sessioni. Tre chiavi separate e non una sola con l'unita'
        # passata dentro: dove va la parola "fa" cambia da lingua a
        # lingua, e qui la frase intera e' un dato.
        # [EN] "How long ago", in compact form, under the session
        # titles. Three separate keys and not one with the unit passed
        # in: where the word "ago" goes changes from language to
        # language, and here the whole phrase is data.
        "agoMin": "{n}m fa",
        "agoHour": "{n}h fa",
        "agoDay": "{n}g fa",
        "turns": {"one": "{n} interazione", "other": "{n} interazioni"},
        "sessions": {"one": "{n} sessione", "other": "{n} sessioni"},
        # Qui il numero arriva gia' formattato (con i separatori delle
        # migliaia), quindi non e' un conteggio da declinare ma un testo da
        # incastrare: niente forma singolare.
        # [EN] Here the number arrives already formatted (with thousands
        # separators), so it is not a count to decline but a text to slot
        # in: no singular form.
        "tokensStr": "{n} token",
        "sessionFallback": "Sessione {id}",
        "noProject": "(senza progetto)",
    },

    # I riquadri che si aprono passando sopra un grafico.
    # [EN] The boxes that open when hovering over a chart.
    "tt": {
        "filterOn": "Filtra su {what}",
        "unfilterOn": "Togli il filtro su {what}",
        "dismiss": "Clicca fuori o premi Esc per chiudere.",
        "showIterations": "Mostra le iterazioni",
        "hideIterations": "Nascondi le iterazioni",
        "noRequest": "(nessuna richiesta registrata)",
        "sessionId": "Sessione: ",
        "subAgentCost": "Costo non determinabile: azione eseguita da un "
                        "sotto-agente delegato (Task/Agent). Il suo consumo "
                        "token non compare nel transcript della sessione "
                        "principale, quindi non e’ stimabile qui -- non e’ "
                        "zero, e’ sconosciuto.",
        "windowNote": "Nel periodo mostrato ({period}): {cost} su {turns}.",
        "span": "dal {from} al {to}",
    },

    # I grafici a barre: come si chiama il raggruppamento, cosa dice il
    # titolo quando le barre sono state tagliate, e la barra di coda.
    # avgOthersProjects e avgOthersSessions dicono la stessa cosa in
    # inglese, ma NON in italiano: "Media altri" concorda con "progetti",
    # "Media altre" con "sessioni". Non e' un plurale, e' un accordo di
    # genere con un nome sottinteso -- due frasi diverse, quindi due chiavi.
    # [EN] The bar charts: what the grouping is called, what the title says
    # when the bars have been cut, and the tail bar.
    # avgOthersProjects and avgOthersSessions say the same thing in English,
    # but NOT in Italian: "Media altri" agrees with "progetti", "Media
    # altre" with "sessioni". It is not a plural, it is gender agreement
    # with an elided noun -- two different sentences, hence two keys.
    "bar": {
        "perDay": "per giorno",
        "perMonth": "per mese",
        "perProject": "per progetto",
        "perSession": "per sessione",
        "lastDays": "ultimi {n} giorni",
        "lastMonths": "ultimi {n} mesi",
        "topProjects": "primi {n} progetti",
        "topSessions": "prime {n} sessioni",
        "allHistory": "tutto lo storico",
        "avgOthersProjects": "Media altri ({n})",
        "avgOthersSessions": "Media altre ({n})",
        "otherProjects": "altri progetti",
        "otherSessions": "altre sessioni",
        "legendOtherProjects": "altri {n} progetti",
        "legendOtherSessions": "altre {n} sessioni",
        "legendOtherModels": "altri {n} modelli",
        # Quando la coda raggruppa cose senza un nome collettivo.
        # [EN] When the tail groups things with no collective noun.
        "legendOtherGeneric": "altri {n}",
        "avgOf": "Media di {n} {noun}",
        "inTotal": "In totale: ",
        "singleBar": "Con questo filtro ogni raggruppamento darebbe una "
                     "barra sola: il totale è nelle schede in cima alla "
                     "pagina.",
        "noData": "Nessun dato ancora.",
    },

    # Il grafico a linee: di che cosa e' il totale che si sta guardando, e
    # su che cosa porta il clic.
    # [EN] The line chart: what the total being looked at is a total of, and
    # what the click leads to.
    "line": {
        "scopeSession": "Totale dell’intera sessione",
        "scopeAll": "Totale complessivo",
        "scopeModel": "Totale per questo modello",
        "scopeProject": "Totale dell’intero progetto",
        "scopeTail": "Totale nel periodo mostrato",
        "thisSession": "questa sessione",
        "thisModel": "questo modello",
        "thisProject": "questo progetto",
        "ariaOverTime": "{what} nel tempo",
        "notEnough": "Nessuna interazione a sufficienza per il grafico",
    },

    # I periodi a calendario della tendina. La forma corta e' quella che
    # resta scritta quando la barra dei filtri si stringe.
    # [EN] The calendar periods of the dropdown. The short form is what
    # stays written when the filter bar narrows.
    "period": {
        "today": "Oggi",
        "week": "Questa settimana",
        "weekShort": "Settimana",
        "month": "Questo mese",
        "monthShort": "Mese",
        "year": "Quest'anno",
        "yearShort": "Anno",
    },

    # Messaggi che non appartengono a nessuna delle famiglie qui sopra.
    # "stale" cita il bottone Aggiorna per nome: il nome arriva come
    # parametro invece di essere riscritto, cosi' se un giorno il bottone
    # cambia etichetta il messaggio la segue da solo.
    # [EN] Messages belonging to none of the families above. "stale" names
    # the refresh button: the name arrives as a parameter instead of being
    # rewritten, so if one day the button changes label the message follows
    # on its own.
    "misc": {
        "stale": "Questi numeri sono quelli letti all'ora indicata: nel "
                 "frattempo potrebbero essercene di nuovi. Premi {refresh} "
                 "per rileggerli.",
    },

    # La pagina del tariffario. Le quattro colonne dei consumi riusano le
    # chiavi delle schede statistiche (stats.input e compagnia): e' lo
    # stesso concetto, e scriverlo due volte vorrebbe dire poterlo tradurre
    # in due modi diversi nella stessa applicazione.
    # [EN] The price list page. The four usage columns reuse the stat card
    # keys (stats.input and friends): it is the same concept, and writing it
    # twice would mean being able to translate it two different ways within
    # the same application.
    "pricingPage": {
        "h1": "Tariffario prezzi — Claude Code",
        "desc": "Prezzi di listino Anthropic come configurati nel tariffario "
                "locale, per milione di token (input, output, cache), "
                "nella valuta scelta in alto a destra",
        "colModel": "Modello",
        "colIdNote": "ID / note",

        # La sezione dei cambi. I codici delle valute (USD, EUR, GBP)
        # non sono qui: li scrive render_pricing.py dal registro in
        # i18n.py, e non si traducono in nessuna lingua.
        # ratesHint finisce con i due punti perche' la data la segue
        # in un elemento a parte: e' un valore, non una parola, e
        # cucirlo dentro la frase vorrebbe dire che ogni lingua deve
        # metterlo nello stesso punto della frase.
        # [EN] The rates section. The currency codes (USD, EUR, GBP)
        # are not here: render_pricing.py writes them from the
        # registry in i18n.py, and they are translated in no
        # language.
        # ratesHint ends with a colon because the date follows it in
        # a separate element: it is a value, not a word, and sewing
        # it into the sentence would mean every language has to put
        # it at the same point of that sentence.
        "ratesH2": "Cambi tra le valute",
        "ratesDesc": "Quanto vale una unità della valuta in riga, "
                     "espressa nella valuta in colonna. La dashboard "
                     "calcola tutto in dollari e converte con questi "
                     "rapporti nella valuta scelta nell'intestazione.",
        "ratesCorner": "1 unità di",
        "ratesHint": "Cambi fissati a mano e non aggiornati in tempo "
                     "reale: la dashboard si genera senza mai andare "
                     "in rete, quindi non c'è nessun servizio di "
                     "cambi da interrogare. Si aggiornano modificando "
                     "USD_RATES in pricing.py. Ultimo aggiornamento:",
        "hint": "Cache write = 1,25&times; il prezzo input con TTL 5 minuti, "
                "<strong>2&times; con TTL 1 ora</strong> (quella usata da "
                "Claude Code, e quindi la quasi totalita' delle scritture di "
                "cache) &middot; cache read = 0,1&times; il prezzo input "
                "&mdash; moltiplicatori standard Anthropic, uguali per ogni "
                "modello.<br>Questi sono i prezzi ufficiali dell'API a "
                "consumo: se l'account e' su piano Pro/Team a canone fisso "
                "non c'e' fatturazione a token, ma la dashboard li usa "
                "comunque come stima di riferimento.",
    },

    "guide": {
        "verdictBase": "Riferimento del confronto.",
        "verdictCheaper": "Conviene finch&eacute; consuma <strong>meno di "
                          "{mult}&times;</strong> i token di {base}.",
        "verdictPricier": "Conviene se consuma <strong>meno del {pct}%</strong> "
                          "dei token di {base}.",
        "promoTitle": "Le soglie qui sopra cambieranno",
        "promoBody": "Il modello di riferimento ({label}) ha una nota di "
                     "listino attiva: <em>{note}</em>. Le soglie di "
                     "convenienza sono calcolate sul prezzo "
                     "<strong>attualmente</strong> in tariffario, quindi "
                     "cambieranno automaticamente quando il listino in "
                     "<code>generate_dashboard/pricing.py</code> verr&agrave; "
                     "aggiornato. Finch&eacute; non lo si aggiorna, per&ograve;, "
                     "sia questa pagina sia i costi della dashboard restano "
                     "fermi al prezzo promozionale.",
    },

    "footer": {
        "generated": "File generato da ~/.claude/hooks/generate_dashboard/, "
                     "richiamato dall'hook Stop.",
    },
    # Le tre schede della barra di navigazione.
    # [EN] The three tabs of the navigation bar.
    "nav": {
        "dashboard": "Dashboard",
        "pricing": "Tariffario",
        "guide": "Guida ai costi",
        # Il collegamento, non solo l'etichetta: la guida e' due file.
        # [EN] The link, not just the label: the guide is two files.
        "guideHref": "guida-costi.html",
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

    # Il simbolo di valuta va DOPO il numero, con uno spazio: "12,50 $",
    # "12,50 €". In inglese va prima e attaccato. Qui c'e' il POSTO del
    # simbolo, non il simbolo: quale sia lo dice la valuta scelta
    # (i18n.CURRENCY_SYMBOLS), ed e' lo stesso in ogni lingua.
    # Prima queste chiavi tenevano anche il simbolo, una per valuta, e
    # il difetto era grosso: il profilo inglese metteva "$" davanti a
    # entrambe le valute, per cui scegliendo gli euro si leggevano
    # importi convertiti in euro col simbolo del dollaro davanti.
    # [EN] The currency symbol goes AFTER the number, with a space:
    # "12,50 $", "12,50 €". In English it goes before and attached. What
    # is here is the symbol's PLACE, not the symbol: which one it is
    # comes from the chosen currency (i18n.CURRENCY_SYMBOLS), and it is
    # the same in every language.
    # These keys used to hold the symbol too, one per currency, and the
    # flaw was a large one: the English profile put "$" in front of both
    # currencies, so choosing euros gave amounts converted into euros
    # with a dollar sign in front of them.
    "moneySymbolBefore": False,
    "moneyGap": " ",

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
CLI = {
    # L'aiuto del comando. Le due colonne sono allineate a mano con degli
    # spazi: chi traduce deve riallinearle, perche' la larghezza della
    # colonna di sinistra dipende dalla lunghezza dei nomi dei comandi, che
    # non si traducono.
    # [EN] The command's help. The two columns are aligned by hand with
    # spaces: whoever translates has to realign them, because the width of
    # the left column depends on the length of the command names, which are
    # not translated.
    "usage": """dashboard-token -- dashboard consumi token di Claude Code

  dashboard-token                 doppio click: sull'installer scaricato
                                  installa, sull'app installata controlla
                                  e applica gli aggiornamenti
  dashboard-token install         installa, da riga di comando (--no-pause per la CI)
  dashboard-token log-tokens      hook Stop -- lo chiama Claude Code
  dashboard-token log-operation   hook PostToolUse -- lo chiama Claude Code
  dashboard-token backfill        ricostruisce lo storico dai transcript delle
                                  sessioni gia' aperte prima dell'installazione
                                  (--dry-run per vedere l'effetto senza scrivere)
  dashboard-token config          le tre personalizzazioni facoltative
  dashboard-token self-update     controlla e installa una versione nuova (-v)
  dashboard-token version         stampa la versione e i percorsi""",

    # Il comando "config": le personalizzazioni facoltative.
    # [EN] The "config" command: the optional customisations.
    "cfg": {
        "title": "== Personalizzazioni facoltative ==",
        "enterKeeps": "Premi INVIO per lasciare tutto com'e'.",
        "outDir": "Cartella in cui vengono generate le pagine HTML.",
        "current": "  attuale: {valore}",
        "outDirPrompt": "  nuova (INVIO = lascia, - = torna al default): ",
        "backToDefault": "  -> tornata al default.",
        "set": "  -> impostata.",
        "langTitle": "Lingua dei messaggi a terminale.",
        "langPrompt": "  nuova ({lingue}, INVIO = lascia, - = automatica): ",
        "langAuto": "automatica",
        "labels": "Etichette per gli account Claude visti su questo PC.",
        "noLabel": "nessuna etichetta",
        "labelsSaved": "  -> etichette salvate.",
        "done": "Fatto. Le modifiche valgono dalla prossima generazione della "
                "dashboard.",
    },

    # Il doppio click sull'applicazione installata: controlla e installa gli
    # aggiornamenti.
    # [EN] Double-clicking the installed application: it checks for and
    # installs updates.
    "upd": {
        "launchedByClaude": "Questa applicazione la lancia Claude Code da sola "
                            "a ogni turno.",
        "yourDashboard": "La tua dashboard e' in:",
        "checking": "Controllo se c'e' una versione piu' recente...",
        "available": "Disponibile la versione {nuova} (adesso hai la {attuale}).",
        "prompt": "Vuoi aggiornare adesso? (S/n): ",
        "promptNo": "n",
        "declined": "Ok, lasciamo stare. Si aggiornera' comunque da solo entro "
                    "24 ore.",
        "downloading": "Scarico e verifico...",
        "failed1": "Aggiornamento non riuscito. Riprova piu' tardi: intanto la",
        "failed2": "versione che hai continua a funzionare.",
        "started1": "Aggiornamento avviato. Si completa da solo in un paio di "
                    "secondi,",
        "started2": "questa finestra si chiude fra poco.",
        "noBinary": "Nessun binario pubblicato per {piattaforma}.",
        "checkFailed": "Controllo aggiornamenti non riuscito: {errore}",
        "noTag": "Release senza tag, ignorata.",
        "upToDate": "Gia' aggiornato ({versione}).",
        "missingAsset": "La release {tag} non contiene {file}.",
        "downloadFailed": "Download non riuscito: {errore}",
        "badSize": "Dimensione inattesa, aggiornamento annullato.",
        "badChecksum": "Checksum non corrispondente, aggiornamento annullato.",
        "noChecksums": "SHA256SUMS non disponibile: verificata solo la dimensione.",
        "writeFailed": "Scrittura dell'installer non riuscita: {errore}",
        "startFailed": "Avvio dell'installer non riuscito: {errore}",
        "notPackaged": "Non impacchettato: niente da aggiornare.",
        "newVersion": "Nuova versione disponibile: {nuova} (attuale {attuale}).",
        "updatingBg": "Aggiornamento a {tag} in corso in background.",
    },

    # Il resto: la versione, l'attesa a fine comando, il comando ignoto.
    # [EN] The rest: the version, the wait at the end of a command, the
    # unknown command.
    "misc": {
        "roleInstaller": "installer",
        "roleApp": "applicazione",
        "exe": "  eseguibile:  {valore}",
        "fromSource": "(sorgenti Python)",
        "installed": "  installata:  {valore}",
        "settings": "  settings:    {valore}",
        "repo": "  repo:        {valore}",
        "unknownCommand": "Comando sconosciuto: {comando}",
        "pressEnter": "Premi INVIO per chiudere...",
    },

    # I messaggi del recupero delle sessioni precedenti all'installazione
    # (backfill.py). I segnaposto {cosi'} stanno nella traduzione e non nel
    # codice perche' l'ordine delle parole cambia da lingua a lingua: "12
    # sessioni esaminate" e "examined 12 sessions" mettono il numero in
    # posti diversi, e solo chi traduce sa dove va.
    # [EN] The messages of the recovery of sessions predating the
    # installation (backfill.py). The {like_this} placeholders live in the
    # translation and not in the code because word order changes between
    # languages: "12 sessioni esaminate" and "examined 12 sessions" put the
    # number in different places, and only whoever translates knows where.
    "backfill": {
        "start": "Recupero delle sessioni precedenti all'installazione...",
        "failed": "Recupero non riuscito: {errore}",
        "failedOk": "L'installazione resta valida: verranno registrate le "
                    "sessioni da qui in avanti.",
        "nothing": "Nessuna sessione precedente trovata: si parte da zero.",
        "sessions": "{esaminate} sessioni esaminate: {recuperate} recuperate, "
                    "{ricostruite} con la cronologia ricostruita.",
        "added": "{turni} turni e {operazioni} operazioni aggiunti allo storico.",
        "timeline": "Registro accessi dell'app: {eventi} cambi di account "
                    "ricostruiti.",
        "noTimeline1": "Registro accessi dell'app non disponibile: l'account verra'",
        "noTimeline2": "attribuito solo dove lo dicono gli hook o i transcript.",
        "accounts": "Account per turno: {timeline} dal registro accessi, {hook} "
                    "dagli hook, {transcript} dai transcript, {ignoti} senza "
                    "traccia (\"{etichetta}\").",
        "rows": "Righe in tokens.csv: {prima} -> {dopo}.",
        "dryRun": "(prova a vuoto: nessun file e' stato modificato)",
        "backup": "Copia di sicurezza: {percorso}",
        "regenerated": "Dashboard rigenerata.",
        "notRegenerated": "Dati salvati, ma la dashboard non si e' rigenerata "
                          "ora: {errore}",
    },
}
