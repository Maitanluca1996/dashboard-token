"""Ricostruzione RETROATTIVA di tokens.csv e operations.csv dai transcript.

Gli hook (log_tokens.py / log_operation.py) registrano solo cio' che accade
DOPO l'installazione: una sessione gia' aperta prima non ha nessuna riga nei
CSV, e le sue eventuali righe successive sono deformate (vedi sotto). Questo
modulo colma il buco leggendo direttamente i transcript che Claude Code
scrive comunque in ~/.claude/projects/<progetto>/<session_id>.jsonl, che
contengono l'intera cronologia con tanto di consumi per chiamata.

DUE PROBLEMI DISTINTI, DUE RIMEDI DISTINTI
------------------------------------------
1) Sessioni mai viste dagli hook: nei CSV non esiste proprio nulla. Qui si
   ricostruisce tutto da zero.

2) Sessioni "a cavallo" dell'installazione: al primo hook Stop,
   session_cumulative_state.json non aveva ancora uno stato precedente per
   quella sessione, quindi compute_turn_delta() ha calcolato il delta
   partendo da zero e ha inglobato TUTTO il consumo pregresso in una sola
   riga, datata al momento dell'installazione. I totali sono giusti, ma la
   cronologia e' schiacciata su un istante sbagliato. Qui quella riga viene
   sostituita dai turni veri, ognuno con la sua data.

L'ACCOUNT SI ATTRIBUISCE PER TURNO, NON PER SESSIONE
----------------------------------------------------
L'account non e' una proprieta' della sessione ma del MOMENTO: su una
macchina su cui vengono usati piu' account, una sessione ripresa a
distanza di settimane puo' attraversarne piu' di uno. Attribuire "per sessione" sbaglia, e
sbaglia in silenzio. Ogni turno riceve percio' il proprio account, cercato
in quest'ordine:

 1. la TIMELINE degli accessi (vedi timeline_account): i log dell'app
    Claude registrano esplicitamente ogni cambio di account con data e ora.
    E' l'unica fonte che copre il passato per intero;
 2. l'account che l'hook ha gia' scritto per quella sessione, ma SOLO dal
    turno in cui l'hook l'ha osservato in poi -- mai all'indietro, o si
    stamperebbe l'account di oggi su turni di settimane fa;
 3. l'UUID dichiarato dal transcript stesso (entry "bridge-session"),
    tradotto in nome leggibile con account_labels.json;
 4. l'etichetta di ripiego ACCOUNT_NON_RILEVATO. Volutamente distinta da
    "sconosciuto", che indica invece una riga registrata dal vivo in cui la
    risoluzione e' fallita.

In nessun caso si tira a indovinare con l'account loggato adesso: una
sessione di mesi fa puo' benissimo essere stata di un altro.

LA COLONNA "origine"
--------------------
Distingue le righe scritte dagli hook ("hook") da quelle ricostruite qui
("backfill"). Non e' cosmetica: senza, dopo il primo backfill non si
distinguerebbe piu' un'osservazione vera da una ricostruita, la regola 2
non saprebbe da quale turno partire, e l'attribuzione si auto-perpetuerebbe
a ogni rilancio cristallizzando eventuali errori.

IDEMPOTENTE PER COSTRUZIONE
---------------------------
Il transcript e' la fonte di verita' per l'intera storia di una sessione:
per ogni sessione con transcript si BUTTANO le righe esistenti e si
riscrivono da capo. Rilanciare il backfill dieci volte produce quindi
esattamente lo stesso risultato della prima -- non esistono duplicati
possibili. Le sessioni senza transcript (cancellato, o proveniente da
un'altra macchina) restano intoccate.

NOTA PER CHI NON CONOSCE PYTHON:
Un "generatore" (le funzioni qui sotto che usano "yield" invece di "return")
e' una funzione che non restituisce tutti i risultati in blocco, ma li
consegna uno alla volta man mano che chi la usa li chiede. Serve qui perche'
i transcript possono essere file da decine di megabyte: leggerli tutti in
memoria per intero sarebbe uno spreco, mentre cosi' se ne tiene una riga
sola alla volta.

[EN] RETROACTIVE reconstruction of tokens.csv and operations.csv from
the transcripts.

The hooks (log_tokens.py / log_operation.py) only record what happens
AFTER the installation: a session already open before it has no row at
all in the CSVs, and its later rows, if any, are distorted (see
below). This module fills the gap by reading directly the transcripts
Claude Code writes anyway in
~/.claude/projects/<project>/<session_id>.jsonl, which contain the
whole history complete with per-call usage.

TWO DISTINCT PROBLEMS, TWO DISTINCT REMEDIES
--------------------------------------------
1) Sessions never seen by the hooks: nothing exists in the CSVs at
   all. Here everything is rebuilt from scratch.

2) Sessions "straddling" the installation: at the first Stop hook,
   session_cumulative_state.json did not yet hold a previous state for
   that session, so compute_turn_delta() computed the delta starting
   from zero and lumped ALL the past usage into a single row, dated at
   the moment of the installation. The totals are right, but the
   history is squashed onto a wrong instant. Here that row gets
   replaced by the real turns, each with its own date.

THE ACCOUNT IS ATTRIBUTED PER TURN, NOT PER SESSION
---------------------------------------------------
The account is not a property of the session but of the MOMENT: on a
machine where more than one account is used, a session resumed weeks
later can span several of them.
Attributing "per session" gets it wrong, and wrong silently. Each turn
therefore receives its own account, looked up in this order:

 1. the login TIMELINE (see timeline_account): the Claude app logs
    explicitly record every account change with date and time. It is
    the only source covering the whole past;
 2. the account the hook already wrote for that session, but ONLY from
    the turn where the hook observed it onwards -- never backwards, or
    today's account would be stamped onto turns from weeks ago;
 3. the UUID declared by the transcript itself ("bridge-session"
    entries), translated to a readable name via account_labels.json;
 4. the ACCOUNT_NON_RILEVATO fallback label. Deliberately distinct
    from "sconosciuto", which instead marks a row recorded live where
    resolution failed.

In no case do we guess using the currently logged-in account: a
session from months ago may well have belonged to another one.

THE "origine" COLUMN
--------------------
Distinguishes the rows written by the hooks ("hook") from those
rebuilt here ("backfill"). It is not cosmetic: without it, after the
first backfill a real observation could no longer be told apart from a
reconstructed one, rule 2 would not know which turn to start from, and
the attribution would self-perpetuate on every re-run, crystallizing
any mistakes.

IDEMPOTENT BY CONSTRUCTION
--------------------------
The transcript is the source of truth for a session's entire history:
for every session with a transcript the existing rows are THROWN AWAY
and rewritten from scratch. Re-running the backfill ten times thus
produces exactly the same result as the first run -- duplicates are
simply impossible. Sessions without a transcript (deleted, or coming
from another machine) are left untouched.

NOTE FOR READERS NEW TO PYTHON:
A "generator" (the functions below using "yield" instead of "return")
is a function that does not return all its results in one go, but
hands them over one at a time as the caller asks for them. It is
needed here because transcripts can be files of tens of megabytes:
reading them into memory whole would be wasteful, whereas this way
only one line at a time is held.
"""
import bisect
import csv
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

from . import config
from . import timeutils

# Etichetta usata nella colonna "account" per i turni ricostruiti di cui non
# possiamo sapere l'account (vedi docstring). Volutamente diversa da
# "sconosciuto", che invece indica una riga registrata dal vivo in cui la
# risoluzione dell'account e' fallita: sono due situazioni diverse e vanno
# distinguibili in dashboard.
# [EN] Label used in the "account" column for rebuilt turns whose
# account we cannot know (see docstring). Deliberately different from
# "sconosciuto", which instead marks a row recorded live where account
# resolution failed: they are two different situations and must stay
# distinguishable in the dashboard.
ACCOUNT_NON_RILEVATO = "non rilevato"

# Valori che NON sono account veri ma ripieghi, e che quindi non vanno mai
# scambiati per un'informazione acquisita: incontrarli equivale a non sapere
# nulla, e al rilancio del backfill si torna a cercare l'account da capo.
# "storico" e' la vecchia etichetta usata prima di ACCOUNT_NON_RILEVATO:
# resta in elenco per non trattare come account vero cio' che una versione
# precedente ha gia' scritto nei CSV di chi aveva installato allora.
# [EN] Values that are NOT real accounts but fallbacks, and must
# therefore never be mistaken for acquired information: finding them
# equals knowing nothing, and on the next backfill run the account is
# looked up again from scratch. "storico" is the old label used before
# ACCOUNT_NON_RILEVATO: it stays in the list so that what a previous
# version already wrote into the CSVs of whoever had installed back
# then is not treated as a real account.
NON_SONO_ACCOUNT = ("sconosciuto", ACCOUNT_NON_RILEVATO, "storico")

# Di quanto un'osservazione dell'hook puo' valere anche per l'istante che la
# PRECEDE. L'hook Stop scrive la sua riga qualche secondo dopo la fine del
# turno, quindi il turno cui si riferisce risulta leggermente anteriore
# all'osservazione: senza questo margine il turno stesso che l'ha generata
# resterebbe senza account. Cinque minuti sono larghi per un hook e stretti
# rispetto a un cambio di account, che comunque, quando esiste, viene deciso
# prima dalla timeline.
# [EN] How far back a hook observation may also apply to the instant
# that PRECEDES it. The Stop hook writes its row a few seconds after
# the end of the turn, so the turn it refers to appears slightly
# earlier than the observation: without this margin the very turn that
# produced it would be left without an account. Five minutes are
# generous for a hook and narrow compared to an account switch, which
# in any case, when one exists, is decided first by the timeline.
MARGINE_OSSERVAZIONE = 5 * 60

# Le stesse intestazioni scritte dagli hook. Devono restare allineate a
# CSV_HEADER di log_tokens.py e log_operation.py: se un giorno si aggiunge
# una colonna li', va aggiunta anche qui.
# [EN] The same headers written by the hooks. They must stay aligned
# with CSV_HEADER in log_tokens.py and log_operation.py: if a column
# is ever added there, it must be added here too.
TOKENS_HEADER = [
    "timestamp", "session_id", "input_tokens", "output_tokens",
    "cache_write_tokens", "cache_read_tokens", "total_tokens",
    "account", "summary", "model", "origine", "cache_write_1h_tokens",
]

OPS_HEADER = [
    "timestamp", "session_id", "tool", "target",
    "input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens", "model",
]

# Valori della colonna "origine" (vedi docstring).
# [EN] Values of the "origine" column (see docstring).
ORIGINE_HOOK = "hook"
ORIGINE_BACKFILL = "backfill"


# ---------------------------------------------------------------- lettura --
# [EN] ----------------------------------------------------------- reading --

def iter_entries(path):
    """Restituisce, una alla volta, le entry JSON valide di un transcript.

    Le righe vuote e quelle non decodificabili vengono semplicemente
    saltate: un transcript troncato (sessione chiusa male, PC spento) non
    deve far fallire la ricostruzione di tutto il resto del file.

    [EN] Yields, one at a time, the valid JSON entries of a
    transcript.

    Empty lines and undecodable ones are simply skipped: a truncated
    transcript (session closed badly, PC switched off) must not make
    the reconstruction of the whole rest of the file fail.
    """
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def find_subagents(main_path):
    """I transcript dei sotto-agenti appartenenti a una sessione.

    Quando Claude Code delega un compito a un sotto-agente (tool Task/Agent),
    quella conversazione NON finisce nel transcript principale: riceve un
    file tutto suo, in una cartella che porta il nome della sessione madre.

        projects/<progetto>/<session_id>.jsonl             <- principale
        projects/<progetto>/<session_id>/subagents/*.jsonl <- sotto-agenti

    Sono consumi veri e spesso ingenti (un sotto-agente e' una conversazione
    intera): ignorarli puo' sottostimare in modo rilevante la sessione
    madre.

    [EN] The transcripts of the subagents belonging to a session.

    When Claude Code delegates a task to a subagent (Task/Agent tool),
    that conversation does NOT end up in the main transcript: it gets
    a file of its own, in a folder named after the parent session.

        projects/<project>/<session_id>.jsonl              <- main
        projects/<project>/<session_id>/subagents/*.jsonl  <- subagents

    This is real and often substantial usage (a subagent is a whole
    conversation): ignoring it can significantly underestimate the
    parent session.
    """
    return sorted(glob.glob(os.path.join(
        os.path.splitext(main_path)[0], "subagents", "*.jsonl")))


def find_transcripts():
    """Mappa {session_id: percorso del transcript} per tutte le sessioni
    presenti su questa macchina.

    Il nome del file .jsonl E' l'id di sessione, quindi non serve aprirlo per
    sapere a chi appartiene. Se lo stesso id comparisse in due cartelle di
    progetto diverse (non dovrebbe, ma non costa nulla difendersi) si tiene
    il file piu' grande, cioe' quello con piu' cronologia dentro.

    [EN] Map {session_id: transcript path} for all the sessions
    present on this machine.

    The .jsonl file name IS the session id, so there is no need to
    open it to know whom it belongs to. If the same id appeared in two
    different project folders (it should not, but defending against it
    costs nothing) the larger file is kept, i.e. the one with more
    history inside.
    """
    found = {}
    percorsi = glob.glob(os.path.join(config.PROJECTS_DIR, "*", "*.jsonl"))
    # Oltre all'albero principale, quelli dell'app desktop in "local agent
    # mode" (vedi config._altre_cartelle_progetti): stessa struttura, solo
    # in un posto diverso.
    # [EN] Besides the main tree, those of the desktop app in "local
    # agent mode" (see config._altre_cartelle_progetti): same
    # structure, just in a different place.
    for extra in config.PROJECT_DIRS_EXTRA:
        percorsi.extend(glob.glob(os.path.join(extra, "*", "*.jsonl")))
    for path in percorsi:
        sid = os.path.splitext(os.path.basename(path))[0]
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        prev = found.get(sid)
        if prev is None or size > prev[1]:
            found[sid] = (path, size)
    return {sid: path for sid, (path, _size) in found.items()}


# ---------------------------------------------------------- formattazione --
# [EN] -------------------------------------------------------- formatting --

def _norm_ts(raw, millis=False):
    """Converte il timestamp del transcript nel formato usato dai CSV.

    Nel transcript e' ISO 8601 con i millisecondi ("2025-01-01T10:40:35.776Z");
    tokens.csv lo vuole al secondo ("...:35Z", come lo scrive log_tokens.py) e
    operations.csv con i millisecondi (come lo scrive log_operation.py). Se
    il valore manca o e' scritto in un modo inatteso lo si restituisce cosi'
    com'e': meglio un timestamp strano che nessuna riga.

    [EN] Converts the transcript timestamp to the format used by the
    CSVs.

    In the transcript it is ISO 8601 with milliseconds
    ("2025-01-01T10:40:35.776Z"); tokens.csv wants it to the second
    ("...:35Z", as log_tokens.py writes it) and operations.csv with
    milliseconds (as log_operation.py writes it). If the value is
    missing or written in an unexpected way it is returned as is:
    better an odd timestamp than no row.
    """
    if not raw:
        return ""
    text = str(raw)
    # fromisoformat non digerisce la "Z" finale (che indica UTC) nelle
    # versioni piu' vecchie di Python: la si sostituisce con l'offset
    # equivalente, che invece capisce sempre.
    # [EN] fromisoformat does not digest the trailing "Z" (which means
    # UTC) on older Python versions: it is replaced with the
    # equivalent offset, which is always understood.
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if millis:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + "{:03d}Z".format(dt.microsecond // 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _etichette_account():
    """Mappa UUID -> nome leggibile, la stessa consultata da resolve_account()
    negli hook. File opzionale: se manca, gli UUID restano tali e quali.

    [EN] Map UUID -> readable name, the same one consulted by
    resolve_account() in the hooks. Optional file: if missing, the
    UUIDs stay exactly as they are."""
    try:
        with open(config.LABELS_FILE, encoding="utf-8", errors="replace") as f:
            etichette = json.load(f)
        return etichette if isinstance(etichette, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


# Chiavi da cui si ricava l'account: "ownerAccountUuid" compare nelle entry
# "bridge-session" (sessioni agganciate all'app o al web), "accountUuid" in
# altre entry di servizio. Sono le uniche tracce dell'account dentro un
# transcript -- una conversazione normale non ne lascia nessuna.
# [EN] Keys the account is derived from: "ownerAccountUuid" appears in
# "bridge-session" entries (sessions attached to the app or the web),
# "accountUuid" in other service entries. They are the only traces of
# the account inside a transcript -- a normal conversation leaves
# none.
_CHIAVI_ACCOUNT = ("ownerAccountUuid", "accountUuid")


def account_dal_transcript(path):
    """UUID dell'account che possedeva la sessione, se il transcript lo dice.

    Contrariamente a quanto si potrebbe pensare, l'account NON e' del tutto
    assente dai transcript: certe entry di servizio lo portano con se'. Non
    ci sono in ogni sessione -- percio' resta necessaria un'etichetta di
    ripiego -- ma quando ci sono e' un dato vero, non una supposizione, e va
    preferito a qualunque ripiego.

    Si esce alla prima occorrenza utile: su un transcript da decine di
    megabyte non ha senso continuare a leggere per riconfermare lo stesso
    valore centinaia di volte.

    [EN] UUID of the account that owned the session, if the transcript
    says so.

    Contrary to what one might think, the account is NOT entirely
    absent from the transcripts: certain service entries carry it
    along. They are not present in every session -- which is why a
    fallback label remains necessary -- but when they are there it is
    a real datum, not a guess, and it must be preferred to any
    fallback.

    We exit at the first useful occurrence: on a transcript of tens of
    megabytes there is no point in reading on to reconfirm the same
    value hundreds of times.
    """
    for e in iter_entries(path):
        for chiave in _CHIAVI_ACCOUNT:
            valore = e.get(chiave)
            if valore:
                return str(valore)
    return None


# Righe come:
#   2025-01-01 09:00:00 [info] [account] Login-state transition
#   (loggedOut: true -> false, uuid: 00000000-... -> 11111111-...), clearing oauth cache
# La freccia nel log e' un carattere unicode, quindi qui si accetta un
# "gruppo di caratteri non-spazio" qualunque al suo posto invece di
# scriverla a mano: cosi' la regex non dipende dalla codifica del file.
# [EN] Matches lines like the ones shown above: "<date> [info]
# [account] Login-state transition (... uuid: old -> new), ...". The
# arrow in the log is a unicode character, so any "group of non-space
# characters" is accepted in its place instead of writing it out: this
# way the regex does not depend on the file's encoding.
_RE_IDENTITA = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b.*\[account\].*"
    r"uuid: \S+ \S+ ([0-9a-fA-F-]{36})\)"
)


def _file_log_app():
    """I main*.log dell'applicazione Claude, dal piu' vecchio al piu' recente.

    [EN] The Claude application's main*.log files, oldest to newest."""
    trovati = []
    for cartella in config.APP_LOG_DIRS:
        try:
            if not os.path.isdir(cartella):
                continue
            for nome in os.listdir(cartella):
                if nome.startswith("main") and nome.endswith(".log"):
                    trovati.append(os.path.join(cartella, nome))
        except OSError:
            continue
    return sorted(trovati)


def timeline_account():
    """Ricostruisce CHI era loggato e QUANDO, leggendo i log dell'app Claude.

    Restituisce una lista ordinata di coppie (istante UTC, uuid account):
    ogni voce dice "da questo momento in poi l'account attivo e' questo",
    fino alla voce successiva.

    PERCHE' E' LA FONTE MIGLIORE: l'account non e' una proprieta' della
    sessione ma del MOMENTO. Su una macchina su cui vengono usati piu'
    account, attribuire l'account "per sessione" sbaglia; attribuirlo
    "per turno" con questa timeline no.
    I log risalgono inoltre molto piu' indietro di qualunque altra traccia
    locale (gli shell-snapshot, per esempio, vengono ripuliti dopo un mese).

    Gli eventi di logout ("-> <none>") si ignorano di proposito: dicono che
    l'account e' finito, non quale sara' il prossimo, e in mezzo non si
    consumano token.

    [EN] Reconstructs WHO was logged in and WHEN, by reading the
    Claude app logs.

    Returns an ordered list of (UTC instant, account uuid) pairs: each
    entry says "from this moment on the active account is this one",
    until the next entry.

    WHY IT IS THE BEST SOURCE: the account is not a property of the
    session but of the MOMENT. On a machine where more than one account
    is used, attributing the account "per session" gets it wrong;
    attributing it "per turn" with this timeline does not. The logs also reach much further back
    than any other local trace (shell snapshots, for instance, are
    cleaned up after a month).

    Logout events ("-> <none>") are ignored on purpose: they say the
    account has ended, not which one comes next, and no tokens are
    consumed in between.
    """
    eventi = set()
    for percorso in _file_log_app():
        try:
            # errors="replace": i log dell'app mescolano testo e frammenti
            # binari, e non devono far fallire la lettura.
            # [EN] errors="replace": the app logs mix text and binary
            # fragments, and they must not make the read fail.
            with open(percorso, encoding="utf-8", errors="replace") as f:
                for riga in f:
                    m = _RE_IDENTITA.match(riga)
                    if m:
                        eventi.add((m.group(1), m.group(2)))
        except OSError:
            continue

    timeline = []
    for quando, uuid in eventi:
        try:
            locale = datetime.strptime(quando, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        # I log sono nell'ora locale della macchina, i CSV in UTC.
        # [EN] The logs are in the machine's local time, the CSVs in
        # UTC.
        timeline.append((timeutils.from_italy_time(locale).timestamp(), uuid))
    timeline.sort()
    return timeline


def _cerca_nella_timeline(timeline, istante):
    """Ultimo account risultato attivo prima o durante "istante", oppure None
    se la timeline non arriva cosi' indietro.

    Ricerca binaria (bisect) invece di scorrere la lista: viene chiamata una
    volta per turno, e i turni possono essere molto numerosi.

    [EN] Last account known to be active before or at "istante", or
    None if the timeline does not reach that far back.

    Binary search (bisect) instead of scanning the list: it is called
    once per turn, and the turns can be very numerous.
    """
    if not timeline or istante is None:
        return None
    i = bisect.bisect_right(timeline, (istante, "￿"))
    return timeline[i - 1][1] if i else None


def _epoch(iso):
    """Da timestamp ISO dei CSV ("2025-01-01T09:34:00Z") a secondi UTC.

    [EN] From the CSVs' ISO timestamp ("2025-01-01T09:34:00Z") to UTC
    seconds."""
    if not iso:
        return None
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def _incremento(visti, msg_id, usage):
    """Quanto di questo "usage" e' NUOVO rispetto a quello gia' contato per lo
    stesso message.id.

    I blocchi di uno stesso messaggio ripetono l'usage, ed e' per questo che si
    deduplica -- ma non sempre lo ripetono IDENTICO: in messaggi reali si
    osserva l'output_tokens crescere fra un'occorrenza e la successiva
    (la prima riga viene scritta a risposta ancora in corso). Scartare le
    occorrenze successive perdeva quella crescita. Si somma percio' solo la
    differenza positiva, campo per campo: i duplicati veri danno zero, gli
    aggiornamenti danno l'incremento.

    [EN] How much of this "usage" is NEW compared to what has already
    been counted for the same message.id.

    The blocks of one same message repeat the usage, which is why we
    deduplicate -- but they do not always repeat it IDENTICALLY: in
    real messages output_tokens can be seen growing between one
    occurrence and the next (the first line is written while the
    response is still in progress). Discarding the later occurrences
    lost that growth. So only the positive difference is added, field
    by field: true duplicates yield zero, updates yield the increment.
    """
    campi = ("input_tokens", "output_tokens",
             "cache_creation_input_tokens", "cache_read_input_tokens")
    nuovo = [usage.get(k, 0) or 0 for k in campi] + [_cache_write_1h(usage)]
    if not msg_id:
        # senza id non c'e' nulla da confrontare
        # [EN] without an id there is nothing to compare against
        return nuovo
    prec = visti.get(msg_id)
    if prec is None:
        visti[msg_id] = nuovo
        return nuovo
    delta = [max(0, n - p) for n, p in zip(nuovo, prec)]
    visti[msg_id] = [max(n, p) for n, p in zip(nuovo, prec)]
    return delta


def _cache_write_1h(usage):
    """Quanti dei token di cache write usano la TTL da UN'ORA.

    Serve perche' le due durate costano diversamente: 1,25x il prezzo input
    per la cache a 5 minuti, 2x per quella a un'ora. Il totale
    "cache_creation_input_tokens" le mescola; la ripartizione sta nel campo
    "cache_creation", presente nei transcript recenti. Se manca, si
    restituisce 0 e il chiamante tratta tutto come cache a 5 minuti --
    esattamente il comportamento precedente, quindi nessuna regressione sui
    log vecchi.

    [EN] How many of the cache write tokens use the ONE-HOUR TTL.

    Needed because the two durations cost differently: 1.25x the input
    price for the 5-minute cache, 2x for the one-hour one. The
    "cache_creation_input_tokens" total mixes them; the split lives in
    the "cache_creation" field, present in recent transcripts. If it
    is missing, 0 is returned and the caller treats everything as
    5-minute cache -- exactly the previous behavior, hence no
    regression on old logs.
    """
    dettaglio = usage.get("cache_creation")
    if not isinstance(dettaglio, dict):
        return 0
    return dettaglio.get("ephemeral_1h_input_tokens", 0) or 0


def _flatten(text, limit):
    """Appiattisce un testo su una riga sola e lo tronca.

    Identico a quanto fanno extract_summary() (limite 80) ed extract_target()
    (limite 200) negli hook: un CSV con dentro degli a-capo sarebbe illeggibile.

    [EN] Flattens a text onto a single line and truncates it.

    Identical to what extract_summary() (limit 80) and
    extract_target() (limit 200) do in the hooks: a CSV with newlines
    inside would be unreadable.
    """
    out = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(out) > limit:
        out = out[:limit] + "..."
    return out


# ---------------------------------------------------- ricostruzione turni --
# [EN] --------------------------------------------------- turn rebuilding --

def rebuild_turns(path, session_id, account):
    """Vedi _rebuild_turns. "account" puo' essere una stringa fissa oppure una
    funzione che, dato il timestamp del turno, restituisce l'account: e' cosi'
    che si attribuisce un account DIVERSO ai turni di una stessa sessione che
    attraversa un cambio di account.

    [EN] See _rebuild_turns. "account" can be a fixed string or a
    function that, given the turn's timestamp, returns the account:
    this is how a DIFFERENT account is attributed to the turns of one
    same session that spans an account switch."""
    decidi = account if callable(account) else (lambda _ts: account)
    return _rebuild_turns(path, session_id, decidi)


def _rebuild_turns(path, session_id, decidi_account):
    """Ricostruisce le righe di tokens.csv per una sessione, una per turno.

    Un "turno" va da un messaggio digitato dall'utente al successivo: e'
    esattamente l'intervallo che l'hook Stop registra come una riga. Nel
    transcript l'inizio di un turno e' l'entry "queue-operation" con
    operation "enqueue", che contiene il testo digitato -- la stessa fonte
    che extract_summary() usa negli hook, quindi il campo "summary" viene
    identico a quello che avrebbe scritto l'hook.

    I consumi si sommano come in sum_transcript_usage(): lo "usage" di una
    chiamata API viene ripetuto uguale su ogni blocco del messaggio (testo,
    ragionamento, tool_use), quindi si deduplica per message.id, altrimenti
    la stessa chiamata verrebbe contata due o tre volte.

    [EN] Rebuilds the tokens.csv rows for a session, one per turn.

    A "turn" runs from one message typed by the user to the next: it
    is exactly the interval the Stop hook records as one row. In the
    transcript the start of a turn is the "queue-operation" entry with
    operation "enqueue", which contains the typed text -- the same
    source extract_summary() uses in the hooks, so the "summary" field
    comes out identical to what the hook would have written.

    Usage adds up as in sum_transcript_usage(): the "usage" of one API
    call is repeated unchanged on every block of the message (text,
    reasoning, tool_use), so it is deduplicated by message.id,
    otherwise the same call would be counted two or three times.
    """
    grezzi = []
    # message.id -> valori gia' contati (vedi _incremento)
    # [EN] message.id -> values already counted (see _incremento)
    seen_msg_ids = {}
    cur = None

    def nuovo_turno(summary):
        return {
            "summary": summary, "model": "", "ts": "",
            "input": 0, "output": 0, "cache_write": 0, "cache_read": 0,
            "cache_write_1h": 0,
        }

    def chiudi(turno):
        # Si tengono anche i turni ancora a zero: i consumi dei sotto-agenti
        # vengono aggiunti dopo, e potrebbero essere l'unico consumo di quel
        # turno. Lo scarto dei turni davvero vuoti avviene alla fine.
        # [EN] Turns still at zero are kept too: subagent usage is
        # added later, and it might be that turn's only usage. Truly
        # empty turns are discarded at the end.
        if turno is not None:
            grezzi.append(turno)

    for e in iter_entries(path):
        tipo = e.get("type")

        if tipo == "queue-operation" and e.get("operation") == "enqueue" and e.get("content"):
            # Inizio di un nuovo turno: si chiude quello in corso e se ne
            # apre uno con il testo appena digitato come riepilogo.
            # [EN] Start of a new turn: the current one is closed and
            # a new one opens with the just-typed text as its summary.
            chiudi(cur)
            cur = nuovo_turno(_flatten(e["content"], 80))
            continue

        if tipo != "assistant":
            continue

        if cur is None:
            # Risposte prima di qualunque enqueue: succede nelle sessioni
            # riprese (--resume / --continue) e in quelle avviate con il
            # prompt passato da riga di comando. Il turno esiste comunque,
            # semplicemente senza riepilogo.
            # [EN] Responses before any enqueue: happens in resumed
            # sessions (--resume / --continue) and in those started
            # with the prompt passed on the command line. The turn
            # exists anyway, simply without a summary.
            cur = nuovo_turno("")

        message = e.get("message") if isinstance(e.get("message"), dict) else None

        # Timestamp e modello si aggiornano a ogni entry, comprese quelle
        # duplicate scartate poco sotto: alla fine del turno restano quelli
        # dell'ultima risposta, cioe' il momento in cui l'hook Stop avrebbe
        # scritto la riga. "<synthetic>" e' un segnaposto interno di Claude
        # Code, non un modello fatturabile: si scarta come in extract_model().
        # [EN] Timestamp and model are updated on every entry,
        # including the duplicates discarded just below: at the end of
        # the turn what remains is the last response's, i.e. the
        # moment the Stop hook would have written the row.
        # "<synthetic>" is an internal Claude Code placeholder, not a
        # billable model: it is discarded as in extract_model().
        if e.get("timestamp"):
            cur["ts"] = _norm_ts(e["timestamp"])
        modello = message.get("model") if message else None
        if modello and modello != "<synthetic>":
            cur["model"] = modello

        usage = (message or {}).get("usage") or e.get("usage")
        if not usage:
            continue

        msg_id = message.get("id") if message else None
        i, o, cw, cr, cw1 = _incremento(seen_msg_ids, msg_id, usage)
        cur["input"] += i
        cur["output"] += o
        cur["cache_write"] += cw
        cur["cache_read"] += cr
        cur["cache_write_1h"] += cw1

    chiudi(cur)

    # I sotto-agenti hanno un transcript separato (vedi find_subagents): il
    # loro consumo appartiene al turno della sessione madre durante il quale
    # sono stati lanciati, e si assegna quindi confrontando i timestamp.
    # [EN] Subagents have a separate transcript (see find_subagents):
    # their usage belongs to the parent-session turn during which they
    # were launched, so it is assigned by comparing timestamps.
    fine_turni = [t["ts"] for t in grezzi]
    for quando, incr, modello in _consumi_subagenti(path, seen_msg_ids):
        if not grezzi:
            break
        # bisect_left sui timestamp di FINE turno (ISO 8601, ordinabili come
        # testo): il primo turno che finisce dopo l'evento e' quello che lo
        # conteneva. Un evento successivo all'ultimo turno -- puo' capitare
        # se il sotto-agente ha terminato dopo l'ultima risposta -- va
        # sull'ultimo.
        # [EN] bisect_left on the turn END timestamps (ISO 8601,
        # sortable as text): the first turn ending after the event is
        # the one that contained it. An event later than the last turn
        # -- it can happen if the subagent finished after the last
        # response -- goes onto the last one.
        i = bisect.bisect_left(fine_turni, quando)
        t = grezzi[min(i, len(grezzi) - 1)]
        t["input"] += incr[0]
        t["output"] += incr[1]
        t["cache_write"] += incr[2]
        t["cache_read"] += incr[3]
        t["cache_write_1h"] += incr[4]
        if not t["model"] and modello and modello != "<synthetic>":
            t["model"] = modello

    righe = []
    for t in grezzi:
        totale = t["input"] + t["output"] + t["cache_write"] + t["cache_read"]
        if totale <= 0:
            # Turno senza alcun consumo: rumore (es. un messaggio accodato e
            # poi annullato). Non produce riga.
            # [EN] Turn with no usage at all: noise (e.g. a message
            # queued and then cancelled). Produces no row.
            continue
        righe.append({
            "timestamp": t["ts"],
            "session_id": session_id,
            "input_tokens": t["input"],
            "output_tokens": t["output"],
            "cache_write_tokens": t["cache_write"],
            "cache_write_1h_tokens": t["cache_write_1h"],
            "cache_read_tokens": t["cache_read"],
            "total_tokens": totale,
            "account": decidi_account(t["ts"]),
            "summary": t["summary"],
            "model": t["model"] or "sconosciuto",
            "origine": ORIGINE_BACKFILL,
        })
    return righe


def _consumi_subagenti(main_path, seen_msg_ids):
    """Consumi dei sotto-agenti di una sessione, in ordine di tempo.

    Restituisce terne (timestamp normalizzato, incrementi, modello). Gli
    incrementi passano dallo stesso archivio "visti" del transcript
    principale, cosi' un messaggio presente in entrambi non viene contato
    due volte.

    [EN] Usage of a session's subagents, in time order.

    Returns triples (normalized timestamp, increments, model). The
    increments go through the same "seen" archive as the main
    transcript, so a message present in both is not counted twice.
    """
    eventi = []
    for percorso in find_subagents(main_path):
        for e in iter_entries(percorso):
            if e.get("type") != "assistant":
                continue
            message = e.get("message") if isinstance(e.get("message"), dict) else None
            usage = (message or {}).get("usage") or e.get("usage")
            if not usage:
                continue
            msg_id = message.get("id") if message else None
            incr = _incremento(seen_msg_ids, msg_id, usage)
            if not any(incr):
                # duplicato esatto: nulla di nuovo da contare
                # [EN] exact duplicate: nothing new to count
                continue
            eventi.append((_norm_ts(e.get("timestamp")),
                           incr,
                           (message or {}).get("model")))
    eventi.sort(key=lambda x: x[0])
    return eventi


# ----------------------------------------------- ricostruzione operazioni --
# [EN] --------------------------------------------- operations rebuilding --

def rebuild_ops(path, session_id):
    """Ricostruisce le righe di operations.csv per una sessione, una per
    chiamata a tool.

    DIFFERENZA VOLUTA RISPETTO ALL'HOOK: attribute_action_cost() gira DURANTE
    la sessione e sa solo che "e' appena stato usato il tool X", quindi per
    non sbagliare attribuzione considera solo i messaggi con un unico blocco
    e per tutti gli altri dichiara "n/d" con costo 0. Qui invece leggiamo il
    transcript a cose fatte: sappiamo esattamente quali tool_use stavano in
    quale messaggio, quindi si attribuisce anche il costo dei tool lanciati
    in parallelo, dividendo lo "usage" del messaggio per il numero di
    tool_use che lo compongono: le righe ricostruite coprono percio' anche i
    tool lanciati in parallelo.

    [EN] Rebuilds the operations.csv rows for a session, one per tool
    call.

    DELIBERATE DIFFERENCE FROM THE HOOK: attribute_action_cost() runs
    DURING the session and only knows that "tool X has just been
    used", so to avoid misattribution it only considers single-block
    messages and for all the others declares "n/d" with cost 0. Here
    instead we read the transcript after the fact: we know exactly
    which tool_use blocks sat in which message, so the cost of tools
    launched in parallel is attributed too, splitting the message's
    "usage" by the number of tool_use blocks composing it: the rebuilt
    rows therefore cover tools launched in parallel too.
    """
    # Ogni blocco di un messaggio finisce su una riga propria del transcript,
    # ripetendo message.id e usage: prima si raccoglie tutto deduplicando per
    # (message.id, id del blocco), poi si conta quanti tool_use aveva ciascun
    # messaggio, e solo alla fine si dividono i costi.
    # [EN] Each block of a message lands on its own transcript line,
    # repeating message.id and usage: first everything is collected
    # deduplicating by (message.id, block id), then the tool_use count
    # of each message is tallied, and only at the end are the costs
    # split.
    records = []
    visti = set()
    per_messaggio = {}

    # Anche le azioni compiute DENTRO un sotto-agente vanno registrate: sono
    # lavoro vero, e senza di esse la tabella delle operazioni non spiega
    # dove sono finiti i token del turno.
    # [EN] Actions performed INSIDE a subagent must be recorded too:
    # they are real work, and without them the operations table does
    # not explain where the turn's tokens went.
    def _tutte_le_entry():
        for e in iter_entries(path):
            yield e
        for percorso in find_subagents(path):
            for e in iter_entries(percorso):
                yield e

    for e in _tutte_le_entry():
        if e.get("type") != "assistant":
            continue
        message = e.get("message") if isinstance(e.get("message"), dict) else None
        if not message:
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            msg_id = message.get("id") or ""
            chiave = (msg_id, block.get("id") or "")
            if chiave in visti:
                continue
            visti.add(chiave)
            per_messaggio[msg_id] = per_messaggio.get(msg_id, 0) + 1
            tool_input = block.get("input")
            if not isinstance(tool_input, dict):
                tool_input = {}
            records.append({
                "msg_id": msg_id,
                "timestamp": _norm_ts(e.get("timestamp"), millis=True),
                "tool": block.get("name") or "?",
                # Stessa scelta di extract_target(): il "su cosa" di un tool
                # sta in file_path (Read/Edit/Write) o in command (Bash).
                # [EN] Same choice as extract_target(): a tool's "on
                # what" lives in file_path (Read/Edit/Write) or in
                # command (Bash).
                "target": _flatten(
                    tool_input.get("file_path") or tool_input.get("command") or "", 200
                ),
                "usage": message.get("usage") or {},
                "model": message.get("model") or "sconosciuto",
            })

    righe = []
    for r in records:
        # max(1, ...) e' la solita difesa contro una divisione per zero.
        # [EN] max(1, ...) is the usual guard against division by
        # zero.
        n = max(1, per_messaggio.get(r["msg_id"], 1))
        u = r["usage"]
        righe.append({
            "timestamp": r["timestamp"],
            "session_id": session_id,
            "tool": r["tool"],
            "target": r["target"],
            "input_tokens": round((u.get("input_tokens", 0) or 0) / n),
            "output_tokens": round((u.get("output_tokens", 0) or 0) / n),
            "cache_write_tokens": round((u.get("cache_creation_input_tokens", 0) or 0) / n),
            "cache_read_tokens": round((u.get("cache_read_input_tokens", 0) or 0) / n),
            "model": r["model"],
        })
    return righe


# ------------------------------------------------------------ lettura CSV --
# [EN] -------------------------------------------------------- CSV reading --

def _read_csv(path, header):
    """Legge un CSV esistente come lista di dizionari, tollerando l'assenza
    del file (prima installazione) e le colonne mancanti (log scritti da una
    versione precedente, prima che quella colonna esistesse).

    [EN] Reads an existing CSV as a list of dictionaries, tolerating a
    missing file (first installation) and missing columns (logs
    written by a previous version, before that column existed)."""
    righe = []
    if not os.path.exists(path):
        return righe
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            righe.append({k: (r.get(k) or "") for k in header})
    return righe


def _write_csv(path, header, righe):
    """Riscrive un CSV per intero, in modo atomico.

    Si scrive prima un file temporaneo e poi lo si sposta al posto
    dell'originale con os.replace(), che il sistema operativo garantisce
    indivisibile: un'interruzione a meta' (crash, PC spento) lascia il CSV
    vecchio intatto invece di uno nuovo troncato. E' lo stesso accorgimento
    usato da setup_hooks per settings.json.

    [EN] Rewrites a CSV in full, atomically.

    A temporary file is written first and then moved over the original
    with os.replace(), which the operating system guarantees to be
    indivisible: an interruption halfway (crash, PC switched off)
    leaves the old CSV intact instead of a new truncated one. It is
    the same precaution setup_hooks uses for settings.json.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in righe:
            w.writerow(r)
    os.replace(tmp, path)


def _backup(path):
    """Copia di sicurezza datata prima di riscrivere un CSV.

    A differenza del backup di settings.json (che ne tiene uno solo) qui si
    conserva uno storico: i CSV sono l'unico archivio dei consumi, e un
    backfill andato storto dev'essere annullabile anche a distanza di giorni.

    [EN] Dated safety copy before rewriting a CSV.

    Unlike the settings.json backup (which keeps only one) here a
    history is preserved: the CSVs are the only archive of the usage,
    and a backfill gone wrong must be reversible even days later.
    """
    if not os.path.exists(path):
        return None
    dest = "{}.bak-{}".format(path, datetime.now().strftime("%Y%m%d-%H%M%S"))
    try:
        shutil.copy2(path, dest)
        return dest
    except OSError:
        return None


def _osservazioni_account(righe_esistenti):
    """Archivio {session_id: [account, istante]} delle osservazioni dirette.

    Un'osservazione e' una riga scritta dall'hook: dice quale account era
    attivo in quel preciso momento. Il backfill pero' RISCRIVE le righe delle
    sessioni che ricostruisce, quindi al rilancio successivo quelle righe --
    e con esse la prova -- non ci sarebbero piu', e la stessa sessione
    verrebbe attribuita in modo diverso: il risultato non sarebbe idempotente.
    Per questo le osservazioni vengono accumulate in un file a parte, che
    cresce e non perde mai nulla.

    Di ogni sessione si tiene l'osservazione PIU' ANTICA: e' quella che
    delimita fin dove indietro l'account puo' valere.

    [EN] Archive {session_id: [account, instant]} of the direct
    observations.

    An observation is a row written by the hook: it says which account
    was active at that precise moment. The backfill however REWRITES
    the rows of the sessions it rebuilds, so on the next run those
    rows -- and with them the evidence -- would be gone, and the same
    session would be attributed differently: the result would not be
    idempotent. For this reason the observations are accumulated in a
    separate file, which grows and never loses anything.

    For each session the OLDEST observation is kept: it is the one
    marking how far back the account can apply.
    """
    try:
        with open(config.OSSERVAZIONI_FILE, encoding="utf-8") as f:
            archivio = json.load(f)
        if not isinstance(archivio, dict):
            archivio = {}
    except (OSError, json.JSONDecodeError):
        archivio = {}

    for r in righe_esistenti:
        # Le righe senza colonna "origine" vengono da una versione precedente
        # degli hook, quando il backfill non esisteva ancora: sono per
        # definizione osservazioni dirette.
        # [EN] Rows without the "origine" column come from a previous
        # version of the hooks, when the backfill did not exist yet:
        # they are by definition direct observations.
        if (r.get("origine") or ORIGINE_HOOK) != ORIGINE_HOOK:
            continue
        acc = (r.get("account") or "").strip()
        if not acc or acc in NON_SONO_ACCOUNT:
            continue
        quando = _epoch(r.get("timestamp"))
        sid = r.get("session_id")
        if quando is None or not sid:
            continue
        prec = archivio.get(sid)
        if not isinstance(prec, list) or len(prec) != 2 or quando < prec[1]:
            archivio[sid] = [acc, quando]

    try:
        os.makedirs(os.path.dirname(config.OSSERVAZIONI_FILE), exist_ok=True)
        with open(config.OSSERVAZIONI_FILE, "w", encoding="utf-8") as f:
            json.dump(archivio, f, ensure_ascii=False)
    except OSError:
        # perderemmo solo un ripiego: non vale un'installazione fallita
        # [EN] we would only lose a fallback: not worth a failed
        # installation
        pass
    return archivio


def _account_osservato(righe_sessione):
    """Account OSSERVATO dagli hook per una sessione, con l'istante della
    prima osservazione.

    Restituisce (account, istante) oppure (None, None). Contano solo le righe
    con origine "hook": quelle ricostruite da un backfill precedente hanno
    l'account che avevamo dedotto noi, e riusarlo come prova sarebbe
    circolare. I valori in NON_SONO_ACCOUNT sono ripieghi, non account:
    trovarli equivale a non sapere nulla.

    L'istante serve perche' l'osservazione vale da quel momento in avanti e
    NON all'indietro: la stessa sessione, ripresa dopo settimane, puo' avere
    turni precedenti fatti con un altro account.

    [EN] Account OBSERVED by the hooks for a session, with the instant
    of the first observation.

    Returns (account, instant) or (None, None). Only rows with origin
    "hook" count: those rebuilt by a previous backfill carry the
    account we ourselves deduced, and reusing it as evidence would be
    circular. The values in NON_SONO_ACCOUNT are fallbacks, not
    accounts: finding them equals knowing nothing.

    The instant matters because the observation applies from that
    moment onwards and NOT backwards: the same session, resumed weeks
    later, may have earlier turns made with another account.
    """
    migliore = None
    for r in righe_sessione:
        if (r.get("origine") or ORIGINE_HOOK) != ORIGINE_HOOK:
            continue
        acc = (r.get("account") or "").strip()
        if not acc or acc in NON_SONO_ACCOUNT:
            continue
        quando = _epoch(r.get("timestamp"))
        if quando is None:
            continue
        if migliore is None or quando < migliore[1]:
            migliore = (acc, quando)
    return migliore if migliore else (None, None)


def _raggruppa(righe):
    """Raggruppa righe CSV per session_id, preservandone l'ordine.

    [EN] Groups CSV rows by session_id, preserving their order."""
    gruppi = {}
    for r in righe:
        gruppi.setdefault(r.get("session_id") or "", []).append(r)
    return gruppi


# -------------------------------------------------------- orchestrazione --
# [EN] ----------------------------------------------------- orchestration --

def backfill(progress=None, dry_run=False):
    """Ricostruisce i due CSV dai transcript e restituisce un riepilogo.

    progress: funzione opzionale chiamata come progress(fatte, totale, nome)
              dopo ogni sessione elaborata, per disegnare una barra di
              avanzamento. Se None non si stampa nulla (comodo nei test).
    dry_run:  calcola tutto ma non tocca il disco. Serve a rispondere alla
              domanda "quanto cambierebbe?" senza rischiare niente.

    [EN] Rebuilds the two CSVs from the transcripts and returns a
    summary.

    progress: optional function called as progress(done, total, name)
              after each processed session, to draw a progress bar.
              If None nothing is printed (handy in tests).
    dry_run:  computes everything but does not touch the disk. It
              answers the question "how much would change?" without
              risking anything.
    """
    transcripts = find_transcripts()
    tokens_esistenti = _read_csv(config.TOKENS_CSV, TOKENS_HEADER)
    ops_esistenti = _read_csv(config.OPS_CSV, OPS_HEADER)
    tokens_per_sessione = _raggruppa(tokens_esistenti)
    ops_per_sessione = _raggruppa(ops_esistenti)

    etichette = _etichette_account()
    timeline = timeline_account()
    osservazioni = _osservazioni_account(tokens_esistenti)

    nuovi_tokens = []
    nuove_ops = []
    stats = {
        "transcript": len(transcripts),
        # mai viste dagli hook
        # [EN] never seen by the hooks
        "sessioni_nuove": 0,
        # gia' presenti, cronologia ricostruita
        # [EN] already present, history rebuilt
        "sessioni_riscritte": 0,
        # Da dove viene l'account, TURNO per turno (non per sessione):
        # [EN] Where the account comes from, TURN by turn (not per
        # session):
        "eventi_timeline": len(timeline),
        # dai log degli accessi dell'app
        # [EN] from the app's login logs
        "account_da_timeline": 0,
        # osservato dall'hook su quella sessione
        # [EN] observed by the hook on that session
        "account_da_hook": 0,
        # dichiarato dal transcript stesso
        # [EN] declared by the transcript itself
        "account_dal_transcript": 0,
        # nessuna traccia: si usa il ripiego
        # [EN] no trace at all: the fallback is used
        "account_ignoto": 0,
        "turni": 0,
        "operazioni": 0,
        "tokens_prima": len(tokens_esistenti),
        "ops_prima": len(ops_esistenti),
        "backup": [],
    }

    # Le righe delle sessioni SENZA transcript vanno conservate cosi' come
    # sono: non abbiamo modo di ricostruirle, cancellarle sarebbe una perdita
    # di dati.
    # [EN] Rows of sessions WITHOUT a transcript must be preserved as
    # they are: we have no way to rebuild them, deleting them would be
    # a loss of data.
    conservate_tokens = [
        r for r in tokens_esistenti if (r.get("session_id") or "") not in transcripts
    ]

    totale = len(transcripts)
    for i, (sid, path) in enumerate(sorted(transcripts.items()), start=1):
        precedenti = tokens_per_sessione.get(sid, [])
        if precedenti:
            stats["sessioni_riscritte"] += 1
        else:
            stats["sessioni_nuove"] += 1

        # L'account si decide TURNO PER TURNO (vedi docstring del modulo):
        # una sessione ripresa a distanza di settimane puo' attraversare piu'
        # account, e stamparne uno solo su tutti i suoi turni sbaglia in
        # silenzio. La chiusura qui sotto viene richiamata da rebuild_turns
        # con il timestamp di ciascun turno.
        # [EN] The account is decided TURN BY TURN (see the module
        # docstring): a session resumed weeks later can span several
        # accounts, and stamping a single one onto all its turns errs
        # silently. The closure below is called back by rebuild_turns
        # with each turn's timestamp.
        osservato, osservato_da = _account_osservato(precedenti)
        if not osservato:
            # Nessuna riga dell'hook per questa sessione nel CSV attuale: puo'
            # essere stata riscritta da un backfill precedente, e in quel caso
            # la prova sopravvive nell'archivio.
            # [EN] No hook row for this session in the current CSV: it
            # may have been rewritten by a previous backfill, in which
            # case the evidence survives in the archive.
            prec = osservazioni.get(sid)
            if isinstance(prec, list) and len(prec) == 2:
                osservato, osservato_da = prec[0], prec[1]
        uuid_transcript = None if osservato else account_dal_transcript(path)
        dal_transcript = etichette.get(uuid_transcript, uuid_transcript) if uuid_transcript else None

        def decidi_account(ts_turno, _oss=osservato, _da=osservato_da, _tr=dal_transcript):
            istante = _epoch(ts_turno)
            uuid = _cerca_nella_timeline(timeline, istante)
            if uuid:
                stats["account_da_timeline"] += 1
                return etichette.get(uuid, uuid)
            # L'osservazione dell'hook vale dal turno osservato in poi,
            # mai prima.
            # [EN] The hook observation applies from the observed turn
            # onwards, never before.
            if (_oss and istante is not None and _da is not None
                    and istante >= _da - MARGINE_OSSERVAZIONE):
                stats["account_da_hook"] += 1
                return _oss
            if _tr:
                stats["account_dal_transcript"] += 1
                return _tr
            stats["account_ignoto"] += 1
            return ACCOUNT_NON_RILEVATO

        turni = rebuild_turns(path, sid, decidi_account)
        nuovi_tokens.extend(turni)
        stats["turni"] += len(turni)

        # operations.csv: qui NON si riscrive nulla di esistente. Le righe
        # registrate dal vivo hanno il timestamp del momento in cui l'hook e'
        # scattato, quelle ricostruite quello scritto nel transcript: sono
        # vicini ma mai identici, quindi non c'e' modo di riconoscere un
        # doppione confrontandoli. Si aggiungono percio' solo le operazioni
        # ANTERIORI alla prima gia' registrata per quella sessione -- che
        # sono esattamente quelle avvenute prima dell'installazione.
        # [EN] operations.csv: nothing existing is rewritten here.
        # Rows recorded live carry the timestamp of the moment the
        # hook fired, rebuilt ones the timestamp written in the
        # transcript: close but never identical, so there is no way to
        # recognize a duplicate by comparing them. Therefore only the
        # operations EARLIER than the first one already recorded for
        # that session are added -- which are exactly those that
        # happened before the installation.
        ops_precedenti = ops_per_sessione.get(sid, [])
        limite = min((r.get("timestamp") or "" for r in ops_precedenti), default=None)
        for riga in rebuild_ops(path, sid):
            if limite is None or (riga["timestamp"] and riga["timestamp"] < limite):
                nuove_ops.append(riga)
                stats["operazioni"] += 1

        if progress:
            progress(i, totale, sid)

    # I timestamp sono in formato ISO 8601, che ha la comoda proprieta' di
    # ordinarsi correttamente anche solo come testo (le cifre piu'
    # significative stanno a sinistra): non serve convertirli in date.
    # [EN] Timestamps are in ISO 8601 format, which has the handy
    # property of sorting correctly even as plain text (the most
    # significant digits sit on the left): no need to convert them
    # into dates.
    tokens_finali = sorted(
        conservate_tokens + nuovi_tokens, key=lambda r: r.get("timestamp") or ""
    )
    ops_finali = sorted(
        ops_esistenti + nuove_ops, key=lambda r: r.get("timestamp") or ""
    )
    stats["tokens_dopo"] = len(tokens_finali)
    stats["ops_dopo"] = len(ops_finali)

    if not dry_run:
        for percorso in (config.TOKENS_CSV, config.OPS_CSV):
            fatto = _backup(percorso)
            if fatto:
                stats["backup"].append(fatto)
        _write_csv(config.TOKENS_CSV, TOKENS_HEADER, tokens_finali)
        _write_csv(config.OPS_CSV, OPS_HEADER, ops_finali)

    return stats


# ----------------------------------------------------- barra di avanzamento --
# [EN] ------------------------------------------------------- progress bar --

class ConsoleProgress(object):
    """Barra di avanzamento testuale per la console dell'installer.

    Su un terminale vero si riscrive sempre la stessa riga usando "\\r"
    (ritorno a capo SENZA andare a capo: riporta il cursore a inizio riga,
    cosi' la scritta successiva copre la precedente). Quando invece l'output
    e' rediretto su file o su un log -- dove "\\r" produrrebbe una riga sola
    illeggibile -- si stampano normali righe di avanzamento ogni 10%.

    [EN] Text progress bar for the installer console.

    On a real terminal the same line is rewritten over and over using
    "\\r" (carriage return WITHOUT a newline: it brings the cursor
    back to the start of the line, so the next write covers the
    previous one). When the output is instead redirected to a file or
    a log -- where "\\r" would produce one unreadable single line --
    normal progress lines are printed every 10%.
    """

    LARGHEZZA = 28

    def __init__(self, stream=None, etichetta="sessioni"):
        self.stream = stream or sys.stdout
        self.etichetta = etichetta
        self.interattivo = bool(getattr(self.stream, "isatty", lambda: False)())
        self._ultima_decina = -1

    def __call__(self, fatte, totale, _nome=None):
        totale = max(1, totale)
        frazione = fatte / totale
        percento = int(frazione * 100)

        if self.interattivo:
            pieni = int(frazione * self.LARGHEZZA)
            barra = "#" * pieni + "-" * (self.LARGHEZZA - pieni)
            testo = "\r  [{}] {:3d}%  {}/{} {}".format(
                barra, percento, fatte, totale, self.etichetta
            )
        else:
            decina = percento // 10
            if decina == self._ultima_decina and fatte < totale:
                return
            self._ultima_decina = decina
            testo = "  {:3d}%  {}/{} {}\n".format(percento, fatte, totale, self.etichetta)

        try:
            self.stream.write(testo)
            self.stream.flush()
        except (OSError, ValueError):
            # Console chiusa o stream non scrivibile: l'avanzamento e' un
            # extra, non deve poter far fallire il backfill.
            # [EN] Console closed or stream not writable: progress is
            # an extra, it must never be able to make the backfill
            # fail.
            self.interattivo = False

    def chiudi(self):
        """Va a capo dopo l'ultima riscrittura della barra, cosi' il
        messaggio successivo non le finisce sopra.

        [EN] Moves to a new line after the bar's last rewrite, so the
        next message does not land on top of it."""
        if self.interattivo:
            try:
                self.stream.write("\n")
                self.stream.flush()
            except (OSError, ValueError):
                pass


def run(dry_run=False, log=None, rigenera=True):
    """Esecuzione completa con messaggi a schermo: e' quello che invoca il
    sottocomando "dashboard-token backfill" e, tramite esso, l'installer.

    Restituisce 0 se e' andata bene, 1 altrimenti -- la convenzione dei
    codici di uscita dei programmi da riga di comando.

    [EN] Full run with on-screen messages: this is what the
    "dashboard-token backfill" subcommand invokes and, through it, the
    installer.

    Returns 0 on success, 1 otherwise -- the exit-code convention of
    command-line programs.
    """
    say = log or (lambda m: print(m))

    say("Recupero delle sessioni precedenti all'installazione...")
    barra = ConsoleProgress()
    try:
        stats = backfill(progress=barra, dry_run=dry_run)
    except Exception as exc:  # noqa: BLE001 -- vedi commento
        # Volutamente larga: il backfill e' un extra in coda a
        # un'installazione gia' riuscita. Qualunque sorpresa dentro un
        # transcript malformato deve produrre un avviso, non
        # un'installazione fallita.
        # [EN] Deliberately broad: the backfill is an extra at the
        # tail of an already-successful installation. Any surprise
        # inside a malformed transcript must produce a warning, not a
        # failed installation.
        barra.chiudi()
        say("  Recupero non riuscito: {}".format(exc))
        say("  L'installazione resta valida: verranno registrate le sessioni da qui in avanti.")
        return 1
    barra.chiudi()

    if stats["transcript"] == 0:
        say("  Nessuna sessione precedente trovata: si parte da zero.")
        return 0

    say("  {} sessioni esaminate: {} recuperate, {} con la cronologia ricostruita.".format(
        stats["transcript"], stats["sessioni_nuove"], stats["sessioni_riscritte"]))
    say("  {} turni e {} operazioni aggiunti allo storico.".format(
        stats["turni"], stats["operazioni"]))
    if stats["eventi_timeline"]:
        say("  Registro accessi dell'app: {} cambi di account ricostruiti.".format(
            stats["eventi_timeline"]))
    else:
        say("  Registro accessi dell'app non disponibile: l'account verra'")
        say("  attribuito solo dove lo dicono gli hook o i transcript.")
    say("  Account per turno: {} dal registro accessi, {} dagli hook, {} dai"
        " transcript, {} senza traccia (\"{}\").".format(
            stats["account_da_timeline"], stats["account_da_hook"],
            stats["account_dal_transcript"], stats["account_ignoto"],
            ACCOUNT_NON_RILEVATO))
    say("  Righe in tokens.csv: {} -> {}.".format(stats["tokens_prima"], stats["tokens_dopo"]))

    if dry_run:
        say("  (prova a vuoto: nessun file e' stato modificato)")
        return 0

    for percorso in stats["backup"]:
        say("  Copia di sicurezza: {}".format(percorso))

    if rigenera:
        try:
            # "from .main import main", NON "from . import main": __init__.py
            # riespone la funzione main() con il nome del package, quindi
            # "from . import main" restituirebbe la FUNZIONE e non il modulo
            # main.py che la contiene.
            # [EN] "from .main import main", NOT "from . import main":
            # __init__.py re-exports the main() function under the
            # package name, so "from . import main" would return the
            # FUNCTION and not the main.py module containing it.
            from .main import main as genera
            genera()
            say("  Dashboard rigenerata.")
        except Exception as exc:  # noqa: BLE001
            # Stessa logica di regenerate_dashboard() in log_tokens.py: i dati
            # sono gia' salvati, le pagine si rifaranno al primo turno utile.
            # [EN] Same logic as regenerate_dashboard() in
            # log_tokens.py: the data is already saved, the pages will
            # be rebuilt at the first useful turn.
            say("  Dati salvati, ma la dashboard non si e' rigenerata ora: {}".format(exc))
    return 0
