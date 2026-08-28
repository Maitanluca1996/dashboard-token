"""Percorsi dei file di input/output e configurazione locale opzionale.

NOTA PER CHI NON CONOSCE PYTHON:
Questo file non ha funzioni: e' un elenco di "variabili globali" (costanti)
che tutti gli altri moduli del package leggono per sapere DOVE si trovano
i file su disco (i log da leggere, le pagine HTML da scrivere). Vengono
calcolate una sola volta, quando il modulo viene importato la prima volta,
e poi riusate ovunque tramite "from . import config" + "config.NOME_VARIABILE".

Per convenzione in Python, le variabili scritte TUTTE_MAIUSCOLE segnalano
"questa e' una costante, non cambiarla mentre il programma gira" (non e'
una regola imposta dal linguaggio, solo una convenzione che tutti seguono).

[EN] Input/output file paths and optional local configuration.

NOTE FOR READERS NEW TO PYTHON:
This file has no functions: it is a list of "global variables"
(constants) that every other module in the package reads to know WHERE
the files live on disk (the logs to read, the HTML pages to write).
They are computed once, when the module is imported for the first
time, and then reused everywhere via "from . import config" +
"config.VARIABLE_NAME".

By Python convention, variables written in ALL_CAPS signal "this is a
constant, do not change it while the program runs" (not a rule
enforced by the language, just a convention everyone follows).
"""
import glob
import json
import os

# os.path.expanduser("~") restituisce la home directory dell'utente corrente
# (es. "C:\Users\MarioRossi" su Windows, "/home/mariorossi" su Linux/macOS).
# E' l'equivalente Python del simbolo "~" che usi nel terminale.
# [EN] os.path.expanduser("~") returns the current user's home
# directory (e.g. "C:\Users\MarioRossi" on Windows, "/home/mariorossi"
# on Linux/macOS). It is the Python equivalent of the "~" symbol you
# use in the terminal.
HOME = os.path.expanduser("~")

# os.path.join incolla pezzi di percorso con il separatore giusto per il
# sistema operativo corrente ("\" su Windows, "/" su macOS/Linux) -- per
# questo non si scrivono mai percorsi con "/" o "\" a mano nel codice.
# [EN] os.path.join glues path pieces together with the right separator
# for the current operating system ("\" on Windows, "/" on macOS/Linux)
# -- this is why paths are never written by hand with "/" or "\" in
# the code.
LOG_DIR = os.path.join(HOME, ".claude", "logs")
TOKENS_CSV = os.path.join(LOG_DIR, "tokens.csv")
OPS_CSV = os.path.join(LOG_DIR, "operations.csv")
CACHE_FILE = os.path.join(LOG_DIR, "session_titles_cache.json")
PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")

# Mappa UUID -> etichetta leggibile degli account, la stessa che consulta
# resolve_account() in log_tokens.py. E' opzionale e locale alla macchina
# (la scrive "dashboard-token config"), quindi non fa parte del pacchetto
# distribuito: serve solo a backfill.py per tradurre in nome leggibile l'UUID
# che riesce a ricavare dai transcript.
# [EN] Map UUID -> readable account label, the same one consulted by
# resolve_account() in log_tokens.py. It is optional and local to the
# machine (written by "dashboard-token config"), so it is not part of
# the distributed package: it only lets backfill.py turn the UUID it
# manages to extract from the transcripts into a readable name.
LABELS_FILE = os.path.join(HOME, ".claude", "hooks", "account_labels.json")

# Archivio delle osservazioni dirette dell'account, una per sessione.
# Esiste perche' il backfill RISCRIVE le righe delle sessioni che ricostruisce,
# cancellando cosi' le righe "origine=hook" da cui aveva ricavato l'account:
# senza questo archivio la prova sparirebbe al primo rilancio, e il risultato
# non sarebbe piu' idempotente. Vedi backfill._osservazioni_account.
# [EN] Archive of the direct account observations, one per session. It
# exists because the backfill REWRITES the rows of the sessions it
# rebuilds, thereby deleting the "origine=hook" rows from which it had
# derived the account: without this archive the evidence would vanish
# at the first re-run, and the result would no longer be idempotent.
# See backfill._osservazioni_account.
OSSERVAZIONI_FILE = os.path.join(LOG_DIR, "account_osservazioni.json")


# Cartella di output: di default ~/.claude/dashboard-token (funziona su
# qualunque macchina senza configurazione). Per usare una cartella diversa
# (es. un repo specifico), creare
# ~/.claude/hooks/dashboard_config.json con {"out_dir": "C:\\percorso\\a\\piacere"}
# -- questo file e' locale alla macchina e non va distribuito col progetto.
# [EN] Output folder: by default ~/.claude/dashboard-token (works on
# any machine with no configuration). To use a different folder (e.g. a
# specific repo), create
# ~/.claude/hooks/dashboard_config.json with
# {"out_dir": "C:\\any\\path\\you\\like"} -- this file is local to the
# machine and must not be shipped with the project.
_CONFIG_PATH = os.path.join(HOME, ".claude", "hooks", "dashboard_config.json")

# Proviamo a leggere dashboard_config.json, ma il file e' OPZIONALE: se non
# esiste (o e' scritto male) va tutto bene comunque, si usa il default sotto.
#
# "try / except" e' il modo Python di dire "prova a fare questa cosa; se va
# storta con uno di questi errori specifici, non bloccare il programma, fai
# invece quello che c'e' scritto nell'except". Qui intercettiamo due errori
# possibili:
#   - OSError: il file non esiste, o non si riesce ad aprirlo (permessi...)
#   - json.JSONDecodeError: il file esiste ma il testo dentro non e' JSON
#     valido (es. e' vuoto, o e' stato modificato a mano e c'e' un errore
#     di sintassi)
# In entrambi i casi il risultato e' semplicemente "nessuna configurazione",
# rappresentato da un dizionario vuoto {}.
# [EN] We try to read dashboard_config.json, but the file is OPTIONAL:
# if it does not exist (or is malformed) everything is still fine, the
# default below gets used.
#
# "try / except" is the Python way of saying "try to do this; if it
# goes wrong with one of these specific errors, do not stop the
# program, do what the except block says instead". Here we catch two
# possible errors:
#   - OSError: the file does not exist, or cannot be opened
#     (permissions...)
#   - json.JSONDecodeError: the file exists but its text is not valid
#     JSON (e.g. it is empty, or was edited by hand and has a syntax
#     error)
# In both cases the outcome is simply "no configuration", represented
# by an empty dictionary {}.
try:
    with open(_CONFIG_PATH, encoding="utf-8") as _f:
        # "with open(...) as _f:" apre il file, ce lo da' con il nome _f, ed
        # e' garantito che il file venga richiuso automaticamente alla fine
        # del blocco indentato sotto -- anche se dentro succede un errore.
        # E' l'equivalente sicuro di "apri, leggi, chiudi" fatto a mano.
        # [EN] "with open(...) as _f:" opens the file, hands it to us
        # under the name _f, and guarantees the file is closed
        # automatically at the end of the indented block below -- even
        # if an error happens inside. It is the safe equivalent of
        # "open, read, close" done by hand.
        # legge il testo JSON e lo trasforma in un dict Python
        # [EN] reads the JSON text and turns it into a Python dict
        _CONFIG = json.load(_f)
except (OSError, json.JSONDecodeError):
    _CONFIG = {}

# dict.get("chiave") restituisce il valore se la chiave esiste, altrimenti
# None (mai un errore). "A or B" in Python restituisce A se A e' "vero"
# (non None, non vuoto, non zero...), altrimenti restituisce B: qui serve
# per dire "usa out_dir dalla config se c'e' e non e' vuoto, altrimenti usa
# il percorso di default".
# [EN] dict.get("key") returns the value if the key exists, otherwise
# None (never an error). "A or B" in Python returns A if A is "truthy"
# (not None, not empty, not zero...), otherwise it returns B: here it
# means "use out_dir from the config if present and non-empty,
# otherwise use the default path".
OUT_DIR = _CONFIG.get("out_dir") or os.path.join(HOME, ".claude", "dashboard-token")
OUT_HTML = os.path.join(OUT_DIR, "dashboard.html")
OUT_PRICING_HTML = os.path.join(OUT_DIR, "pricing.html")
OUT_GUIDE_HTML = os.path.join(OUT_DIR, "guida-costi.html")

# File JS separati, caricati dalle pagine con <script src="...">: tenendo
# fuori dai 3 file .html sia i dati di sessione (grosso payload che cambia
# ad ogni turno) sia l'orario di generazione (cambia ad ogni rigenerazione,
# anche senza nuovi dati), i diff su dashboard.html/pricing.html/
# guida-costi.html restano puliti e mostrano solo le vere modifiche di
# struttura/logica, mai il "rumore" di dati e orario che cambiano da soli.
# [EN] Separate JS files, loaded by the pages via <script src="...">:
# keeping both the session data (a large payload that changes every
# turn) and the generation time (which changes on every regeneration,
# even with no new data) out of the 3 .html files means the diffs on
# dashboard.html/pricing.html/guida-costi.html stay clean and show
# only real structure/logic changes, never the "noise" of data and
# time changing on their own.
OUT_DATA_JS = os.path.join(OUT_DIR, "dashboard-data.js")
OUT_META_JS = os.path.join(OUT_DIR, "site-meta.js")


def _cartelle_log_app():
    """Dove l'applicazione Claude scrive i propri log (main*.log).

    Sono la fonte piu' preziosa per backfill.py: registrano ESPLICITAMENTE
    ogni cambio di account con data e ora ("[account] Login-state
    transition ... uuid: X -> Y"), e risalgono molto piu' indietro dei log
    di questo progetto. Le cartelle cambiano per sistema operativo, quindi
    si provano tutte e si tengono quelle che esistono davvero.

    [EN] Where the Claude application writes its own logs (main*.log).

    They are the most valuable source for backfill.py: they EXPLICITLY
    record every account change with date and time ("[account]
    Login-state transition ... uuid: X -> Y"), and they reach much
    further back than this project's logs. The folders differ per
    operating system, so all of them are tried and only those that
    actually exist are kept.
    """
    candidate = []
    # Override manuale, da dashboard_config.json: {"app_log_dir": "..."}.
    # Serve per le installazioni fuori standard e, soprattutto, quando
    # Python gira dentro un container MSIX (installato dal Microsoft Store /
    # Python Install Manager): li' %APPDATA%\\Claude e' VIRTUALIZZATO e la
    # cartella risulta semplicemente inesistente, anche se c'e'. E' lo
    # stesso inciampo documentato in log_tokens.account_uuid_candidates().
    # L'applicazione impacchettata non ne soffre (e' un normale processo
    # Windows), ma chi lancia i sorgenti a mano si'.
    # [EN] Manual override, from dashboard_config.json:
    # {"app_log_dir": "..."}. It serves non-standard installations and,
    # above all, the case where Python runs inside an MSIX container
    # (installed from the Microsoft Store / Python Install Manager):
    # there %APPDATA%\\Claude is VIRTUALIZED and the folder simply
    # appears not to exist, even though it is there. It is the same
    # pitfall documented in log_tokens.account_uuid_candidates(). The
    # packaged application does not suffer from it (it is a regular
    # Windows process), but whoever runs the sources by hand does.
    manuale = _CONFIG.get("app_log_dir")
    if manuale:
        candidate.append(manuale)
    appdata = os.environ.get("APPDATA")
    if appdata:
        # Windows
        candidate.append(os.path.join(appdata, "Claude", "logs"))
    # macOS
    candidate.append(os.path.join(HOME, "Library", "Application Support", "Claude", "logs"))
    # Linux
    candidate.append(os.path.join(HOME, ".config", "Claude", "logs"))
    return candidate


APP_LOG_DIRS = _cartelle_log_app()


def _altre_cartelle_progetti():
    """Altri alberi di transcript oltre a ~/.claude/projects.

    L'applicazione Claude, quando lavora in "local agent mode", da' a ogni
    sessione una home tutta sua e ci scrive dentro un albero .claude/projects
    completo:

        <app>/local-agent-mode-sessions/<account>/<org>/local_<id>/.claude/projects/...

    Sono sessioni vere con consumi veri, semplicemente in un posto diverso.
    Il livello variabile e' triplo, da qui i tre "*" nel pattern.

    [EN] Other transcript trees besides ~/.claude/projects.

    The Claude application, when working in "local agent mode", gives
    every session a home of its own and writes a full .claude/projects
    tree inside it:

        <app>/local-agent-mode-sessions/<account>/<org>/local_<id>/.claude/projects/...

    These are real sessions with real usage, simply in a different
    place. The variable level is threefold, hence the three "*" in the
    pattern.
    """
    radici = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        radici.append(os.path.join(appdata, "Claude"))
    radici.append(os.path.join(HOME, "Library", "Application Support", "Claude"))
    radici.append(os.path.join(HOME, ".config", "Claude"))

    trovate = []
    for radice in radici:
        pattern = os.path.join(radice, "local-agent-mode-sessions",
                               "*", "*", "*", ".claude", "projects")
        try:
            trovate.extend(d for d in glob.glob(pattern) if os.path.isdir(d))
        except OSError:
            continue
    return trovate


PROJECT_DIRS_EXTRA = _altre_cartelle_progetti()
