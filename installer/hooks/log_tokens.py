#!/usr/bin/env python3
"""Hook Stop: a fine turno legge il transcript e somma i token usati,
poi appende una riga di riepilogo in tokens.csv.

Invocato in exec form (niente shell): Claude Code passa il payload JSON
dell'evento su stdin esattamente come in shell form.

NOTA PER CHI NON CONOSCE PYTHON:
Un "hook" di Claude Code e' semplicemente un programma esterno che Claude
Code lancia da solo in certi momenti (qui: "Stop", cioe' ogni volta che un
turno di conversazione finisce). Claude Code gli passa delle informazioni
tramite "stdin" (standard input: lo stesso canale che useresti se lanciassi
il programma a mano e gli scrivessi qualcosa in un terminale), sotto forma
di testo JSON. Questo script legge quel JSON, calcola quanti token sono
stati usati nell'ultimo turno, e li aggiunge come nuova riga in un file CSV
che funge da "registro storico" su disco.

[EN] Stop hook: at the end of each turn it reads the transcript and sums
the tokens used, then appends a summary row to tokens.csv.

Invoked in exec form (no shell): Claude Code passes the event's JSON
payload on stdin exactly as in shell form.

NOTE FOR THOSE WHO DON'T KNOW PYTHON:
A Claude Code "hook" is simply an external program that Claude Code
launches on its own at certain moments (here: "Stop", i.e. every time a
conversation turn ends). Claude Code passes it information via "stdin"
(standard input: the same channel you would use if you launched the
program by hand and typed something to it in a terminal), as JSON text.
This script reads that JSON, computes how many tokens were used in the
last turn, and appends them as a new row to a CSV file that acts as a
"historical ledger" on disk.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

# --- Percorsi usati da questo script (calcolati una sola volta all'avvio) --
# [EN] --- Paths used by this script (computed only once at startup) ---
HOME = os.path.expanduser("~")
# cartella in cui si trova QUESTO file
# [EN] the folder THIS file lives in
HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HOME, ".claude", "logs")
LOG_FILE = os.path.join(LOG_DIR, "tokens.csv")
STATE_FILE = os.path.join(LOG_DIR, "session_cumulative_state.json")
LABELS_FILE = os.path.join(HOOKS_DIR, "account_labels.json")
# Configurazione di Claude Code stesso: da qui si ricava l'account loggato
# (vedi account_uuid_candidates() per il perche' e' la fonte primaria).
# [EN] Claude Code's own configuration: the logged-in account is derived
# [EN] from here (see account_uuid_candidates() for why it is the primary
# [EN] source).
CLAUDE_CODE_CONFIG = os.path.join(HOME, ".claude.json")

# Nomi delle colonne di tokens.csv, nell'ordine in cui vengono scritte.
# [EN] Column names of tokens.csv, in the order they are written.
CSV_HEADER = [
    "timestamp", "session_id", "input_tokens", "output_tokens",
    "cache_write_tokens", "cache_read_tokens", "total_tokens",
    "account", "summary", "model", "origine", "cache_write_1h_tokens",
    "turn_start",
]

# Valore della colonna "origine" per le righe scritte qui: sono OSSERVAZIONI
# dirette (l'account letto dalla configurazione nel momento esatto del turno),
# a differenza di quelle ricostruite a posteriori da generate_dashboard/
# backfill.py, che scrive "backfill". La distinzione non e' cosmetica: e' cio'
# che permette al backfill di sapere quali righe sono prove e quali no, e
# quindi di non riciclare all'infinito le proprie deduzioni. Vedi la docstring
# di backfill.py.
# [EN] Value of the "origine" column for the rows written here: they are
# [EN] direct OBSERVATIONS (the account read from the configuration at the
# [EN] exact moment of the turn), unlike the ones reconstructed after the
# [EN] fact by generate_dashboard/backfill.py, which writes "backfill". The
# [EN] distinction is not cosmetic: it is what lets the backfill know which
# [EN] rows are evidence and which are not, and therefore avoid endlessly
# [EN] recycling its own deductions. See the backfill.py docstring.
ORIGINE = "hook"


def subagent_transcripts(transcript_path):
    """I transcript dei sotto-agenti lanciati da questa sessione.

    Quando Claude Code delega un compito a un sotto-agente (tool Task/Agent),
    quella conversazione NON finisce nel transcript principale: riceve un
    file tutto suo, in una cartella che porta il nome della sessione madre.

        projects/<progetto>/<session_id>.jsonl             <- principale
        projects/<progetto>/<session_id>/subagents/*.jsonl <- sotto-agenti

    Vanno sommati insieme al principale, altrimenti il consumo del turno
    risulta sistematicamente inferiore al vero ogni volta che il turno ha
    delegato qualcosa -- e un sotto-agente e' una conversazione intera, non
    una chiamata isolata.

    [EN] The transcripts of the subagents launched by this session.

    When Claude Code delegates a task to a subagent (Task/Agent tool), that
    conversation does NOT end up in the main transcript: it gets a file all
    of its own, in a folder named after the parent session.

        projects/<project>/<session_id>.jsonl             <- main
        projects/<project>/<session_id>/subagents/*.jsonl <- subagents

    They must be added up together with the main one, otherwise the turn's
    consumption comes out systematically lower than the truth every time
    the turn delegated something -- and a subagent is a whole conversation,
    not an isolated call.
    """
    return sorted(glob.glob(os.path.join(
        os.path.splitext(transcript_path)[0], "subagents", "*.jsonl")))


def sum_transcript_usage(transcript_path):
    """Legge l'intero transcript della sessione, sotto-agenti compresi, e
    restituisce i 4 totali CUMULATIVI di token usati fino a questo momento
    (non solo nell'ultimo turno: quello si calcola dopo, in
    compute_turn_delta).

    [EN] Reads the session's entire transcript, subagents included, and
    returns the 4 CUMULATIVE totals of tokens used up to this moment (not
    just in the last turn: that one is computed later, in
    compute_turn_delta).
    """
    # Il transcript e' un .jsonl con l'INTERA cronologia di sessione. Una
    # singola chiamata API con piu' blocchi (thinking/text/tool_use) viene
    # scritta come piu' righe che condividono lo stesso message.id e la
    # stessa 'usage': deduplichiamo per message.id per non contarla piu'
    # volte. cache_write e cache_read restano separati (prezzi diversi).
    # [EN] The transcript is a .jsonl with the ENTIRE session history. A
    # [EN] single API call with several blocks (thinking/text/tool_use) is
    # [EN] written as several lines sharing the same message.id and the same
    # [EN] 'usage': we deduplicate by message.id so we don't count it more
    # [EN] than once. cache_write and cache_read stay separate (different
    # [EN] prices).
    # message.id -> valori gia' contati per quel messaggio
    # [EN] message.id -> values already counted for that message
    seen_msg_ids = {}
    # input, output, cache_write, cache_read, cache_write a TTL 1 ora.
    # L'ultimo e' un SOTTOINSIEME del terzo, non un addendo: serve solo a
    # sapere quanta parte della cache write va prezzata 2x invece di 1,25x.
    # [EN] input, output, cache_write, cache_read, cache write at 1h TTL.
    # [EN] The last one is a SUBSET of the third, not an addend: it only
    # [EN] serves to know how much of the cache write must be priced 2x
    # [EN] instead of 1.25x.
    totali = [0, 0, 0, 0, 0]

    def somma(percorso):
        """Aggiunge a "totali" i consumi di un singolo file di transcript.

        [EN] Adds the consumption of a single transcript file to "totali".
        """
        try:
            # errors="replace": alcuni caratteri nel transcript potrebbero non
            # essere UTF-8 valido (raro, ma possibile); li si sostituisce con
            # un segnaposto invece di far crashare la lettura dell'intero file.
            # [EN] errors="replace": some characters in the transcript might
            # [EN] not be valid UTF-8 (rare, but possible); they get replaced
            # [EN] with a placeholder instead of crashing the read of the
            # [EN] whole file.
            f = open(percorso, encoding="utf-8", errors="replace")
        except OSError:
            # un sotto-agente illeggibile non deve far perdere il resto
            # [EN] an unreadable subagent must not cause the rest to be lost
            return
        with f:
            # scorre il file una riga alla volta
            # [EN] scans the file one line at a time
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    # riga non-JSON valida (rara, ma non blocca tutto)
                    # [EN] a line that is not valid JSON (rare, and it does
                    # [EN] not block everything)
                    continue

                # "entry.get('message')" e' None se la riga non ha quella
                # chiave; "isinstance(x, dict)" controlla che sia davvero un
                # dizionario e non, per esempio, una stringa o un numero --
                # doppia sicurezza prima di provare a leggerci dentro.
                # [EN] "entry.get('message')" is None if the line lacks that
                # [EN] key; "isinstance(x, dict)" checks it really is a
                # [EN] dictionary and not, for example, a string or a number
                # [EN] -- double safety before trying to read inside it.
                message = entry.get("message") if isinstance(entry.get("message"), dict) else None
                usage = message.get("usage") if message else None
                if not usage:
                    # Alcune righe hanno "usage" direttamente al livello
                    # principale invece che dentro "message" (formati diversi
                    # di evento nel transcript).
                    # [EN] Some lines have "usage" directly at the top level
                    # [EN] instead of inside "message" (different event
                    # [EN] formats in the transcript).
                    usage = entry.get("usage")
                if not usage:
                    # questa riga non contiene dati di consumo token
                    # [EN] this line contains no token usage data
                    continue

                # I blocchi di uno stesso messaggio ripetono l'usage, ma non
                # sempre IDENTICO: la prima riga puo' essere scritta a risposta
                # ancora in corso, e l'output_tokens cresce nelle successive.
                # Si somma percio' solo l'incremento campo per campo: un
                # duplicato esatto vale zero, un aggiornamento vale la
                # differenza. Scartare le occorrenze successive perdeva quella
                # crescita.
                # [EN] The blocks of one same message repeat the usage, but
                # [EN] not always IDENTICALLY: the first line may be written
                # [EN] while the reply is still in progress, and output_tokens
                # [EN] grows in the following ones. So we only add the
                # [EN] field-by-field increment: an exact duplicate counts as
                # [EN] zero, an update counts as the difference. Discarding
                # [EN] the later occurrences lost that growth.
                dettaglio = usage.get("cache_creation")
                cw_1h = 0
                if isinstance(dettaglio, dict):
                    cw_1h = dettaglio.get("ephemeral_1h_input_tokens", 0) or 0
                nuovo = [
                    usage.get("input_tokens", 0) or 0,
                    usage.get("output_tokens", 0) or 0,
                    usage.get("cache_creation_input_tokens", 0) or 0,
                    usage.get("cache_read_input_tokens", 0) or 0,
                    cw_1h,
                ]
                msg_id = message.get("id") if message else None
                if msg_id:
                    prec = seen_msg_ids.get(msg_id)
                    if prec is not None:
                        incremento = [max(0, n - p) for n, p in zip(nuovo, prec)]
                        seen_msg_ids[msg_id] = [max(n, p) for n, p in zip(nuovo, prec)]
                        nuovo = incremento
                    else:
                        seen_msg_ids[msg_id] = list(nuovo)
                for i, v in enumerate(nuovo):
                    totali[i] += v

    # Un unico insieme "gia' visto" condiviso fra tutti i file, cosi' un
    # messaggio che comparisse in due di essi non verrebbe contato due volte.
    # [EN] A single "already seen" set shared across all the files, so a
    # [EN] message that appeared in two of them would not be counted twice.
    somma(transcript_path)
    for percorso in subagent_transcripts(transcript_path):
        somma(percorso)
    return tuple(totali)


def compute_turn_delta(session_id, cumulative):
    """Trasforma i totali cumulativi (dall'inizio sessione) nel consumo del
    SOLO turno appena concluso, confrontandoli con l'ultimo valore
    cumulativo salvato la volta precedente per la stessa sessione.

    [EN] Turns the cumulative totals (since session start) into the
    consumption of ONLY the turn just ended, comparing them with the last
    cumulative value saved the previous time for the same session.
    """
    # Sottraiamo l'ultimo cumulativo noto per questa sessione per ottenere
    # il consumo del SOLO turno appena concluso.
    # [EN] We subtract the last known cumulative for this session to obtain
    # [EN] the consumption of ONLY the turn just ended.
    input_tok, output_tok, cache_write_tok, cache_read_tok, cw_1h_tok = cumulative

    # STATE_FILE tiene, per ogni sessione ancora aperta, l'ultimo totale
    # cumulativo visto: serve da "memoria" tra un turno e l'altro (ogni
    # esecuzione di questo script parte da zero, non ha altro modo di
    # ricordare cosa era gia' stato contato prima).
    # [EN] STATE_FILE keeps, for each still-open session, the last cumulative
    # [EN] total seen: it acts as "memory" between one turn and the next
    # [EN] (each run of this script starts from zero, it has no other way to
    # [EN] remember what had already been counted before).
    try:
        with open(STATE_FILE, encoding="utf-8") as sf:
            state = json.load(sf)
    except (OSError, json.JSONDecodeError):
        # primo turno in assoluto, o file corrotto: si riparte da vuoto
        # [EN] very first turn ever, or corrupted file: start over from empty
        state = {}

    prev = state.get(session_id, {"input": 0, "output": 0, "cache_write": 0,
                                  "cache_read": 0, "cache_write_1h": 0})

    # "max(0, nuovo - vecchio)" calcola la differenza, ma non lascia mai
    # scendere sotto zero: protezione contro casi limite in cui il
    # cumulativo sembrasse "tornare indietro" (es. un transcript
    # troncato/riscritto), che altrimenti produrrebbero un numero negativo
    # senza senso in tokens.csv.
    # [EN] "max(0, new - old)" computes the difference, but never lets it
    # [EN] drop below zero: protection against edge cases where the
    # [EN] cumulative would seem to "go backwards" (e.g. a
    # [EN] truncated/rewritten transcript), which would otherwise produce a
    # [EN] meaningless negative number in tokens.csv.
    delta = (
        max(0, input_tok - prev.get("input", 0)),
        max(0, output_tok - prev.get("output", 0)),
        max(0, cache_write_tok - prev.get("cache_write", 0)),
        max(0, cache_read_tok - prev.get("cache_read", 0)),
        max(0, cw_1h_tok - prev.get("cache_write_1h", 0)),
    )

    # Aggiorniamo subito lo stato salvato con i nuovi totali cumulativi,
    # cosi' il prossimo turno della stessa sessione calcolera' il delta
    # corretto rispetto a QUESTO momento.
    # [EN] We immediately update the saved state with the new cumulative
    # [EN] totals, so the next turn of the same session will compute the
    # [EN] correct delta relative to THIS moment.
    state[session_id] = {
        "input": input_tok, "output": output_tok,
        "cache_write": cache_write_tok, "cache_read": cache_read_tok,
        "cache_write_1h": cw_1h_tok,
    }
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as sf:
        json.dump(state, sf)

    return delta


def _read_json(path):
    """Legge un file JSON e restituisce il dizionario, o {} se il file non
    c'e' / non e' leggibile / non e' JSON valido.

    Serve perche' tutte le fonti da cui proviamo a ricavare l'account sono
    OPZIONALI: nessuna di loro deve poter far fallire l'hook.

    [EN] Reads a JSON file and returns the dictionary, or {} if the file is
    missing / not readable / not valid JSON.

    Needed because all the sources we try to derive the account from are
    OPTIONAL: none of them may be allowed to make the hook fail.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def account_uuid_candidates():
    """Restituisce, in ordine di preferenza, gli UUID di account trovati
    sulla macchina. La prima fonte che risponde vince.

    ATTENZIONE (motivo per cui le fonti sono due e in QUEST'ordine):
    la fonte storica era %APPDATA%\\Claude\\config.json (app desktop Claude),
    ma se Python e' installato dal Microsoft Store / Python Install Manager
    gira dentro un container MSIX che VIRTUALIZZA %APPDATA%: da li' dentro
    la cartella %APPDATA%\\Claude semplicemente NON esiste (open() alza
    FileNotFoundError anche se il file c'e' davvero), e l'account finiva
    sempre come "sconosciuto". ~/.claude.json invece sta nella home vera e
    si legge sempre, quindi e' la fonte primaria.

    [EN] Returns, in order of preference, the account UUIDs found on this
    machine. The first source that answers wins.

    WARNING (the reason why the sources are two and in THIS order): the
    historical source was %APPDATA%\\Claude\\config.json (Claude desktop
    app), but if Python is installed from the Microsoft Store / Python
    Install Manager it runs inside an MSIX container that VIRTUALIZES
    %APPDATA%: from in there the %APPDATA%\\Claude folder simply does NOT
    exist (open() raises FileNotFoundError even though the file is really
    there), and the account always ended up as "sconosciuto".
    ~/.claude.json instead lives in the real home and can always be read,
    so it is the primary source.
    """
    candidates = []

    # 1) ~/.claude.json e' il file di configurazione di Claude Code stesso:
    #    contiene un blocco "oauthAccount" con l'uuid dell'account loggato.
    # [EN] 1) ~/.claude.json is Claude Code's own configuration file: it
    # [EN]    contains an "oauthAccount" block with the logged-in account's
    # [EN]    uuid.
    oauth = _read_json(CLAUDE_CODE_CONFIG).get("oauthAccount") or {}
    candidates.append(oauth.get("accountUuid"))

    # 2) %APPDATA%\Claude\config.json (app desktop Claude): fonte di
    #    ripiego, usata solo se la prima non ha dato nulla.
    #    os.environ.get("APPDATA", "") legge la variabile d'ambiente di
    #    Windows che punta alla cartella dati applicazioni dell'utente
    #    corrente ("" come ripiego se non esistesse, es. su Linux/macOS).
    # [EN] 2) %APPDATA%\Claude\config.json (Claude desktop app): fallback
    # [EN]    source, used only if the first one yielded nothing.
    # [EN]    os.environ.get("APPDATA", "") reads the Windows environment
    # [EN]    variable pointing to the current user's application data
    # [EN]    folder ("" as a fallback if it did not exist, e.g. on
    # [EN]    Linux/macOS).
    desktop_config = os.path.join(os.environ.get("APPDATA", ""), "Claude", "config.json")
    candidates.append(_read_json(desktop_config).get("lastKnownAccountUuid"))

    # Tiene solo i valori effettivamente trovati (scarta None e stringhe vuote).
    # [EN] Keeps only the values actually found (discards None and empty
    # [EN] strings).
    return [c for c in candidates if c]


def resolve_account():
    """Determina quale account Claude ha generato questo turno, con
    un'etichetta leggibile se configurata, altrimenti l'UUID grezzo.

    [EN] Determines which Claude account generated this turn, with a
    readable label if configured, otherwise the raw UUID.
    """
    # Le etichette leggibili sono opzionali e locali alla macchina
    # (account_labels.json, non incluso nella distribuzione): fallback
    # all'uuid grezzo, o "sconosciuto" se non disponibile.
    # [EN] Readable labels are optional and local to the machine
    # [EN] (account_labels.json, not part of the distributed package): fall
    # [EN] back to the raw uuid, or "sconosciuto" if unavailable.
    uuid_labels = _read_json(LABELS_FILE)

    for uuid in account_uuid_candidates():
        # uuid_labels.get(uuid, uuid): se questo uuid ha un'etichetta
        # configurata la usa, altrimenti mostra l'uuid stesso.
        # [EN] uuid_labels.get(uuid, uuid): if this uuid has a configured
        # [EN] label use it, otherwise show the uuid itself.
        return uuid_labels.get(uuid, uuid)
    return "sconosciuto"


def extract_summary(transcript_path):
    """Estrae un breve riassunto testuale di cosa e' stato chiesto
    nell'ultimo turno, da mostrare in dashboard accanto ai numeri.

    [EN] Extracts a short textual summary of what was asked in the last
    turn, to show in the dashboard next to the numbers.
    """
    # Le entry "queue-operation"/"enqueue" sono il testo grezzo digitato
    # dall'utente, a differenza delle entry "user" (per lo piu' risultati
    # di tool). Prendiamo l'ultima enqueue non vuota del turno.
    # [EN] The "queue-operation"/"enqueue" entries are the raw text typed by
    # [EN] the user, unlike the "user" entries (mostly tool results). We
    # [EN] take the turn's last non-empty enqueue.
    msg = ""
    with open(transcript_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "queue-operation" and e.get("operation") == "enqueue":
                content = e.get("content")
                if content:
                    # Non ci fermiamo alla prima trovata: continuando il
                    # ciclo, l'ultima assegnazione a "msg" resta quella
                    # dell'ultimo messaggio del genere nel file (il piu'
                    # recente, dato che il transcript e' in ordine
                    # cronologico).
                    # [EN] We don't stop at the first one found: by letting
                    # [EN] the loop continue, the last assignment to "msg"
                    # [EN] remains the one from the last such message in the
                    # [EN] file (the most recent, since the transcript is in
                    # [EN] chronological order).
                    msg = content

    # re.sub(pattern, sostituto, testo) sostituisce ogni occorrenza del
    # pattern con il testo indicato: "\s+" vuol dire "una o piu' spazi/a-capo
    # di fila", sostituiti con un singolo spazio -- utile perche' il testo
    # digitato dall'utente puo' avere piu' righe, che qui vogliamo
    # appiattire su una riga sola per il CSV. str(msg): forza msg a essere
    # una stringa anche se per qualche motivo contenesse un altro tipo.
    # [EN] re.sub(pattern, replacement, text) replaces every occurrence of
    # [EN] the pattern with the given text: "\s+" means "one or more
    # [EN] consecutive spaces/newlines", replaced with a single space --
    # [EN] useful because the text typed by the user may span several lines,
    # [EN] which here we want to flatten onto a single line for the CSV.
    # [EN] str(msg): forces msg to be a string even if for some reason it
    # [EN] held another type.
    msg = re.sub(r"\s+", " ", str(msg)).strip()
    if len(msg) > 80:
        # Troncamento a 80 caratteri con puntini di sospensione, per non
        # riempire il CSV (e la dashboard) con richieste lunghissime.
        # [EN] Truncation to 80 characters with an ellipsis, so as not to
        # [EN] fill the CSV (and the dashboard) with very long requests.
        msg = msg[:80] + "..."
    return msg


def extract_turn_start(transcript_path):
    """L'istante in cui l'utente ha scritto il messaggio che ha aperto
    questo turno, non quello -- a volte molto piu' tardi -- in cui si e'
    concluso e "timestamp" e' stato preso. Stessa fonte di
    extract_summary() (l'ultima "enqueue" del transcript), ma qui
    interessa il suo timestamp: e' quell'istante, non la fine del turno,
    a far scattare la finestra di 5 ore del piano flat (vedi
    addBlockPeriods in templates/dashboard.html).

    Restituisce None se non c'e' nessuna enqueue (turno sintetico o
    transcript troncato): chi chiama ricade sul timestamp di fine turno.

    [EN] The instant the user wrote the message that opened this turn,
    not the -- sometimes much later -- one at which it ended and
    "timestamp" was taken. Same source as extract_summary() (the
    transcript's last "enqueue"), but here its timestamp matters: that
    instant, not the turn's end, starts the flat plan's 5-hour window
    (see addBlockPeriods in templates/dashboard.html).

    Returns None if there is no enqueue (synthetic turn or truncated
    transcript): the caller falls back to the turn-end timestamp.
    """
    ts = None
    with open(transcript_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "queue-operation" and e.get("operation") == "enqueue":
                if e.get("content"):
                    # Come in extract_summary(): non ci si ferma alla prima,
                    # l'ultima assegnazione resta quella dell'enqueue piu'
                    # recente nel file.
                    # [EN] As in extract_summary(): we do not stop at the
                    # [EN] first one, the last assignment remains the most
                    # [EN] recent enqueue's in the file.
                    ts = e.get("timestamp") or ts
    return ts


def extract_model(transcript_path):
    """Determina quale modello (es. "claude-sonnet-5") ha effettivamente
    risposto nell'ultimo turno.

    [EN] Determines which model (e.g. "claude-sonnet-5") actually replied
    in the last turn.
    """
    # "<synthetic>" e' un placeholder interno (non un modello fatturabile):
    # scartato a favore dell'ultimo modello vero trovato nel turno.
    # [EN] "<synthetic>" is an internal placeholder (not a billable model):
    # [EN] discarded in favor of the last real model found in the turn.
    model = ""
    with open(transcript_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") != "assistant":
                continue
            # "or {}" evita un errore se message() fosse None
            # [EN] "or {}" avoids an error if message() were None
            msg = e.get("message") or {}
            m = msg.get("model")
            if m and m != "<synthetic>":
                # ultima trovata "buona" vince, come in extract_summary
                # [EN] the last "good" one found wins, as in extract_summary
                model = m
    return model or "sconosciuto"


def _colonne_esistenti():
    """Quante colonne dichiara l'intestazione di tokens.csv gia' presente.

    Serve perche' la colonna "origine" e' stata aggiunta dopo: su un CSV
    scritto da una versione precedente l'intestazione ne dichiara una in
    meno, e appendere comunque il valore in piu' produrrebbe righe piu'
    lunghe dell'intestazione -- che csv.DictReader infilerebbe sotto una
    chiave fasulla, sporcando la lettura. Meglio scrivere una riga in
    formato vecchio: sara' il prossimo backfill a riscrivere il file
    intero con l'intestazione nuova (e le righe senza "origine" valgono
    comunque come scritte dall'hook, essendo le uniche che esistevano).
    Restituisce None se il file non c'e' ancora o non e' leggibile.

    [EN] How many columns the header of the already-present tokens.csv
    declares.

    Needed because the "origine" column was added later: on a CSV written
    by a previous version the header declares one fewer, and appending the
    extra value anyway would produce rows longer than the header -- which
    csv.DictReader would stuff under a bogus key, polluting the read.
    Better to write a row in the old format: the next backfill will rewrite
    the whole file with the new header (and rows without "origine" still
    count as written by the hook, being the only ones that existed).
    Returns None if the file does not exist yet or is not readable.
    """
    try:
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            intestazione = f.readline()
    except OSError:
        return None
    if not intestazione.strip():
        return None
    return len(next(csv.reader([intestazione])))


def append_csv_row(row):
    """Aggiunge una riga in fondo a tokens.csv, scrivendo prima
    l'intestazione se il file non esiste ancora.

    [EN] Appends a row at the end of tokens.csv, writing the header first
    if the file does not exist yet.
    """
    write_header = not os.path.exists(LOG_FILE)
    if not write_header:
        colonne = _colonne_esistenti()
        # Tronca la riga alle colonne che il file dichiara davvero (mai
        # allungarla: le colonne mancanti sono in coda, e sono le nuove).
        # [EN] Truncate the row to the columns the file really declares
        # [EN] (never lengthen it: the missing columns are at the end, and
        # [EN] they are the new ones).
        if colonne and colonne < len(row):
            row = row[:colonne]
    os.makedirs(LOG_DIR, exist_ok=True)
    # "a" (append) apre il file in modalita' "aggiungi in fondo" invece che
    # "sovrascrivi tutto" (che sarebbe "w", write): ogni turno aggiunge una
    # riga senza cancellare la cronologia gia' salvata. newline="" e'
    # richiesto dal modulo csv su Windows per evitare righe vuote doppie.
    # [EN] "a" (append) opens the file in "add at the end" mode instead of
    # [EN] "overwrite everything" (which would be "w", write): each turn
    # [EN] adds a row without erasing the history already saved. newline=""
    # [EN] is required by the csv module on Windows to avoid doubled blank
    # [EN] lines.
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)


def regenerate_dashboard():
    """Chiama il package generate_dashboard/ per rigenerare le pagine HTML
    subito dopo aver salvato i nuovi dati.

    [EN] Calls the generate_dashboard/ package to regenerate the HTML pages
    right after saving the new data.
    """
    try:
        # sys.path e' la lista di cartelle in cui Python cerca i moduli
        # quando fai "import qualcosa". Ci aggiungiamo HOOKS_DIR (la
        # cartella di questo stesso script) solo se non c'e' gia', cosi'
        # "import generate_dashboard" sotto trova la cartella
        # generate_dashboard/ che sta li' accanto.
        # [EN] sys.path is the list of folders where Python looks for
        # [EN] modules when you do "import something". We add HOOKS_DIR (the
        # [EN] folder of this very script) only if it is not there already,
        # [EN] so the "import generate_dashboard" below finds the
        # [EN] generate_dashboard/ folder sitting right next to it.
        if HOOKS_DIR not in sys.path:
            sys.path.insert(0, HOOKS_DIR)
        import generate_dashboard
        generate_dashboard.main()
    except Exception:
        # Qualunque errore nella rigenerazione della dashboard (bug, file
        # mancante, ecc.) NON deve far fallire l'hook Stop nel suo compito
        # principale, gia' completato sopra: salvare la riga in tokens.csv.
        # Il turno resta comunque registrato anche se la dashboard non si
        # aggiorna in quel momento.
        # [EN] Any error while regenerating the dashboard (bug, missing
        # [EN] file, etc.) must NOT make the Stop hook fail at its main job,
        # [EN] already completed above: saving the row into tokens.csv. The
        # [EN] turn stays recorded even if the dashboard does not refresh at
        # [EN] that moment.
        pass


def main():
    # sys.stdin.read() puo' rompersi su alcune macchine se Claude Code scrive
    # il payload con un BOM UTF-8 in testa (json rifiuta un BOM esplicito con
    # "Unexpected UTF-8 BOM"): leggiamo i byte grezzi e decodifichiamo con
    # utf-8-sig, che toglie il BOM se presente e si comporta come utf-8
    # altrimenti.
    # [EN] sys.stdin.read() can break on some machines if Claude Code writes
    # [EN] the payload with a UTF-8 BOM at the start (json rejects an
    # [EN] explicit BOM with "Unexpected UTF-8 BOM"): we read the raw bytes
    # [EN] and decode with utf-8-sig, which strips the BOM if present and
    # [EN] behaves like utf-8 otherwise.
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "?")
    # strftime formatta un datetime come testo secondo un modello: "%Y-%m-%dT%H:%M:%SZ"
    # produce es. "2026-08-25T10:40:00Z" (formato ISO 8601, standard e
    # ordinabile alfabeticamente come una data).
    # [EN] strftime formats a datetime as text according to a template:
    # [EN] "%Y-%m-%dT%H:%M:%SZ" produces e.g. "2026-08-25T10:40:00Z"
    # [EN] (ISO 8601 format, standard and alphabetically sortable as a
    # [EN] date).
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not os.path.isfile(transcript_path):
        # Payload senza un transcript valido: non c'e' nulla da leggere,
        # usciamo silenziosamente senza scrivere nulla nel CSV.
        # [EN] Payload without a valid transcript: there is nothing to read,
        # [EN] we exit silently without writing anything to the CSV.
        return

    cumulative = sum_transcript_usage(transcript_path)
    (input_tok, output_tok, cache_write_tok, cache_read_tok,
     cw_1h_tok) = compute_turn_delta(session_id, cumulative)
    account = resolve_account()
    summary = extract_summary(transcript_path)
    model = extract_model(transcript_path)
    # Puo' essere None (vedi extract_turn_start): "or ''" scrive una
    # cella vuota nel CSV, che _read_csv/data.read_tokens() leggono gia'
    # come "assente" e trattano ricadendo su "timestamp".
    # [EN] Can be None (see extract_turn_start): "or ''" writes an empty
    # [EN] cell in the CSV, which _read_csv/data.read_tokens() already
    # [EN] read as "absent" and handle by falling back to "timestamp".
    turn_start = extract_turn_start(transcript_path) or ""
    total = input_tok + output_tok + cache_write_tok + cache_read_tok

    append_csv_row([
        timestamp, session_id, input_tok, output_tok, cache_write_tok,
        cache_read_tok, total, account, summary, model, ORIGINE, cw_1h_tok,
        turn_start,
    ])

    regenerate_dashboard()


# Vedi la spiegazione di questo pattern in generate_dashboard/__init__.py:
# "esegui main() solo se questo file viene lanciato direttamente, non se
# viene importato da un altro script". Claude Code lo lancia sempre
# direttamente (e' cosi' che e' configurato in ~/.claude/settings.json),
# quindi in pratica main() gira sempre quando questo hook scatta.
# [EN] See the explanation of this pattern in generate_dashboard/__init__.py:
# [EN] "run main() only if this file is launched directly, not when it is
# [EN] imported by another script". Claude Code always launches it directly
# [EN] (that is how it is configured in ~/.claude/settings.json), so in
# [EN] practice main() always runs when this hook fires.
if __name__ == "__main__":
    main()
