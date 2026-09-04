"""Genera dashboard.html e, a fianco, dashboard-data.js: aggrega
turni/operazioni per sessione e li trasforma in JSON -- il rendering vero e
proprio (filtri, grafici, tabella interazioni) e' lato JS nel template.

NOTA PER CHI NON CONOSCE PYTHON:
Questo modulo non genera HTML "a mano" pezzo per pezzo: prepara un grande
dizionario Python con tutti i dati (sessioni, turni, operazioni, prezzi), lo
trasforma in testo JSON con json.dumps(...), e lo scrive in dashboard-data.js
come variabile JS. Il file dashboard.html risultante si limita a caricarlo
con <script src="dashboard-data.js">, e tutto il resto del lavoro (filtri,
grafici, tabelle) lo fa il JavaScript nel browser leggendo quei dati --
Python qui fa solo da "cuoco che prepara gli ingredienti", non "impiatta"
lui stesso l'interfaccia.

[EN] Generates dashboard.html and, next to it, dashboard-data.js:
aggregates turns/operations per session and turns them into JSON -- the
actual rendering (filters, charts, interaction table) is done JS-side
in the template.

NOTE FOR THOSE UNFAMILIAR WITH PYTHON:
This module does not generate HTML "by hand" piece by piece: it
prepares a big Python dictionary with all the data (sessions, turns,
operations, prices), turns it into JSON text with json.dumps(...), and
writes it into dashboard-data.js as a JS variable. The resulting
dashboard.html file merely loads it with <script
src="dashboard-data.js">, and all the rest of the work (filters,
charts, tables) is done by the JavaScript in the browser reading that
data -- Python here only acts as the "cook preparing the ingredients",
it does not "plate" the interface itself.
"""
import json

from . import config
from . import data
from . import pricing
from . import sessions
from . import templating


def _collect_sessions(tokens, ops):
    """Ordina le sessioni per ultima interazione (piu' recente prima) e
    calcola, per ciascuna, l'ultimo timestamp visto e il numero di turni.

    Riceve "tokens" e "ops": due LISTE di dizionari (una riga di
    tokens.csv/operations.csv ciascuna, gia' lette da data.py). Restituisce
    una TUPLA di tre valori insieme -- in Python si puo' restituire piu' di
    un risultato da una funzione mettendoli separati da virgola; chi chiama
    la funzione li "spacchetta" in tre variabili separate, come si vede in
    render() piu' sotto: "sessions_sorted, last_seen, session_stats = ...".

    [EN] Sorts the sessions by last interaction (most recent first) and
    computes, for each one, the last seen timestamp and the number of
    turns.

    It receives "tokens" and "ops": two LISTS of dictionaries (one row
    of tokens.csv/operations.csv each, already read by data.py). It
    returns a TUPLE of three values together -- in Python you can
    return more than one result from a function by separating them with
    commas; the caller "unpacks" them into three separate variables, as
    seen in render() further down:
    "sessions_sorted, last_seen, session_stats = ...".
    """
    # --- Passo 1: elenco delle sessioni, in ordine di "prima comparsa" -----
    # "ordered_ids" e' una lista, "seen" e' un SET (un insieme senza
    # duplicati e senza ordine, pensato per controlli veloci del tipo
    # "questo elemento c'e' gia'?" con "in"). Scorriamo tutti i turni: la
    # prima volta che vediamo un session_id lo aggiungiamo sia al set (per
    # non riaggiungerlo mai piu') sia alla lista (che mantiene l'ordine).
    # [EN] --- Step 1: list of sessions, in "first appearance" order ---
    # "ordered_ids" is a list, "seen" is a SET (a collection with no
    # duplicates and no order, meant for fast checks of the kind "is
    # this element already there?" with "in"). We iterate over all the
    # turns: the first time we see a session_id we add it both to the
    # set (so we never add it again) and to the list (which keeps the
    # order).
    ordered_ids = []
    seen = set()
    for t in tokens:
        if t["session_id"] not in seen:
            seen.add(t["session_id"])
            ordered_ids.append(t["session_id"])
    # Ripetiamo lo stesso controllo sulle operazioni, per il raro caso in
    # cui una sessione abbia operazioni registrate ma nessun turno completo
    # ancora chiuso (es. il turno e' ancora in corso quando si guarda la
    # dashboard).
    # [EN] We repeat the same check on the operations, for the rare
    # case where a session has recorded operations but no complete turn
    # closed yet (e.g. the turn is still in progress when the dashboard
    # is viewed).
    for o in ops:
        sid = o.get("session_id")
        if sid and sid not in seen:
            seen.add(sid)
            ordered_ids.append(sid)

    # --- Passo 2: ultimo timestamp visto per ciascuna sessione --------------
    # "last_seen" e' un dizionario {session_id: timestamp_piu_recente}.
    # I timestamp sono stringhe in formato ISO (es. "2026-08-25T10:40:00Z"):
    # confrontare due stringhe ISO con "<" o "max()" funziona correttamente
    # come confronto cronologico, perche' quel formato mette prima l'anno,
    # poi il mese, poi il giorno ecc. -- non serve convertirle in oggetti
    # data per sapere qual e' la piu' recente.
    # [EN] --- Step 2: last seen timestamp for each session ---
    # "last_seen" is a dictionary {session_id: most_recent_timestamp}.
    # Timestamps are strings in ISO format (e.g.
    # "2026-08-25T10:40:00Z"): comparing two ISO strings with "<" or
    # "max()" works correctly as a chronological comparison, because
    # that format puts the year first, then the month, then the day
    # etc. -- no need to convert them to date objects to know which one
    # is the most recent.
    last_seen = {}
    for t in tokens:
        last_seen[t["session_id"]] = t["timestamp"]
    for o in ops:
        sid = o.get("session_id")
        if sid:
            # Una sessione ha sia turni che operazioni: teniamo il piu'
            # recente tra i due. o.get("timestamp", "") usa "" se manca,
            # cosi' max() ha comunque due stringhe da confrontare.
            # [EN] A session has both turns and operations: we keep the
            # most recent of the two. o.get("timestamp", "") uses "" if
            # missing, so max() still has two strings to compare.
            last_seen[sid] = max(last_seen.get(sid, ""), o.get("timestamp", ""))

    # --- Passo 3: numero di turni per sessione ------------------------------
    # Numero di interazioni per sessione (mostrato nella tendina Sessione).
    # [EN] --- Step 3: number of turns per session ---
    # Number of interactions per session (shown in the Session
    # dropdown).
    session_stats = {}
    for t in tokens:
        sid = t["session_id"]
        # dict.setdefault(chiave, default) vuol dire: "se la chiave non
        # c'e' ancora, creala con questo valore di default; se c'e' gia',
        # non toccarla e restituisci quella esistente" -- serve per
        # inizializzare il contatore a {"count": 0} solo la prima volta che
        # si incontra ciascuna sessione, senza un doppio controllo esplicito.
        # [EN] dict.setdefault(key, default) means: "if the key is not
        # there yet, create it with this default value; if it is
        # already there, leave it alone and return the existing one" --
        # it serves to initialize the counter to {"count": 0} only the
        # first time each session is encountered, without an explicit
        # double check.
        session_stats.setdefault(sid, {"count": 0})
        session_stats[sid]["count"] += 1

    # --- Passo 4: ordiniamo per data piu' recente ---------------------------
    # sorted(lista, key=funzione, reverse=True): riordina "ordered_ids"
    # usando come criterio di confronto il valore restituito da "key" per
    # ciascun elemento (qui: il suo last_seen, o "" se mancante) e
    # reverse=True vuol dire "dal piu' grande al piu' piccolo", cioe' dalla
    # sessione piu' recente alla piu' vecchia. "lambda s: ..." e' una
    # funzione anonima scritta in una riga sola, usata qui solo per questo
    # ordinamento (equivalente a definire una funzione con "def" a parte,
    # ma piu' compatta per un uso singolo e semplice come questo).
    # [EN] --- Step 4: sort by most recent date ---
    # sorted(list, key=function, reverse=True): reorders "ordered_ids"
    # using as comparison criterion the value returned by "key" for
    # each element (here: its last_seen, or "" if missing) and
    # reverse=True means "from largest to smallest", i.e. from the most
    # recent session to the oldest. "lambda s: ..." is an anonymous
    # function written on a single line, used here only for this sort
    # (equivalent to defining a separate function with "def", but more
    # compact for a single, simple use like this one).
    sessions_sorted = sorted(ordered_ids, key=lambda s: last_seen.get(s, ""), reverse=True)
    return sessions_sorted, last_seen, session_stats


def _build_payload(tokens, ops, sessions_sorted, session_info, last_seen, session_stats):
    """Costruisce il dizionario finale che verra' trasformato in JSON e
    incollato nella pagina. Ogni chiave di primo livello ("turns", "ops",
    "sessions", ...) e' un pezzo di dati che il JavaScript del template
    legge per popolare tabelle e grafici.

    [EN] Builds the final dictionary that will be turned into JSON and
    pasted into the page. Every top-level key ("turns", "ops",
    "sessions", ...) is a piece of data the template's JavaScript reads
    to populate tables and charts."""
    return {
        # "turns" e' costruita con una LIST COMPREHENSION: e' un modo
        # compatto, molto usato in Python, di scrivere
        #     turns = []
        #     for t in tokens:
        #         turns.append({...})
        # tutto in una riga sola dentro le parentesi quadre [ ... for t in tokens].
        # Qui si crea un dizionario piu' piccolo per ogni turno, con nomi di
        # chiave abbreviati (i, o, cw, cr, tot...) apposta per rendere il
        # JSON incorporato in pagina piu' leggero da scaricare nel browser.
        # [EN] "turns" is built with a LIST COMPREHENSION: it is a
        # compact, very common Python way of writing
        #     turns = []
        #     for t in tokens:
        #         turns.append({...})
        # all on a single line inside the square brackets
        # [ ... for t in tokens].
        # Here a smaller dictionary is created for each turn, with
        # abbreviated key names (i, o, cw, cr, tot...) on purpose, to
        # make the JSON embedded in the page lighter to download in the
        # browser.
        "turns": [
            {"ts": t["timestamp"], "sid": t["session_id"], "i": t["input"], "o": t["output"],
             "cw": t["cache_write"], "cw1": t["cache_write_1h"],
             "cr": t["cache_read"], "tot": t["total"], "acc": t["account"],
             "sum": t["summary"], "model": t["model"],
             # "st" e non "start": stessa convenzione di abbreviazione delle
             # chiavi vicine. Uguale a "ts" sulle righe scritte prima che
             # data.read_tokens() sapesse leggere questo dato (t["start"] e'
             # gia' ricaduto su t["timestamp"] li', vedi data.py): il JS
             # legge sempre "st" per ricostruire le finestre di 5 ore, senza
             # bisogno di un "||" di ripiego ad ogni lettura.
             # [EN] "st" and not "start": same abbreviation convention as
             # the neighboring keys. Equal to "ts" on rows written before
             # data.read_tokens() knew how to read this figure (t["start"]
             # already fell back to t["timestamp"] there, see data.py): the
             # JS always reads "st" to rebuild the 5-hour windows, with no
             # need for a fallback "||" on every read.
             "st": t["start"]}
            for t in tokens
        ],
        "ops": [
            {
                "ts": o.get("timestamp", ""), "sid": o.get("session_id", ""),
                "tool": o.get("tool", ""), "target": o.get("target", ""),
                # A differenza di "turns" sopra, qui i valori arrivano
                # ancora come STRINGHE (operations.csv non e' passato da
                # data.read_tokens, che li convertiva gia' in int): per
                # questo li si converte solo ora, con data.safe_int(), che
                # torna 0 se il valore manca o non e' un numero valido.
                # [EN] Unlike "turns" above, here the values still
                # arrive as STRINGS (operations.csv did not go through
                # data.read_tokens, which already converted them to
                # int): that is why they are converted only now, with
                # data.safe_int(), which returns 0 if the value is
                # missing or is not a valid number.
                "i": data.safe_int(o.get("input_tokens")), "o": data.safe_int(o.get("output_tokens")),
                "cw": data.safe_int(o.get("cache_write_tokens")), "cr": data.safe_int(o.get("cache_read_tokens")),
                "model": o.get("model") or pricing.DEFAULT_MODEL_KEY,
            }
            for o in ops
        ],
        "sessions": [
            {
                "id": sid,
                "title": session_info[sid]["title"],
                "project": session_info[sid].get("project"),
                "lastTs": last_seen.get(sid, ""),
                "count": session_stats.get(sid, {}).get("count", 0),
            }
            for sid in sessions_sorted
        ],
        # Il listino prezzi intero viene passato al JavaScript cosi' com'e':
        # cosi' i calcoli di costo mostrati in pagina (che cambiano a
        # seconda dei filtri scelti dall'utente, quindi vanno rifatti nel
        # browser, non solo una volta in Python) usano sempre lo stesso
        # listino di pricing.py, senza doverlo duplicare a mano nel
        # JavaScript del template.
        # [EN] The whole price list is passed to the JavaScript as-is:
        # this way the cost calculations shown on the page (which
        # change depending on the filters chosen by the user, so they
        # must be redone in the browser, not just once in Python)
        # always use the same price list from pricing.py, without
        # having to duplicate it by hand in the template's JavaScript.
        "modelPricing": pricing.MODEL_PRICING,
        "cacheWrite1hMultiplier": pricing.CACHE_WRITE_1H_MULTIPLIER,
        "defaultModelKey": pricing.DEFAULT_MODEL_KEY,
    }


def render(tokens, ops):
    """Punto d'ingresso del modulo, chiamato da main.py. Scrive il file
    finale config.OUT_HTML (dashboard.html) e, a fianco, config.OUT_DATA_JS
    (dashboard-data.js) con i dati di sessione/turni/prezzi.

    [EN] Entry point of the module, called by main.py. Writes the final
    file config.OUT_HTML (dashboard.html) and, next to it,
    config.OUT_DATA_JS (dashboard-data.js) with the
    session/turn/price data."""
    sessions_sorted, last_seen, session_stats = _collect_sessions(tokens, ops)

    # tokens[-1] prende l'ULTIMO elemento della lista (l'indice -1 in Python
    # vuol dire "il primo contando dalla fine"): siccome tokens.csv viene
    # scritto in ordine cronologico (append_csv_row in log_tokens.py
    # aggiunge sempre in fondo), l'ultimo turno registrato e' anche il piu'
    # recente -- e la sua sessione e' quella "corrente", che vogliamo
    # sempre ri-risolvere (vedi sessions.resolve_all_session_info) invece
    # di fidarci della cache, perche' potrebbe essere ancora in corso.
    # "if tokens else None": se la lista e' vuota (prima esecuzione in
    # assoluto, nessun turno mai registrato), evitiamo l'errore che si
    # avrebbe leggendo l'ultimo elemento di una lista vuota.
    # [EN] tokens[-1] takes the LAST element of the list (index -1 in
    # Python means "the first counting from the end"): since tokens.csv
    # is written in chronological order (append_csv_row in
    # log_tokens.py always appends at the bottom), the last recorded
    # turn is also the most recent one -- and its session is the
    # "current" one, which we always want to re-resolve (see
    # sessions.resolve_all_session_info) instead of trusting the cache,
    # because it might still be in progress.
    # "if tokens else None": if the list is empty (the very first run
    # ever, no turn ever recorded), we avoid the error we would get
    # reading the last element of an empty list.
    most_recent_id = tokens[-1]["session_id"] if tokens else None
    session_info = sessions.resolve_all_session_info(sessions_sorted, most_recent_id)

    payload = _build_payload(tokens, ops, sessions_sorted, session_info, last_seen, session_stats)

    # json.dumps(payload) trasforma il dizionario Python in una stringa di
    # testo JSON (l'operazione inversa di json.load/json.loads).
    # ensure_ascii=False: mantiene lettere accentate leggibili invece di
    # convertirle in sequenze di escape.
    # .replace("</", "<\\/"): protezione di sicurezza. Anche se questo JSON
    # non finisce piu' dentro un <script> nell'HTML ma in un file .js a
    # parte, resta dentro una stringa JS (var DASHBOARD_DATA = ...;): se un
    # riassunto di sessione contenesse letteralmente "</script>" e quel file
    # venisse mai incollato a mano dentro una pagina, la barra "escaped" lo
    # rende comunque innocuo, senza cambiare il significato del JSON (con
    # "\/" o senza, in JSON "/" si legge identico).
    # [EN] json.dumps(payload) turns the Python dictionary into a JSON
    # text string (the inverse operation of json.load/json.loads).
    # ensure_ascii=False: keeps accented letters readable instead of
    # converting them into escape sequences.
    # .replace("</", "<\\/"): safety protection. Even though this JSON
    # no longer ends up inside a <script> in the HTML but in a separate
    # .js file, it still sits inside a JS string
    # (var DASHBOARD_DATA = ...;): if a session summary literally
    # contained "</script>" and that file were ever pasted by hand into
    # a page, the escaped slash keeps it harmless anyway, without
    # changing the meaning of the JSON (with "\/" or without, in JSON
    # "/" reads the same).
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    # I dati (sessioni/turni/prezzi) vivono in un file .js a parte, caricato
    # dal template con <script src="dashboard-data.js"> invece che incollati
    # dentro dashboard.html: cosi' dashboard.html cambia solo quando cambia
    # davvero la pagina (struttura/logica), non ad ogni turno registrato.
    # [EN] The data (sessions/turns/prices) lives in a separate .js
    # file, loaded by the template with <script
    # src="dashboard-data.js"> instead of being pasted inside
    # dashboard.html: this way dashboard.html changes only when the
    # page really changes (structure/logic), not on every recorded
    # turn.
    with open(config.OUT_DATA_JS, "w", encoding="utf-8") as f:
        f.write("var DASHBOARD_DATA = " + data_json + ";\n")

    html = templating.load_template("dashboard.html")
    # __HEADER_CSS__ e __SITE_HEADER__ sono i due segnaposto che il
    # template dashboard.html lascia liberi per l'intestazione/navbar
    # condivisa: templating.HEADER_CSS e' il CSS (identico su tutte e 3 le
    # pagine), templating.render_header("dashboard", ...) genera l'HTML
    # della barra di navigazione con la scheda "Dashboard" evidenziata
    # come attiva (vedi generate_dashboard/header.py).
    # [EN] __HEADER_CSS__ and __SITE_HEADER__ are the two placeholders
    # the dashboard.html template leaves free for the shared
    # header/navbar: templating.HEADER_CSS is the CSS (identical on all
    # 3 pages), templating.render_header("dashboard", ...) generates
    # the navigation bar HTML with the "Dashboard" tab highlighted as
    # active (see generate_dashboard/header.py).
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
    # refresh_control=True: solo qui i numeri cambiano ad ogni turno, quindi
    # solo qui l'intestazione porta il bottone "Aggiorna" (nascosto finche'
    # i dati sono freschi -- lo accende lo script in fondo al template).
    # [EN] refresh_control=True: only here do the numbers change every
    # turn, so only here does the header carry the "Aggiorna" button
    # (hidden while the data is fresh -- the script at the bottom of
    # the template turns it on).
    html = html.replace(
        "__SITE_HEADER__",
        templating.render_header("dashboard", refresh_control=True,
                                 currency_control=True),
    )

    with open(config.OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
